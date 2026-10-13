"""
annotate_skill_sections.py — Skill 段级埋点改造器

功能:读取 Claude Code 会话 JSONL,为每条事件推断它属于哪个 skill 的哪一段,
输出同结构的新 JSONL + 段级报告。

用法:
    python annotate_skill_sections.py <input.jsonl>
    python annotate_skill_sections.py <input.jsonl> --output-dir <dir>

设计原则:
- 复用:不重写 JSONL 解析,从 langfuse_upload.convert 和 trace_board_v2 借函数
- 不破坏:原 JSONL 不动,新文件带 .annotated.jsonl 后缀
- 幂等:已含 attributionSkillSection 的事件跳过
- 流式:边读边写,内存 < 50MB

输入字段约定(沿用 CC 原生 camelCase):
  attributionSkill          原字段
  attributionSkillSection   新字段,值如 "step3-2-2b"
  attributionSkillSectionTitle  新字段,段标题
  attributionInferenceConfidence  新字段,0.0~1.0
  attributionInferenceMethod  新字段,8 种 method 之一
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ─────────────────────────────── 工具:复用 trace_board_v2 ───────────────────────────────

def _safe_dict(v: Any) -> dict:
    """trace_board_v2 风格的 dict 安全取值"""
    return v if isinstance(v, dict) else {}


def extract_text(content: Any) -> str:
    """从 message.content 抽 text,支持 str / list[block]"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict) and blk.get("type") == "text":
                parts.append(blk.get("text", ""))
        return "\n".join(parts)
    return ""


def extract_thinking(content: Any) -> str:
    """从 message.content 抽 thinking"""
    if isinstance(content, list):
        parts = []
        for blk in content:
            if isinstance(blk, dict) and blk.get("type") == "thinking":
                parts.append(blk.get("thinking", ""))
        return "\n".join(parts)
    return ""


def extract_tool_uses(content: Any) -> list[dict]:
    """从 message.content 抽 tool_use 块"""
    if not isinstance(content, list):
        return []
    return [blk for blk in content if isinstance(blk, dict) and blk.get("type") == "tool_use"]


def extract_tool_results(content: Any) -> list[dict]:
    """从 message.content 抽 tool_result 块"""
    if not isinstance(content, list):
        return []
    return [blk for blk in content if isinstance(blk, dict) and blk.get("type") == "tool_result"]


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None


# ─────────────────────────────── 数据结构 ───────────────────────────────

@dataclass
class SectionState:
    skill: Optional[str] = None
    section_id: Optional[str] = None
    section_title: Optional[str] = None
    confidence: float = 0.0
    method: Optional[str] = None
    skill_call_index: int = 0  # 第几次 Skill tool_use
    last_event_ts: Optional[str] = None
    last_event_line: int = 0
    skill_body_seen_for_call: dict[int, bool] = field(default_factory=dict)
    section_history: list[tuple[int, str, str, float, str]] = field(default_factory=list)
    # 子 skill 上下文(在 aid-applying step3-2 / step3-2-2b 内隐式激活的子 skill)
    sub_skill: Optional[str] = None
    sub_skill_section: Optional[str] = None
    # 父→子 skill 调用转换 log:(line, parent_skill, child_skill)
    # 用这个在 stage3_transform 后处理时按 parent 聚合 sub_skills_invoked
    sub_skill_call_log: list[tuple[int, str, str]] = field(default_factory=list)


@dataclass
class AnnotationStats:
    total_events: int = 0
    annotated_events: int = 0
    explicit_skill_call: int = 0
    skill_body_injection: int = 0
    step_literal_match: int = 0
    section_keyword: int = 0
    iron_law: int = 0
    tool_pattern: int = 0
    time_gap: int = 0
    unknown: int = 0
    confidence_histogram: Counter = field(default_factory=Counter)
    skill_runs: dict[tuple[str, int], dict] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


# ─────────────────────────────── 信号匹配 ───────────────────────────────

