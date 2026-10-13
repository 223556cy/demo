"""
aid-code-root-cause / 代码抽取工具

功能:从 JSONL 抽所有 Write/Edit tool_use 事件的代码片段 + 上下文
给 LLM 提供分析输入(LLM 自己用 7 个角度思考,不用 regex)

输入:.jsonl(annotated 或 原始)
输出:
  - events.json(LLM 可读,含 event_id + thinking + code_diff)
  - summary.md(可读摘要)
  - worktree_gap.json(可选,仅 --include-worktree 时生成,列出 JSONL 未触碰的 .ets)

设计要点(2026-08 修订):
- thinking 字段取自**最近一条**含 thinking 块的 assistant 消息(向前最多 THINKING_LOOKBACK 步),
  因为 thinking 块在 Claude Code JSONL 里几乎从不与 Write/Edit 同条 message
- event_id 优先用 tool_use.id(稳定),fallback 到 L<line>:<file_stem>
- Edit 事件额外输出 code_diff(简化 unified diff),便于 LLM 看 before/after
- 抽不到 old_string 的 Edit 事件用占位符"// (no old_string provided)",不冒充 "new file"

v1.3 修订(2026-08):
- 加 --include-worktree <dir>:扫 worktree 中所有 .ets/源文件,与 JSONL 中被改过的文件对比,
  输出 untouched_files(LLM 必须自己 Read 这部分代码,否则会盲掉)。
- summary.md 角度数 6 → 7(增加 Build routing)。
"""
import difflib
import json
import re
import sys
import argparse
from pathlib import Path


# ============== 常量(可通过 CLI 覆盖) ==============

# 关注的源文件后缀(鸿蒙/通用)— 留可扩展,缺类型可改这里或加 CLI flag
SOURCE_EXTS = (".ets", ".ts", ".js", ".mjs", ".py", ".json5", ".hml", ".css")

# 代码长度门槛:低于此字符数视为微小改动,丢弃
DEFAULT_MIN_CODE_LEN = 50

# 向前回溯多少条 assistant 消息找 thinking 块
DEFAULT_THINKING_LOOKBACK = 5

# diff 输出控制
DEFAULT_DIFF_CONTEXT = 3             # unified_diff 的 context 行数
DEFAULT_DIFF_MAX_LINES = 30          # diff 总行数超过此值则截断
DEFAULT_DIFF_WRITE_PREVIEW_LINES = 6 # Write 事件无 old 时,preview 前 N 行(默认 = 2 * context)

# worktree 扫描时跳过的目录(2026-08 v1.3 新增)
WORKTREE_SKIP_DIRS = (
    ".git", ".hvigor", "node_modules", "build", "dist",
    ".idea", ".vscode", ".claude", "oh_modules",
    "build-profile", "outputs", ".test",
    "__pycache__", ".gradle", "coverage",
)

# 内部:用 placeholder 标识 Edit 事件没传 old_string
NO_OLD_STRING_PLACEHOLDER = "// (no old_string provided in tool input)"


# ============== JSONL 字段名常量 ==============

# 消息类型 / 块类型
MSG_TYPE_ASSISTANT = "assistant"
BLK_TYPE_THINKING = "thinking"
BLK_TYPE_TOOL_USE = "tool_use"
TOOL_NAMES = ("Write", "Edit")

# tool_use.input 字段
INPUT_FILE_PATH = "file_path"
INPUT_CONTENT = "content"          # Write
INPUT_NEW_STRING = "new_string"    # Edit
INPUT_OLD_STRING = "old_string"    # Edit

# tool_use 字段
TOOL_USE_ID = "id"

# 顶层字段
TOP_TYPE = "type"
TOP_MESSAGE = "message"
TOP_TIMESTAMP = "timestamp"


# ============== 派生 ID / 会话 ==============

def _file_name(fp: str) -> str:
    """统一用 Path().name 取文件名,避免双重 split。"""
    return Path(fp).name


