"""annotated_viewer.py — 把 annotated.jsonl 转成可搜索的 HTML 表格"""
import json
import html
from pathlib import Path
from collections import Counter

src = Path(r"D:\huawei\my_sessions\sessions\claude-code\dev-01\_raw\D--huawei-Demo-worktrees-issue-26\2026-06-17\264c5a16-f4f1-48ff-9f40-d215e1cc2567.annotated.jsonl")
out = Path(r"D:\huawei\Demo\annotated_viewer.html")

# 解析所有行
rows = []
with src.open("r", encoding="utf-8") as f:
    for line_no, line in enumerate(f, 1):
        rec = json.loads(line)
        msg = rec.get("message", {})
        # 取关键内容摘要
        content = msg.get("content", [])
        summary = ""
        if isinstance(content, list):
            for blk in content[:1]:
                if isinstance(blk, dict):
                    t = blk.get("type", "")
                    if t == "thinking":
                        summary = blk.get("thinking", "")[:150]
                    elif t == "text":
                        summary = blk.get("text", "")[:150]
                    elif t == "tool_use":
                        name = blk.get("name", "?")
                        inp = blk.get("input", {})
                        if name == "Skill":
                            summary = f"Skill({inp.get('skill', '?')}) args={inp.get('args', '')[:80]}"
                        elif name == "Bash":
                            summary = f"Bash: {(inp.get('command') or '')[:150]}"
                        elif name in ("Read", "Write", "Edit"):
                            summary = f"{name}: {(inp.get('file_path') or '')[:120]}"
                        else:
                            summary = f"{name}: {str(inp)[:120]}"
                    elif t == "tool_result":
                        s = str(blk.get("content", ""))[:150]
                        summary = f"→ {s}"
        elif isinstance(content, str):
            summary = content[:150]

        rows.append({
            "line": line_no,
            "type": rec.get("type", ""),
            "uuid": rec.get("uuid", "")[:8],
            "ts": rec.get("timestamp", "")[11:19],
            "skill": rec.get("attributionSkill") or "-",
            "section": rec.get("attributionSkillSection") or "-",
            "sub_skill": rec.get("attributionSubSkill") or "-",
            "conf": rec.get("attributionInferenceConfidence", 0.0),
            "method": rec.get("attributionInferenceMethod", "fallback"),
            "summary": summary,
        })

# 统计
skill_counter = Counter(r["skill"] for r in rows)
section_counter = Counter(f'{r["skill"]}:{r["section"]}' for r in rows)
method_counter = Counter(r["method"] for r in rows)

# 渲染 HTML
skill_options = "\n".join(
    f'<option value="{html.escape(s)}">{html.escape(s)} ({skill_counter[s]})</option>'
    for s in sorted(skill_counter.keys())
)
section_options = "\n".join(
    f'<option value="{html.escape(s)}">{html.escape(s)} ({section_counter[s]})</option>'
    for s in sorted(section_counter.keys(), key=lambda x: -section_counter[x])
)
method_options = "\n".join(
    f'<option value="{html.escape(m)}">{html.escape(m)} ({method_counter[m]})</option>'
    for m in sorted(method_counter.keys(), key=lambda x: -method_counter[x])
)

# 表格行
table_rows = "\n".join(
    f"""<tr data-line="{r['line']}" data-skill="{html.escape(r['skill'])}" data-section="{html.escape(r['section'])}" data-method="{html.escape(r['method'])}">
    <td class="num">{r['line']}</td>
    <td><span class="type type-{r['type'][:8]}">{r['type'][:14]}</span></td>
    <td class="ts">{r['ts']}</td>
    <td class="uuid">{r['uuid']}</td>
    <td class="skill">{html.escape(r['skill'])}</td>
    <td class="section">{html.escape(r['section'])}</td>
    <td class="sub">{html.escape(r['sub_skill'])}</td>
    <td class="conf conf-{int(r['conf']*10)//2}">{r['conf']:.2f}</td>
    <td class="method">{html.escape(r['method'])}</td>
    <td class="summary">{html.escape(r['summary'])}</td>
</tr>"""
    for r in rows
)