def match_step_literal(thought: str, skill: str, dictionary: dict) -> Optional[tuple[str, str]]:
    """P2:thinking/text 中 step 字面量匹配(大小写不敏感)"""
    if not thought or not skill:
        return None
    skill_def = _safe_dict(dictionary.get("skills", {})).get(skill)
    if not skill_def:
        return None
    sections = skill_def.get("sections", [])
    candidates: list[tuple[int, str, str, list[str]]] = []
    for sec in sections:
        specificity = len(sec["section_id"]) + sum(len(p) for p in sec.get("step_patterns", []))
        candidates.append((specificity, sec["section_id"], sec["title"], sec.get("step_patterns", [])))
    candidates.sort(key=lambda x: x[0], reverse=True)
    for _spec, sec_id, title, patterns in candidates:
        for p in patterns:
            try:
                if re.search(p, thought, re.IGNORECASE):
                    return sec_id, title
            except re.error:
                continue
    return None


def match_section_keyword(thought: str, skill: str, dictionary: dict) -> Optional[tuple[str, str]]:
    """P3:段标题关键词命中(返回所有命中 section,按 hits 数排序)"""
    if not thought or not skill:
        return None
    skill_def = _safe_dict(dictionary.get("skills", {})).get(skill)
    if not skill_def:
        return None
    matches: list[tuple[str, str, int]] = []
    for sec in skill_def.get("sections", []):
        kws = sec.get("keywords", [])
        hits = sum(1 for kw in kws if kw and kw.lower() in thought.lower())
        if hits > 0:
            matches.append((sec["section_id"], sec["title"], hits))
    if not matches:
        return None
    # 取 hits 最多的
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches[0][0], matches[0][1]


def match_iron_law(thought: str, skill: str, dictionary: dict) -> Optional[tuple[str, str]]:
    """P4:铁律编号 / 强制工具调用模式"""
    if not thought or not skill:
        return None
    skill_def = _safe_dict(dictionary.get("skills", {})).get(skill)
    if not skill_def:
        return None
    for sec in skill_def.get("sections", []):
        for il in sec.get("iron_laws", []):
            if il and il in thought:
                return sec["section_id"], sec["title"]
    return None


def match_bash_pattern(command: str, skill: str, dictionary: dict) -> Optional[tuple[str, str]]:
    """P5:Bash 命令字符串模式"""
    if not command or not skill:
        return None
    skill_def = _safe_dict(dictionary.get("skills", {})).get(skill)
    if not skill_def:
        return None
    cmd_lower = command.lower()
    for sec in skill_def.get("sections", []):
        for pat in sec.get("tool_patterns", []):
            if pat and pat.lower() in cmd_lower:
                return sec["section_id"], sec["title"]
    return None


def get_bash_command(record: dict) -> Optional[str]:
    """从 assistant.tool_use 里抽 Bash 的 command 字段"""
    for tu in extract_tool_uses(_safe_dict(record.get("message", {})).get("content")):
        if tu.get("name") == "Bash":
            inp = _safe_dict(tu.get("input"))
            return inp.get("command")
    return None


# aid-applying 段 → 期望的子 skill 映射(基于 SKILL.md 强制调用规则)
# 注意:step3-2-1 段常合并到 step3-2,所以 step3-2 也包含 tdd-enforcer
EXPECTED_SUB_SKILLS = {
    "aid-applying": {
        "step3-2": ["tdd-enforcer"],
        "step3-2-1": ["tdd-enforcer"],
        "step3-2-2b": ["harmonyos-ui-test"],
    },
}


