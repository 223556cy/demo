"""
skill_md_parser.py — 从 SKILL.md 解析出"预期步骤序列"

支持的命名风格:
  - step N[-M[-K]]  (连字符制, aid-applying / aid-implementing)
  - step X.Y        (小数点制, aid-planning / mod-design)
  - Step X          (空格制, rq-codebase / aid-init / aid-archiving)
  - 阶段 X / 步骤 X (中文, harmonyos-ui-test)
  - D1..D10         (mod-design 设计章节)
  - RED/GREEN/REFACTOR (tdd-enforcer 颜色)
  - 自由标题        (rq-parse / rq-clarify 工作流子段,无编号)

输出 expected.json:
  {
    "schema_version": "1.0",
    "skills": {
      "aid-applying": {
        "naming_style": "...",
        "sections": [
          {"id": "step3-0", "title": "环境检查", "level": 2, "mandatory": true,
           "sub_skills": [], "iron_laws": []},
          ...
        ],
        "sub_skills_required": [
          {"parent_section": "step3-2-1", "sub_skill": "tdd-enforcer", "rule_text": "..."},
          ...
        ]
      }
    }
  }
"""
import json
import re
from pathlib import Path
from typing import Optional


# 命名风格优先级(从最具体到最宽松)
HEADING_PATTERNS = [
    # step N[-M[-K]] 包括 letter 后缀 (step3-2-2b / step3-2-2b-降级)
    (re.compile(r"^step\s*(\d+(?:-\d*[a-zA-Z一-鿿]*)*)\b\s*[:：]?\s*(.*)$"), "step-hyphen", "step"),
    # step X.Y (aid-planning / mod-design)
    (re.compile(r"^step\s*(\d+(?:\.\d+)*)\b\s*[:：]?\s*(.*)$"), "step-dot", "step"),
    # Step N (rq-codebase / aid-init / aid-archiving)
    (re.compile(r"^Step\s*(\d+(?:\.\d+)*)\b\s*[:：]?\s*(.*)$"), "Step-space", "Step"),
    # 阶段 N / 步骤 N (harmonyos-ui-test / aid-analysis-root-cause 步骤 B-0)
    # 支持可选 letter 后缀 (如 B-0 / C-2.1) 或纯字母 (D / E / F)
    (re.compile(r"^(?:阶段|步骤)\s*([BCDEF])([-.]?)(\d+(?:\.\d+)*)?\s*[\.、:：]?\s*(.*)$"), "alpha-digit", None),
    (re.compile(r"^(?:阶段|步骤)\s*([一二三四五六七八九十\d]+)\b\s*[:：]?\s*(.*)$"), "chinese", "step"),
    # D1..D10 (mod-design)
    (re.compile(r"^D(\d+)\s*[:：]?\s*(.*)$"), "D-chapter", "D"),
    # RED/GREEN/REFACTOR (tdd-enforcer)
    (re.compile(r"^(RED|GREEN|REFACTOR)\b\s*[:：\-]?\s*(.*)$"), "tdd-color", None),
]


def parse_heading(text: str, level: int = 2) -> Optional[tuple[str, str, str]]:
    """解析一个标题行(如 '### step3-0:环境检查')
    返回 (section_id, title, style) 或 None

    **严格**:只接受匹配已知 step 模式的标题,自由文本标题(## 概述 等)直接丢弃
    """
    t = text.strip()
    # 去掉前导的 # 空格
    t = re.sub(r"^#+\s*", "", t)
    if not t:
        return None
    for pat, style, prefix in HEADING_PATTERNS:
        m = pat.match(t)
        if m:
            num_or_letter = m.group(1)
            num = None
            title = ""
            # 根据 pattern style 决定 num/title 从哪个 group 取
            if style == "alpha-digit":
                # 4 groups: letter, separator, number (optional), title
                num_or_letter = m.group(1)
                sep = m.group(2) or "-"
                num = m.group(3)  # 可选 (D / E / F 无 number)
                title = m.group(4).strip().lstrip("：:.") if m.lastindex >= 4 else ""
                # 拼 sec_id
                if num:
                    sec_id = f"{num_or_letter}-{num}"
                else:
                    sec_id = num_or_letter
                return (sec_id, title, style)
            elif style == "chinese":
                # 2 groups: chinese_num, title
                num = m.group(1)
                title = m.group(2).strip().lstrip("：:").strip()
            elif style == "step-hyphen" or style == "step-dot" or style == "Step-space":
                # 2 groups: number, title
                num = m.group(1)
                title = m.group(2).strip().lstrip("：:").strip()
            elif style == "D-chapter":
                # 2 groups: number, title
                num = m.group(1)
                title = m.group(2).strip().lstrip("：:").strip()
            elif style == "tdd-color":
                # 2 groups: color, title
                title = m.group(2).strip().lstrip("：:").strip()
            else:
                title = ""
            # 中文数字转阿拉伯
            cn_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "零": 0}
            if num and num in cn_map:
                num = str(cn_map[num])
            # 拼 sec_id
            if prefix == "step":
                sec_id = f"step{num}"
            elif prefix == "Step":
                sec_id = f"Step{num}"
            elif prefix == "D":
                sec_id = f"D{num}"
            elif style == "tdd-color":
                sec_id = num_or_letter
            else:
                sec_id = num_or_letter
            return (sec_id, title, style)
    return None


