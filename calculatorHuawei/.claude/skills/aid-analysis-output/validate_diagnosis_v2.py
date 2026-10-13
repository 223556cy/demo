#!/usr/bin/env python3
"""
validate_diagnosis_v2.py — 校验 analysis 6-skill pipeline 最终输出

校验目标: .claude/analysis-logs/<YYYY-MM-DD>/issue-<N>-diagnosis.json
校验对象: issue_ticket JSON 字段
校验依据: aid-analysis-output/SKILL.md v2.1 规范的 5 条铁律 + aid-analysis-root-cause/SKILL.md 的 19 条铁律

退出码:
  0 = 通过
  1 = 校验失败(具体失败原因在 stderr)
  2 = 文件读取/解析错误

用法:
  python validate_diagnosis_v2.py <path-to-diagnosis.json>
  python validate_diagnosis_v2.py <path-to-diagnosis.json> --verbose
"""
import json
import sys
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


# 候选 skill 花名册(从 aid-analysis-root-cause/SKILL.md C-0 段)
TARGET_SKILL_ROSTER = {
    "aid-planning", "aid-implementing", "aid-applying", "tdd-enforcer",
    "rq-parse", "rq-clarify", "rq-codebase",
    "mod-design", "aid-init", "aid-archiving", "aid-monitor", "aid-reviewing",
    "dfr-fmea-harmony", "harmonyos-ui-test", "prd-generator",
}

# problem_signature 10 选 1(从 references/signature-library.md)
SIGNATURE_ROSTER = {
    "multi-step-skip", "equiv-class-insufficient", "env-probe-incomplete",
    "forbidden-block-bypassed", "cross-stage-contract-leak",
    "silent-production-failure", "multi-bug-discovered",
    "default-value-trap", "runtime-only-bug", "closed-loop-verified",
}

# defect_dimension 5 选 1
DEFECT_DIMENSION_ROSTER = {
    "planning-stage", "implementing-stage", "applying-stage",
    "archiving-stage", "cross-stage",
}

# discovery_timing 5 选 1
DISCOVERY_TIMING_ROSTER = {
    "review", "integration", "production", "self-found", "regression",
}

# fix_path 3 选 1
FIX_PATH_ROSTER = {"modify-existing", "create-new", "N/A"}


class ValidationError:
    """校验错误记录"""
    def __init__(self, rule_id: str, severity: str, message: str):
        self.rule_id = rule_id  # 铁律编号,如 "#11" 或 "P0-1"
        self.severity = severity  # "ERROR" | "WARN"
        self.message = message

    def __str__(self):
        return f"[{self.severity}][{self.rule_id}] {self.message}"


def check_iron_law_1(ticket: Dict) -> List[ValidationError]:
    """铁律 #1: target_skill_filename 必填且是花名册成员"""
    errors = []
    target = ticket.get("target_skill_filename")
    if not target:
        errors.append(ValidationError("#1", "ERROR", "target_skill_filename 字段缺失"))
        return errors
    if target == "N/A":
        return errors  # D 类外部因素允许 N/A
    if target not in TARGET_SKILL_ROSTER:
        errors.append(ValidationError(
            "#1", "ERROR",
            f"target_skill_filename='{target}' 不在花名册中(必须从 15 个 skill 中选,或填 N/A)"
        ))
    return errors


def check_iron_law_2(ticket: Dict) -> List[ValidationError]:
    """铁律 #2: D 类 → target_skill_filename='N/A' + target_skill_section/line_range 也 N/A"""
    errors = []
    target = ticket.get("target_skill_filename", "")
    if target == "N/A":
        for f in ("target_skill_section", "target_line_range"):
            v = ticket.get(f)
            if v and v != "N/A":
                errors.append(ValidationError(
                    "#2", "ERROR",
                    f"D 类外部因素要求 {f}='N/A', 但实际='{v}'"
                ))
    return errors


def check_iron_law_3(ticket: Dict) -> List[ValidationError]:
    """铁律 #3: 13 个 v2.0 必填字段不允许缺失"""
    errors = []
    required = [
        "target_skill_section", "target_line_range", "additional_root_causes",
        "exhaustion_check", "runtime_evidence", "zero_states_checked",
        "fix_coverage_matrix", "defect_dimension", "discovery_timing",
        "reasoning_method", "problem_signature", "evidence_strength",
        "alternative_branches_excluded",
    ]
    for f in required:
        if f not in ticket:
            errors.append(ValidationError(
                "#3", "ERROR",
                f"v2.0 必填字段 '{f}' 缺失"
            ))
    return errors


