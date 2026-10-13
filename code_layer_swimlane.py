"""
code_layer_swimlane.py — v2:基于真实证据的代码层泳道图

不再手填 cell。从实际事件流读出:
- L580-590:Edit GraphPage.ets 改默认值
- L600+:rebuild + reinstall
- L427:screenshot/uitest 触发

横向 lane = 代码文件
纵向 = 事件时间
每个 cell = 该文件在该事件的内容(从 Edit 内容 / Bash 命令读出)
"""
import json
import re
from pathlib import Path
from collections import defaultdict


def collect_evidence(jsonl_path: Path, worktree: Path) -> dict:
    """从 JSONL 抽:(line, layer, content, type)"""
    events = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            rec = json.loads(line)
            msg = rec.get("message", {})
            content_list = msg.get("content", []) if isinstance(msg.get("content"), list) else []

            # Edit / Write 工具
            for blk in content_list:
                if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                    continue
                name = blk.get("name")
                if name in ("Edit", "Write"):
                    fp = blk.get("input", {}).get("file_path", "")
                    # 找文件名(去掉 worktree 前缀)
                    try:
                        rel = str(Path(fp).resolve().relative_to(worktree.resolve()))
                    except ValueError:
                        rel = fp.split("/")[-1].split("\\")[-1]
                    inp = blk.get("input", {})
                    events.append({
                        "line": ln,
                        "type": name,
                        "file": rel,
                        "old": (inp.get("old_string") or "")[:100],
                        "new": (inp.get("new_string") or "")[:100],
                        "ts": rec.get("timestamp"),
                    })
                elif name == "Bash":
                    cmd = blk.get("input", {}).get("command", "")
                    # UI 测试命令
                    if any(kw in cmd for kw in ["hdc list", "hdc tconn", "hdc install", "hdc shell uitest", "screencap", "dumpLayout"]):
                        events.append({
                            "line": ln,
                            "type": "Bash",
                            "file": "hdc(deploy/test)",
                            "command": cmd[:150],
                            "ts": rec.get("timestamp"),
                        })
    return events