def extract_mandatory_markers(body: str) -> tuple[bool, list[str], list[int]]:
    """从段体里抽 mandatory 标记 + 强制调用的子 skill + 铁律编号
    返回 (is_mandatory, sub_skills_required, iron_laws)
    """
    is_mandatory = False
    sub_skills = []
    iron_laws = []

    # mandatory 关键词
    mandatory_kw = ["必须", "强制", "必:", "必。", "必 ", "铁律", "硬门禁", "imperative"]
    for kw in mandatory_kw:
        if kw in body:
            is_mandatory = True
            break

    # 强制调用子 skill:`skill('xxx')` 或 `skill("xxx")`
    for m in re.finditer(r"skill\(['\"]([a-z][a-z0-9\-]*)['\"]\)", body):
        sub_skills.append(m.group(1))

    # 铁律 N
    for m in re.finditer(r"铁律\s*(\d+)", body):
        iron_laws.append(int(m.group(1)))

    return is_mandatory, list(set(sub_skills)), list(set(iron_laws))


def extract_expected_products(text: str) -> list:
    """从 SKILL.md 文本里抽"预期产物文件"

    启发式:找 markdown 表格里"产出" / "模板" 列 + 文件名模式(.md / .ets / .test.ets)
    """
    products = []

    # 1. 找 markdown 表格行("| 文件名 | 用途 |" 类似)
    for line in text.split("\n"):
        m = re.match(r"\|\s*[`]?([\w\-\.]+\.(?:md|ets|test\.ets|json|yaml|yml|properties|json5))\s*[`]?\s*\|", line)
        if m:
            fn = m.group(1)
            # 排除 README/LICENSE 之类
            if fn.lower() in ("readme.md", "license.md"):
                continue
            products.append({"file": fn, "evidence": "table_column"})

    # 2. 找产物路径描述如 "产出 proposal.md" 或 "写 tasks.md"(允许无空格)
    for m in re.finditer(r"(产出|写|生成)\s*[`]?([\w\-\./\\]+\.(?:md|ets|test\.ets|json|yaml|yml|properties|json5))[`]?", text):
        fn = m.group(2).split("/")[-1].split("\\")[-1]
        if fn.lower() in ("readme.md", "license.md"):
            continue
        products.append({"file": fn, "evidence": f"verb={m.group(1)}"})

    # 3. 找 → filename 形式(如 "→ proposal.md")
    for m in re.finditer(r"→\s*[`]?([\w\-\./\\]+\.(?:md|ets|test\.ets))[`]?", text):
        fn = m.group(1).split("/")[-1].split("\\")[-1]
        if fn.lower() in ("readme.md", "license.md"):
            continue
        products.append({"file": fn, "evidence": "arrow"})

    # 4. 表格第 3 列"产出 xxx.md"形式
    for m in re.finditer(r"\|\s*(产出|写|生成)\s+[`]?([\w\-\./\\]+\.(?:md|ets|test\.ets))[`]?\s*\|", text):
        fn = m.group(2).split("/")[-1].split("\\")[-1]
        if fn.lower() in ("readme.md", "license.md"):
            continue
        products.append({"file": fn, "evidence": f"table_verb={m.group(1)}"})

    # 5. 表格中只列文件名的(不管哪列)— 文件名 + (必须|必填|应当|输出)
    for m in re.finditer(r"\|\s*[`]?([\w\-\./\\]+\.(?:md|ets|test\.ets))[`]?\s*\|[^|\n]*(?:必须|必填|应当|输出|应当产出)[^|\n]*\|", text):
        fn = m.group(1).split("/")[-1].split("\\")[-1]
        if fn.lower() in ("readme.md", "license.md"):
            continue
        products.append({"file": fn, "evidence": "table_must"})

    # 6. design-review.md 在 step9 必查清单(常见产物)
    if "design-review.md" in text:
        products.append({"file": "design-review.md", "evidence": "common_aid_artifact"})

    # 去重
    seen = set()
    deduped = []
    for p in products:
        if p["file"] not in seen:
            seen.add(p["file"])
            deduped.append(p)
    return deduped