def _event_id(tool_use_id: str, jsonl_line: int, file_name: str) -> str:
    """生成稳定 event_id:
    - 优先用 tool_use.id(Claude Code 一定分配,跨 export 稳定)
    - fallback 到 L<line>:<file_stem>(旧 JSONL / 缺 id 时)
    """
    stem = Path(file_name).stem
    if tool_use_id:
        return f"{tool_use_id}:{stem}"
    return f"L{jsonl_line}:{stem}"


def _clean_session_id(stem: str) -> str:
    """从 JSONL 文件名推 session_id:
    支持 xxx.annotated.jsonl / xxx.jsonl / xxx.jsonl.annotated.jsonl
    取最后一个 .jsonl 之前、剥掉 .annotated 后缀的部分。
    """
    s = stem
    while True:
        new_s = re.sub(r"\.annotated\.jsonl$", "", s)
        if new_s == s:
            new_s = re.sub(r"\.jsonl$", "", s)
        if new_s == s:
            break
        s = new_s
    return s


# ============== Diff 生成 ==============

def _make_diff(
    old: str,
    new: str,
    context: int = DEFAULT_DIFF_CONTEXT,
    max_lines: int = DEFAULT_DIFF_MAX_LINES,
    write_preview_lines: int = DEFAULT_DIFF_WRITE_PREVIEW_LINES,
) -> str:
    """生成精简 unified diff(只保留前 N 行变更,避免 events.json 爆炸)。

    三种情况:
    - old 非空:标准 unified_diff
    - old 为空且 tool 是 Write(由调用方传 is_write=True 时):标 "+++ (new file)"
    - old 为空且 tool 是 Edit:标 "+++ (no old_string in tool input)" — 避免被 LLM 误读成"新建文件"
    """
    if not old:
        lines = new.splitlines(keepends=True)[:write_preview_lines]
        out = "+++ (no old_string in tool input)\n" + "".join(lines)
        total = len(new.splitlines())
        if total > len(lines):
            out += f"\n... [+{total - len(lines)} lines]"
        return out
    diff_lines = list(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        n=context,
        fromfile="old",
        tofile="new",
        lineterm="",
    ))
    if not diff_lines:
        return ""
    diff_text = "\n".join(line.rstrip("\n") for line in diff_lines) + "\n"
    diff_line_list = diff_text.splitlines()
    if len(diff_line_list) > max_lines:
        kept = "\n".join(diff_line_list[:max_lines])
        return kept + f"\n... [+{len(diff_line_list) - max_lines} more diff lines]\n"
    return diff_text


# ============== 主流程 ==============

def _parse_message(rec: dict):
    """从一条 record 提取 (msg, content_list),失败返回 (None, None)。
    两遍扫描用同一份解析,行为一致。"""
    if rec.get(TOP_TYPE) != MSG_TYPE_ASSISTANT:
        return None, None
    msg = rec.get(TOP_MESSAGE, {})
    if not isinstance(msg, dict):
        return None, None
    content_list = msg.get("content", [])
    if not isinstance(content_list, list):
        return None, None
    return msg, content_list


def _extract_thinking(content_list: list) -> str:
    """从一条 assistant message 的 content 数组里找 thinking 块的文本。"""
    for blk in content_list:
        if isinstance(blk, dict) and blk.get("type") == BLK_TYPE_THINKING:
            return blk.get("thinking", "") or ""
    return ""