def check_iron_law_4(ticket: Dict) -> List[ValidationError]:
    """铁律 #4: optimization_direction 必填(兼容空 dict 表示 N/A)"""
    # 铁律 #11 在 check_iron_law_11 中独立校验
    return []


def check_iron_law_5(ticket: Dict) -> List[ValidationError]:
    """铁律 #5: 逻辑链 — root_cause_analysis 必须能拆出 fact→fact→推断→L3 箭头链"""
    errors = []
    chain = ticket.get("root_cause_analysis", "")
    if not chain:
        errors.append(ValidationError("#5", "ERROR", "root_cause_analysis 字段缺失"))
        return errors
    # 至少 2 个箭头
    arrow_count = chain.count("→")
    if arrow_count < 2:
        errors.append(ValidationError(
            "#5", "ERROR",
            f"root_cause_analysis 箭头数 < 2(实际 {arrow_count}), 链条不成立"
        ))
    return errors


def check_iron_law_6(ticket: Dict) -> List[ValidationError]:
    """铁律 #6: 通用性 — C-1 三问都"否"才允许归 D 类(本铁律靠字段值校验而非内容)"""
    # 此铁律校验需要 C-1 三问的实际回答(在 analysis 阶段产出),这里不强制
    return []


def check_iron_law_7(ticket: Dict) -> List[ValidationError]:
    """铁律 #7: 证据 — 每个 fact 必须有 [源]L# 行号引用"""
    errors = []
    chain = ticket.get("root_cause_analysis", "")
    if not chain:
        return errors
    # 检查 [xxx#L#] 或 [xxx L#] 或 commit hash 引用
    has_evidence = bool(re.search(r"\[[^\]]*L\d+|commit\s+[0-9a-f]{7,}|jsonl#", chain))
    if not has_evidence:
        errors.append(ValidationError(
            "#7", "ERROR",
            "root_cause_analysis 中未发现证据引用([xxx#L#] / commit hash / jsonl#)"
        ))
    return errors


def check_iron_law_8(ticket: Dict) -> List[ValidationError]:
    """铁律 #8: 精确定位 — target_skill_section + target_line_range 必须真实存在(N/A 除外)"""
    # 实际验证需要 Read SKILL.md 文件,这里只做格式校验
    errors = []
    target = ticket.get("target_skill_filename", "")
    if target == "N/A":
        return errors
    section = ticket.get("target_skill_section", "")
    line_range = ticket.get("target_line_range", "")
    if not section or section == "N/A":
        errors.append(ValidationError("#8", "ERROR", "target_skill_section 不能为空"))
    if not line_range or line_range == "N/A":
        errors.append(ValidationError("#8", "ERROR", "target_line_range 不能为空"))
    # line_range 格式校验 L100-L130
    if line_range and line_range != "N/A":
        if not re.match(r"^L\d+(-L\d+)?$", line_range):
            errors.append(ValidationError(
                "#8", "WARN",
                f"target_line_range='{line_range}' 格式异常(期望 L100 或 L100-L130)"
            ))
    return errors


def check_iron_law_9(ticket: Dict) -> List[ValidationError]:
    """铁律 #9: 证据强度 — evidence_strength 覆盖所有 anchors; speculated 不准作为 L3 唯一支撑"""
    errors = []
    es = ticket.get("evidence_strength", {})
    if not isinstance(es, dict):
        errors.append(ValidationError("#9", "ERROR", "evidence_strength 必须是 dict"))
        return errors
    # 警告:如果所有 evidence_strength 都是 speculated
    if es and all(v == "speculated" for v in es.values()):
        errors.append(ValidationError(
            "#9", "ERROR",
            "所有 evidence_strength 都是 'speculated', L3 不允许以 speculated 为唯一支撑"
        ))
    return errors


def check_iron_law_10(ticket: Dict) -> List[ValidationError]:
    """铁律 #10: 备选链 — alternative_branches_excluded 至少 1 条"""
    errors = []
    ab = ticket.get("alternative_branches_excluded", [])
    if not isinstance(ab, list):
        errors.append(ValidationError("#10", "ERROR", "alternative_branches_excluded 必须是 array"))
        return errors
    if len(ab) < 1:
        errors.append(ValidationError(
            "#10", "ERROR",
            "alternative_branches_excluded 至少 1 条(单链 = 推理脆弱)"
        ))
    return errors


