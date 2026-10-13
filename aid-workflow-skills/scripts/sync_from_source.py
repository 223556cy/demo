#!/usr/bin/env python3
"""
sync_from_source.py
===================
一次性脚本：从 calculatorHuawei/.claude/skills/* 把所有 skill 拉到本仓库 skills/。

用法：
    python scripts/sync_from_source.py                    # 拉全部
    python scripts/sync_from_source.py --skill aid-applying   # 只拉一个

之后用 sync_to_agents.py 反向同步到 agent profile。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DST = REPO_ROOT / "skills"
SOURCE = Path("D:/huawei/Demo/calculatorHuawei/.claude/skills")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default=None, help="只同步指定 skill")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"❌ 源不存在: {SOURCE}")
        sys.exit(1)

    skills = ([args.skill] if args.skill
              else sorted(s.name for s in SOURCE.iterdir() if s.is_dir()))

    print(f"📥 源: {SOURCE}")
    print(f"📦 目标: {SKILLS_DST}")
    print(f"📋 待同步: {len(skills)} skills\n")

    for name in skills:
        src = SOURCE / name
        dst = SKILLS_DST / name
        if not src.exists():
            print(f"  ✗ {name}: src 不存在")
            continue
        if args.dry_run:
            print(f"  · {name}: would copy")
            continue
        dst.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        n_files = sum(1 for _ in dst.rglob("*") if _.is_file())
        print(f"  ✓ {name}: {n_files} files")


if __name__ == "__main__":
    main()