def parse_skill_md(path: Path) -> dict:
    """解析单个 SKILL.md,返回 sections 列表 + mandatory_sub_skills"""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 先找所有 H2/H3/H4 标题及其行号
    sections_raw = []  # (line_no, level, full_heading_text)
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            continue
        level = len(m.group(1))
        heading_text = m.group(2)
        parsed = parse_heading(heading_text, level)
        if parsed:
            sec_id, title, style = parsed
            sections_raw.append((i, level, sec_id, title, style))

    # 对每个 section,从 heading 到下一个 heading 取 body
    sections = []
    for idx, (line_no, level, sec_id, title, style) in enumerate(sections_raw):
        # body:从这一行到下一个 section heading
        if idx + 1 < len(sections_raw):
            body_end = sections_raw[idx + 1][0] - 1
        else:
            body_end = len(lines)
        body_lines = lines[line_no:body_end]
        body = "\n".join(body_lines)

        is_mandatory, sub_skills, iron_laws = extract_mandatory_markers(body)

        sections.append({
            "id": sec_id,
            "title": title,
            "level": level,
            "line_no": line_no,
            "mandatory": is_mandatory,
            "sub_skills_required": sub_skills,
            "iron_laws": iron_laws,
        })

    # 提取 mandatory sub_skills(独立于段的、整个 skill 范围的强制调用)
    full_text_mandates = []
    full_body = text
    is_mand, sub_skills_global, _ = extract_mandatory_markers(full_body)
    if sub_skills_global:
        # 对每个 sub_skill,找**最近的上方 section**(因为 sub_skill 通常在 section body 里)
        for ss in sub_skills_global:
            # 在全文找 `skill('ss')` 或 `skill("ss")` 出现的行号
            ss_line_nos = []
            for i, line in enumerate(lines, 1):
                if f"skill('{ss}')" in line or f'skill("{ss}")' in line:
                    ss_line_nos.append(i)

            # 找最近的(在它之前的)section
            parent_sec = "unknown"
            for ssln in ss_line_nos:
                # 找 ssln 之前的最近一个 section
                closest_sec = None
                for sec in sections:
                    if sec["line_no"] <= ssln:
                        closest_sec = sec
                    else:
                        break
                if closest_sec:
                    parent_sec = closest_sec["id"]
                    break

            full_text_mandates.append({
                "parent_section": parent_sec,
                "sub_skill": ss,
            })

    # 找 naming_style
    styles = set(s["level"] for s in sections)  # placeholder
    if sections:
        # 多数 style
        from collections import Counter
        style_counts = Counter()
        for sec in sections:
            # 反推 style 从 sec_id 模式
            sid = sec["id"]
            if re.match(r"^\d+(-\d+)*$", sid):
                style_counts["step-hyphen"] += 1
            elif re.match(r"^\d+(\.\d+)*$", sid):
                style_counts["step-dot"] += 1
            elif re.match(r"^D\d+$", sid):
                style_counts["D-chapter"] += 1
            elif sid in ("RED", "GREEN", "REFACTOR"):
                style_counts["tdd-color"] += 1
            else:
                style_counts["free-text"] += 1
        naming_style = style_counts.most_common(1)[0][0] if style_counts else "unknown"
    else:
        naming_style = "unknown"

    return {
        "sections": sections,
        "sub_skills_required": full_text_mandates,
        "naming_style": naming_style,
        "section_count": len(sections),
        "expected_products": extract_expected_products(text),
    }


def parse_all_skills(skills_root: Path) -> dict:
    """扫整个 skills 目录,解析所有 SKILL.md(忽略 .bak 备份)"""
    result = {
        "schema_version": "1.0",
        "description": "从 SKILL.md 解析的预期步骤序列。每个 skill 一组 sections + mandatory sub_skills。",
        "skills": {},
    }
    for skill_dir in sorted(skills_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.endswith(".bak"):
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        skill_name = skill_dir.name
        try:
            parsed = parse_skill_md(skill_md)
            result["skills"][skill_name] = parsed
        except Exception as e:
            print(f"WARN: failed to parse {skill_name}: {e}")
    return result


if __name__ == "__main__":
    import sys
    skills_root = Path(r"D:\huawei\Demo\calculatorHuawei\.claude\skills")
    out_path = Path(r"D:\huawei\Demo\skill_expected.json")

    expected = parse_all_skills(skills_root)
    out_path.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {out_path}")
    print()
    print("=== 解析结果汇总 ===")
    for skill, info in expected["skills"].items():
        ns = info["section_count"]
        sub_reqs = len(info["sub_skills_required"])
        mandatory_count = sum(1 for s in info["sections"] if s["mandatory"])
        print(f"  {skill:20} | {ns:2} 段 | mandatory={mandatory_count:2} | 强制 sub-skill={sub_reqs}")

    # 抽查 aid-applying
    print()
    print("=== 抽查: aid-applying ===")
    for sec in expected["skills"]["aid-applying"]["sections"]:
        sub = ",".join(sec["sub_skills_required"]) or "-"
        iron = ",".join(str(i) for i in sec["iron_laws"]) or "-"
        mark = "MUST" if sec["mandatory"] else "  -"
        print(f"  [{mark}] {sec['id']:15} | {sec['title']:25} | sub={sub:20} | iron={iron}")

    print()
    print(f"aid-applying 的 mandatory sub_skills:")
    for ms in expected["skills"]["aid-applying"]["sub_skills_required"]:
        print(f"  {ms['parent_section']:15} → {ms['sub_skill']}")