def infer_sub_skill(
    state: SectionState,
    record: dict,
    combined_text: str,
    bash_cmd: Optional[str],
    dictionary: dict,
) -> Optional[str]:
    """推断子 skill 上下文(基于父段 + 行为模式)

    触发条件:state.skill 是父 skill 且 state.section_id 在 EXPECTED_SUB_SKILLS 中
    行为匹配:子 skill 的 keywords 或 tool_patterns 命中
    """
    if not state.skill or not state.section_id:
        return None
    expected = EXPECTED_SUB_SKILLS.get(state.skill, {}).get(state.section_id, [])
    if not expected:
        return None
    text_lower = combined_text.lower() if combined_text else ""
    cmd_lower = (bash_cmd or "").lower()
    for sub_skill_name in expected:
        skill_def = _safe_dict(dictionary.get("skills", {})).get(sub_skill_name)
        if not skill_def:
            continue
        for sec in skill_def.get("sections", []):
            # keyword 命中
            kws = sec.get("keywords", [])
            if any((kw and kw.lower() in text_lower) for kw in kws):
                return f"{sub_skill_name}:{sec['section_id']}"
            # tool_pattern 命中
            for pat in sec.get("tool_patterns", []):
                if pat and pat.lower() in cmd_lower:
                    return f"{sub_skill_name}:{sec['section_id']}"
    return None


# 检查 SKILL.md 强制子 skill 调用规则是否被违反
SUB_SKILL_VIOLATIONS = {
    "aid-applying": {
        "step3-2": {
            "required": ["tdd-enforcer"],
            "rule": "SKILL.md step3-2-1:必须使用 skill('tdd-enforcer')(在 step3-2 范围内)",
        },
        "step3-2-1": {
            "required": ["tdd-enforcer"],
            "rule": "SKILL.md step3-2-1:必须使用 skill('tdd-enforcer')",
        },
        "step3-2-2b": {
            "required": ["harmonyos-ui-test"],
            "rule": "SKILL.md step3-2-2b:必须调用 skill('harmonyos-ui-test')",
        },
    },
}


# ─────────────────────────────── 段切换判定 ───────────────────────────────

def is_more_specific(new_sec: str, old_sec: str, skill: str, dictionary: dict) -> bool:
    """判断 new_sec 是否可作为当前段。
    规则:
    - 没有 old_sec:任何 new_sec 都可
    - new == old:不可(没意义)
    - new 比 old 更具体(更深的层级,如 step3-2-2b > step3-2):允许
    - new 和 old 同级:允许(段切换,只要 new 不是旧的就切)
    - new 比 old 更浅:不允许(违反单调性)
    """
    if not old_sec:
        return True
    if new_sec == old_sec:
        return False
    # 用 . 分层判断深度
    def depth(sec: str) -> int:
        return sec.count("-") + sec.count(".")
    new_d = depth(new_sec)
    old_d = depth(old_sec)
    if new_d > old_d:
        return True
    if new_d < old_d:
        return False
    # 同级:切换
    return True


# ─────────────────────────────── 核心:单事件推断 ───────────────────────────────

METHOD_COUNTER_ATTRS = {
    "explicit-skill-call": "explicit_skill_call",
    "skill-body-injection": "skill_body_injection",
    "step-literal-match": "step_literal_match",
    "section-keyword": "section_keyword",
    "iron-law": "iron_law",
    "tool-pattern": "tool_pattern",
    "time-gap": "time_gap",
}


