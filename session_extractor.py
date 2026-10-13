"""
session_extractor.py — 从 annotated JSONL 抽出"实际做了什么"

输出 actual.json:
  {
    "session_id": "...",
    "timeline": [
      {"line": 40, "type": "skill_call", "skill": "aid-planning", "is_sub_skill": false},
      {"line": 54, "type": "skill_call", "skill": "rq-parse", "is_sub_skill": true, "parent": "aid-planning"},
      ...
      {"line": 216, "type": "product_write", "skill": "aid-applying", "section": "step3-2",
       "file": "PlotUtils.test.ets", "evidence": "按 tasks.md 测试代码"},
      ...
    ],
    "skill_runs": {
      "aid-planning": {"line_range": [40, 53], "sub_skills_called": ["rq-parse", "rq-clarify", ...]},
      ...
    },
    "products": [
      {"file": "proposal.md", "line": 65, "skill": "aid-planning"},
      ...
    ]
  }

与 skill_expected.json(预期)对比即可:
  - expected 有但 actual 没 → MISSING
  - actual 有但 expected 没 → EXTRA
  - 顺序对不上 → OUT-OF-ORDER
"""
import json
import re
from pathlib import Path
from collections import defaultdict


# 产物文件 → 反推 step 的映射
PRODUCT_TO_SECTION = {
    # aid-applying
    "apply-report.md": ("aid-applying", "step3-4", "产出应用报告"),
    "tests/PlotUtils.test.mjs": ("aid-applying", "step3-2", "TDD Node mock 测试"),
    "PlotUtils.test.ets": ("aid-applying", "step3-2", "TDD ETS 测试"),
    "PlotUtils.ets": ("aid-applying", "step3-2", "TDD 实现"),
    "GraphViewModel.ets": ("aid-applying", "step3-2", "TDD 实现"),
    "GraphPage.ets": ("aid-applying", "step3-2", "渲染页"),
    # aid-implementing
    "tasks.md": ("aid-implementing", "step2-3", "产出 tasks.md"),
    # aid-planning (and sub-skills)
    "proposal.md": ("aid-planning", "step2", "需求理解"),
    "delta-spec.md": ("aid-planning", "step4", "需求spec设计"),
    "info.md": ("aid-planning", "step5", "代码仓理解"),
    "delta-design.md": ("aid-planning", "step8", "组件设计"),
    "design-review.md": ("aid-planning", "step9", "设计审视"),
    "todo.md": ("aid-planning", "step1", "任务追踪"),
}

# Bash 命令 → 反推 step
BASH_PATTERN_TO_SECTION = [
    (re.compile(r"hvigorw\s+--version|node\s+--version|gradlew\s+--version"), ("aid-applying", "step3-0", "环境检查")),
    (re.compile(r"hdc\s+(?:list|tconn|shell|install|hilog|file|snapshot|screenshot)"), ("aid-applying", "step3-2-2b", "HarmonyOS UI 测试")),
    (re.compile(r"pytest|jest|npm\s+test|hvigorw\s+test|gradlew\s+test|mvn\s+test|cargo\s+test"), ("aid-applying", "step3-2-2", "运行测试")),
    (re.compile(r"git\s+(add|commit|push)"), (None, None, "git 操作")),  # 不反推 skill
    (re.compile(r"^mkdir|^cp\s|^rm\s"), (None, None, "文件操作")),  # 不反推
]

# 判断 sub-skill 调用(parent skill 还在 stack 里)
SUB_SKILL_PARENTS = {
    "rq-parse": "aid-planning",
    "rq-clarify": "aid-planning",
    "rq-codebase": "aid-planning",
    "mod-design": "aid-planning",
    "aid-implementing": "aid-planning",
    "aid-applying": "aid-implementing",
    "tdd-enforcer": "aid-applying",
    "harmonyos-ui-test": "aid-applying",
}


