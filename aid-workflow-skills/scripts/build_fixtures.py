#!/usr/bin/env python3
"""
build_fixtures.py
=================
把 calculatorHuawei/worktrees/issue-N/ + calculatorHuawei/specs/changes/ 的 12 个
已完成 issue 打包成回归测试 fixture。

每个 fixture 形如：
    tests/regression/cases/issue-13/
        ├── fixture.json        # 元数据 + 路径引用（不含实际代码，节省 repo 体积）
        ├── spec/               # proposal.md / info.md / design.md / tasks.md
        └── expected/           # apply-report.md + expected_compile.json
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT     = Path(__file__).resolve().parent.parent
WORKTREES_DIR = Path("D:/huawei/Demo/worktrees")
SPECS_DIR     = Path("D:/huawei/Demo/calculatorHuawei/specs")
CASES_DIR     = REPO_ROOT / "tests" / "regression" / "cases"

# 12 个已完成 issue
COMPLETED_ISSUES = [
    (1,  1,  "百分号按钮",     "UX 增强",     0),
    (3,  2,  "实时预览早期",   "实时预览",    0),
    (9,  1,  "百分号回归",     "UX 增强",     0),
    (11, 2,  "实时预览",       "实时预览",    0),
    (13, 7,  "二维码分享",     "分享",        2),
    (14, 8,  "单位换算v1",     "单位换算",    4),
    (15, 14, "历史日期分组",   "历史增强",    2),
    (16, 11, "长按sin菜单",    "手势增强",    1),
    (17, 10, "粘贴即计算",     "粘贴计算",    1),
    (18, 8,  "NL单位换算",     "单位换算",    2),
    (22, 3,  "程序员模式",     "程序员模式",  1),
    (24, 4,  "历史搜索",       "历史增强",    1),
]


def find_spec_dir(issue_num: int) -> Path | None:
    """在 SPECS_DIR 下找引用了 issue_num 的 change 目录。"""
    for sub in ["changes", "archives"]:
        root = SPECS_DIR / sub
        if not root.exists():
            continue
        for c in root.glob("*requirement*"):
            prop = c / "proposal.md"
            if not prop.exists():
                continue
            head = prop.read_text(encoding="utf-8", errors="ignore")[:1000]
            if f"#{issue_num}" in head or f"# {issue_num}" in head:
                return c
    return None


def get_actual_diff(worktree: Path) -> str:
    """取 worktree 的 git diff（head vs first commit）。"""
    try:
        r = subprocess.run(
            ["git", "-C", str(worktree), "log", "--all", "--pretty=format:", "-p"],
            capture_output=True, timeout=30,
        )
        return r.stdout.decode("utf-8", errors="replace")[:30000]
    except Exception:
        return ""


def build_fixture(issue_num: int, req_id: int, req_name: str,
                  category: str, rev_rounds: int) -> dict | None:
    worktree = WORKTREES_DIR / f"issue-{issue_num}"
    if not worktree.exists():
        print(f"  ✗ issue-{issue_num}: worktree 不存在")
        return None

    spec_dir = find_spec_dir(issue_num)
    if not spec_dir:
        print(f"  ✗ issue-{issue_num}: 找不到 spec 目录")
        return None

    case_dir = CASES_DIR / f"issue-{issue_num}"
    spec_dst = case_dir / "spec"
    expected_dst = case_dir / "expected"

    if case_dir.exists():
        shutil.rmtree(case_dir)
    spec_dst.mkdir(parents=True)
    expected_dst.mkdir(parents=True)

    # 复制 spec 文档
    for fname in ["proposal.md", "info.md", "design.md", "delta-spec.md",
                  "tasks.md", "apply-report.md", "todo.md"]:
        src = spec_dir / fname
        if src.exists():
            shutil.copy2(src, spec_dst / fname)

    # 抓 expected diff
    diff = get_actual_diff(worktree)
    (expected_dst / "expected.diff").write_text(diff, encoding="utf-8")

    # 写 fixture.json
    fixture = {
        "id": f"issue-{issue_num}",
        "issue": {
            "number": issue_num,
            "title": f"#{issue_num} {req_name}",
            "category": category,
            "requirement_id": req_id,
            "rev_01_rounds": rev_rounds,
        },
        "paths": {
            # 沙箱里跑回归时从这里复制 baseline
            "baseline_worktree": str(worktree),
            "opencalc_subpath": "opencalc" if (worktree / "opencalc").exists() else ".",
        },
        "spec_dir": str(spec_dst),
        "expected": {
            "diff_file": str(expected_dst / "expected.diff"),
            "compile_exit": 0,            # 已完成 issue 都通过编译
            "test_pass": True,
        },
        # 是否触发 UI 测试
        "ui_test": {
            "required": category in {"分享", "手势增强", "历史增强", "UX 增强",
                                     "单位换算", "程序员模式", "粘贴计算",
                                     "实时预览"},
            "fixture_path": None,         # UI test fixture 由 ui_test_runner.py 准备
        },
    }
    (case_dir / "fixture.json").write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return fixture


def main():
    print(f"📂 输出: {CASES_DIR}\n")
    fixtures = []
    for issue_num, req_id, req_name, cat, rev in COMPLETED_ISSUES:
        print(f"-> issue-{issue_num} ({req_name})")
        f = build_fixture(issue_num, req_id, req_name, cat, rev)
        if f:
            fixtures.append(f)
    print(f"\n✅ 打包 {len(fixtures)}/{len(COMPLETED_ISSUES)} 个 fixture")
    index = {"count": len(fixtures), "cases": [f["id"] for f in fixtures]}
    (CASES_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