def build_html(events: list, worktree: Path) -> str:
    """基于 events 构建泳道图"""

    # Lane = 文件
    files = sorted(set(e["file"] for e in events if e["file"] != "hdc(deploy/test)"))
    files.append("hdc(deploy/test)")

    # Time events 按 line 排序
    sorted_events = sorted(events, key=lambda e: e["line"])

    css = """
    *{box-sizing:border-box}
    body{font-family:-apple-system,Segoe UI,sans-serif;margin:0;padding:24px;background:#fafafa;color:#222}
    h1{margin:0 0 8px;font-size:22px}
    .sub{color:#666;font-size:13px;margin-bottom:20px}
    .swim{display:grid;gap:1px;background:#ddd;border:1px solid #ccc;border-radius:6px;overflow:hidden;font-size:12px;font-family:monospace}
    .swim .h{background:#2a78d6;color:#fff;padding:8px;font-weight:600;text-align:center;font-size:12px}
    .swim .h.row{background:#1e5bb8}
    .swim .lane{background:#f5f5f5;padding:8px;font-weight:600;font-size:11px}
    .swim .cell{background:#fff;padding:6px;font-size:11px;line-height:1.4;border-left:3px solid transparent}
    .swim .cell.empty{background:#fafafa;color:#ccc}
    .swim .cell.write{background:#fef3c7;border-left-color:#f59e0b}
    .swim .cell.edit{background:#fee2e2;border-left-color:#dc2626}
    .swim .cell.bash{background:#dbeafe;border-left-color:#3b82f6}
    .legend{margin:20px 0;padding:14px;background:#fff;border-radius:6px;border:1px solid #e5e5e5;font-size:13px}
    .legend span{display:inline-block;padding:3px 10px;margin:0 8px 0 0;border-radius:4px;font-family:monospace;font-size:11px}
    """

    # 构建表头
    max_per_col = max((sum(1 for e in sorted_events if e["file"] == f) for f in files), default=1)
    n_cols = max(len(sorted_events), 5)

    # 用 HTML table 网格(grid-template-columns 不灵活,改用 table)
    rows_html = []

    # 表头(列名 = 事件 line + 类型)
    header_cells = '<th>Line ↓ / File →</th>'
    for f in files:
        short = f.replace("opencalc/entry/src/main/ets/", "").replace("specs/changes/20260617-requirement-add-plot-graph/", "")
        header_cells += f'<th style="writing-mode:vertical-lr;min-width:60px">{short}</th>'
    rows_html.append(f"<tr>{header_cells}</tr>")

    # 行 = 事件(每个事件一行,看哪些文件参与了)
    for i, e in enumerate(sorted_events):
        row_cells = f'<td style="background:#f0f0f0;font-weight:600;padding:4px 8px;min-width:80px">L{e["line"]}<br><small style="font-weight:normal;color:#666">{e["type"]}</small></td>'
        for f in files:
            if e["file"] == f:
                if e["type"] == "Edit":
                    content = f'<div style="color:#dc2626;font-weight:bold">EDIT</div><div>- {e["old"][:60]}...</div><div>+ {e["new"][:60]}...</div>'
                    row_cells += f'<td class="cell edit">{content}</td>'
                elif e["type"] == "Write":
                    content = f'<div style="color:#a16207;font-weight:bold">WRITE</div><div>{e["new"][:100]}...</div>'
                    row_cells += f'<td class="cell write">{content}</td>'
                elif e["type"] == "Bash":
                    content = f'<div style="color:#1e40af;font-weight:bold">Bash</div><div>{e["command"][:120]}</div>'
                    row_cells += f'<td class="cell bash">{content}</td>'
                else:
                    row_cells += f'<td class="cell">{e.get("command", e.get("old", ""))[:100]}</td>'
            else:
                row_cells += '<td class="cell empty"></td>'
        rows_html.append(f"<tr>{row_cells}</tr>")

    legend_html = """
    <div class="legend">
      <strong>图例:</strong>
      <span class="cell edit">Edit 改源码</span>
      <span class="cell write">Write 新建文件</span>
      <span class="cell bash">Bash 部署/测试</span>
      <span class="cell empty">该文件无操作</span>
    </div>
    """

    # 提取关键洞察
    insight_html = """
    <h2 style="margin-top:30px">📌 关键洞察(基于证据)</h2>
    <ol style="line-height:1.8;font-size:14px">
      <li><b>L580-590 Edit GraphPage.ets</b>: agent 修改默认值 <code>-6.283185307 → '-2'</code>(以为是"用户输入")</li>
      <li><b>no tap/input 命令</b>: agent 没真去模拟器点 TextInput,改源码后 rebuild + reinstall</li>
      <li><b>aboutToAppear 不会从 TextInput 默认值同步到 vm.xMin</b>:所以 vm.xMin 仍是 GraphViewModel 默认的 <code>-2*Math.PI</code></li>
      <li><b>绘制按钮点一次 → vm.compute() 用 vm.xMin=-2π → 渲染 -2π 到 2π 的曲线</b>(不是 -2 到 2)</li>
      <li><b>真正的 root cause</b>: <code>@State xMinInput</code> 和 <code>vm.xMin</code> 在 <code>aboutToAppear</code> 没建立初始同步,改源码默认值不会影响 vm</li>
    </ol>
    """

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Code Layer Swim Lane (evidence-based)</title>
<style>{css}</style>
</head>
<body>
<h1>🏊 代码层泳道图(基于证据)</h1>
<div class="sub">264c5a16 Issue #26 · 行=事件流(从上到下) · 列=代码文件</div>
{legend_html}
<table class="swim" style="width:100%;border-collapse:collapse">
{"".join(rows_html)}
</table>
{insight_html}
</body></html>
"""


if __name__ == "__main__":
    jsonl = Path(r"D:\huawei\my_sessions\sessions\claude-code\dev-01\_raw\D--huawei-Demo-worktrees-issue-26\2026-06-17\264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl")
    worktree = Path(r"D:\huawei\Demo\worktrees\issue-26")

    events = collect_evidence(jsonl, worktree)
    print(f"共收集 {len(events)} 个证据事件")

    html = build_html(events, worktree)
    out = Path(r"D:\huawei\Demo\code_layer_swimlane_v2.html")
    out.write_text(html, encoding="utf-8")
    print(f"OK: {out} ({out.stat().st_size:,} bytes)")