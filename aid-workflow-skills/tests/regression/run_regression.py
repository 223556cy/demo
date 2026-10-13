#!/usr/bin/env python3
"""
run_regression.py
=================
跑 12 个历史 issue 的回归测试。

对每个 issue：
  1. 复制 baseline worktree 到沙箱
  2. 应用 expected diff（来自历史产出的、已知能编过的代码改动）
  3. 跑 build_hap.bat assembleHap（编译）
  4. 跑 build_hap.bat test@entry（单元测试）
  5. 跑 ui_test_runner.run_ui_test()（如果 fixture.ui_test.required）

输出：
  - reports/branches/<branch>/results.json   (机器可读)
  - reports/branches/<branch>/report.md     (人可读)

用法：
    python tests/regression/run_regression.py                # 跑全部
    python tests/regression/run_regression.py --only issue-13  # 单个
    python tests/regression/run_regression.py --no-ui        # 跳过 UI 测试
    python tests/regression/run_regression.py --branch skillopt-01-fix-tdd  # 指定 branch
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CASES_DIR = REPO_ROOT / "tests" / "regression" / "cases"
REPORTS_DIR = REPO_ROOT / "reports" / "branches"
SANDBASE = Path(tempfile.gettempdir()) / "aidwf_regression_sandboxes"

BUILD_CMD = ["cmd", "/c", "build_hap.bat", "assembleHap", "--no-daemon"]
TEST_CMD  = ["cmd", "/c", "build_hap.bat", "test@entry", "--no-daemon"]


@dataclass
class CaseResult:
    id: str
    title: str
    compile_exit: int = -1
    compile_errors: int = 99
    compile_time_s: float = 0.0
    test_exit: int = -1
    test_pass_rate: float = 0.0
    test_count: int = 0
    ui_test_run: bool = False
    ui_pass: int = 0
    ui_bug: int = 0
    ui_test_reason: str = "skipped"
    patch_applied: bool = False
    total_time_s: float = 0.0
    error: str = ""


def _run(cmd: list[str], cwd: Path, env: dict, timeout: int) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=timeout)
        return {"exit_code": r.returncode,
                "stdout": r.stdout[-2000:],
                "stderr": r.stderr[-2000:],
                "time_s": time.time() - t0}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "timeout": True,
                "stdout": "", "stderr": "timeout", "time_s": timeout}
    except Exception as e:
        return {"exit_code": -1, "error": str(e),
                "stdout": "", "stderr": "", "time_s": time.time() - t0}


def _env() -> dict:
    env = os.environ.copy()  # type: ignore
    env.setdefault("DEVECO_SDK_HOME", r"C:\Program Files\Huawei\DevEco Studio\sdk")
    env.setdefault("JAVA_HOME", r"C:\Program Files\Java\jdk-17")
    return env


def _count_errors(log: str) -> int:
    import re
    return sum(1 for line in (log or "").splitlines()
               if re.search(r"^.*\b(error:|ERROR|Failed)\b", line, re.I))


def _parse_test_pass_rate(stdout: str) -> tuple[float, int]:
    import re
    if not stdout:
        return 0.0, 0
    m = re.search(r"(\d+)\s*passed.*?(\d+)\s*failed", stdout, re.I)
    if m:
        p, f = int(m.group(1)), int(m.group(2))
        t = p + f
        return (p / t if t else 0.0), t
    m = re.search(r"(\d+)\s*/\s*(\d+)\s*Tests", stdout, re.I)
    if m:
        p, t = int(m.group(1)), int(m.group(2))
        return p / max(t, 1), t
    return 0.0, 0


def run_one_case(fixture: dict, *, run_ui: bool) -> CaseResult:
    import os
    res = CaseResult(id=fixture["id"], title=fixture["issue"]["title"])
    t_total = time.time()
    try:
        worktree = Path(fixture["paths"]["baseline_worktree"])
        oc_subpath = fixture["paths"]["opencalc_subpath"]

        # 准备沙箱
        SANDBASE.mkdir(parents=True, exist_ok=True)
        sandbox = SANDBASE / f"{fixture['id']}_{os.getpid()}_{int(time.time())}"
        if sandbox.exists():
            shutil.rmtree(sandbox)
        shutil.copytree(
            worktree, sandbox, symlinks=True,
            ignore=shutil.ignore_patterns(
                ".git", "build", "node_modules", "oh_modules",
                ".hvigor", ".idea", ".claude", "*.log", "ai_auto_test",
            ),
        )
        oc_root = sandbox / oc_subpath
        env = _env()

        # 应用 expected diff
        diff_file = Path(fixture["expected"]["diff_file"])
        if diff_file.exists() and diff_file.stat().st_size > 0:
            patch = diff_file.read_text(encoding="utf-8", errors="ignore")
            tmp_diff = oc_root / "_regression.diff"
            tmp_diff.write_text(patch, encoding="utf-8")
            try:
                r = subprocess.run(
                    ["git", "apply", "--whitespace=nowarn", "--reject", str(tmp_diff)],
                    cwd=oc_root, capture_output=True, text=True, timeout=60,
                )
                res.patch_applied = (r.returncode == 0)
                if not res.patch_applied:
                    res.error = f"git apply failed: {r.stderr[:200]}"
            except Exception as e:
                res.error = f"apply exception: {e}"
            finally:
                if tmp_diff.exists():
                    tmp_diff.unlink()

        if not res.patch_applied:
            res.total_time_s = time.time() - t_total
            try: shutil.rmtree(sandbox)
            except: pass
            return res

        # 编译
        cr = _run(BUILD_CMD, oc_root, env, timeout=1500)
        res.compile_exit = cr["exit_code"]
        res.compile_time_s = cr["time_s"]
        res.compile_errors = _count_errors(cr["stdout"] + cr["stderr"])

        # 单元测试
        tr = _run(TEST_CMD, oc_root, env, timeout=1500)
        res.test_exit = tr["exit_code"]
        res.test_pass_rate, res.test_count = _parse_test_pass_rate(tr["stdout"])

        # UI 测试（可选）
        if run_ui and fixture.get("ui_test", {}).get("required"):
            try:
                sys.path.insert(0, str(REPO_ROOT / "tests" / "regression"))
                from ui_test_runner import run_ui_test
                ui_res = run_ui_test(oc_root, fixture, env)
                res.ui_test_run = True
                res.ui_pass = ui_res.get("pass", 0)
                res.ui_bug = ui_res.get("bug", 0)
                res.ui_test_reason = ui_res.get("reason", "ok")
            except Exception as e:
                res.ui_test_reason = f"runner exception: {e}"
        else:
            res.ui_test_reason = "not required" if not fixture.get("ui_test", {}).get("required") else "disabled"

        # 清理
        try: shutil.rmtree(sandbox)
        except: pass

    except Exception as e:
        res.error = str(e)

    res.total_time_s = time.time() - t_total
    return res


def make_report(results: list[CaseResult], branch: str) -> tuple[dict, str]:
    n = len(results)
    compile_pass = sum(1 for r in results if r.compile_exit == 0)
    test_pass = sum(1 for r in results if r.test_pass_rate > 0.5)
    ui_run = sum(1 for r in results if r.ui_test_run)
    ui_pass = sum(1 for r in results if r.ui_pass > 0 and r.ui_bug == 0)

    summary = {
        "branch": branch,
        "total_cases": n,
        "compile_pass": compile_pass,
        "compile_rate": round(compile_pass / max(n, 1), 3),
        "test_pass": test_pass,
        "test_rate": round(test_pass / max(n, 1), 3),
        "ui_test_run": ui_run,
        "ui_pass": ui_pass,
        "ui_rate": round(ui_pass / max(ui_run, 1), 3),
        "total_time_s": round(sum(r.total_time_s for r in results), 1),
    }

    md = [
        f"# 回归测试报告 — `{branch}`",
        "",
        f"## 总览",
        f"| 指标 | 数值 |",
        f"|---|---|",
        f"| 总用例 | {n} |",
        f"| 编译通过 | {compile_pass} ({summary['compile_rate']*100:.1f}%) |",
        f"| 单元测试通过 | {test_pass} ({summary['test_rate']*100:.1f}%) |",
        f"| UI 测试执行 | {ui_run} |",
        f"| UI 测试通过 | {ui_pass} |",
        f"| 总耗时 | {summary['total_time_s']}s |",
        "",
        "## 明细",
        "| Issue | 标题 | 编译 | 单元测试 | UI 测试 | 耗时 |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        c = "✅" if r.compile_exit == 0 else f"❌(err={r.compile_errors})"
        t = f"{r.test_pass_rate*100:.0f}%({r.test_count})" if r.test_count else "—"
        u = f"{r.ui_pass}P/{r.ui_bug}B" if r.ui_test_run else "—"
        if r.ui_test_reason and r.ui_test_reason not in ("ok", "not required", "disabled"):
            u = f"⚠ {r.ui_test_reason[:20]}"
        md.append(f"| `{r.id}` | {r.title[:30]} | {c} | {t} | {u} | {r.total_time_s:.0f}s |")

    return summary, "\n".join(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="只跑指定 issue (e.g. issue-13)")
    ap.add_argument("--no-ui", action="store_true", help="跳过 UI 测试")
    ap.add_argument("--branch", default="local", help="分支名（影响报告路径）")
    ap.add_argument("--max-time", type=int, default=1500, help="编译单次超时（秒）")
    args = ap.parse_args()

    if not CASES_DIR.exists():
        print(f"❌ {CASES_DIR} 不存在，请先跑 build_fixtures.py")
        sys.exit(1)

    fixtures = []
    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir() or not (case_dir / "fixture.json").exists():
            continue
        fix = json.loads((case_dir / "fixture.json").read_text(encoding="utf-8"))
        if args.only and fix["id"] != args.only:
            continue
        fixtures.append(fix)

    if not fixtures:
        print(f"❌ 没找到 fixture（filter={args.only}）")
        sys.exit(1)

    print(f"🚀 跑 {len(fixtures)} 个回归用例（branch={args.branch}, ui={not args.no_ui}）\n")
    results = []
    for i, fix in enumerate(fixtures, 1):
        print(f"[{i}/{len(fixtures)}] {fix['id']} - {fix['issue']['title']}")
        r = run_one_case(fix, run_ui=not args.no_ui)
        c = "✅" if r.compile_exit == 0 else "❌"
        print(f"          compile={c}({r.compile_time_s:.0f}s) test={r.test_pass_rate*100:.0f}% ui={'run' if r.ui_test_run else 'skip'}")
        results.append(r)

    # 写报告
    out_dir = REPORTS_DIR / args.branch
    out_dir.mkdir(parents=True, exist_ok=True)
    summary, md = make_report(results, args.branch)
    (out_dir / "results.json").write_text(
        json.dumps({"summary": summary,
                    "cases": [asdict(r) for r in results]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out_dir / "report.md").write_text(md, encoding="utf-8")

    print(f"\n📊 总览: 编译 {summary['compile_rate']*100:.0f}%, "
          f"测试 {summary['test_rate']*100:.0f}%, UI {summary['ui_rate']*100:.0f}%, "
          f"耗时 {summary['total_time_s']}s")
    print(f"📁 报告: {out_dir/'report.md'}")


if __name__ == "__main__":
    import os  # noqa: E402
    main()