def check_iron_law_11(ticket: Dict) -> List[ValidationError]:
    """铁律 #11: 结构化修复 — optimization_direction 必须是 6 字段 dict(不是 str)"""
    errors = []
    od = ticket.get("optimization_direction")
    if od is None:
        errors.append(ValidationError("#11", "ERROR", "optimization_direction 字段缺失"))
        return errors
    if not isinstance(od, dict):
        errors.append(ValidationError(
            "#11", "ERROR",
            f"optimization_direction 必须是 dict(6 字段), 实际类型={type(od).__name__}"
        ))
        return errors
    required_fields = [
        "fix_action", "fix_rationale", "future_scenarios_covered",
        "related_skills_to_sync", "acceptance_criteria", "revert_plan",
    ]
    for f in required_fields:
        if f not in od:
            errors.append(ValidationError(
                "#11", "ERROR",
                f"optimization_direction 缺 6 字段之一: '{f}'"
            ))
    # fix_action 不能空
    if od.get("fix_action") in (None, "", "N/A"):
        # D 类允许 N/A
        if ticket.get("target_skill_filename") != "N/A":
            errors.append(ValidationError(
                "#11", "ERROR",
                "fix_action 不允许为空(非 D 类时)"
            ))
    return errors


def check_iron_law_12(ticket: Dict) -> List[ValidationError]:
    """铁律 #12: 多维度分类 — defect_dimension + discovery_timing + reasoning_method + problem_signature 4 字段必填"""
    errors = []
    dd = ticket.get("defect_dimension")
    if dd and dd not in DEFECT_DIMENSION_ROSTER:
        errors.append(ValidationError(
            "#12", "ERROR",
            f"defect_dimension='{dd}' 不在枚举中(必须从 5 类中选)"
        ))
    dt = ticket.get("discovery_timing")
    if dt and dt not in DISCOVERY_TIMING_ROSTER:
        errors.append(ValidationError(
            "#12", "ERROR",
            f"discovery_timing='{dt}' 不在枚举中(必须从 5 类中选)"
        ))
    rm = ticket.get("reasoning_method")
    if rm and (not isinstance(rm, list) or len(rm) < 1):
        errors.append(ValidationError(
            "#12", "ERROR",
            "reasoning_method 必须是非空 array(primary + secondary)"
        ))
    ps = ticket.get("problem_signature")
    if ps and ps not in SIGNATURE_ROSTER:
        errors.append(ValidationError(
            "#12", "ERROR",
            f"problem_signature='{ps}' 不在 10 签名库中"
        ))
    return errors


def check_iron_law_13(ticket: Dict) -> List[ValidationError]:
    """铁律 #13: 多源证据 — B-1 必须覆盖 ≥ 2 类来源(在根因层由 SKILL.md 强制,本校验器粗略检查)"""
    # 校验 evidence_anchors 至少有 2 个不同来源
    anchors = ticket.get("evidence_anchors", [])
    if isinstance(anchors, list) and len(anchors) < 2:
        return [ValidationError(
            "#13", "WARN",
            f"evidence_anchors 数量 < 2(实际 {len(anchors)}), B-1 多源证据要求覆盖 ≥ 2 类"
        )]
    return []


def check_iron_law_14(ticket: Dict) -> List[ValidationError]:
    """铁律 #14: 因果机制 — root_cause_analysis 必须含 ≥ 1 个 [机制: ...] 标记"""
    errors = []
    chain = ticket.get("root_cause_analysis", "")
    if not chain:
        return errors
    if "[机制:" not in chain and "[机制：" not in chain:
        errors.append(ValidationError(
            "#14", "ERROR",
            "root_cause_analysis 必须含 ≥ 1 个 [机制: ...] 标记"
        ))
    return errors


