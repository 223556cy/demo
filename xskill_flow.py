"""
xskill_flow.py - 把 AID skill 目录解析成跨 skill 数据流图

输入: 一个 .claude/skills/ 目录(含 aid-planning / aid-implementing / aid-applying 等)
输出: Mermaid 图 + 结构化字典

用法:
    from xskill_flow import parse_aid_workflow, build_xskill_mermaid
    wf = parse_aid_workflow("D:/huawei/Demo/calculatorHuawei/.claude/skills")
    print(build_xskill_mermaid(wf))
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================
# 1. Markdown section 切分
# ============================================================

def _split_markdown_sections(md_text: str) -> List[dict]:
    """按 heading 切分 markdown,保留层级"""
    lines = md_text.split("\n")
    sections, current = [], None
    for line in lines:
        m = re.match(r"^(#+)\s+(.+)$", line)
        if m:
            if current is not None:
                sections.append(current)
            current = {
                "level": len(m.group(1)),
                "title": m.group(2).strip(),
                "body_lines": [],
            }
        else:
            if current is not None:
                current["body_lines"].append(line)
    if current is not None:
        sections.append(current)
    for s in sections:
        s["body"] = "\n".join(s["body_lines"]).strip()
    return sections


# ============================================================
# 2. Step title 解析
# ============================================================

# 容忍多种 step_id 写法:
#   step1           (无下标)
#   step1.1         (aid-planning 用 . 不是 -)
#   step3-0         (aid-applying 顶层)
#   step3-0-1       (aid-applying 子步骤)
#   step3-2-2b      (数字 + 字母后缀)
#   step3-2-2b-降级  (字母 + 中文后缀,如 aid-applying 铁律 7 段)
STEP_ID_RE = re.compile(
    r"^(step\d+(?:[-.][a-zA-Z0-9_一-鿿]+)*)"
)


def _parse_step_title(title: str) -> Optional[Tuple[str, str]]:
    """从 heading 文本里抽 step_id 和名字。
    贪心匹配 step_id 字符,跳过可选分隔符(:/：),剩余为 name。"""
    t = title.strip()
    if not t.lower().startswith("step"):
        return None
    m = STEP_ID_RE.match(t)
    if not m:
        return None
    step_id_raw = m.group(1)
    rest = t[len(step_id_raw):].strip()
    # 容忍分隔符(中文/英文冒号)
    rest = re.sub(r"^[：:]\s*", "", rest)
    # 统一把 . 替换成 - 以便和文件引用对齐
    step_id = step_id_raw.replace(".", "-")
    return step_id, rest


# ============================================================
# 3. 单 skill 解析
# ============================================================

PRODUCES_PATTERNS = [
    r"\*\*产物[^*]*?\*\*[：:]\s*(.+?)(?=\n\n|\n###|\n##|\Z)",
    r"\*\*输出[^*]*?\*\*[：:]\s*(.+?)(?=\n\n|\n###|\n##|\Z)",
    r"\*\*主要产出[^*]*?\*\*[：:]\s*(.+?)(?=\n\n|\n###|\n##|\Z)",
    # 兜底:在 X 中产出/写入/输出
    r"在\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))\s*[`'\"]?\s*中[产出写入输出]",
    r"产出\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
    r"写入\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
]
CONSUMES_PATTERNS = [
    r"\*\*输入[^*]*?\*\*[：:]\s*(.+?)(?=\n\n|\n###|\n##|\Z)",
    r"\*\*前置条件[^*]*?\*\*[：:](.+?)(?=\n\n|\n###|\n##|\Z)",
    r"\*\*确认.{0,5}已满足[^*]*?\*\*[：:](.+?)(?=\n\n|\n###|\n##|\Z)",
    # 兜底:阅读/加载/根据 X
    r"阅读\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
    r"加载\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
    r"根据\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))\s*中",
    r"参考\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
    r"按照\s*[`'\"]?([^`'\"]*\.(?:md|json|yaml|yml|toml))",
]
FILE_PATTERNS = [
    r"`?([\w/\\.:-]+\.(?:md|ets|ts|tsx|js|mjs|json|yaml|yml|toml|py|bat|sh|txt))`?",
]
CROSSREF_PATTERNS = [
    r"在\s*(step\d+(?:-\d+)*)\s*[之前前]",
    r"必须先[有执完成]?\s*(step\d+(?:-\d+)*)",
    r"参考\s*(step\d+(?:-\d+)*)",
    r"依赖\s*(step\d+(?:-\d+)*)",
    r"step\s*(step\d+(?:-\d+)*)\s*必须",
]
SKILL_CALL_RE = re.compile(r"""skill\(\s*['"]([\w-]+)['"]\s*\)""")
SKILL_FILE_REF_RE = re.compile(
    r"`([\w/\\.:{}-一-鿿]+\.(?:md|ets|json|yaml|yml|toml))`")


def parse_skill_to_dag(skill_md_path: str) -> dict:
    """解析单个 SKILL.md -> 内部 DAG + 产物/消费 + 文件引用"""
    md_text = Path(skill_md_path).read_text(encoding="utf-8")
    sections = _split_markdown_sections(md_text)

    skill_name = Path(skill_md_path).parent.name
    steps: Dict[str, dict] = {}
    top_flow: List[str] = []
    last_step_by_level: Dict[int, str] = {}

    for sec in sections:
        parsed = _parse_step_title(sec["title"])
        if not parsed:
            continue
        step_id, name = parsed

        parent_step = None
        for lvl in range(sec["level"] - 1, 1, -1):
            if lvl in last_step_by_level:
                parent_step = last_step_by_level[lvl]
                break

        node = {
            "step_id": step_id,
            "name": name,
            "level": sec["level"],
            "section": parent_step or "",
            "body": sec["body"],
            "consumes": [],
            "produces": [],
            "cross_refs": [],
            "files_in": [],
            "files_out": [],
            "skill_calls": [],
        }
        steps[step_id] = node
        last_step_by_level[sec["level"]] = step_id
        for k in list(last_step_by_level.keys()):
            if k > sec["level"]:
                del last_step_by_level[k]

        # 顶层 step 进入 top_flow:无父 step(section 为空)的 step
        if not parent_step:
            top_flow.append(step_id)

    # 抽 consumes / produces / cross_refs / files / skill_calls
    for step_id, node in steps.items():
        body = node["body"]

        for pat in PRODUCES_PATTERNS:
            for m in re.finditer(pat, body, re.MULTILINE | re.DOTALL):
                items = re.split(r"[\n;,、]", m.group(1))
                node["produces"].extend(
                    x.strip("-*· ").strip() for x in items
                    if x.strip() and len(x.strip()) < 200
                )
        for pat in CONSUMES_PATTERNS:
            for m in re.finditer(pat, body, re.MULTILINE | re.DOTALL):
                items = re.split(r"[\n;,、]", m.group(1))
                node["consumes"].extend(
                    x.strip("-*· ").strip() for x in items
                    if x.strip() and len(x.strip()) < 200
                )

        for pat in CROSSREF_PATTERNS:
            for m in re.finditer(pat, body):
                ref = m.group(1)
                if ref != step_id and ref in steps:
                    node["cross_refs"].append(ref)

        for f in SKILL_FILE_REF_RE.findall(body):
            node["files_in"].append(f)
            node["files_out"].append(f)

        for m in SKILL_CALL_RE.finditer(body):
            node["skill_calls"].append(m.group(1))

        # 5e) markdown table 解析 — aid-planning 风格的"步骤 / 产出"表
        #    找表格行 "| stepN | ... | 产出 X | skill |"
        for line in body.split("\n"):
            line_s = line.strip()
            if not line_s.startswith("|"):
                continue
            cells = [c.strip() for c in line_s.split("|")[1:-1]]
            if len(cells) < 3:
                continue
            # aid-planning 表头顺序:步骤|名称|主要产出|必须使用的 Skill
            # 找含 "step" 关键词 + 数字的 cell 判断这行属于哪个 step
            row_step_id = None
            for c in cells:
                m = re.search(r"(step\d+(?:[-.]\d+)*)", c)
                if m:
                    row_step_id = m.group(1).replace(".", "-")
                    break
            if row_step_id != step_id:
                continue
            # 找含文件名的 cell 视为 produces
            for c in cells:
                fname = re.search(r"([\w/\\.:-]+\.(?:md|json|yaml|yml|toml))", c)
                if fname:
                    node["produces"].append(fname.group(1))

    # 内部 consumes_edges (sequence + cross_ref)
    edges = []
    by_section: Dict[str, List[str]] = {}
    for sid, n in steps.items():
        by_section.setdefault(n["section"] or "__root__", []).append(sid)
    for sec, ids in by_section.items():
        for i in range(len(ids) - 1):
            a, b = ids[i], ids[i + 1]
            for prod in steps[a]["produces"]:
                edges.append({"from": a, "to": b, "data": prod,
                              "via": "sequence"})
    for sid, n in steps.items():
        for ref in n["cross_refs"]:
            for prod in steps[ref]["produces"]:
                edges.append({"from": ref, "to": sid, "data": prod,
                              "via": "crossref"})

    return {
        "skill_name": skill_name,
        "top_flow": top_flow,
        "steps": steps,
        "consumes_edges": edges,
    }


def parse_skill_call_chain(skill_md_path: str) -> List[Tuple[str, str]]:
    md_text = Path(skill_md_path).read_text(encoding="utf-8")
    sections = _split_markdown_sections(md_text)
    calls = []
    for sec in sections:
        parsed = _parse_step_title(sec["title"])
        if not parsed:
            continue
        step_id, _ = parsed
        body = sec["body"]
        for m in SKILL_CALL_RE.finditer(body):
            calls.append((step_id, m.group(1)))
    return calls


# ============================================================
# 4. 跨 skill DAG
# ============================================================

def parse_aid_workflow(skills_dir: str) -> dict:
    """解析整个 .claude/skills/ 目录,构建跨 skill 数据流图"""
    skills_root = Path(skills_dir)
    skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()
                  and (d / "SKILL.md").exists()
                  and not d.name.endswith(".bak")]

    per_skill_dags = {}
    per_skill_calls = {}
    for sd in skill_dirs:
        name = sd.name
        per_skill_dags[name] = parse_skill_to_dag(str(sd / "SKILL.md"))
        per_skill_calls[name] = parse_skill_call_chain(str(sd / "SKILL.md"))

    # 跨 skill 文件边
    file_producer_index: Dict[str, Tuple[str, str]] = {}
    file_consumer_index: Dict[str, List[Tuple[str, str]]] = {}

    # 允许中文字符 + 模板占位符的 file path 正则
    FILE_PATH_RE = re.compile(
        r"[\w/\\.:{}-一-鿿]+\.(?:md|json|yaml|yml|toml)"
    )

    for skill_name, dag in per_skill_dags.items():
        for step_id, node in dag["steps"].items():
            for f in node["files_in"]:
                file_consumer_index.setdefault(f, []).append((skill_name, step_id))
            for prod in node["produces"]:
                for f in FILE_PATH_RE.findall(prod):
                    if f not in file_producer_index:
                        file_producer_index[f] = (skill_name, step_id)

    cross_file_edges = []
    # 用 basename + 完整路径两种方式做匹配(因为 producer 和 consumer 可能用不同写法)
    def _file_keys(f: str) -> List[str]:
        """给一个文件路径返回所有可匹配的 key"""
        keys = [f]  # 完整路径
        # basename
        bn = re.split(r"[\\/]", f)[-1]
        if bn != f:
            keys.append(bn)
        # 去模板前缀的 basename
        for prefix in ("{CHANGES_ROOT}/", "{CHANGES_ROOT}\\"):
            if f.startswith(prefix):
                stripped = f[len(prefix):]
                keys.append(stripped)
                keys.append(re.split(r"[\\/]", stripped)[-1])
        return list(set(keys))

    # 给 producer 和 consumer 都用 keys 索引
    producer_keys: Dict[str, Tuple[str, str]] = {}
    for f, (skill, step) in file_producer_index.items():
        for k in _file_keys(f):
            producer_keys.setdefault(k, (skill, step))

    for f, consumers in file_consumer_index.items():
        for cons_skill, cons_step in consumers:
            for k in _file_keys(f):
                if k in producer_keys:
                    prod_skill, prod_step = producer_keys[k]
                    if cons_skill == prod_skill:
                        continue
                    cross_file_edges.append({
                        "file": f, "from_skill": prod_skill,
                        "from_step": prod_step, "to_skill": cons_skill,
                        "to_step": cons_step,
                    })
                    break  # 一对配一次即可

    # 去重
    seen = set()
    deduped = []
    for e in cross_file_edges:
        key = (e["file"], e["from_skill"], e["from_step"],
               e["to_skill"], e["to_step"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    cross_file_edges = deduped

    # 跨 skill 调用边
    cross_call_edges = []
    for caller_skill, calls in per_skill_calls.items():
        for caller_step, sub_skill in calls:
            cross_call_edges.append({
                "from_skill": caller_skill,
                "from_step": caller_step,
                "sub_skill": sub_skill,
            })

    top_order = ["aid-init", "aid-planning", "aid-implementing",
                 "aid-applying", "aid-archiving", "aid-monitor"]
    top_flow = [s for s in top_order if s in per_skill_dags]

    return {
        "top_flow": top_flow,
        "skills": {n: {"dag": d, "calls": per_skill_calls[n]}
                   for n, d in per_skill_dags.items()},
        "cross_file_edges": cross_file_edges,
        "cross_call_edges": cross_call_edges,
    }


# ============================================================
# 5. Mermaid 可视化
# ============================================================

XSKILL_EDGE_STYLES = {
    "file_produce": {"arrow": "-->",  "label": "产出", "color": "#43a047"},
    "file_consume": {"arrow": "-.->", "label": "消费", "color": "#1e88e5"},
    "skill_call":   {"arrow": "==>",  "label": "调用", "color": "#8e24aa"},
    "top_flow":     {"arrow": "==>",  "label": "→",    "color": "#616161"},
}


def _sanitize_mermaid(text: str, limit: int = 40) -> str:
    if not text:
        return ""
    safe = re.sub(r"[^\w一-龥\s._/-]", " ", str(text))
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe[:limit] + ("…" if len(safe) > limit else "")


def build_xskill_mermaid(workflow: dict,
                         focus_skills: Optional[List[str]] = None) -> str:
    """
    把跨 skill 数据流图渲染成 Mermaid。
    focus_skills: 只画这些 skill(及它们的直接邻居);None 表示全画
    """
    lines = ["graph LR"]
    # 样式定义
    lines.append("    classDef skill fill:#fff3e0,stroke:#fb8c00,"
                 "stroke-width:2px,color:#000;")
    lines.append("    classDef step fill:#e8f5e9,stroke:#43a047,color:#000;")
    lines.append("    classDef file fill:#e3f2fd,stroke:#1e88e5,color:#000;")
    lines.append("    classDef call fill:#f3e5f5,stroke:#8e24aa,color:#000;")
    lines.append("    classDef flow fill:#fffde7,stroke:#fbc02d,"
                 "stroke-width:2px,color:#000;")

    skills = workflow["skills"]
    cross_file = workflow["cross_file_edges"]
    cross_call = workflow["cross_call_edges"]
    top_flow = workflow["top_flow"]

    # 决定画哪些 skill
    if focus_skills:
        target_skills = set(focus_skills)
        # 把有直接关系的邻居也加进来
        for e in cross_file + cross_call:
            target_skills.add(e.get("from_skill", ""))
            target_skills.add(e.get("to_skill", ""))
            target_skills.add(e.get("sub_skill", ""))
    else:
        target_skills = set(skills.keys())

    # 1) 每个 skill 一个 subgraph,内部画 step
    skill_node_ids: Dict[str, str] = {}
    file_node_ids: Dict[str, str] = {}
    call_node_ids: Dict[str, str] = {}
    next_id = [0]

    def nid():
        next_id[0] += 1
        return f"N{next_id[0]}"

    edges_mermaid = []

    for skill_name in sorted(skills.keys()):
        if skill_name not in target_skills:
            continue
        dag = skills[skill_name]["dag"]

        sid = nid()
        skill_node_ids[skill_name] = sid
        # skill 节点本身(作为 subgraph 入口)
        label = f"📦 {_sanitize_mermaid(skill_name, 20)}"
        # 这里用 subgraph 而不是普通节点
        lines.append(f'    subgraph {sid}["{label}"]')
        lines.append("        direction TB")

        # 在 subgraph 里画顶层 step (top_flow) 和它的产物文件
        for step_id in dag["top_flow"]:
            if step_id not in dag["steps"]:
                continue
            node = dag["steps"][step_id]
            sp_id = nid()
            sp_label = f"{_sanitize_mermaid(node['name'], 30)}"
            lines.append(f'        {sp_id}["⚙️ {step_id}<br/>{sp_label}"]:::step')

            # 找该 step 显式产出的文件
            for prod in node["produces"]:
                files = re.findall(
                    r"[\w/\\.:-]+\.(?:md|json|yaml|yml|toml)", prod)
                for f in files:
                    if f not in file_node_ids:
                        fid = nid()
                        file_node_ids[f] = fid
                        # 文件节点放在 subgraph 里
                        fname = _sanitize_mermaid(f.split("/")[-1], 25)
                        lines.append(f'        {fid}["📄 {fname}"]:::file')
                    edges_mermaid.append(
                        (sp_id, file_node_ids[f], "file_produce", False))

        # skill_call 节点(在 subgraph 里画指向外部的调用)
        for caller_step, sub_skill in skills[skill_name]["calls"]:
            if sub_skill not in target_skills:
                continue
            # 给这个 caller step 一个标记
            # 简化:不画 caller step 节点,直接画 call 节点
            call_key = f"{skill_name}.{caller_step}->{sub_skill}"
            if call_key in call_node_ids:
                continue
            call_id = nid()
            call_node_ids[call_key] = call_id
            lines.append(f'        {call_id}["🎯 skill({sub_skill})"]:::call')
            # caller step 节点 - 简化:不画,直接连 call
            edges_mermaid.append(
                (sid, call_id, "skill_call", True))  # cross subgraph

        lines.append("    end")

    # 2) 跨 skill 文件边
    for e in cross_file:
        if (e["from_skill"] not in target_skills
                or e["to_skill"] not in target_skills):
            continue
        f = e["file"]
        if f not in file_node_ids:
            fid = nid()
            file_node_ids[f] = fid
            fname = _sanitize_mermaid(f.split("/")[-1], 25)
            # 跨 skill 的文件放外面
            lines.append(f'    {fid}["📄 {fname}"]:::file')
        src_skill_id = skill_node_ids.get(e["from_skill"])
        dst_skill_id = skill_node_ids.get(e["to_skill"])
        if src_skill_id and dst_skill_id:
            edges_mermaid.append(
                (file_node_ids[f], dst_skill_id,
                 "file_consume", True))  # 跨 subgraph

    # 3) 顶层 AID flow 边
    for i in range(len(top_flow) - 1):
        if top_flow[i] in skill_node_ids and top_flow[i + 1] in skill_node_ids:
            edges_mermaid.append(
                (skill_node_ids[top_flow[i]],
                 skill_node_ids[top_flow[i + 1]],
                 "top_flow", True))

    # 4) 把跨 subgraph 的 call 边连到目标 skill
    for key, call_id in call_node_ids.items():
        parts = key.split("->")
        if len(parts) != 2:
            continue
        target_skill = parts[1]
        if target_skill in skill_node_ids:
            edges_mermaid.append(
                (call_id, skill_node_ids[target_skill],
                 "skill_call", True))

    # 5) 输出所有边 + linkStyle
    for i, (src, dst, kind, cross) in enumerate(edges_mermaid):
        style = XSKILL_EDGE_STYLES[kind]
        width = "2.5px" if cross else "1.5px"
        lines.append(f'    {src} {style["arrow"]}|{style["label"]}| {dst}')
        lines.append(
            f'    linkStyle {i} stroke:{style["color"]},'
            f'stroke-width:{width}{",stroke-dasharray:5 5" if "-.->" in style["arrow"] else ""};')

    # 6) 图例
    lines.append("")
    lines.append("    %% 图例:")
    lines.append("    %% 📦 skill  ⚙️ step  📄 file  🎯 skill() call")
    lines.append("    %% 🟢 实线绿 = 产出   🔵 虚线蓝 = 消费   "
                 "🟣 双线紫 = sub-skill 调用   ⬛ 双线灰 = 顶层 AID flow")
    return "\n".join(lines)


# ============================================================
# 6. 命令行入口
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python xskill_flow.py <skills_dir> [focus_skill1,focus_skill2,...]")
        sys.exit(1)

    skills_dir = sys.argv[1]
    focus = sys.argv[2].split(",") if len(sys.argv) > 2 else None

    wf = parse_aid_workflow(skills_dir)
    print(f"## 解析结果\n")
    print(f"- Skill 数: {len(wf['skills'])}")
    print(f"- 顶层 flow: {' → '.join(wf['top_flow'])}")
    print(f"- 跨 skill 文件边: {len(wf['cross_file_edges'])}")
    print(f"- 跨 skill skill() 调用边: {len(wf['cross_call_edges'])}")
    print(f"\n## Mermaid 图\n")
    print("```mermaid")
    print(build_xskill_mermaid(wf, focus))
    print("```")
