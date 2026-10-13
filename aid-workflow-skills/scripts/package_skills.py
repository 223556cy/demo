#!/usr/bin/env python3
"""
package_skills.py
=================
校验 skills/ 目录完整性：每个 skill 必有 SKILL.md，frontmatter 合法，
引用 {CHANGES_ROOT} 等变量被替换。

用法：
    python scripts/package_skills.py            # 检查所有
    python scripts/package_skills.py --strict   # 严格模式（任何 warning 都报错）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
UNRESOLVED_VAR_RE = re.compile(r"\{[A-Z_]+\}")


def check_skill(skill_dir: Path) -> list[str]:
    issues = []
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        issues.append(f"[{name}] 缺少 SKILL.md")
        return issues

    text = skill_md.read_text(encoding="utf-8")

    # 1. frontmatter 必填
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        issues.append(f"[{name}] SKILL.md 缺 frontmatter (---...---)")
    else:
        fm = fm_match.group(1)
        if "name:" not in fm:
            issues.append(f"[{name}] frontmatter 缺 'name:'")
        if "description:" not in fm:
            issues.append(f"[{name}] frontmatter 缺 'description:'")

    # 2. 必填段落（仅 aid-* 流程类 skill 检查，sub-skill/rq-* 不强制）
    if name.startswith("aid-") and name not in {"aid-init", "aid-monitor"}:
        for sec in ["# ", "## 概述", "## 前置条件"]:
            if sec not in text:
                issues.append(f"[{name}] 缺段落: {sec}")

    # 3. 残留未替换变量
    unresolved = set(UNRESOLVED_VAR_RE.findall(text))
    # 允许 {项目名} {YYYYMMDD} 之类的不算
    allowed = {"CHANGES_ROOT", "YYYYMMDD", "项目名", "YYYY-MM-DD",
               "HHmm", "类型", "名称", "特性"}
    bad_unresolved = {v for v in unresolved
                      if v.strip("{}").split()[0] not in allowed
                      and v not in {"{HHmm}", "{YYYYMMDD}"}}
    if bad_unresolved:
        issues.append(f"[{name}] 残留未替换变量: {bad_unresolved}")

    # 4. 铁律 (aid-applying 必查)
    if name == "aid-applying":
        iron_laws = [
            ("build_hap.bat", "铁律 A: build_hap.bat"),
            ("harmonyos-ui-test", "铁律 C: UI test 调 skill"),
        ]
        for keyword, desc in iron_laws:
            if keyword not in text:
                issues.append(f"[{name}] {desc} 缺失")

    return issues


def main():
    # 强制 stdout UTF-8 (避免 Windows GBK console 踩 UnicodeEncodeError 坑)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="任何 issue 都视为错误")
    args = ap.parse_args()

    if not SKILLS_DIR.exists():
        print(f"[ERR] {SKILLS_DIR} 不存在")
        sys.exit(1)

    skills = sorted([s for s in SKILLS_DIR.iterdir() if s.is_dir()])
    all_issues = []
    for skill in skills:
        issues = check_skill(skill)
        all_issues.extend(issues)

    print(f"📋 检查 {len(skills)} skills:")
    for skill in skills:
        n = len([i for i in all_issues if i.startswith(f"[{skill.name}]")])
        marker = "✓" if n == 0 else "✗"
        print(f"  {marker} {skill.name}  ({n} issues)")

    if all_issues:
        print(f"\n⚠️  发现 {len(all_issues)} 个问题:")
        for i in all_issues:
            print(f"  {i}")
        if args.strict:
            sys.exit(1)
    else:
        print(f"\n✅ 所有 skill 校验通过")


if __name__ == "__main__":
    main()
