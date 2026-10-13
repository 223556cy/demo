"""
diff_visualizer.py — 把 expected/actual/diff 渲染成 HTML

布局:
  - Top: 摘要(总差异 + 分类 + 关键违规)
  - 中: 预期 vs 实际 双列卡片(每个调用的 skill)
  - 底: 完整 diff 列表
"""
import json
import html
from pathlib import Path


def render_html(expected: dict, actual: dict, diff: dict) -> str:
    css = """
    body{font-family:-apple-system,Segoe UI,sans-serif;margin:0;background:#fafafa;color:#222}
    header{background:linear-gradient(135deg,#2a78d6,#1e5bb8);color:#fff;padding:20px 24px;box-shadow:0 2px 8px #0002}
    h1{margin:0;font-size:22px}
    .sub{font-size:13px;opacity:0.9;margin-top:6px;font-family:monospace}
    .container{max-width:1400px;margin:0 auto;padding:16px}
    .summary{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap}
    .kpi{background:#fff;padding:14px 18px;border-radius:8px;box-shadow:0 1px 4px #0001;min-width:140px}
    .kpi-val{font-size:28px;font-weight:bold;color:#2a78d6}
    .kpi-lbl{font-size:12px;color:#888;margin-top:4px}
    .kpi-warn .kpi-val{color:#d97706}
    .kpi-err .kpi-val{color:#dc2626}
    .kpi-ok .kpi-val{color:#16a34a}
    h2{margin:24px 0 12px;font-size:16px;color:#444;border-bottom:2px solid #e5e5e5;padding-bottom:6px}
    .skills-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
    .card{background:#fff;border-radius:8px;padding:16px;box-shadow:0 1px 4px #0001}
    .card-title{font-size:15px;font-weight:600;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
    .badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .badge-ok{background:#dcfce7;color:#15803d}
    .badge-warn{background:#fef3c7;color:#a16207}
    .badge-err{background:#fee2e2;color:#b91c1c}
    .section-list{list-style:none;padding:0;margin:0}
    .section-list li{padding:4px 8px;margin:2px 0;border-radius:4px;font-size:13px;display:flex;align-items:center;gap:6px}
    .sec-mandatory{background:#fef9c3;color:#854d0e}
    .sec-done{background:#dcfce7;color:#14532d}
    .sec-missing{background:#fee2e2;color:#7f1d1d;text-decoration:line-through}
    .sec-extra{background:#e0e7ff;color:#3730a3}
    .sec-neutral{background:#f5f5f5;color:#525252}
    .icon-must::before{content:"⚠";color:#a16207}
    .icon-done::before{content:"✓";color:#15803d}
    .icon-miss::before{content:"✗";color:#b91c1c}
    .icon-neutral::before{content:"·";color:#999}
    details{background:#fff;border-radius:6px;padding:8px 12px;margin:4px 0;font-size:13px;border:1px solid #e5e5e5}
    summary{cursor:pointer;font-weight:500}
    .timeline{margin-top:16px;padding:12px;background:#fff;border-radius:8px;box-shadow:0 1px 4px #0001}
    .timeline-event{padding:6px 10px;margin:4px 0;border-left:3px solid #2a78d6;background:#f9fafb;border-radius:0 4px 4px 0;font-family:monospace;font-size:12px}
    .timeline-event .line{color:#888;font-weight:bold;margin-right:8px}
    .timeline-event .type{background:#2a78d6;color:#fff;padding:1px 6px;border-radius:3px;font-size:11px;margin-right:8px;font-family:sans-serif}
    .timeline-event .subskill{color:#a16207;font-style:italic}
    .timeline-event .product{color:#16a34a}
    .timeline-event .bash{color:#6366f1}
    .diff-table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px #0001}
    .diff-table th{background:#f0f0f0;text-align:left;padding:10px;font-weight:600;border-bottom:2px solid #ccc}
    .diff-table td{padding:8px 10px;border-bottom:1px solid #eee}
    .diff-warn{background:#fffbeb}
    .diff-info{background:#f0f9ff}
    .diff-row{font-family:monospace;font-size:12px}
    """

    # 摘要
    summary_html = f"""
    <div class="summary">
        <div class="kpi kpi-err"><div class="kpi-val">{diff['total_diffs']}</div><div class="kpi-lbl">总差异</div></div>
        <div class="kpi kpi-warn"><div class="kpi-val">{diff['severity_summary'].get('warn', 0)}</div><div class="kpi-lbl">⚠️ 警告</div></div>
        <div class="kpi"><div class="kpi-val">{diff['severity_summary'].get('info', 0)}</div><div class="kpi-lbl">ℹ️ 信息</div></div>
        <div class="kpi kpi-ok"><div class="kpi-val">{len(actual['skill_calls_sequence'])}</div><div class="kpi-lbl">Skill 调用</div></div>
        <div class="kpi kpi-ok"><div class="kpi-val">{len(actual['products'])}</div><div class="kpi-lbl">产物文件</div></div>
        <div class="kpi kpi-ok"><div class="kpi-val">{actual['total_events']}</div><div class="kpi-lbl">Timeline events</div></div>
    </div>
    """

    # 关键违规(severity=warn 的,过滤掉显然可争议的)
    critical = [d for d in diff["diffs"] if d["severity"] == "warn"]
    critical_html = "<h2>🔍 关键违规 (warn)</h2>"
    if not critical:
        critical_html += "<p style='color:#16a34a'>✅ 没有 warn 级违规</p>"
    else:
        critical_html += "<table class='diff-table'><thead><tr><th width='180'>类型</th><th width='200'>Skill</th><th width='200'>Section / Sub</th><th>详情</th></tr></thead><tbody>"
        for d in critical:
            sec_or_sub = d.get("section", "-")
            if "sub_skill" in d:
                sec_or_sub = f"→ {d['sub_skill']}"
            critical_html += f"""<tr class='diff-warn'>
                <td><span class='badge badge-warn'>{d['type']}</span></td>
                <td><b>{html.escape(d.get('skill', '?'))}</b></td>
                <td>{html.escape(sec_or_sub)}</td>
                <td class='diff-row'>{html.escape(d['detail'])}</td>
            </tr>"""
        critical_html += "</tbody></table>"

    # 双列卡片:每个调用的 skill 显示 expected sections vs actual sections
    skill_cards = "<h2>📊 Skill 维度对比 (预期 vs 实际)</h2><div class='skills-grid'>"
    for skill_name, run_info in actual["skill_runs"].items():
        if skill_name not in expected["skills"]:
            continue
        exp = expected["skills"][skill_name]
        # 预期 sections(mandatory)
        exp_mand = {s["id"] for s in exp["sections"] if s.get("mandatory")}
        # 实际 executed sections
        actual_secs = set(run_info.get("sections_executed", []))
        # 子 skill 调用
        subs_called = {s["sub_skill"] for s in run_info.get("sub_skills_called", [])}

        # 计算 missing/extra
        missing_mand = exp_mand - actual_secs
        missing_sub = {ms["sub_skill"] for ms in exp.get("sub_skills_required", []) if ms["sub_skill"] not in subs_called}

        # 卡片
        cards_inner = f"""<div class='card'>
            <div class='card-title'>
                <span>{html.escape(skill_name)}</span>
                <span>
                    {'<span class="badge badge-err">违规</span>' if missing_mand or missing_sub else '<span class="badge badge-ok">合规</span>'}
                </span>
            </div>"""

        # expected sections
        cards_inner += "<div style='font-size:12px;color:#888;margin:6px 0'>预期 mandatory 段:</div><ul class='section-list'>"
        for sec in exp["sections"]:
            if sec.get("mandatory"):
                in_actual = sec["id"] in actual_secs
                css_class = "sec-done" if in_actual else "sec-missing"
                icon = "icon-done" if in_actual else "icon-miss"
                cards_inner += f"""<li class='{css_class}'><span class='{icon}'></span>{html.escape(sec['id'])} — {html.escape(sec['title'])}</li>"""
        cards_inner += "</ul>"

        # 子 skill 调用
        if exp.get("sub_skills_required"):
            cards_inner += "<div style='font-size:12px;color:#888;margin:10px 0 6px'>强制子 skill:</div><ul class='section-list'>"
            for ms in exp["sub_skills_required"]:
                called = ms["sub_skill"] in subs_called
                css_class = "sec-done" if called else "sec-missing"
                icon = "icon-done" if called else "icon-miss"
                cards_inner += f"""<li class='{css_class}'><span class='{icon}'></span>skill('{html.escape(ms['sub_skill'])}') <small>(parent: {html.escape(ms['parent_section'])})</small></li>"""
            cards_inner += "</ul>"

        cards_inner += "</div>"
        skill_cards += cards_inner

    skill_cards += "</div>"

    # Timeline(实际执行顺序)
    timeline_html = "<h2>📜 实际执行 Timeline</h2><div class='timeline'>"
    for entry in actual["timeline"][:50]:  # 限 50
        ev_type = entry["type"]
        line = entry["line"]
        if ev_type == "skill_call":
            sub_marker = " <span class='subskill'>(sub-skill)</span>" if entry.get("is_sub_skill") else ""
            timeline_html += f"""<div class='timeline-event'><span class='line'>L{line}</span><span class='type'>Skill</span>调 <b>{html.escape(entry['skill'])}</b>{sub_marker}</div>"""
        elif ev_type == "product_write":
            timeline_html += f"""<div class='timeline-event'><span class='line'>L{line}</span><span class='type'>产出</span><span class='product'>{html.escape(entry['file'])}</span> ({html.escape(entry['skill'])}:{html.escape(entry.get('section', '-'))})</div>"""
        elif ev_type == "bash_action":
            timeline_html += f"""<div class='timeline-event'><span class='line'>L{line}</span><span class='type'>Bash</span><span class='bash'>{html.escape(entry.get('title', '?'))}</span></div>"""
    timeline_html += "</div>"

    # 全 diff 列表
    full_diff_html = "<h2>📋 完整 Diff 列表</h2><table class='diff-table'><thead><tr><th>类型</th><th>Severity</th><th>Skill</th><th>Section</th><th>详情</th></tr></thead><tbody>"
    for d in diff["diffs"]:
        sec = d.get("section", d.get("sub_skill", "-"))
        cls = "diff-warn" if d["severity"] == "warn" else "diff-info"
        full_diff_html += f"""<tr class='{cls}'>
            <td>{d['type']}</td>
            <td>{d['severity']}</td>
            <td><b>{html.escape(d.get('skill', '-'))}</b></td>
            <td>{html.escape(sec)}</td>
            <td class='diff-row'>{html.escape(d['detail'])}</td>
        </tr>"""
    full_diff_html += "</tbody></table>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Skill Diff: Expected vs Actual</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>🔬 Skill Diff Viewer — Expected vs Actual</h1>
<div class="sub">Session: {html.escape(actual['session_id'])} · 264c5a16 Issue #26 函数图像</div>
</header>
<div class="container">
{summary_html}
{critical_html}
{skill_cards}
{timeline_html}
{full_diff_html}
</div>
</body></html>
"""


if __name__ == "__main__":
    expected = json.loads(Path(r"D:\huawei\Demo\skill_expected.json").read_text(encoding="utf-8"))
    actual = json.loads(Path(r"D:\huawei\Demo\session_actual.json").read_text(encoding="utf-8"))
    diff = json.loads(Path(r"D:\huawei\Demo\skill_diff.json").read_text(encoding="utf-8"))
    out = Path(r"D:\huawei\Demo\skill_diff_viewer.html")

    html_doc = render_html(expected, actual, diff)
    out.write_text(html_doc, encoding="utf-8")
    print(f"OK: {out} ({out.stat().st_size:,} bytes)")