def extract(
    jsonl_path: Path,
    min_code_len: int = DEFAULT_MIN_CODE_LEN,
    thinking_lookback: int = DEFAULT_THINKING_LOOKBACK,
    diff_context: int = DEFAULT_DIFF_CONTEXT,
    diff_max_lines: int = DEFAULT_DIFF_MAX_LINES,
    diff_write_preview_lines: int = DEFAULT_DIFF_WRITE_PREVIEW_LINES,
    include_worktree: Path | None = None,
) -> tuple:
    """从 JSONL 抽 Write/Edit 事件的代码 + thinking。

    thinking 字段取自最近一条含 thinking 块的 assistant 消息(向前最多 thinking_lookback 步),
    同时记 thinking_offset = 回溯步数(0=同 message;1-N=前 N 条 message;None=未找到)。

    include_worktree: 若提供,扫 worktree 下源文件,与 JSONL 触过的文件对比,输出
    (events, untouched_files)。untouched_files 是 JSONL 视野盲区,LLM 必须自己 Read。
    """
    events = []

    # 第一遍:为每条 assistant message 解析 thinking 上下文
    # - 自身有 thinking 块 → (text, "self", 0)
    # - 自身无,前 N 条内有 → (text, "prior", N)
    # - 都没有 → 不进 line_thinking,第二遍用默认 ("", None, None)
    line_thinking = {}
    with jsonl_path.open("r", encoding="utf-8") as f:
        last_thinking_line = None
        last_thinking_text = ""
        for ln, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            msg, content_list = _parse_message(rec)
            if content_list is None:
                continue
            t = _extract_thinking(content_list)
            if t:
                last_thinking_line = ln
                last_thinking_text = t
                line_thinking[ln] = (t, "self", 0)
            elif last_thinking_line is not None and (ln - last_thinking_line) <= thinking_lookback:
                line_thinking[ln] = (last_thinking_text, "prior", ln - last_thinking_line)

    # 第二遍:抽 Write/Edit 事件,把 thinking 接上
    with jsonl_path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            msg, content_list = _parse_message(rec)
            if content_list is None:
                continue
            thinking_text, thinking_src, thinking_offset = line_thinking.get(ln, ("", None, None))

            for blk in content_list:
                if not isinstance(blk, dict) or blk.get("type") != BLK_TYPE_TOOL_USE:
                    continue
                name = blk.get("name")
                if name not in TOOL_NAMES:
                    continue
                inp = blk.get("input", {})
                fp = inp.get(INPUT_FILE_PATH, "")
                if not fp or not fp.endswith(SOURCE_EXTS):
                    continue
                if name == "Edit":
                    code = inp.get(INPUT_NEW_STRING, "")
                    old = inp.get(INPUT_OLD_STRING, "")
                    if old and old == code:
                        continue
                else:  # Write
                    code = inp.get(INPUT_CONTENT, "")
                    old = ""
                if not code or len(code) < min_code_len:
                    continue

                file_name = _file_name(fp)
                tu_id = blk.get(TOOL_USE_ID, "") or ""
                events.append({
                    "event_id": _event_id(tu_id, ln, file_name),
                    "tool_use_id": tu_id,  # 留底,便于 LLM 引用
                    "line": ln,
                    "file": file_name,
                    "full_path": fp,
                    "tool": name,
                    "code": code,
                    "old_code": old,
                    "code_diff": _make_diff(
                        old, code,
                        context=diff_context,
                        max_lines=diff_max_lines,
                        write_preview_lines=diff_write_preview_lines,
                    ),
                    "code_len": len(code),
                    "thinking": thinking_text,
                    "thinking_source": thinking_src,  # "self" | "prior" | None
                    "thinking_offset": thinking_offset,  # 0=同 message, 1-N=前 N 条
                    "ts": rec.get(TOP_TIMESTAMP),
                })

    # v1.3:扫 worktree,挑出 JSONL 未触碰的文件
    untouched_files: list[dict] = []
    if include_worktree is not None and include_worktree.exists():
        touched_files = {e["full_path"] for e in events}
        worktree_root = include_worktree.resolve()
        for src_path in worktree_root.rglob("*"):
            if not src_path.is_file():
                continue
            if not src_path.name.endswith(SOURCE_EXTS):
                continue
            # 跳过指定目录
            rel = src_path.relative_to(worktree_root)
            if any(part in WORKTREE_SKIP_DIRS for part in rel.parts):
                continue
            abs_path = str(src_path).replace("\\", "/")
            # 匹配方式:精确匹配绝对路径,或相对路径匹配(LLM 引用时常用相对)
            rel_posix = str(rel).replace("\\", "/")
            if abs_path in touched_files or rel_posix in touched_files:
                continue
            untouched_files.append({
                "path": abs_path,
                "rel_path": rel_posix,
                "size_bytes": src_path.stat().st_size,
            })
        # 按文件大小降序(优先看大文件,改动概率大)
        untouched_files.sort(key=lambda x: -x["size_bytes"])

    return events, untouched_files