def annotate_event(
    record: dict,
    state: SectionState,
    line_no: int,
    dictionary: dict,
) -> tuple[dict, SectionState, str]:
    """
    对单条事件做段级推断。返回 (新字段 dict, 更新后的 state, method 字符串)。
    method ∈ {explicit-skill-call, skill-body-injection, step-literal-match,
              section-keyword, iron-law, tool-pattern, time-gap, fallback}.
    """
    new_fields: dict[str, Any] = {}

    # ─── P0: Skill tool_use(最高优先级)───
    tool_uses = extract_tool_uses(_safe_dict(record.get("message", {})).get("content"))
    skill_tool = next((tu for tu in tool_uses if tu.get("name") == "Skill"), None)
    if skill_tool is not None:
        skill_name = _safe_dict(skill_tool.get("input")).get("skill")
        if skill_name:
            # 父→子 skill 切换记录:旧 skill 调用了新 skill 作为子 skill
            if state.skill and state.skill != skill_name:
                state.sub_skill_call_log.append((line_no, state.skill, skill_name))
            state.skill = skill_name
            state.section_id = "init"
            state.section_title = "skill 启动"
            state.confidence = 1.0
            state.method = "explicit-skill-call"
            state.skill_call_index += 1
            state.skill_body_seen_for_call[state.skill_call_index] = False
            new_fields["attributionSkill"] = skill_name
            new_fields["attributionSkillSection"] = "init"
            new_fields["attributionSkillSectionTitle"] = "skill 启动"
            new_fields["attributionInferenceConfidence"] = 1.0
            new_fields["attributionInferenceMethod"] = "explicit-skill-call"
            return new_fields, state, "explicit-skill-call"

    # ─── P1: isMeta=true 的 user 行(SKILL.md 注入)───
    if (
        record.get("isMeta") is True
        and _safe_dict(record.get("message", {})).get("role") == "user"
    ):
        if state.skill:
            state.skill_body_seen_for_call[state.skill_call_index] = True
            new_fields["attributionSkill"] = state.skill
            new_fields["attributionSkillSection"] = state.section_id or "body"
            new_fields["attributionSkillSectionTitle"] = state.section_title or "skill body 注入"
            new_fields["attributionInferenceConfidence"] = max(0.95, state.confidence)
            new_fields["attributionInferenceMethod"] = "skill-body-injection"
            # confidence 单调递增
            state.confidence = new_fields["attributionInferenceConfidence"]
            state.method = "skill-body-injection"
            return new_fields, state, "skill-body-injection"

    # 无 skill 上下文的事件:不强行赋值,fallback 沿用 state
    thought = extract_thinking(_safe_dict(record.get("message", {})).get("content"))
    text = extract_text(_safe_dict(record.get("message", {})).get("content"))
    combined = (thought + "\n" + text).strip()

    # ─── P2: step 字面量匹配 ───
    if combined and state.skill:
        step_match = match_step_literal(combined, state.skill, dictionary)
        if step_match:
            sec_id, title = step_match
            if is_more_specific(sec_id, state.section_id or "", state.skill, dictionary):
                state.section_id = sec_id
                state.section_title = title
                state.section_history.append((line_no, sec_id, title, 0.9, "step-literal-match"))
            new_fields["attributionSkill"] = state.skill
            new_fields["attributionSkillSection"] = state.section_id
            new_fields["attributionSkillSectionTitle"] = state.section_title
            new_fields["attributionInferenceConfidence"] = max(0.9, state.confidence)
            new_fields["attributionInferenceMethod"] = "step-literal-match"
            state.confidence = max(state.confidence, 0.9)
            state.method = "step-literal-match"
            return new_fields, state, "step-literal-match"

    # ─── P3: 段标题关键词 ───
    if combined and state.skill:
        kw_match = match_section_keyword(combined, state.skill, dictionary)
        if kw_match:
            sec_id, title = kw_match
            if is_more_specific(sec_id, state.section_id or "", state.skill, dictionary):
                state.section_id = sec_id
                state.section_title = title
                state.section_history.append((line_no, sec_id, title, 0.7, "section-keyword"))
            new_fields["attributionSkill"] = state.skill
            new_fields["attributionSkillSection"] = state.section_id
            new_fields["attributionSkillSectionTitle"] = state.section_title
            new_fields["attributionInferenceConfidence"] = max(0.7, state.confidence)
            new_fields["attributionInferenceMethod"] = "section-keyword"
            state.confidence = max(state.confidence, 0.7)
            state.method = "section-keyword"
            return new_fields, state, "section-keyword"

    # ─── P4: 铁律编号 / 强制模式 ───
    if combined and state.skill:
        iron_match = match_iron_law(combined, state.skill, dictionary)
        if iron_match:
            sec_id, title = iron_match
            new_fields["attributionSkill"] = state.skill
            new_fields["attributionSkillSection"] = sec_id
            new_fields["attributionSkillSectionTitle"] = title
            new_fields["attributionInferenceConfidence"] = max(0.5, state.confidence)
            new_fields["attributionInferenceMethod"] = "iron-law"
            state.confidence = max(state.confidence, 0.5)
            state.method = "iron-law"
            return new_fields, state, "iron-law"

    # ─── P5: Bash 命令字符串模式 ───
    if state.skill and record.get("type") == "assistant":
        cmd = get_bash_command(record)
        if cmd:
            bp_match = match_bash_pattern(cmd, state.skill, dictionary)
            if bp_match:
                sec_id, title = bp_match
                new_fields["attributionSkill"] = state.skill
                new_fields["attributionSkillSection"] = sec_id
                new_fields["attributionSkillSectionTitle"] = title
                new_fields["attributionInferenceConfidence"] = max(0.4, state.confidence)
                new_fields["attributionInferenceMethod"] = "tool-pattern"
                state.confidence = max(state.confidence, 0.4)
                state.method = "tool-pattern"
                return new_fields, state, "tool-pattern"

    # ─── P6: 时间间隔(60s+) ───
    cur_ts = record.get("timestamp")
    if cur_ts and state.last_event_ts and state.skill:
        prev_dt = parse_iso(state.last_event_ts)
        cur_dt = parse_iso(cur_ts)
        if prev_dt and cur_dt:
            gap = (cur_dt - prev_dt).total_seconds()
            if gap > 60:
                new_fields["attributionSkill"] = state.skill
                new_fields["attributionSkillSection"] = state.section_id
                new_fields["attributionSkillSectionTitle"] = state.section_title
                new_fields["attributionInferenceConfidence"] = max(0.3, state.confidence)
                new_fields["attributionInferenceMethod"] = "time-gap"
                state.confidence = max(state.confidence, 0.3)
                # P6 不覆盖 state.method(弱信号)
                return new_fields, state, "time-gap"

    # ─── fallback ───
    # 不继承上一个 method,fallback 事件明确标 "fallback"
    new_fields["attributionSkill"] = state.skill
    new_fields["attributionSkillSection"] = state.section_id
    new_fields["attributionSkillSectionTitle"] = state.section_title
    new_fields["attributionInferenceConfidence"] = state.confidence
    new_fields["attributionInferenceMethod"] = "fallback"
    return new_fields, state, "fallback"


