#!/usr/bin/env python3
"""
sync_to_agents.py
=================
从 source-of-truth (本仓库 main 分支对应的 skills/ 目录) 同步到 4 个 agent profile：

  1. calculatorHuawei/.claude/skills/*       (项目本地)
  2. C:/Users/26909/.claude/skills/*         (用户全局 Claude)
  3. C:/Users/26909/.opencode/skills/*       (opencode)
  4. C:/Users/26909/.../hermes/profiles/dev-01/skills/*  (Hermes dev-01 profile)

默认只同步第 1 个（项目本地），其他用 --target 参数显式选择。
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"

DEFAULT_TARGETS = {
    "project":   Path("D:/huawei/Demo/calculatorHuawei/.claude/skills"),
    "claude":    Path("C:/Users/26909/.claude/skills"),
    "opencode":  Path("C:/Users/26909/.opencode/skills"),
    "hermes":    Path("C:/Users/26909/AppData/Local/hermes/profiles/dev-01/skills"),
}


def sync_skill(name: str, src_dir: Path, dst_dir: Path, *, dry_run: bool) -> str:
    src = src_dir / name
    dst = dst_dir / name
    if not src.exists():
        return f"  ✗ {name}: src missing ({src})"
    if dry_run:
        return f"  · {name}: would sync → {dst}"
    dst.mkdir(parents=True, exist_ok=True)
    # 备份现有
    if dst.exists():
        backup = dst.with_suffix(dst.suffix + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(dst, backup)
        shutil.rmtree(dst)
    # 复制
    shutil.copytree(src, dst)
    return f"  ✓ {name}: → {dst}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=list(DEFAULT_TARGETS.keys()) + ["all"],
                    default="project",
                    help="同步目标（默认 project = calculatorHuawei 本地）")
    ap.add_argument("--skill", default=None,
                    help="只同步指定 skill（不指定=全部）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只显示要做什么，不真同步")
    ap.add_argument("--list", action="store_true", help="列出可同步的 skills")
    args = ap.parse_args()

    if args.list:
        print("可同步的 skills（来自 skills/）:")
        for s in sorted(SKILLS_SRC.iterdir()):
            if s.is_dir():
                print(f"  - {s.name}")
        return

    if not SKILLS_SRC.exists():
        print(f"❌ {SKILLS_SRC} 不存在")
        sys.exit(1)

    targets = (list(DEFAULT_TARGETS.values()) if args.target == "all"
               else [DEFAULT_TARGETS[args.target]])

    skills_to_sync = ([args.skill] if args.skill
                      else [s.name for s in sorted(SKILLS_SRC.iterdir()) if s.is_dir()])

    print(f"📦 源: {SKILLS_SRC}")
    print(f"🎯 目标: {[str(t) for t in targets]}")
    print(f"📋 待同步: {len(skills_to_sync)} skills\n")

    for target in targets:
        print(f"→ {target}")
        if not target.parent.exists() and not args.dry_run:
            print(f"  ⚠ 父目录不存在: {target.parent}，跳过")
            continue
        for name in skills_to_sync:
            print(sync_skill(name, SKILLS_SRC, target, dry_run=args.dry_run))
        print()


if __name__ == "__main__":
    main()
