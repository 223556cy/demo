"""
diff_engine.py — 预期(expected) vs 实际(actual) diff

3 类不匹配:
  - MISSING:  expected 有但 actual 没做
  - EXTRA:    actual 做了但 expected 没要求
  - OUT-OF-ORDER: 顺序与预期不符

3 个比对维度:
  - skill-level: 调了哪些 skill / 漏了哪些 skill
  - section-level: 在 skill 内做了哪些 step / 漏了哪些 step
  - sub-skill-level: 是否调了 mandatory 子 skill
"""
import json
import sys
from pathlib import Path


def load_expected(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_actual(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def diff_skill_level(expected: dict, actual: dict) -> list:
    """skill 级别:expected 里有的 skill,实际是否调了?

    只算"可能相关"的 skill:被当前调用的 skill 的 sub_skills_required 引用、或在 aid-workflow 主链上"""
    diffs = []
    # 当前 session 调用的所有 skill + 它们的 sub_skills_required
    actual_skills_called = set(actual["skill_runs"].keys())
    relevant_skills = set()
    for skill in actual_skills_called:
        relevant_skills.add(skill)
        if skill in expected["skills"]:
            for ms in expected["skills"][skill].get("sub_skills_required", []):
                relevant_skills.add(ms["sub_skill"])

    # AID 主链(aid-planning, aid-implementing, aid-applying, aid-archiving, aid-init, aid-monitor)
    # 这些总是相关的
    AID_MAIN = {"aid-planning", "aid-implementing", "aid-applying", "aid-archiving", "aid-init", "aid-monitor"}
    relevant_skills |= AID_MAIN

    for skill in sorted(expected["skills"].keys() - actual_skills_called):
        if skill not in relevant_skills:
            continue
        skill_info = expected["skills"][skill]
        if skill_info["section_count"] > 0:
            diffs.append({
                "type": "MISSING_SKILL",
                "severity": "warn",
                "skill": skill,
                "detail": f"SKILL.md 定义且本任务相关,但 agent 没调({skill_info['section_count']} 段)",
            })

    for skill in sorted(actual_skills_called - expected["skills"].keys()):
        diffs.append({
            "type": "EXTRA_SKILL",
            "severity": "info",
            "skill": skill,
            "detail": "agent 调用了 SKILL.md 目录外的 skill",
        })
    return diffs


def diff_section_level(expected: dict, actual: dict) -> list:
    """段级别:对每个调用的 skill,看 expected 段是否都执行了"""
    diffs = []
    for skill, run_info in actual["skill_runs"].items():
        if skill not in expected["skills"]:
            continue
        exp = expected["skills"][skill]
        exp_sections = {s["id"] for s in exp["sections"] if s.get("mandatory")}
        actual_sections = set(run_info.get("sections_executed", []))

        # MISSING mandatory section
        missing = exp_sections - actual_sections
        for sec_id in sorted(missing):
            sec_info = next((s for s in exp["sections"] if s["id"] == sec_id), None)
            title = sec_info["title"] if sec_info else "?"
            diffs.append({
                "type": "MISSING_MANDATORY_SECTION",
                "severity": "warn" if sec_info and sec_info.get("mandatory") else "info",
                "skill": skill,
                "section": sec_id,
                "title": title,
                "detail": f"SKILL.md 强制要求该段,但 agent 未做",
            })
    return diffs


def diff_subskill_level(expected: dict, actual: dict) -> list:
    """mandatory 子 skill 检查 + behavior evidence fallback

    3 类合规判断:
    - explicit_call: agent 真的调了 Skill tool → 合规
    - inline_behavior: agent 没调 Skill 但 thinking/Bash 痕迹显示做了子 skill 的工作 → 半合规(in-line)
    - missing: 啥都没有 → 真违规
    """
    diffs = []
    # 行为指纹(关键词 + 命令)→ 子 skill
    BEHAVIOR_FINGERPRINTS = {
        "tdd-enforcer": {
            "thinking_kw": ["TDD", "RED", "GREEN", "REFACTOR", "Iron Law", "写失败测试", "测试失败", "测试通过"],
            "bash_kw": ["pytest", "jest", "node ", "mock_test", ".test.mjs", "npm test", "hvigorw test", "hvigorw assembleHap"],
            "min_thinking_hits": 2,
            "min_bash_hits": 2,  # node + test.mjs 都得有
        },
        "harmonyos-ui-test": {
            "thinking_kw": ["hdc", "uitest", "AVD", "真机", "模拟器", "harmonyos-ui-test"],
            "bash_kw": ["hdc list", "hdc tconn", "hdc shell", "hdc install", "hdc file", "hdc snapshot", "hdc screenshot", "screencap", "uitest", "dump_main"],
            "min_thinking_hits": 2,
            "min_bash_hits": 3,  # 6 阶段要求多个 hdc 命令
        },
    }

    # 收集所有 thinking / Bash 文本(按 skill 父级)
    annotated_path = Path(r"D:\huawei\my_sessions\sessions\claude-code\dev-01\_raw\D--huawei-Demo-worktrees-issue-26\2026-06-17\264c5a16-f4f1-48ff-9f40-d215e1cc2567.annotated.jsonl")
    skill_behaviors = {}  # skill_name → {thinking_text, bash_text}
    if annotated_path.exists():
        with annotated_path.open("r", encoding="utf-8") as f:
            current_skill = None
            for line in f:
                rec = json.loads(line)
                msg = rec.get("message", {})
                content = msg.get("content", []) if isinstance(msg.get("content"), list) else []

                # 更新当前 skill
                skill = rec.get("attributionSkill")
                if skill and skill != current_skill:
                    current_skill = skill
                    if current_skill not in skill_behaviors:
                        skill_behaviors[current_skill] = {"thinking": [], "bash": []}

                if current_skill and skill == current_skill:
                    for blk in content:
                        if not isinstance(blk, dict): continue
                        if blk.get("type") == "thinking":
                            skill_behaviors[current_skill]["thinking"].append(blk.get("thinking", ""))
                        elif blk.get("type") == "tool_use" and blk.get("name") == "Bash":
                            cmd = blk.get("input", {}).get("command", "")
                            skill_behaviors[current_skill]["bash"].append(cmd)

    for skill, run_info in actual["skill_runs"].items():
        if skill not in expected["skills"]:
            continue
        exp = expected["skills"][skill]
        mandatory_subs = exp.get("sub_skills_required", [])
        actual_subs = {s["sub_skill"] for s in run_info.get("sub_skills_called", [])}

        for ms in mandatory_subs:
            required_sub = ms["sub_skill"]
            parent_section = ms.get("parent_section", "?")
            if required_sub in actual_subs:
                continue  # 显式调了,合规

            # 没显式调,检查 behavior evidence
            evidence_status = "missing"
            evidence_detail = ""

            if required_sub in BEHAVIOR_FINGERPRINTS:
                fp = BEHAVIOR_FINGERPRINTS[required_sub]
                behaviors = skill_behaviors.get(skill, {"thinking": [], "bash": []})
                thinking_text = "\n".join(behaviors["thinking"]).lower()
                bash_text = "\n".join(behaviors["bash"]).lower()

                think_hits = sum(1 for kw in fp["thinking_kw"] if kw.lower() in thinking_text)
                bash_hits = sum(1 for kw in fp["bash_kw"] if kw.lower() in bash_text)

                if think_hits >= fp["min_thinking_hits"] and bash_hits >= fp["min_bash_hits"]:
                    evidence_status = "inline_behavior"
                    evidence_detail = f"(thinking 命中 {think_hits} 个关键词,Bash 命中 {bash_hits} 个模式 — agent 内联了行为但没走 Skill 流程)"
                elif think_hits > 0 or bash_hits > 0:
                    evidence_status = "partial_behavior"
                    evidence_detail = f"(thinking 命中 {think_hits},Bash 命中 {bash_hits} — 部分做了但不全)"
                else:
                    evidence_status = "missing"
                    evidence_detail = "(thinking + Bash 均无相关痕迹)"

            if evidence_status == "inline_behavior":
                diffs.append({
                    "type": "MISSING_MANDATORY_SUBSKILL_INLINE",
                    "severity": "info",  # 降为 info,agent 做了工作
                    "skill": skill,
                    "parent_section": parent_section,
                    "sub_skill": required_sub,
                    "detail": f"SKILL.md 要求 {skill}:{parent_section} 必须调 skill('{required_sub}'),agent 没调 Skill tool,但行为痕迹显示 agent 内联了 {required_sub} 的工作{evidence_detail}",
                })
            elif evidence_status == "partial_behavior":
                diffs.append({
                    "type": "MISSING_MANDATORY_SUBSKILL_PARTIAL",
                    "severity": "warn",
                    "skill": skill,
                    "parent_section": parent_section,
                    "sub_skill": required_sub,
                    "detail": f"SKILL.md 要求 {skill}:{parent_section} 必须调 skill('{required_sub}'),agent 没调 Skill tool,行为痕迹部分{evidence_detail}",
                })
            else:
                diffs.append({
                    "type": "MISSING_MANDATORY_SUBSKILL",
                    "severity": "warn",
                    "skill": skill,
                    "parent_section": parent_section,
                    "sub_skill": required_sub,
                    "detail": f"SKILL.md 要求 {skill}:{parent_section} 必须调 skill('{required_sub}'),agent 没调{evidence_detail}",
                })
    return diffs


def diff_product_level(expected: dict, actual: dict) -> list:
    """产物文件检查:SKILL.md expected_products vs actual products"""
    diffs = []
    actual_files = {p["file"].split("/")[-1].split("\\")[-1] for p in actual["products"]}

    for skill, run_info in actual["skill_runs"].items():
        if skill not in expected["skills"]:
            continue
        exp = expected["skills"][skill]
        exp_products = exp.get("expected_products", [])
        # 模板文件白名单 — 这些从 templates/ 目录 copy,不视作硬要求
        TEMPLATE_FILES = ("-template.md", "package.json", "capabilities.json", "settings.json", "tsconfig.json")
        # 条件性产出文件 — 只在特定场景(如架构变更)才产出
        CONDITIONAL_FILES = {"new-arch.md", "design.md", "info.md"}
        for ep in exp_products:
            fn = ep["file"]
            if any(fn.endswith(t) for t in TEMPLATE_FILES):
                continue
            if fn in CONDITIONAL_FILES:
                continue
            if fn not in actual_files:
                # 找最相近的产物文件(可能改了大小写/路径)
                similar = next((f for f in actual_files if fn.lower() in f.lower() or f.lower() in fn.lower()), None)
                if similar:
                    continue  # 模糊匹配到了
                diffs.append({
                    "type": "MISSING_PRODUCT",
                    "severity": "warn",
                    "skill": skill,
                    "file": fn,
                    "evidence": ep.get("evidence", "?"),
                    "detail": f"SKILL.md 提到应产出 {fn}({ep.get('evidence', '?')}),但 session 未产出",
                })

    # 反向:实际产出了但 SKILL.md 没要求的(可能多余)
    # 白名单:明显是代码产物的文件类型,SKILL.md 不需要逐一列出
    CODE_FILE_EXTENSIONS = (".ets", ".ts", ".js", ".mjs", ".cjs", ".cpp", ".h", ".hpp", ".kt", ".swift", ".dart", ".java", ".py")
    # todo.md 是任务追踪(每个 skill 都要更新),不是产出物
    TASK_TRACKER_FILES = {"todo.md"}
    for p in actual["products"]:
        fn = p["file"].split("/")[-1].split("\\")[-1]
        if fn.startswith(".") or fn.endswith((".bak",)):
            continue
        if fn in TASK_TRACKER_FILES:
            continue
        if fn.endswith(CODE_FILE_EXTENSIONS):
            continue  # 代码文件是默认产物,SKILL.md 不需要列
        # 找对应 skill 的 expected_products
        skill = p.get("skill", "?")
        exp = expected["skills"].get(skill, {})
        exp_files = {e["file"] for e in exp.get("expected_products", [])}
        if skill in expected["skills"] and fn not in exp_files:
            # 模糊匹配
            similar = next((e for e in exp_files if fn.lower() in e.lower() or e.lower() in fn.lower()), None)
            if similar:
                continue
            diffs.append({
                "type": "EXTRA_PRODUCT",
                "severity": "info",
                "skill": skill,
                "file": fn,
                "detail": f"agent 产出了 {fn},但 SKILL.md 未要求(可能 agent 自加产物,如测试辅助文件)",
            })
    return diffs


def compute_diff(expected: dict, actual: dict) -> dict:
    """综合 diff"""
    all_diffs = []
    all_diffs.extend(diff_skill_level(expected, actual))
    all_diffs.extend(diff_section_level(expected, actual))
    all_diffs.extend(diff_subskill_level(expected, actual))
    all_diffs.extend(diff_product_level(expected, actual))

    # 统计
    severity_counter = {"warn": 0, "info": 0}
    type_counter = {}
    for d in all_diffs:
        severity_counter[d["severity"]] = severity_counter.get(d["severity"], 0) + 1
        type_counter[d["type"]] = type_counter.get(d["type"], 0) + 1

    return {
        "session_id": actual["session_id"],
        "total_diffs": len(all_diffs),
        "severity_summary": severity_counter,
        "type_summary": type_counter,
        "diffs": all_diffs,
    }


if __name__ == "__main__":
    expected = load_expected(Path(r"D:\huawei\Demo\skill_expected.json"))
    actual = load_actual(Path(r"D:\huawei\Demo\session_actual.json"))

    diff = compute_diff(expected, actual)
    out_path = Path(r"D:\huawei\Demo\skill_diff.json")
    out_path.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {out_path}")
    print()
    print(f"=== Diff 结果 ===")
    print(f"总差异: {diff['total_diffs']}")
    print(f"  warn: {diff['severity_summary'].get('warn', 0)}")
    print(f"  info: {diff['severity_summary'].get('info', 0)}")
    print()
    print("按类型:")
    for t, c in sorted(diff["type_summary"].items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print()
    print("=== 详情(按严重度排序) ===")
    sorted_diffs = sorted(diff["diffs"], key=lambda d: (0 if d["severity"] == "warn" else 1))
    for d in sorted_diffs:
        sev_marker = "⚠️" if d["severity"] == "warn" else "ℹ️"
        print(f"  {sev_marker} [{d['type']}] {d.get('skill', '?')} " + (
            f"/{d.get('section', '?')}" if 'section' in d else ""
        ) + f" — {d['detail']}")