def check_iron_law_15(ticket: Dict) -> List[ValidationError]:
    """铁律 #15: 运行时证据 — 行为类 bug 必须有 runtime_evidence ≥ 1 条"""
    errors = []
    re_list = ticket.get("runtime_evidence", [])
    if not isinstance(re_list, list):
        errors.append(ValidationError("#15", "ERROR", "runtime_evidence 必须是 array"))
        return errors
    # 状态机切换/竞态/跨进程/计算偏差/UI 渲染 这几类 bug 必须有 runtime evidence
    # 简化判断:如果 problem_signature 是 runtime-only-bug / multi-bug-discovered 必须有 ≥ 1
    ps = ticket.get("problem_signature", "")
    if ps in ("runtime-only-bug", "multi-bug-discovered", "silent-production-failure"):
        if len(re_list) < 1:
            errors.append(ValidationError(
                "#15", "WARN",
                f"problem_signature='{ps}' 通常需要 runtime_evidence,但当前为空"
            ))
    return errors


def check_iron_law_16(ticket: Dict) -> List[ValidationError]:
    """铁律 #16: 零状态穷尽 — zero_states_checked 必须 ≥ 3 条"""
    errors = []
    zs = ticket.get("zero_states_checked", [])
    if not isinstance(zs, list):
        errors.append(ValidationError("#16", "ERROR", "zero_states_checked 必须是 array"))
        return errors
    if len(zs) < 3:
        errors.append(ValidationError(
            "#16", "ERROR",
            f"zero_states_checked 必须 ≥ 3 条(zero-data/default-config/cold-start), 实际 {len(zs)}"
        ))
    return errors


def check_iron_law_17(ticket: Dict) -> List[ValidationError]:
    """铁律 #17: 多 bug 穷尽 — multi_bug_confirmed=true 时 additional_root_causes 必须非空"""
    errors = []
    ec = ticket.get("exhaustion_check", {})
    if isinstance(ec, dict) and ec.get("multi_bug_confirmed") is True:
        arc = ticket.get("additional_root_causes", [])
        if not isinstance(arc, list) or len(arc) < 1:
            errors.append(ValidationError(
                "#17", "ERROR",
                "exhaustion_check.multi_bug_confirmed=true 但 additional_root_causes 为空"
            ))
    return errors


def check_iron_law_18(ticket: Dict) -> List[ValidationError]:
    """铁律 #18: 修复覆盖闭环 — fix_coverage_matrix 覆盖主链 L3 + 所有 additional L3"""
    errors = []
    fcm = ticket.get("fix_coverage_matrix", [])
    if not isinstance(fcm, list):
        errors.append(ValidationError("#18", "ERROR", "fix_coverage_matrix 必须是 array"))
        return errors
    # 主链 L3 的 anchor id 必有一行(用 L3-1 或 L3-main 标记)
    main_ids = {row.get("l3_anchor_id") for row in fcm if isinstance(row, dict)}
    arc = ticket.get("additional_root_causes", [])
    if isinstance(arc, list):
        for arc_item in arc:
            if isinstance(arc_item, dict) and arc_item.get("l3_anchor_id"):
                if arc_item["l3_anchor_id"] not in main_ids:
                    errors.append(ValidationError(
                        "#18", "ERROR",
                        f"additional_root_causes 中 '{arc_item['l3_anchor_id']}' 在 fix_coverage_matrix 无对应行"
                    ))
    # 任一行 covered=false 报错
    for row in fcm:
        if isinstance(row, dict) and row.get("covered") is False:
            cb = row.get("covered_by", "")
            if not (isinstance(cb, str) and cb.startswith("N/A")):
                errors.append(ValidationError(
                    "#18", "ERROR",
                    f"fix_coverage_matrix 行 l3_anchor_id='{row.get('l3_anchor_id')}' covered=false 但 covered_by 未说明 N/A 原因"
                ))
    return errors


def check_iron_law_19(ticket: Dict) -> List[ValidationError]:
    """铁律 #19: 修复路径 — fix_path 必填 3 选 1; create-new 时 proposed_skill_name + purpose 必填"""
    errors = []
    fp = ticket.get("fix_path")
    if fp not in FIX_PATH_ROSTER:
        errors.append(ValidationError(
            "#19", "ERROR",
            f"fix_path='{fp}' 不在 3 选 1 枚举(modify-existing/create-new/N/A)"
        ))
        return errors
    if fp == "create-new":
        name = ticket.get("proposed_skill_name")
        purpose = ticket.get("proposed_skill_purpose")
        if not name:
            errors.append(ValidationError(
                "#19", "ERROR",
                "fix_path=create-new 时 proposed_skill_name 必填"
            ))
        elif not re.match(r"^[a-z0-9-]+$", name):
            errors.append(ValidationError(
                "#19", "ERROR",
                f"proposed_skill_name='{name}' 含非法字符(只允许小写字母数字和连字符)"
            ))
        if not purpose:
            errors.append(ValidationError("#19", "ERROR", "fix_path=create-new 时 proposed_skill_purpose 必填"))
    return errors