html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>annotated.jsonl Viewer - 264c5a16</title>
<style>
body{{font-family:-apple-system,Segoe UI,sans-serif;margin:0;background:#f5f5f5}}
header{{background:#2a78d6;color:#fff;padding:16px 24px;box-shadow:0 2px 8px #0002}}
h1{{margin:0;font-size:20px}}
.subtitle{{font-size:13px;opacity:0.85;margin-top:4px}}
.kpis{{display:flex;gap:12px;padding:16px 24px;background:#fff;border-bottom:1px solid #ddd;flex-wrap:wrap}}
.kpi{{background:#e3f2fd;padding:8px 14px;border-radius:6px;font-size:13px}}
.kpi b{{color:#2a78d6;font-size:18px;display:block}}
.controls{{padding:12px 24px;background:#fff;display:flex;gap:10px;flex-wrap:wrap;align-items:center;border-bottom:1px solid #ddd}}
.controls input,.controls select{{padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:13px}}
.controls input{{min-width:240px}}
table{{width:100%;border-collapse:collapse;font-size:12px;background:#fff}}
th{{background:#f0f0f0;text-align:left;padding:8px 10px;position:sticky;top:0;z-index:1;border-bottom:2px solid #888;font-weight:600}}
td{{padding:6px 10px;border-bottom:1px solid #eee;vertical-align:top}}
tr:hover{{background:#f5f9ff}}
.num{{color:#888;font-family:monospace;width:50px}}
.ts{{color:#888;font-family:monospace;width:60px}}
.uuid{{color:#888;font-family:monospace;font-size:11px;width:80px}}
.skill{{font-family:monospace;font-size:11px;width:120px}}
.section{{font-family:monospace;font-size:11px;width:130px;color:#666}}
.sub{{font-family:monospace;font-size:11px;width:160px;color:#888}}
.conf{{font-family:monospace;width:50px;text-align:right}}
.conf-0,.conf-1{{color:#999}}
.conf-2,.conf-3{{color:#d97706}}
.conf-4,.conf-5{{color:#f59e0b}}
.conf-6,.conf-7{{color:#65a30d}}
.conf-8,.conf-9,.conf-10{{color:#16a34a;font-weight:bold}}
.method{{font-size:10px;color:#888;width:120px}}
.type{{padding:1px 6px;border-radius:3px;font-size:11px;font-family:monospace;background:#e0e0e0}}
.type-assistant{{background:#dbeafe;color:#1e40af}}
.type-user{{background:#fef3c7;color:#92400e}}
.type-attachmen{{background:#f3e8ff;color:#6b21a8}}
.summary{{font-family:monospace;font-size:11px;color:#444;max-width:600px;word-break:break-all;line-height:1.4}}
footer{{padding:12px 24px;background:#fafafa;font-size:12px;color:#666;border-top:1px solid #ddd}}
#count{{font-weight:bold;color:#2a78d6}}
</style>
</head>
<body>
<header>
<h1>📋 annotated.jsonl Viewer</h1>
<div class="subtitle">Session 264c5a16-f4f1-48ff-9f40-d215e1cc2567 · 692 events · Mapped to skill:section:sub_skill</div>
</header>

<div class="kpis">
<div class="kpi"><b>{len(rows)}</b>total events</div>
<div class="kpi"><b>{sum(1 for r in rows if r['skill'] != '-')}</b>skill-attributed</div>
<div class="kpi"><b>{len(skill_counter) - (1 if '-' in skill_counter else 0)}</b>distinct skills</div>
<div class="kpi"><b>{len(section_counter) - (1 if '- in' in str(section_counter) else 0)}</b>distinct sections</div>
<div class="kpi"><b>{sum(1 for r in rows if r['sub_skill'] != '-')}</b>sub-skill hits</div>
<div class="kpi"><b>{sum(1 for r in rows if r['method'] == 'fallback')}</b>fallback (inherited)</div>
</div>

<div class="controls">
<input id="search" type="text" placeholder="搜索 summary / uuid / 段..." />
<select id="filter-skill"><option value="">— skill (all) —</option>{skill_options}</select>
<select id="filter-section"><option value="">— section (all) —</option>{section_options}</select>
<select id="filter-method"><option value="">— method (all) —</option>{method_options}</select>
<button onclick="resetFilters()" style="padding:6px 12px;background:#fff;border:1px solid #ccc;border-radius:4px;cursor:pointer">Reset</button>
<span style="margin-left:auto;font-size:13px">显示 <span id="count">0</span> / {len(rows)}</span>
</div>

<table id="tbl">
<thead>
<tr>
<th>line</th><th>type</th><th>time</th><th>uuid</th>
<th>skill</th><th>section</th><th>sub_skill</th>
<th>conf</th><th>method</th><th>summary</th>
</tr>
</thead>
<tbody>
{table_rows}
</tbody>
</table>

<footer>Generated by annotated_viewer.py · click any column header to sort (browser native) · use search/filter to narrow</footer>

<script>
const rows = document.querySelectorAll('#tbl tbody tr');
const search = document.getElementById('search');
const fs = document.getElementById('filter-skill');
const fc = document.getElementById('filter-section');
const fm = document.getElementById('filter-method');
const cnt = document.getElementById('count');

function apply() {{
  const q = search.value.toLowerCase();
  const s = fs.value;
  const c = fc.value;
  const m = fm.value;
  let n = 0;
  rows.forEach(r => {{
    const match = (!q || r.innerText.toLowerCase().includes(q))
      && (!s || r.dataset.skill === s)
      && (!c || r.dataset.section === c)
      && (!m || r.dataset.method === m);
    r.style.display = match ? '' : 'none';
    if (match) n++;
  }});
  cnt.textContent = n;
}}
[search, fs, fc, fm].forEach(el => el.addEventListener('input', apply));
function resetFilters() {{
  search.value = ''; fs.value = ''; fc.value = ''; fm.value = '';
  apply();
}}
apply();
</script>
</body></html>
"""

out.write_text(html_doc, encoding="utf-8")
print(f"OK: {out}")
print(f"     {len(rows)} events, {len(skill_counter)} skills, {len(section_counter)} sections")
print(f"     {sum(1 for r in rows if r['sub_skill'] != '-')} sub-skill hits")
print(f"     size: {out.stat().st_size:,} bytes")