def extract_session(jsonl_path: Path) -> dict:
    """从 annotated JSONL 抽出实际执行轨迹"""
    timeline = []
    skill_stack = []  # 当前活跃 skill 栈
    skill_runs = {}  # skill → {line_range, sub_skills_called, products}
    products = []
    skill_calls_seq = []  # Skill tool_use 顺序
    bash_cmds = []  # 关键 Bash
    violations = []  # SKILL.md 违反

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            rec_type = rec.get("type")
            msg = rec.get("message", {})
            content = msg.get("content", []) if isinstance(msg.get("content"), list) else []

            # ===== 1. Skill tool_use 检测 =====
            for blk in content if isinstance(content, list) else []:
                if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                    continue
                if blk.get("name") == "Skill":
                    skill_name = blk.get("input", {}).get("skill", "?")
                    is_sub = bool(skill_stack) and skill_stack[-1] != skill_name
                    parent = skill_stack[-1] if skill_stack else None
                    entry = {
                        "line": line_no,
                        "type": "skill_call",
                        "skill": skill_name,
                        "is_sub_skill": is_sub,
                        "parent": parent,
                        "ts": rec.get("timestamp"),
                    }
                    timeline.append(entry)
                    skill_calls_seq.append((line_no, skill_name, is_sub, parent))

                    # 推入栈
                    skill_stack.append(skill_name)
                    # 记录 skill_run(注意:每次重入同一 skill 也开新 run)
                    if skill_name not in skill_runs:
                        skill_runs[skill_name] = {
                            "first_line": line_no,
                            "last_line": line_no,
                            "sub_skills_called": [],
                            "products": [],
                            "iron_laws_violated": [],
                        }
                    else:
                        skill_runs[skill_name]["last_line"] = line_no
                    # 关键修复:这个 sub_skill 是**整个祖先栈**的子 skill,不只是直接父
                    for ancestor in skill_stack[:-1]:  # 排除 self
                        if ancestor in skill_runs:
                            skill_runs[ancestor]["sub_skills_called"].append({
                                "sub_skill": skill_name,
                                "line": line_no,
                                "via": skill_stack[:-2] + [ancestor] if len(skill_stack) > 2 else [ancestor],
                            })
                elif blk.get("name") == "Write":
                    fp = blk.get("input", {}).get("file_path", "")
                    # 看是不是产物文件
                    for prod_pattern, (skill, sec, title) in PRODUCT_TO_SECTION.items():
                        if prod_pattern in fp:
                            parent = skill_stack[-1] if skill_stack else None
                            entry = {
                                "line": line_no,
                                "type": "product_write",
                                "skill": skill,
                                "section": sec,
                                "title": title,
                                "file": fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1],
                                "parent_skill": parent,
                            }
                            timeline.append(entry)
                            products.append({"file": fp, "line": line_no, "skill": skill, "section": sec})
                            if skill in skill_runs:
                                skill_runs[skill]["products"].append({"file": fp, "line": line_no, "section": sec})
                                skill_runs[skill]["last_line"] = line_no
                            break
                elif blk.get("name") == "Bash":
                    cmd = blk.get("input", {}).get("command", "")
                    for pat, (skill, sec, title) in BASH_PATTERN_TO_SECTION:
                        if pat.search(cmd):
                            if skill:  # 有关联 skill 才记
                                entry = {
                                    "line": line_no,
                                    "type": "bash_action",
                                    "skill": skill,
                                    "section": sec,
                                    "title": title,
                                    "command": cmd[:200],
                                }
                                timeline.append(entry)
                                bash_cmds.append((line_no, skill, sec, cmd))
                                # 更新 skill_run 的 last_line
                                if skill in skill_runs:
                                    skill_runs[skill]["last_line"] = line_no
                            break

            # ===== 2. Skill body injection (isMeta=true) 推 skill 上下文 =====
            if rec_type == "user" and rec.get("isMeta") and skill_stack:
                # SKILL.md 文档被注入,意味着这个 skill 真正开始执行
                # 已在 P0/P1 状态机中处理过,这里只需辅助
                pass

            # ===== 3. 段切换检测(从 thinking 或工具反推) =====
            section = rec.get("attributionSkillSection")
            skill = rec.get("attributionSkill")
            sub_skill = rec.get("attributionSubSkill")
            method = rec.get("attributionInferenceMethod")
            conf = rec.get("attributionInferenceConfidence", 0)

            # 只记录强信号(P0/P1/P2 + 高置信度)的段切换
            if skill and section and method in ("explicit-skill-call", "skill-body-injection", "step-literal-match"):
                # 检查是否是"新段"(相对于上一事件)
                pass  # 这里不强求,因为 timeline 已有 skill_call

            # ===== 4. Pop skill stack(当 tool_result 是 Skill 启动时) =====
            if rec_type == "user":
                tr = rec.get("toolUseResult")
                if isinstance(tr, dict) and "Launching skill:" in str(tr.get("stdout", "")):
                    # 弹栈
                    if skill_stack:
                        skill_stack.pop()

    # ===== 5. 计算每个 skill_run 的实际段(从 timeline 收集) =====
    for skill_name, info in skill_runs.items():
        # 收集所有 section 出现
        sections_seen = set()
        for entry in timeline:
            if entry.get("skill") == skill_name and "section" in entry:
                sections_seen.add(entry["section"])
        info["sections_executed"] = sorted(sections_seen)

    return {
        "session_id": jsonl_path.stem.replace(".annotated", ""),
        "total_events": len(timeline),
        "timeline": timeline,
        "skill_runs": skill_runs,
        "products": products,
        "skill_calls_sequence": skill_calls_seq,
        "bash_actions": bash_cmds,
    }


if __name__ == "__main__":
    import sys
    jsonl_path = Path(r"D:\huawei\my_sessions\sessions\claude-code\dev-01\_raw\D--huawei-Demo-worktrees-issue-26\2026-06-17\264c5a16-f4f1-48ff-9f40-d215e1cc2567.annotated.jsonl")
    out_path = Path(r"D:\huawei\Demo\session_actual.json")

    actual = extract_session(jsonl_path)
    out_path.write_text(json.dumps(actual, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {out_path}")
    print(f"     {actual['total_events']} timeline events")
    print()
    print("=== Skill 调用顺序 ===")
    for line, skill, is_sub, parent in actual["skill_calls_sequence"]:
        sub_marker = "  (sub)" if is_sub else "      "
        parent_str = f"[parent={parent}]" if parent else ""
        print(f"  line {line:3} {sub_marker} {skill:25} {parent_str}")

    print()
    print("=== 产物文件 ===")
    for p in actual["products"]:
        print(f"  line {p['line']:3} {p['skill']:20}:{p['section']:15} {p['file'].split('/')[-1]}")

    print()
    print("=== Skill Runs ===")
    for skill_name, info in actual["skill_runs"].items():
        subs = ", ".join(s["sub_skill"] for s in info["sub_skills_called"]) or "-"
        secs = ", ".join(info["sections_executed"]) or "-"
        prods = ", ".join(p["file"].split("/")[-1].split("\\")[-1] for p in info["products"]) or "-"
        print(f"  {skill_name:25} lines={info['first_line']}-{info['last_line']}")
        print(f"    sub-skills: {subs}")
        print(f"    sections: {secs}")
        print(f"    products: {prods}")