def check_v2_1_extension(ticket: Dict) -> List[ValidationError]:
    """铁律 #20: 7 个 v2.1 扩展字段键必须存在(允许空值/空数组/null)"""
    errors = []
    required = [
        "error_log_paths", "error_summary", "log_anchors",
        "spec_to_code_mapping", "bug_location", "fix_path",
        "proposed_skill_name",  # 已在 #19 校验,这里只检查键存在
    ]
    for f in required:
        if f not in ticket:
            errors.append(ValidationError("#20", "ERROR", f"v2.1 扩展字段 '{f}' 键缺失"))
    return errors


# 校验器注册表
IRON_LAW_CHECKS = [
    ("#1 target_skill_filename", check_iron_law_1),
    ("#2 D 类字段", check_iron_law_2),
    ("#3 13 必填字段", check_iron_law_3),
    ("#4 optimization_direction 必填(占位)", check_iron_law_4),
    ("#5 逻辑链箭头", check_iron_law_5),
    ("#6 通用性(C-1 答在 analysis 阶段)", check_iron_law_6),
    ("#7 证据引用", check_iron_law_7),
    ("#8 精确定位", check_iron_law_8),
    ("#9 证据强度", check_iron_law_9),
    ("#10 备选链", check_iron_law_10),
    ("#11 结构化修复", check_iron_law_11),
    ("#12 多维度分类", check_iron_law_12),
    ("#13 多源证据", check_iron_law_13),
    ("#14 因果机制", check_iron_law_14),
    ("#15 运行时证据", check_iron_law_15),
    ("#16 零状态", check_iron_law_16),
    ("#17 多 bug", check_iron_law_17),
    ("#18 修复覆盖闭环", check_iron_law_18),
    ("#19 修复路径", check_iron_law_19),
    ("#20 v2.1 扩展字段键", check_v2_1_extension),
]


def validate(ticket: Dict) -> Tuple[bool, List[ValidationError]]:
    """对单个 issue_ticket 执行全部铁律校验

    Returns:
        (passed, errors)
        passed: bool — 是否通过
        errors: List[ValidationError] — 全部错误(包含 WARN 和 ERROR)
    """
    all_errors = []
    for rule_name, check_fn in IRON_LAW_CHECKS:
        try:
            all_errors.extend(check_fn(ticket))
        except Exception as e:
            all_errors.append(ValidationError(
                rule_name, "ERROR",
                f"校验器自身异常: {type(e).__name__}: {e}"
            ))
    has_error = any(e.severity == "ERROR" for e in all_errors)
    return (not has_error, all_errors)


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_diagnosis_v2.py <path-to-diagnosis.json> [--verbose]", file=sys.stderr)
        sys.exit(2)

    json_path = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv

    if not json_path.exists():
        print(f"文件不存在: {json_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(2)

    if "issue_ticket" not in data:
        print("顶层缺 'issue_ticket' 键", file=sys.stderr)
        sys.exit(2)

    ticket = data["issue_ticket"]
    passed, errors = validate(ticket)

    # 输出结果
    if verbose:
        print(f"校验文件: {json_path}")
        print(f"issue_number: {ticket.get('issue_number', 'N/A')}")
        print(f"verdict: {ticket.get('verdict', 'N/A')}")
        print(f"target_skill: {ticket.get('target_skill_filename', 'N/A')}")
        print(f"problem_signature: {ticket.get('problem_signature', 'N/A')}")
        print(f"字段数: {len(ticket)} (期望 >= 20)")
        print("-" * 60)

    if passed:
        if verbose:
            print("[PASS] 全部铁律通过")
        else:
            print("PASS")
        sys.exit(0)
    else:
        # 分级输出
        errors_only = [e for e in errors if e.severity == "ERROR"]
        warns = [e for e in errors if e.severity == "WARN"]

        print(f"[FAIL] 校验失败: {len(errors_only)} ERROR, {len(warns)} WARN", file=sys.stderr)
        for e in errors_only:
            print(f"  {e}", file=sys.stderr)
        for w in warns:
            print(f"  {w}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