# ─────────────────────────────── Stage 1-5 ───────────────────────────────

def stage1_load_and_backup(input_path: Path, backup_dir: Path) -> Path:
    """原文件复制到 backup_dir/.bak.<unix_ts>"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{input_path.stem}.bak.{int(time.time())}"
    shutil.copy2(input_path, backup_path)
    return backup_path


def stage2_load_dictionary(dict_path: Path) -> dict:
    with dict_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def stage3_transform(
    input_path: Path,
    output_path: Path,
    dictionary: dict,
    stats: AnnotationStats,
) -> SectionState:
    """行级 transform 引擎"""
    state = SectionState()
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    diagnostics: list[str] = []

    with input_path.open("r", encoding="utf-8") as src, tmp_path.open("w", encoding="utf-8") as dst:
        for line_no, raw_line in enumerate(src, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                diagnostics.append(f"line {line_no}: json error: {e.msg}")
                continue

            stats.total_events += 1

            # 幂等:已有 attributionSkillSection 就跳过推断
            if "attributionSkillSection" in record:
                # 仍要更新 state.method 以便后续事件 fallback 用
                state.last_event_ts = record.get("timestamp")
                state.last_event_line = line_no
                dst.write(json.dumps(record, ensure_ascii=False) + "\n")
                stats.annotated_events += 1
                continue

            new_fields, state, method = annotate_event(record, state, line_no, dictionary)
            # 子 skill 后处理(独立于主段信号)
            thought = extract_thinking(_safe_dict(record.get("message", {})).get("content"))
            text = extract_text(_safe_dict(record.get("message", {})).get("content"))
            combined = (thought + "\n" + text).strip()
            bash_cmd = get_bash_command(record)
            sub_skill = infer_sub_skill(state, record, combined, bash_cmd, dictionary)
            if sub_skill:
                new_fields["attributionSubSkill"] = sub_skill
                state.sub_skill = sub_skill
                state.sub_skill_section = sub_skill.split(":", 1)[1] if ":" in sub_skill else None
            record.update(new_fields)
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")
            state.last_event_ts = record.get("timestamp")
            state.last_event_line = line_no
            stats.annotated_events += 1
            counter_attr = METHOD_COUNTER_ATTRS.get(method)
            if counter_attr and hasattr(stats, counter_attr):
                setattr(stats, counter_attr, getattr(stats, counter_attr) + 1)
            else:
                stats.unknown += 1
            # counter 上 +1
            stats.confidence_histogram[round(new_fields.get("attributionInferenceConfidence", 0.0), 2)] += 1
            # skill_run 累积
            skill_key = (state.skill or "unknown", state.skill_call_index)
            if skill_key not in stats.skill_runs and state.skill:
                stats.skill_runs[skill_key] = {
                    "skill": state.skill,
                    "call_index": state.skill_call_index,
                    "first_line": line_no,
                    "last_line": line_no,
                    "sections_seen": set(),
                }
            if state.skill:
                stats.skill_runs[skill_key]["last_line"] = line_no
                sec_id = new_fields.get("attributionSkillSection")
                if sec_id:
                    stats.skill_runs[skill_key]["sections_seen"].add(sec_id)

    # 原子 rename
    tmp_path.replace(output_path)
    stats.diagnostics.extend(diagnostics)

    # ── 用 sub_skill_call_log 填充 per-skill-run 的 sub_skills_invoked ──
    # 关键修复:之前 state.invoked_sub_skills 在 skill 切换时残留,导致
    # rq-parse 继承了 aid-planning 的子 skill 列表。改用 transition log 精确归因
    for line, parent, child in state.sub_skill_call_log:
        # 找到 parent 的 skill_run(call_index 不重要,因为 aid-planning 只调一次)
        for (sname, _cid), run_info in stats.skill_runs.items():
            if sname == parent:
                run_info.setdefault("sub_skills_invoked", set()).add(child)

    # ── SKILL.md 强制子 skill 调用规则检查 ──
    for (skill_name, _), run_info in stats.skill_runs.items():
        rules = SUB_SKILL_VIOLATIONS.get(skill_name, {})
        for sec_id, rule_def in rules.items():
            if sec_id in run_info["sections_seen"]:
                required = rule_def["required"]
                invoked = run_info.get("sub_skills_invoked", set())
                missing = [r for r in required if r not in invoked]
                if missing:
                    stats.diagnostics.append(
                        f"SKILL.md 违反 @ {skill_name}:{sec_id} (lines {run_info['first_line']}-{run_info['last_line']}): "
                        f"必须调 {[m + '()' for m in missing]} 但实际未调. "
                        f"agent 把 {missing} 行为内联了 — 触发子 skill 上下文推断(attributionSubSkill)."
                    )

    return state


def stage4_report(
    stats: AnnotationStats,
    output_dir: Path,
    session_id: str,
    source_path: Path,
    annotated_path: Path,
) -> None:
    """写 .section_report.json 和 .spot_check.md"""
    # 序列化 skill_runs(set → list)
    skill_runs_serialized = []
    for k, v in stats.skill_runs.items():
        skill_runs_serialized.append({
            "skill": v["skill"],
            "call_index": v["call_index"],
            "line_range": [v["first_line"], v["last_line"]],
            "sections_detected": sorted(v["sections_seen"]),
            "sub_skills_invoked": sorted(v.get("sub_skills_invoked", set())),
        })

    method_dist = {
        "explicit-skill-call": stats.explicit_skill_call,
        "skill-body-injection": stats.skill_body_injection,
        "step-literal-match": stats.step_literal_match,
        "section-keyword": stats.section_keyword,
        "iron-law": stats.iron_law,
        "tool-pattern": stats.tool_pattern,
        "time-gap": stats.time_gap,
        "unknown": stats.unknown,
    }

    annotated_with_skill = sum(1 for v in stats.skill_runs.values())
    coverage = {
        "total_events": stats.total_events,
        "annotated_events": stats.annotated_events,
        "skill_attributed_runs": annotated_with_skill,
    }

    # 提取 SKILL.md 违反条目
    skill_md_violations = [d for d in stats.diagnostics if d.startswith("SKILL.md 违反")]
    other_diagnostics = [d for d in stats.diagnostics if not d.startswith("SKILL.md 违反")]

    report = {
        "session_id": session_id,
        "source_path": str(source_path),
        "annotated_path": str(annotated_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage": coverage,
        "method_distribution": method_dist,
        "confidence_histogram": dict(sorted(stats.confidence_histogram.items(), reverse=True)),
        "skill_runs": skill_runs_serialized,
        "skill_md_violations": skill_md_violations,
        "diagnostics": other_diagnostics,
    }
    report_path = output_dir / f"{session_id}.section_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[stage4] report written: {report_path}")


# ─────────────────────────────── 主入口 ───────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Annotate JSONL with skill section metadata")
    parser.add_argument("input", type=Path, help="input jsonl path")
    parser.add_argument("--output-dir", type=Path, default=None, help="output dir (default: sibling)")
    parser.add_argument("--backup-dir", type=Path, default=Path(r"D:\huawei\my_sessions\sessions\bin\backups"),
                        help="backup dir for original jsonl")
    parser.add_argument("--dictionary", type=Path, default=Path(__file__).parent / "skill_section_dictionary.json",
                        help="skill section dictionary")
    parser.add_argument("--dry-run", action="store_true", help="don't write output files")
    args = parser.parse_args(argv)

    input_path: Path = args.input.resolve()
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        return 1

    output_dir: Path = (args.output_dir or input_path.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir: Path = args.backup_dir.resolve()

    session_id = input_path.stem
    annotated_path = output_dir / f"{session_id}.annotated.jsonl"

    print(f"[main] input:  {input_path}")
    print(f"[main] output: {annotated_path}")
    print(f"[main] backup: {backup_dir}")
    print(f"[main] dict:   {args.dictionary}")

    # Stage 1: backup
    backup_path = stage1_load_and_backup(input_path, backup_dir)
    print(f"[stage1] backup: {backup_path}")

    # Stage 2: dictionary
    dictionary = stage2_load_dictionary(args.dictionary)
    skills_count = len(dictionary.get("skills", {}))
    print(f"[stage2] dictionary loaded: {skills_count} skills")

    # Stage 3: transform
    stats = AnnotationStats()
    if not args.dry_run:
        stage3_transform(input_path, annotated_path, dictionary, stats)
        print(f"[stage3] transform done: {stats.total_events} events, {stats.annotated_events} annotated")
    else:
        print("[stage3] dry-run: skipping transform")

    # Stage 4: report
    if not args.dry_run:
        stage4_report(stats, output_dir, session_id, input_path, annotated_path)

    # Stage 5: summary
    print()
    print("=" * 60)
    print(f"Total events:    {stats.total_events}")
    print(f"Annotated:       {stats.annotated_events}")
    print(f"Skill runs:      {len(stats.skill_runs)}")
    print(f"Method dist:     {dict((k, v) for k, v in [('P0', stats.explicit_skill_call), ('P1', stats.skill_body_injection), ('P2', stats.step_literal_match), ('P3', stats.section_keyword), ('P4', stats.iron_law), ('P5', stats.tool_pattern), ('P6', stats.time_gap), ('unknown', stats.unknown)] if v > 0)}")
    if stats.diagnostics:
        print(f"Diagnostics ({len(stats.diagnostics)}):")
        for d in stats.diagnostics[:10]:
            print(f"  - {d}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