def _find_touched_paths_from_jsonl(jsonl_path: Path) -> set:
    """第二遍扫描(从原始 JSONL)提取所有 full_path 集合 — 兜底,
    用于 worktree 扫描时容错:即使没跑 extract(),也能对比路径。"""
    paths = set()
    if not jsonl_path.exists():
        return paths
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            msg, content_list = _parse_message(rec)
            if content_list is None:
                continue
            for blk in content_list:
                if not isinstance(blk, dict) or blk.get("type") != BLK_TYPE_TOOL_USE:
                    continue
                name = blk.get("name")
                if name not in TOOL_NAMES:
                    continue
                fp = blk.get("input", {}).get(INPUT_FILE_PATH, "")
                if fp:
                    paths.add(str(fp).replace("\\", "/"))
    return paths


def write_summary(
    events: list,
    jsonl_path: Path,
    out_dir: Path,
    untouched_files: list[dict] | None = None,
    include_worktree: Path | None = None,
):
    """写 events.json + summary.md + worktree_gap.json(可选)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "events.json"
    json_out.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # v1.3:worktree_gap.json — 列出 JSONL 未触碰的源文件
    if untouched_files is not None and include_worktree is not None:
        gap_out = out_dir / "worktree_gap.json"
        gap_data = {
            "worktree_root": str(include_worktree.resolve()).replace("\\", "/"),
            "jsonl": str(jsonl_path).replace("\\", "/"),
            "untouched_files": untouched_files,
            "summary_stats": {
                "touched_files_count": len({e["full_path"] for e in events}),
                "untouched_files_count": len(untouched_files),
                "untouched_total_bytes": sum(f["size_bytes"] for f in untouched_files),
            },
            "warning": (
                "这些文件在 JSONL session 内**完全没被改过**。"
                "LLM 必须自己 Read 这些文件 + hdc 实测验证,"
                "否则会盲掉(参见 SKILL.md '输入分层' 段 / Bug 1+Bug 3 程序员模式锚点案例)。"
            ),
        }
        gap_out.write_text(
            json.dumps(gap_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 统计 thinking 命中率
    n_self = sum(1 for e in events if e["thinking_source"] == "self")
    n_prior = sum(1 for e in events if e["thinking_source"] == "prior")
    n_none = sum(1 for e in events if e["thinking_source"] is None)
    n_edit = sum(1 for e in events if e["tool"] == "Edit")
    n_write = sum(1 for e in events if e["tool"] == "Write")
    n_with_diff = sum(1 for e in events if e.get("code_diff"))

    md = [
        "# Code 事件摘要(给 LLM 分析用)",
        "",
        f"- **源**: {jsonl_path}",
        f"- **总事件**: {len(events)} 个 Write/Edit ({n_write} Write / {n_edit} Edit, {n_with_diff} 个有 diff)",
        f"- **thinking 命中**: {n_self} 同 message / {n_prior} 前 N message / {n_none} 未找到",
        "",
        "## 事件列表",
        "",
        "| event_id | Line | Tool | File | Code 字符数 | thinking 源 |",
        "|---|---|---|---|---|---|",
    ]
    for e in events:
        ts = e["thinking_source"] or "—"
        if ts == "prior" and e["thinking_offset"]:
            ts = f"prior-{e['thinking_offset']}"
        md.append(
            f"| `{e['event_id']}` | L{e['line']} | {e['tool']} | "
            f"`{e['file']}` | {e['code_len']} | {ts} |"
        )

    md += [
        "",
        "## 给 LLM 的指引",
        "",
        "对每个事件,按 7 角度思考(see references/code-issues-angles.md):",
        "1. State consistency(含 ArkUI 响应式追踪 / 跨文件 import 污染 / **回调契约错位**)",
        "2. Timing",
        "3. Defaults(含符号/方向/比较运算符反转 / **回调参数硬编码**)",
        "4. Verification",
        "5. Errors",
        "6. Resources",
        "7. **Build routing**(v1.3 新增 — build() 路由分支完整性)",
        "",
        "每个角度问子问题(见 angles.md)。命中就记 finding(严重度 critical/major/minor)。",
        "区分\"代码 bug 存在\"vs\"本次 session 实际触发\"。",
        "",
        "**v1.3 强制前置自检** (出报告前必做):",
        "1. **JSONL gap 分析** — 列出 events.json 里没出现的关键文件(若 --include-worktree,见 worktree_gap.json)",
        "2. **hdc 验证可行性** — UI / Build routing 类 finding 没 hdc dump 佐证 → 标 '未验证' + 严重度降一级",
        "3. **agent trail ≠ live bug** — agent 反复改同一区域 = 他当时碰到的错;但**未必是当前代码 bug**",
        "",
        "**优先关注**:",
        "- 改源码默认值的 Write(可能影响所有用户)",
        "- 改测试断言的 Edit(可能让 bug 漏检) — 看 events.json 的 `code_diff` 字段",
        "- thinking 块里 agent 自称『看起来对』『应该没问题』的推断(高频漏判区) — 见 events.json 的 `thinking` 字段(`thinking_source=prior-N` 时是前 N 条 message 的意图,不是同轮)",
        "- **同一文件被改 ≥ 5 次且方向反复横跳**(agent 探索 trail 标记,**必须** git diff 验证是否还在当前代码)",
        "",
        "**finding 模板新增 `代码 diff` 字段**(Edit 事件必填,Write 事件写关键片段):",
        "见 templates/llm-prompt-template.md",
    ]

    # v1.3:worktree gap 段
    if untouched_files is not None and include_worktree is not None:
        md += [
            "",
            "## ⚠️ JSONL 视野盲区(LLM 必须自己 Read)",
            "",
            f"- **worktree 根**: `{include_worktree}`",
            f"- **JSONL 已触碰的文件数**: {len({e['full_path'] for e in events})}",
            f"- **JSONL 未触碰的文件数**: {len(untouched_files)} (共 {sum(f['size_bytes'] for f in untouched_files):,} 字节)",
            "",
            "下列文件在本次 session 内**完全没被改过** — LLM 必须 Read 这些文件 + hdc 实测验证:",
            "",
            "| 路径 | 大小 |",
            "|---|---|",
        ]
        for f in untouched_files[:50]:  # 最多列 50
            md.append(f"| `{f['rel_path']}` | {f['size_bytes']:,} |")
        if len(untouched_files) > 50:
            md.append(f"| ... 还有 {len(untouched_files) - 50} 个文件未列出(完整列表见 worktree_gap.json) |")
        md += [
            "",
            "**为什么必须 Read?** :",
            "- JSONL only 视野 = agent 当天动过的那块代码,**≠** issue 完整 bug 集",
            "- 锚点案例:程序员模式 Bug 1(`onClick` 写死 DEC)在 JSONL 内**完整存在**于 worktree 但 agent 当天没改 `onClick` 语义,LLM 仅看 JSONL 看不到",
            "- 锚点案例:程序员模式 Bug 3(`build()` 路由错位)在 worktree 但 dev-01 当天没动 build() 段,JSONL 也看不到",
            "",
            "**怎么用**:",
            "- 找出 'untouched' 中跟 issue 相关的关键文件(例如 CalculatorPage.ets, ProgrammerPanel.ets)",
            "- Read 关键段落(build() / onClick / @Builder 等)",
            "- 跑 hdc dump / screenshot 验证(finding 落到 UI 层时)",
            "- 落进 report.md 的'JSONL gap 自检'段",
        ]

    md_out = out_dir / "summary.md"
    md_out.write_text("\n".join(md), encoding="utf-8")
    return json_out, md_out


def main():
    # v1.3:Windows GBK 控制台兼容 — 重设 stdout 为 utf-8 避免 print emoji 报错
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    p = argparse.ArgumentParser(
        description="Extract Write/Edit code events from JSONL (aid-code-root-cause)"
    )
    p.add_argument(
        "jsonl", type=Path, nargs="?",
        default=None,
        help="JSONL 文件路径(必传,不再有默认路径)",
    )
    p.add_argument(
        "-o", "--output-dir", type=Path,
        default=None,
        help=(
            "输出目录。默认: <jsonl_dir>/.claude/analysis-reports/code-root-cause/<session_id>/。"
            "注意:默认路径假设 JSONL 在 worktree 内的 .claude/ 目录;"
            "若 JSONL 在其他位置(如 <repo_root> 或临时目录),请用 -o 显式指定,避免污染项目根目录。"
        ),
    )
    p.add_argument(
        "--min-len", type=int, default=DEFAULT_MIN_CODE_LEN,
        help=f"代码长度门槛,低于此字符数丢弃(默认 {DEFAULT_MIN_CODE_LEN})",
    )
    p.add_argument(
        "--lookback", type=int, default=DEFAULT_THINKING_LOOKBACK,
        help=f"向前回溯 N 条 assistant 消息找 thinking 块(默认 {DEFAULT_THINKING_LOOKBACK})",
    )
    p.add_argument(
        "--diff-context", type=int, default=DEFAULT_DIFF_CONTEXT,
        help=f"unified_diff 的 context 行数(默认 {DEFAULT_DIFF_CONTEXT})",
    )
    p.add_argument(
        "--diff-max-lines", type=int, default=DEFAULT_DIFF_MAX_LINES,
        help=f"diff 总行数超过此值则截断(默认 {DEFAULT_DIFF_MAX_LINES})",
    )
    p.add_argument(
        "--diff-write-preview", type=int, default=DEFAULT_DIFF_WRITE_PREVIEW_LINES,
        help=f"Write 事件无 old 时 preview 前 N 行(默认 {DEFAULT_DIFF_WRITE_PREVIEW_LINES})",
    )
    p.add_argument(
        "--include-worktree", type=Path, default=None,
        help=(
            "(v1.3 新增)worktree 根目录路径。扫该目录下源文件,与 JSONL 触过的对比,"
            "输出 worktree_gap.json 列出未触碰的文件。LLM 必须 Read 这些文件 + hdc 实测,"
            "否则 JSONL-only 视野会盲掉(锚点案例:程序员模式 Bug 1+Bug 3)。"
        ),
    )
    args = p.parse_args()

    if not args.jsonl:
        p.error("必须传入 JSONL 文件路径(见 SKILL.md)")

    args.jsonl = args.jsonl.resolve()
    if not args.jsonl.exists():
        print(f"ERROR: JSONL not found: {args.jsonl}", file=sys.stderr)
        sys.exit(1)

    if args.output_dir:
        out_dir = args.output_dir.resolve()
    else:
        session_id = _clean_session_id(args.jsonl.stem)
        jsonl_dir = args.jsonl.parent
        out_dir = jsonl_dir / ".claude" / "analysis-reports" / "code-root-cause" / session_id

    print(f"=== aid-code-root-cause / 代码抽取 ===")
    print(f"源: {args.jsonl}")
    print(f"输出: {out_dir}")
    print()

    events, untouched_files = extract(
        args.jsonl,
        min_code_len=args.min_len,
        thinking_lookback=args.lookback,
        diff_context=args.diff_context,
        diff_max_lines=args.diff_max_lines,
        diff_write_preview_lines=args.diff_write_preview,
        include_worktree=args.include_worktree,
    )
    n_thinking = sum(1 for e in events if e["thinking"])
    print(f"抽到 {len(events)} 个 Write/Edit 事件,其中 {n_thinking} 个有 thinking 上下文")
    if args.include_worktree is not None:
        n_untouched = len(untouched_files)
        total_bytes = sum(f["size_bytes"] for f in untouched_files)
        print(f"worktree 未触碰文件数: {n_untouched} (共 {total_bytes:,} 字节)")
    print()

    json_out, md_out = write_summary(
        events, args.jsonl, out_dir,
        untouched_files=untouched_files if args.include_worktree else None,
        include_worktree=args.include_worktree,
    )
    print(f"  {json_out}")
    print(f"  {md_out}")
    if args.include_worktree is not None and untouched_files:
        print(f"  {out_dir / 'worktree_gap.json'}")
    print()
    print("下一步:LLM 读 events.json + worktree_gap.json + references/code-issues-angles.md,")
    print("       逐个 event 问 7 角度(按 summary.md 的优先级)")
    print("       ⚠️ 若有 worktree_gap.json,**必须** Read 标 [NOT-TOUCHED-BY-AGENT] 的文件")


if __name__ == "__main__":
    main()
