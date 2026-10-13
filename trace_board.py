import json
import os
import re
import streamlit as st
import streamlit_antd_components as sac
from typing import Dict, List, Tuple, Optional

# ==========================================
# ⚙️ 1. 配置常量
# ==========================================
BASH_NAV = {"cd", "pwd", "ls", "mkdir", "pushd", "popd", "rmdir"}
BASH_INFO = {"cat", "head", "tail", "find", "grep", "wc", "echo", "env",
             "tree", "which", "file", "stat", "du", "df"}

CONTRACT_EXTS = {".md", ".yaml", ".yml", ".json", ".toml"}

ERROR_CATEGORIES = {
    "Network":      ["Connection refused", "ETIMEDOUT", "getaddrinfo failed",
                     "DNS", "ECONNRESET"],
    "Timeout":      ["timed out", "TimeoutExpired", "deadline exceeded"],
    "Permission":   ["Permission denied", "EACCES", "EPERM", "forbidden"],
    "FileNotFound": ["No such file", "FileNotFoundError", "ENOENT"],
    "BuildError":   ["SyntaxError", "IndentationError", "could not compile",
                     "tsc error", "eslint"],
    "GitError":     ["CONFLICT", "merge failed", "rejected",
                     "non-fast-forward", "fatal: pathspec"],
    "RuntimeError": ["Traceback", "Exception", "panic"],
    "EditError":    ["String to replace not found", "String not found",
                     "File has not been read"],
    "TestFailure":  ["AssertionError", "Assertion failed", "assertTrue",
                     "assertEquals", "assertEqual", "assert ",
                     "Expected", "FAILED", "pytest"],
    "BashError":    ["Exit code", "tool_use_error"],
}
# 优先级：基础设施 → 构建/工具 → 运行时 → 测试 → 工具级 → Bash 兜底
ERROR_PRIORITY = ["Network", "Timeout", "Permission", "FileNotFound",
                  "BuildError", "GitError", "RuntimeError", "TestFailure",
                  "EditError", "BashError"]

# 因果图 7 类边样式（sequential 用于无 Thought 时的连续 Action 衔接）
EDGE_STYLES = {
    "decision":    {"arrow": "-.->", "label": "驱动",  "color": "#8e24aa"},
    "generation":  {"arrow": "-->",  "label": "生成",  "color": "#fb8c00"},
    "consumption": {"arrow": "-.->", "label": "读取",  "color": "#1e88e5"},
    "failure":     {"arrow": "==>",  "label": "导致",  "color": "#e53935"},
    "correction":  {"arrow": "==>",  "label": "纠偏",  "color": "#fbc02d"},
    "rewriting":   {"arrow": "-->",  "label": "改写",  "color": "#757575"},
    "sequential":  {"arrow": "-->",  "label": "then",  "color": "#bdbdbd"},
}

# ==========================================
# 🔧 2. 辅助函数
# ==========================================
_MERMAID_SAFE = re.compile(r'[^A-Za-z0-9一-龥\s._/-]')

def sanitize(txt, max_len=60):
    """白名单化 Mermaid label 文本：去掉所有特殊字符"""
    if txt is None:
        return ""
    s = _MERMAID_SAFE.sub(' ', str(txt))
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:max_len] + ("..." if len(s) > max_len else "")


def classify_bash(command):
    if not command:
        return "ACTION"
    first = command.strip().split()[0]
    first = first.split("=")[-1] if "=" in first else first
    if first in BASH_NAV:
        return "NAV"
    if first in BASH_INFO:
        return "INFO"
    return "ACTION"


def classify_error(stderr):
    """按优先级匹配 + word boundary 防误判"""
    s = stderr.lower()
    for cat in ERROR_PRIORITY:
        for kw in ERROR_CATEGORIES[cat]:
            kw_clean = kw.lower().strip()
            if kw_clean and re.search(rf'\b{re.escape(kw_clean)}\b', s):
                return cat
    return "UnknownError"


def is_retryable(stderr, category):
    """启发式：transient 类错误可重试"""
    if category in {"Network", "Timeout"}:
        return True
    sl = stderr.lower()
    return bool("rate limit" in sl or "429" in sl or "503" in sl)


def artifact_key(file_path, base_cwd):
    """全局唯一 artifact key：相对 base_cwd 的路径（防同名撞车）"""
    if not file_path:
        return ""
    try:
        return os.path.relpath(file_path, base_cwd).replace("\\", "/")
    except (ValueError, OSError):
        return os.path.basename(file_path)


def is_contract(file_path):
    return os.path.splitext(file_path)[1].lower() in CONTRACT_EXTS


def basename(p):
    return str(p).split('/')[-1].split('\\')[-1]


# ==========================================
# 🚀 3. 核心 AST 引擎 & 因果事件流
# ==========================================
def build_trace_ast_v2(jsonl_path, top_keywords, sub_keywords):
    """
    返回 5 元组:
      ast              树形节点（Stage/Skill/Action/Thought/Human/Error）
      all_types        所有出现的节点类型
      error_nodes      所有 Error 节点（侧边栏用）
      flat_events      时序事件流（因果图用）
      record_cwd       session 工作目录（用于计算 artifact 相对路径）
    """
    if not jsonl_path or not os.path.exists(jsonl_path):
        return [], set(), [], [], ""

    ast = []
    flat_events = []
    node_index = 1
    all_discovered_types = set()

    current_stage = None
    current_subskill = None
    pending_tools: Dict[str, dict] = {}
    error_nodes: List[dict] = []
    record_cwd = ""

    def make_label(base, idx):
        return f"{base.replace(chr(10), ' ')}  #{idx}"

    def get_active_container():
        if current_subskill:
            return current_subskill["children"]
        if current_stage:
            return current_stage["children"]
        return ast

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue

            msg = record.get("message", {})
            if not msg:
                continue
            role = msg.get("role")
            content = msg.get("content")
            record_cwd = record.get("cwd") or record_cwd

            # ============ User role ============
            if role == "user":
                if isinstance(content, str):
                    is_goal = (node_index == 1)
                    label = make_label(
                        f"🎯 [v_goal] {content[:40]}..." if is_goal
                        else f"👤 [v_human] {content[:40]}...",
                        node_index)
                    node = {
                        "id": f"node_{node_index}", "label": label,
                        "type": "Human", "children": [],
                        "summary": {"errors": 0}, "raw": record,
                        "desc": content,
                        "attrs": {"is_goal": is_goal},
                    }
                    ast.append(node)
                    all_discovered_types.add("Human")
                    flat_events.append({
                        "type": "Human",
                        "mid": f"node_{node_index}",
                        "text": content,
                        "is_goal": is_goal,
                        "stage": current_stage["skill_name"] if current_stage else None,
                    })
                    node_index += 1

                elif isinstance(content, list):
                    for block in content:
                        if block.get("type") != "tool_result":
                            continue
                        t_id = block.get("tool_use_id")
                        is_err = block.get("is_error", False)
                        t_content = str(block.get("content", ""))

                        if t_id not in pending_tools:
                            continue
                        parent = pending_tools[t_id]
                        t_name = parent["attrs"]["tool_type"]

                        if is_err:
                            err_cat = classify_error(t_content)
                            err_label = make_label(
                                f"🔴 [v_error] {err_cat}: {t_content[:30]}...",
                                node_index)
                            err_node = {
                                "id": f"node_{node_index}", "label": err_label,
                                "type": "Error", "children": [],
                                "summary": {"errors": 0}, "raw": block,
                                "desc": f"产生 {err_cat} 异常",
                                "attrs": {
                                    "exit_code": 1,
                                    "stderr_full": t_content,
                                    "error_category": err_cat,
                                    "is_retryable": is_retryable(t_content, err_cat),
                                    "parent_action_id": t_id,
                                    "args": parent["attrs"]["args"],
                                },
                            }
                            parent["children"].append(err_node)
                            error_nodes.append(err_node)
                            all_discovered_types.add("Error")
                            for p in [current_subskill, current_stage]:
                                if p:
                                    p["summary"]["errors"] += 1

                            flat_events.append({
                                "type": "Error",
                                "mid": f"node_{node_index}",
                                "action_mid": parent["id"],
                                "category": err_cat,
                                "stderr": t_content,
                                "args": parent["attrs"]["args"],
                                "is_retryable": is_retryable(t_content, err_cat),
                                "stage": current_stage["skill_name"] if current_stage else None,
                            })
                            node_index += 1
                        else:
                            parent["attrs"]["exit_code"] = 0
                            parent["attrs"]["result_preview"] = t_content[:100]
                            parent["attrs"]["result_full"] = t_content

                            if t_name in ("Write", "Edit"):
                                fp = parent["attrs"]["args"].get("file_path", "")
                                if fp:
                                    key = artifact_key(fp, record_cwd)
                                    flat_events.append({
                                        "type": "Artifact_Gen",
                                        "action_mid": parent["id"],
                                        "file_path": fp,
                                        "artifact_key": key,
                                        "is_contract": is_contract(fp),
                                        "stage": current_stage["skill_name"] if current_stage else None,
                                        "skill": current_subskill["skill_name"] if current_subskill
                                                 else (current_stage["skill_name"] if current_stage else None),
                                    })
                        del pending_tools[t_id]

            # ============ Assistant role ============
            elif role == "assistant":
                if isinstance(content, list):
                    for block in content:
                        btype = block.get("type")

                        # Thought
                        if btype in ("thinking", "text"):
                            text = block.get("thinking") or block.get("text", "")
                            t_node = {
                                "id": f"node_{node_index}",
                                "label": make_label(f"🧠 {text[:35]}...", node_index),
                                "type": "Thought", "children": [],
                                "summary": {"errors": 0}, "raw": block,
                                "desc": text,
                            }
                            get_active_container().append(t_node)
                            all_discovered_types.add("Thought")
                            flat_events.append({
                                "type": "Thought",
                                "mid": f"node_{node_index}",
                                "text": text,
                                "stage": current_stage["skill_name"] if current_stage else None,
                            })
                            node_index += 1

                        # Tool use
                        elif btype == "tool_use":
                            t_id = block.get("id")
                            t_name = block.get("name")
                            t_args = block.get("input", {})
                            action_target = t_args.get(
                                "skill", t_args.get("task_name", t_name))

                            is_top = any(kw.strip().lower() in action_target.lower()
                                         for kw in top_keywords if kw.strip())
                            is_sub = any(kw.strip().lower() in action_target.lower()
                                         for kw in sub_keywords if kw.strip())

                            # Stage
                            if is_top:
                                s_node = {
                                    "id": f"node_{node_index}",
                                    "label": make_label(
                                        f"📦 [Stage: {action_target}]", node_index),
                                    "type": "Stage", "skill_name": action_target,
                                    "children": [], "summary": {"errors": 0},
                                    "raw": block,
                                    "desc": f"主阶段: {action_target}",
                                }
                                ast.append(s_node)
                                current_stage = s_node
                                current_subskill = None
                                all_discovered_types.add("Stage")
                                flat_events.append({
                                    "type": "Stage_Start",
                                    "mid": f"node_{node_index}",
                                    "name": action_target,
                                })
                                node_index += 1

                            # Skill
                            elif is_sub:
                                s_node = {
                                    "id": f"node_{node_index}",
                                    "label": make_label(
                                        f"🧩 [Sub-Skill: {action_target}]", node_index),
                                    "type": "Skill", "skill_name": action_target,
                                    "children": [], "summary": {"errors": 0},
                                    "raw": block,
                                    "desc": f"子技能: {action_target}",
                                    "attrs": {"parent_stage":
                                              current_stage["skill_name"]
                                              if current_stage else None},
                                }
                                if current_stage:
                                    current_stage["children"].append(s_node)
                                else:
                                    ast.append(s_node)
                                current_subskill = s_node
                                all_discovered_types.add("Skill")
                                flat_events.append({
                                    "type": "Skill_Start",
                                    "mid": f"node_{node_index}",
                                    "name": action_target,
                                    "stage": current_stage["skill_name"]
                                             if current_stage else None,
                                })
                                node_index += 1

                            # 普通 Action（Bash/Read/Write/Edit）
                            else:
                                bash_cls = ""
                                if t_name == "Bash":
                                    bash_cls = classify_bash(t_args.get("command", ""))

                                tc_node = {
                                    "id": f"node_{node_index}",
                                    "label": make_label(f"🛠️ {t_name}", node_index),
                                    "type": "Action", "children": [],
                                    "summary": {"errors": 0},
                                    "raw": block, "desc": f"执行 {t_name}",
                                    "attrs": {
                                        "tool_type": t_name,
                                        "bash_class": bash_cls,
                                        "args": t_args,
                                        "result_preview": "⏳ 执行中...",
                                        "result_full": "",
                                    },
                                }
                                get_active_container().append(tc_node)
                                pending_tools[t_id] = tc_node
                                all_discovered_types.add("Action")

                                # NAV/INFO 类 Bash 不进因果图
                                skip = (t_name == "Bash" and
                                        bash_cls in ("NAV", "INFO"))
                                if not skip:
                                    flat_events.append({
                                        "type": "Action",
                                        "mid": f"node_{node_index}",
                                        "tool_id": t_id,
                                        "tool_type": t_name,
                                        "bash_class": bash_cls,
                                        "args": t_args,
                                        "stage": current_stage["skill_name"]
                                                 if current_stage else None,
                                        "skill": current_subskill["skill_name"] if current_subskill
                                                 else (current_stage["skill_name"] if current_stage else None),
                                    })
                                node_index += 1

    return ast, all_discovered_types, error_nodes, flat_events, record_cwd


# ==========================================
# 🕸️ 4. Mermaid 因果图生成器（6 类边 + 多版本 + 跨 Stage 加粗）
# ==========================================
def build_causal_mermaid(flat_events, record_cwd="", granularity="中观"):
    lines = ["graph TD"]
    # 节点样式
    lines.append("classDef goal     fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,color:#000;")
    lines.append("classDef thought  fill:#f3e5f5,stroke:#8e24aa,stroke-dasharray:5 5,color:#000;")
    lines.append("classDef action   fill:#e8f5e9,stroke:#43a047,color:#000;")
    lines.append("classDef error    fill:#ffebee,stroke:#e53935,stroke-width:2px,color:#000;")
    lines.append("classDef artifact fill:#fff3e0,stroke:#fb8c00,color:#000;")
    lines.append("classDef human    fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#000;")

    is_micro = "微观" in granularity
    is_macro = "宏观" in granularity

    # 收集边（延迟输出，确保 subgraph 都已开好）
    edges: List[Tuple[str, str, str, bool]] = []
    # artifact_key -> [(art_mid, ver, is_contract)]
    artifact_versions: Dict[str, List[Tuple[str, int, bool]]] = {}
    # node_mid -> stage_name (用于跨 Stage 判断)
    stage_scope: Dict[str, Optional[str]] = {}

    sub_stack: List[str] = []
    last_decision_src: Optional[str] = None
    last_action_mid: Optional[str] = None

    def open_subgraph(mid, label):
        lines.append(f'    subgraph {mid}["{label}"]')
        lines.append("        direction TB")

    def close_subgraph():
        lines.append("    end")

    def close_to_level(level):
        while len(sub_stack) > level:
            close_subgraph()
            sub_stack.pop()

    for idx, ev in enumerate(flat_events):
        etype = ev["type"]

        # ---------- 容器边界 ----------
        if etype == "Stage_Start":
            close_to_level(0)
            open_subgraph(ev["mid"], f"📦 Stage: {sanitize(ev['name'], 30)}")
            sub_stack.append(ev["mid"])
            stage_scope[ev["mid"]] = ev["name"]
            last_decision_src = None
            last_action_mid = None
            continue

        if etype == "Skill_Start":
            if is_macro:
                stage_scope[f"skill_{idx}"] = ev.get("stage")
                continue
            close_to_level(1)
            open_subgraph(ev["mid"], f"🧩 Skill: {sanitize(ev['name'], 30)}")
            sub_stack.append(ev["mid"])
            stage_scope[ev["mid"]] = ev.get("stage")
            last_decision_src = None
            last_action_mid = None
            continue

        # ---------- Human / Goal ----------
        if etype == "Human":
            if is_macro:
                continue
            mid = ev["mid"]
            is_goal = ev.get("is_goal", False)
            icon = "🎯" if is_goal else "👤"
            cls = "goal" if is_goal else "human"
            lines.append(f'    {mid}["{icon} {sanitize(ev["text"], 50)}"]:::{cls}')
            stage_scope[mid] = ev.get("stage")
            last_decision_src = mid
            last_action_mid = None

        # ---------- Thought ----------
        elif etype == "Thought":
            if is_macro or not is_micro:
                continue
            mid = ev["mid"]
            lines.append(f'    {mid}["🧠 {sanitize(ev["text"], 40)}"]:::thought')
            stage_scope[mid] = ev.get("stage")
            last_decision_src = mid

        # ---------- Action ----------
        elif etype == "Action":
            t_name = ev["tool_type"]
            t_args = ev["args"]
            mid = ev["mid"]
            stage = ev.get("stage")

            # 中观/宏观：Read 不画主节点，但画一个 📖 锚点承载消费边
            if not is_micro and t_name == "Read":
                fp = t_args.get("file_path", "")
                key = artifact_key(fp, record_cwd) if record_cwd else basename(fp)
                if key in artifact_versions and artifact_versions[key]:
                    art_mid, _, _ = artifact_versions[key][-1]
                    anchor = f"R_{idx}"
                    lines.append(f'    {anchor}["📖 {sanitize(basename(fp), 30)}"]:::action')
                    stage_scope[anchor] = stage
                    src_stage = stage_scope.get(art_mid)
                    cross = src_stage is not None and stage is not None and src_stage != stage
                    edges.append((art_mid, anchor, "consumption", cross))
                continue

            # 宏观：只保留 Write/Edit（产物生成节点）
            if is_macro and t_name not in ("Write", "Edit"):
                stage_scope[mid] = stage
                last_action_mid = mid
                continue

            if t_name == "Bash":
                cmd = t_args.get("command", "")
                label = f'🛠️ Bash: {sanitize(cmd, 50)}'
            else:
                label = f'🛠️ {t_name}: {sanitize(basename(t_args.get("file_path", "")), 40)}'
            lines.append(f'    {mid}["{label}"]:::action')
            stage_scope[mid] = stage

            # Decision 边：上一个 Thought/Human → 当前 Action
            if last_decision_src and last_decision_src != mid:
                src_stage = stage_scope.get(last_decision_src)
                cross = src_stage is not None and stage is not None and src_stage != stage
                edges.append((last_decision_src, mid, "decision", cross))
            # Sequential 边：无 Thought 时的连续 Action 衔接（同 Stage 内）
            elif last_action_mid and not last_decision_src and \
                    stage_scope.get(last_action_mid) == stage:
                edges.append((last_action_mid, mid, "sequential", False))

            # Consumption 边（仅契约类）
            fp = t_args.get("file_path", "")
            if fp and t_name in ("Read", "Edit"):
                key = artifact_key(fp, record_cwd) if record_cwd else basename(fp)
                if key in artifact_versions and artifact_versions[key]:
                    art_mid, _, is_c = artifact_versions[key][-1]
                    if is_c:
                        src_stage = stage_scope.get(art_mid)
                        cross = src_stage is not None and stage is not None and src_stage != stage
                        edges.append((art_mid, mid, "consumption", cross))

            if t_name == "Bash":
                cmd = t_args.get("command", "")
                for key, versions in artifact_versions.items():
                    if not versions:
                        continue
                    art_mid, _, is_c = versions[-1]
                    if not is_c:
                        continue
                    if key in cmd or basename(key) in cmd:
                        src_stage = stage_scope.get(art_mid)
                        cross = src_stage is not None and stage is not None and src_stage != stage
                        edges.append((art_mid, mid, "consumption", cross))

            last_action_mid = mid
            last_decision_src = None

        # ---------- Artifact Generation ----------
        elif etype == "Artifact_Gen":
            if is_macro:
                continue
            key = ev["artifact_key"]
            is_c = ev["is_contract"]
            art_mid = f"Art_{idx}"

            versions = artifact_versions.setdefault(key, [])
            ver = len(versions) + 1
            versions.append((art_mid, ver, is_c))

            # Rewriting 边：旧版 → 新版
            if ver > 1:
                old_mid = versions[-2][0]
                edges.append((old_mid, art_mid, "rewriting", False))

            display = basename(key) if not is_c else f"📑 {basename(key)}"
            lines.append(f'    {art_mid}[("{display} (v{ver})")]:::artifact')
            stage_scope[art_mid] = ev.get("stage")

            # Generation 边：触发 Action → Artifact
            if last_action_mid:
                src_stage = stage_scope.get(last_action_mid)
                dst_stage = ev.get("stage")
                cross = src_stage is not None and dst_stage is not None and src_stage != dst_stage
                edges.append((last_action_mid, art_mid, "generation", cross))

        # ---------- Error ----------
        elif etype == "Error":
            if is_macro:
                continue
            mid = ev["mid"]
            act_mid = ev.get("action_mid")
            cat = ev["category"]
            retry_icon = "🔁" if ev.get("is_retryable") else "⛔"
            lines.append(f'    {mid}["🔴 {retry_icon} {cat}: '
                         f'{sanitize(ev.get("stderr", ""), 40)}"]:::error')
            stage_scope[mid] = ev.get("stage")

            if act_mid:
                src_stage = stage_scope.get(act_mid)
                dst_stage = ev.get("stage")
                cross = src_stage is not None and dst_stage is not None and src_stage != dst_stage
                edges.append((act_mid, mid, "failure", cross))

                # Ghost 节点：如果是 Read/Edit 失败且产物未生成
                args = ev.get("args", {})
                fp = args.get("file_path", "") if isinstance(args, dict) else ""
                if fp:
                    key = artifact_key(fp, record_cwd) if record_cwd else basename(fp)
                    if not artifact_versions.get(key):
                        ghost_mid = f"Ghost_{idx}"
                        lines.append(f'    {ghost_mid}["❌ 缺失: '
                                     f'{sanitize(basename(key), 25)}"]:::error')
                        edges.append((ghost_mid, mid, "failure", False))

    # 关闭所有未关的 subgraph
    close_to_level(0)

    # 输出所有边 + linkStyle 着色
    for i, (src, dst, kind, cross) in enumerate(edges):
        style = EDGE_STYLES[kind]
        lines.append(f'    {src} {style["arrow"]}|{style["label"]}| {dst}')
        width = "3px" if cross else "1.5px"
        lines.append(f'    linkStyle {i} stroke:{style["color"]},stroke-width:{width};')

    return "\n".join(lines)


# ==========================================
# 📦 4.5 产物溯源：按产物维度重建因果
# ==========================================
def build_product_graph(events, cwd):
    """
    从 flat_events 中按"产物"维度提取依赖关系。
    返回:
      products: {artifact_key: {writes, reads, edits, thoughts, errors,
                                 producers, consumers, first_stage}}
      edges:    [(src_key, dst_key), ...]  # 逻辑依赖边
                "同一 Skill 内：先读 X 后写 Y" => X -> Y
    """
    products = {}
    edges = set()

    current_stage = None
    current_skill = None
    last_thought = None
    reads_in_skill: list = []

    def ensure(key):
        if key not in products:
            products[key] = {
                "writes": [], "reads": [], "edits": [],
                "thoughts": [], "errors": [],
                "producers": set(), "consumers": set(),
                "first_stage": None,
            }
        return products[key]

    for ev in events:
        etype = ev["type"]

        if etype == "Stage_Start":
            current_stage = ev["name"]
            current_skill = None
            last_thought = None
            reads_in_skill = []

        elif etype == "Skill_Start":
            current_skill = ev["name"]
            last_thought = None
            reads_in_skill = []

        elif etype == "Thought":
            last_thought = ev["mid"]

        elif etype == "Action":
            t_name = ev["tool_type"]
            fp = ev["args"].get("file_path", "")
            if fp:
                key = artifact_key(fp, cwd) if cwd else basename(fp)
                p = ensure(key)
                if p["first_stage"] is None:
                    p["first_stage"] = current_stage
                entry = {
                    "action_mid": ev["mid"],
                    "stage": current_stage,
                    "skill": current_skill,
                }
                if t_name == "Read":
                    p["reads"].append(entry)
                    reads_in_skill.append(key)
                    if current_skill:
                        p["consumers"].add((current_skill, current_stage))
                elif t_name == "Edit":
                    p["edits"].append(entry)
                    if current_skill:
                        p["producers"].add((current_skill, current_stage))
                if last_thought:
                    p["thoughts"].append(last_thought)
            last_thought = None

        elif etype == "Artifact_Gen":
            key = ev["artifact_key"]
            p = ensure(key)
            ev_skill = ev.get("skill") or current_skill
            ev_stage = ev.get("stage") or current_stage
            if p["first_stage"] is None:
                p["first_stage"] = ev_stage
            p["writes"].append({
                "action_mid": ev["action_mid"],
                "stage": ev_stage,
                "skill": ev_skill,
                "is_contract": ev.get("is_contract", False),
            })
            if ev_skill:
                p["producers"].add((ev_skill, ev_stage))
            # 逻辑依赖边：本 Skill 内，先读了 X，后写了 Y => X -> Y
            for r in reads_in_skill:
                if r != key:
                    edges.add((r, key))

        elif etype == "Error":
            args = ev.get("args", {})
            fp = args.get("file_path", "") if isinstance(args, dict) else ""
            if fp:
                key = artifact_key(fp, cwd) if cwd else basename(fp)
                if key in products:
                    products[key]["errors"].append({
                        "category": ev["category"],
                        "stderr": ev.get("stderr", "")[:200],
                        "action_mid": ev.get("action_mid"),
                    })

    # set -> sorted list
    for p in products.values():
        p["producers"] = sorted(p["producers"])
        p["consumers"] = sorted(p["consumers"])

    return products, sorted(edges)


_NODE_TYPE_STYLE = {
    "contract": ("📑", "contract", "#fff3e0", "#fb8c00"),
    "design":   ("📐", "design",   "#fff9c4", "#f57c00"),
    "code":     ("💻", "code",     "#e8f5e9", "#43a047"),
    "test":     ("🧪", "test",     "#f3e5f5", "#8e24aa"),
    "script":   ("🐍", "script",   "#e0f7fa", "#00838f"),
    "config":   ("⚙️", "config",  "#f5f5f5", "#616161"),
    "fail":     ("❌", "fail",     "#ffcdd2", "#c62828"),
}


def _classify_product(fname):
    """根据文件名返回 (icon, class_name, fill, stroke)"""
    fn = fname.lower()
    ext = os.path.splitext(fn)[1]
    if "report" in fn or "apply-report" in fn:
        return _NODE_TYPE_STYLE["fail"]
    if ext in (".md", ".yaml", ".yml", ".json", ".toml"):
        if "design" in fn:
            return _NODE_TYPE_STYLE["design"]
        return _NODE_TYPE_STYLE["contract"]
    if ".test." in fn or fn.startswith("test_") or "/test/" in fn:
        return _NODE_TYPE_STYLE["test"]
    if ext in (".py",):
        return _NODE_TYPE_STYLE["script"]
    if ext in (".ets", ".ts", ".tsx", ".js", ".mjs"):
        return _NODE_TYPE_STYLE["code"]
    if ext in (".yaml", ".yml"):
        return _NODE_TYPE_STYLE["config"]
    return _NODE_TYPE_STYLE["contract"]


# AID workflow 静态逻辑依赖（基于文件名模式）
AID_LOGICAL_DEP_PATTERNS = [
    # ── Planning → Design ──
    (r"proposal\.md$",          r"delta-design\.md$"),
    (r"info\.md$",               r"delta-design\.md$"),
    (r"delta-spec\.md$",         r"delta-design\.md$"),
    # ── Design → Tasks ──
    (r"delta-design\.md$",      r"tasks\.md$"),
    (r"tasks\.md$",              r"todo\.md$"),
    # ── Design acceptance criteria → 测试 ──
    (r"delta-design\.md$",      r".*test\.(ets|mjs)$"),
    # ── Code → 对应测试 ──
    (r"Calculator\.ets$",        r"Calculator\.test\.(ets|mjs)$"),
    (r"PlotUtils\.ets$",         r"PlotUtils\.test\.(ets|mjs)$"),
    (r"GraphViewModel\.ets$",    r"GraphViewModel\.test\.(ets|mjs)$"),
    (r"Calculator\.source\.mjs$", r"Calculator\.test\.mjs$"),
    (r"PlotUtils\.source\.mjs$",  r"PlotUtils\.test\.mjs$"),
    # ── 任务/测试/设计 → 应用报告 ──
    (r".*\.test\.(ets|mjs)$",    r"apply-report\.md$"),
    (r"tasks\.md$",              r"apply-report\.md$"),
    (r"delta-design\.md$",       r"apply-report\.md$"),
]


def compute_logical_edges(products):
    """根据 AID workflow 静态模式推导逻辑依赖边"""
    edges = set()
    keys = list(products.keys())
    for src_pat, dst_pat in AID_LOGICAL_DEP_PATTERNS:
        src_re = re.compile(src_pat)
        dst_re = re.compile(dst_pat)
        for src_key in keys:
            if src_re.search(basename(src_key)):
                for dst_key in keys:
                    if src_key != dst_key and dst_re.search(basename(dst_key)):
                        edges.add((src_key, dst_key))
    return edges


def build_product_mermaid(products, edges, file_filter=None):
    """
    全局产物依赖图（不分 subgraph）：
      节点 = 产物，按类型上色
      实线（橙）= 仅逻辑依赖，未被消费   ← RCA 核心信号
      虚线（蓝）= 数据消费（session 观察到）
      加粗（绿）= 逻辑 + 消费都有        ← 健康
      file_filter: list[ext] 限定只画某些扩展名的节点，默认 None 画全部
    """
    lines = ["graph LR"]
    for _, cls, fill, stroke in _NODE_TYPE_STYLE.values():
        parts = [f"fill:{fill}", f"stroke:{stroke}"]
        if cls in ("design", "fail"):
            parts.append("stroke-width:2px")
        parts.append("color:#000")
        lines.append(f"classDef {cls} {','.join(parts)};")

    # 按扩展名过滤（默认只保留契约类 .md/.yaml/.json/.toml）
    if file_filter:
        kept = {k: v for k, v in products.items()
                if os.path.splitext(basename(k))[1].lower() in file_filter}
    else:
        kept = dict(products)

    # mid 映射
    key_to_id = {}
    for i, key in enumerate(kept.keys(), 1):
        key_to_id[key] = f"P{i}"

    # 渲染过滤后的节点
    for key, info in kept.items():
        mid = key_to_id[key]
        fname = basename(key)
        icon, cls, _, _ = _classify_product(fname)
        display = fname if len(fname) <= 35 else fname[:33] + ".."
        ver = len(info["writes"])
        ver_str = f" v{ver}" if ver > 1 else ""
        err_str = " ❌" if info["errors"] else ""
        lines.append(f'    {mid}["{icon} {display}{ver_str}{err_str}"]:::{cls}')

    # 计算逻辑依赖（基于过滤后的产物）
    logical = compute_logical_edges(kept)
    observed = set(edges) & set(kept.keys())
    both = observed & logical
    obs_only = observed - logical
    log_only = logical - observed

    edge_specs = []
    for src, dst in both:
        s, d = key_to_id.get(src), key_to_id.get(dst)
        if s and d and s != d:
            lines.append(f"    {s} ==>|\"✓\"| {d}")
            edge_specs.append((s, d, "both"))
    for src, dst in obs_only:
        s, d = key_to_id.get(src), key_to_id.get(dst)
        if s and d and s != d:
            lines.append(f"    {s} -.->|\"消费\"| {d}")
            edge_specs.append((s, d, "obs"))
    for src, dst in log_only:
        s, d = key_to_id.get(src), key_to_id.get(dst)
        if s and d and s != d:
            lines.append(f"    {s} ==>|\"⚠未消费\"| {d}")
            edge_specs.append((s, d, "log"))

    for idx, (_, _, kind) in enumerate(edge_specs):
        if kind == "both":
            lines.append(f"    linkStyle {idx} stroke:#2e7d32,stroke-width:2.5px;")
        elif kind == "obs":
            lines.append(f"    linkStyle {idx} stroke:#1e88e5,stroke-width:1.5px;")
        elif kind == "log":
            lines.append(f"    linkStyle {idx} stroke:#c62828,stroke-width:2.5px;")

    legend = (
        '\n    %% 图例:'
        '\n    %%  🟢 实线绿 = 逻辑依赖 + 消费都有 (健康)'
        '\n    %%  🔵 虚线蓝 = 仅消费（观察到但无逻辑依据）'
        '\n    %%  🔴 实线红 = 仅逻辑依赖（理应消费但未消费）← RCA 关键'
    )
    lines.append(legend)

    return "\n".join(lines), key_to_id


def build_node_lookup(ast_nodes):
    """mid -> node 映射，方便下钻查 action / thought 详情"""
    lookup = {}
    def walk(nodes):
        for n in nodes:
            lookup[n.get("id")] = n
            walk(n.get("children", []))
    walk(ast_nodes)
    return lookup


def read_artifact_content(artifact_key, base_cwd):
    """读取产物的实际文件内容（如果存在）"""
    if not base_cwd:
        return None
    full = os.path.join(base_cwd, artifact_key)
    if not os.path.exists(full):
        return None
    try:
        with open(full, 'r', encoding='utf-8') as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        try:
            with open(full, 'r', encoding='gbk') as f:
                return f.read()
        except Exception:
            return None


def find_content_references(content, all_product_fnames):
    """
    在 .md 内容里扫其他 .md 文件名（被引用 = 内容级依赖）
    返回被引用文件列表
    """
    if not content:
        return []
    refs = []
    for fname in all_product_fnames:
        # 匹配文件名（不需要扩展名全匹配，避免误中 .py 等）
        if fname in content:
            refs.append(fname)
    return refs
def filter_tree(nodes, selected_types):
    filtered = []
    for node in nodes:
        children = filter_tree(node.get("children", []), selected_types)
        if node["type"] in selected_types or len(children) > 0:
            new_node = node.copy()
            new_node["children"] = children
            filtered.append(new_node)
    return filtered


def build_tree_items_and_map(ast_nodes, node_map):
    tree_items = []
    for node in ast_nodes:
        err_count = node.get("summary", {}).get("errors", 0)
        display_label = node["label"]
        if err_count > 0 and node["type"] != "Error":
            display_label += f"  🔴×{err_count}"
        node_map[display_label] = node

        children_items = build_tree_items_and_map(node.get("children", []), node_map)
        tree_items.append(sac.TreeItem(
            label=display_label,
            children=children_items if children_items else None))
    return tree_items


# --- Streamlit 页面渲染 ---
st.set_page_config(page_title="Agent Trace RCA Board",
                   layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(
    "<style>.block-container { padding-top: 1rem; padding-bottom: 0rem; "
    "max-width: 100%; } h1 { font-size: 1.5rem !important; "
    "margin-bottom: 0 !important; } .stJson { background-color: #f8f9fa; "
    "border-radius: 8px; padding: 10px; }</style>",
    unsafe_allow_html=True)

st.title("⚡ Agent Execution Trace (RCA Board)")
st.divider()

target_jsonl = os.environ.get("TRACE_JSONL_PATH",
                              "264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl")
with st.sidebar:
    st.header("⚙️ 动态解析规则")
    jsonl_file = st.text_input("Trace 路径", value=target_jsonl)
    top_input = st.text_area("📦 顶级阶段关键词",
                             value="planning, implementing, applying, aid-")
    sub_input = st.text_area("🧩 子技能容器关键词",
                             value="tdd-, rq-, mod-, harmonyos-, test")

ast_data, all_types, error_nodes, flat_events, record_cwd = build_trace_ast_v2(
    jsonl_file,
    [k.strip() for k in top_input.split(",")],
    [k.strip() for k in sub_input.split(",")],
)

if not ast_data:
    st.warning("👈 请输入有效的 .jsonl 路径！")
    st.stop()

with st.sidebar:
    st.markdown("---")
    selected_types = st.multiselect("🔍 节点类型过滤",
                                    sorted(list(all_types)),
                                    default=sorted(list(all_types)))
    st.markdown("---")
    st.markdown(f"##### 🚨 错误专区 (共 {len(error_nodes)} 个)")
    if len(error_nodes) == 0:
        st.success("✅ 完美执行，无报错")
    else:
        for err in error_nodes:
            st.error(
                f"**[{err['attrs']['error_category']}]** "
                f"{err['attrs']['stderr_full'][:60]}...")

# 三视图 Tab：产物溯源为默认
tab_product, tab_trace, tab_causal = st.tabs([
    "🎯 产物溯源 (Product Lineage)",
    "🌳 执行链路树 (Execution Trace)",
    "🕸️ 逻辑因果图 (Causal Lineage)",
])
VIEWPORT_HEIGHT = 750

# ============ TAB 1: 产物溯源（默认）============
with tab_product:
    products, prod_edges = build_product_graph(flat_events, record_cwd)
    node_lookup = build_node_lookup(ast_data)

    if not products:
        st.info("未发现产物数据")
    else:
        # 文件类型过滤
        file_ext_filter = st.radio(
            "📂 显示文件类型",
            options=["仅契约 (.md/.yaml/.json)", "全部文件"],
            horizontal=True,
            index=0,
        )
        active_filter = (
            {".md", ".yaml", ".yml", ".json", ".toml"}
            if "仅契约" in file_ext_filter
            else None
        )

        col_l, col_r = st.columns([5, 5], gap="large")

        with col_l:
            st.markdown("##### 🎯 产物依赖图")
            mermaid_code, _ = build_product_mermaid(products, prod_edges, file_filter=active_filter)
            with st.container(height=VIEWPORT_HEIGHT, border=True):
                st.markdown(f"```mermaid\n{mermaid_code}\n```")

        with col_r:
            st.markdown("##### 🔍 产物下钻")
            # 只列契约文件
            if active_filter:
                prod_keys = [k for k in products
                             if os.path.splitext(basename(k))[1].lower() in active_filter]
            else:
                prod_keys = sorted(products.keys(),
                                   key=lambda k: (products[k].get("first_stage") or "z", k))
            prod_keys = sorted(prod_keys,
                               key=lambda k: (products[k].get("first_stage") or "z", k))

            display_options = []
            for k in prod_keys:
                fname = basename(k)
                p = products[k]
                stage = (p.get("first_stage") or "").replace("aid-", "").upper()
                err_mark = " ❌" if p["errors"] else ""
                display_options.append(f"[{stage:11s}] {fname}{err_mark}")
            selected_display = st.selectbox(
                "选择产物查看详情",
                options=display_options,
                index=0,
                label_visibility="collapsed",
            )
            selected_key = prod_keys[display_options.index(selected_display)]

            with st.container(height=VIEWPORT_HEIGHT - 80, border=True):
                info = products[selected_key]
                fname = basename(selected_key)

                ext = os.path.splitext(fname)[1]
                if ext in (".md", ".yaml", ".yml", ".json"):
                    header = f"📑 契约文件：`{fname}`"
                elif ".test." in fname or fname.startswith("test_"):
                    header = f"🧪 测试文件：`{fname}`"
                elif ext in (".py", ".ets", ".ts", ".js", ".mjs"):
                    header = f"💻 代码文件：`{fname}`"
                else:
                    header = f"📄 文件：`{fname}`"
                st.markdown(f"### {header}")
                st.caption(f"路径：`{selected_key}`")

                ver = len(info["writes"])
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("版本数", ver)
                col_b.metric("读取数", len(info["reads"]))
                col_c.metric("编辑数", len(info["edits"]))
                col_d.metric("错误数", len(info["errors"]))

                st.markdown("---")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**📤 生产者**")
                    if info["producers"]:
                        for skill, stage in info["producers"]:
                            st.markdown(f"- `{skill}` ({stage})")
                    else:
                        st.caption("_无_")
                with c2:
                    st.markdown("**📥 消费者**")
                    if info["consumers"]:
                        for skill, stage in info["consumers"]:
                            st.markdown(f"- `{skill}` ({stage})")
                    else:
                        st.warning("⚠️ 无任何消费者（RCA 信号）")

                st.markdown("---")

                if info["writes"]:
                    st.markdown(f"**📝 写入历史 ({len(info['writes'])})**")
                    for w in info["writes"]:
                        node = node_lookup.get(w["action_mid"])
                        cmd = ""
                        if node and "args" in node.get("attrs", {}):
                            content = node["attrs"]["args"].get("content", "")
                            if content:
                                cmd = f" — `{content[:60]}...`" if len(content) > 60 else f" — `{content}`"
                        st.markdown(f"- `{w['skill'] or '?'}` 写入 ({w['action_mid']}){cmd}")

                if info["reads"]:
                    st.markdown(f"**📖 读取历史 ({len(info['reads'])})**")
                    for r in info["reads"]:
                        st.markdown(f"- `{r['skill'] or '?'}` 读取 ({r['action_mid']})")

                if info["thoughts"]:
                    st.markdown(f"**🧠 关联思考 ({len(info['thoughts'])})**")
                    for t_mid in info["thoughts"][:5]:
                        t_node = node_lookup.get(t_mid)
                        if t_node:
                            desc = t_node.get("desc", "")[:80]
                            st.markdown(f"- _{desc}..._")

                if info["errors"]:
                    st.markdown(f"**❌ 关联错误 ({len(info['errors'])})**")
                    for e in info["errors"]:
                        st.error(f"[{e['category']}] {e['stderr'][:100]}...")

                # 依赖关系（同时显示 session 观察 + 逻辑）
                logical = compute_logical_edges(products)
                obs_upstream = [s for s, d in prod_edges if d == selected_key]
                obs_downstream = [s for s, d in prod_edges if s == selected_key and d != s]
                log_upstream = [s for s, d in logical if d == selected_key]
                log_downstream = [s for s, d in logical if s == selected_key and d != s]

                if obs_upstream or obs_downstream or log_upstream or log_downstream:
                    st.markdown("---")
                    st.markdown("**🔗 依赖关系**")
                    if log_upstream:
                        st.markdown(f"上游（逻辑）: {len(log_upstream)}")
                        for u in log_upstream[:5]:
                            mark = "🔴" if u not in [x[0] for x in obs_upstream] else "🟢"
                            st.markdown(f"  {mark} ← `{basename(u)}`")
                    if obs_upstream:
                        st.markdown(f"上游（消费）: {len(obs_upstream)}")
                        for u in obs_upstream[:5]:
                            mark = "🟢" if u in [x[0] for x in log_upstream] else "🔵"
                            st.markdown(f"  {mark} ← `{basename(u)}`")
                    if log_downstream:
                        st.markdown(f"下游（逻辑）: {len(log_downstream)}")
                        for d in log_downstream[:5]:
                            mark = "🔴" if d not in [x[1] for x in obs_downstream] else "🟢"
                            st.markdown(f"  {mark} → `{basename(d)}`")
                    if obs_downstream:
                        st.markdown(f"下游（消费）: {len(obs_downstream)}")
                        for d in obs_downstream[:5]:
                            mark = "🟢" if d in [x[1] for x in log_downstream] else "🔵"
                            st.markdown(f"  {mark} → `{basename(d)}`")

                # 文件内容（仅契约文件）
                if ext in (".md", ".yaml", ".yml", ".txt"):
                    st.markdown("---")
                    st.markdown("**📄 文件内容**")
                    content = read_artifact_content(selected_key, record_cwd)
                    if content is None:
                        st.caption(f"_文件不存在或无法读取（cwd={record_cwd}）_")
                    else:
                        # 检测内部引用
                        all_fnames = [basename(k) for k in products.keys()]
                        refs = find_content_references(content, all_fnames)
                        if refs:
                            st.info(f"🔗 内容中引用了 {len(refs)} 个其他产物：{', '.join(f'`{r}`' for r in refs)}")
                        with st.expander("展开查看全文", expanded=False):
                            st.code(content, language="markdown" if ext == ".md" else "yaml")

# ============ TAB 2: 执行树（辅助）============
with tab_trace:
    col_left, col_right = st.columns([4, 6], gap="large")
    dynamic_details_map = {}
    sac_tree_items = build_tree_items_and_map(
        filter_tree(ast_data, selected_types), dynamic_details_map)

    with col_left:
        st.markdown("##### 🌳 动态嵌套树")
        with st.container(height=VIEWPORT_HEIGHT, border=True):
            selected_label = sac.tree(
                items=sac_tree_items, index=0, open_all=True,
                size='sm', show_line=True, return_index=False)

    with col_right:
        st.markdown("##### 📝 节点审查")
        with st.container(height=VIEWPORT_HEIGHT, border=True):
            if selected_label and selected_label in dynamic_details_map:
                data = dynamic_details_map[selected_label]
                st.markdown(f"### {data['type']}")
                if data["type"] == "Error":
                    st.error(f"🚨 **{data['attrs']['error_category']}**")
                    st.code(data['attrs']['stderr_full'], language="bash")
                elif data["type"] == "Action":
                    attrs = data.get("attrs", {})
                    st.markdown(f"**操作工具**: `{attrs.get('tool_type')}`")
                    if attrs.get("tool_type") in ["Write", "Edit"]:
                        fname = attrs.get("args", {}).get("file_path", "")
                        st.markdown(f"**📄 产物**: `{fname}`")
                        st.code(
                            attrs.get("args", {}).get(
                                "content",
                                attrs.get("args", {}).get("code", "")),
                            language="typescript")
                    elif attrs.get("tool_type") == "Bash":
                        st.markdown(
                            f"**💻 命令**: `{attrs.get('args', {}).get('command', '')}`")
                        if attrs.get("exit_code") == 0:
                            st.success("Exit Code: 0 (成功)")
                        else:
                            st.warning("Exit Code 异常")
                        st.text_area(
                            "Console 输出",
                            attrs.get("result_full", "暂无"),
                            height=300, label_visibility="collapsed")
                else:
                    st.markdown(f"**摘要**: {data['desc']}")
                    st.json(data["raw"])
            else:
                st.info("👈 请在左侧 Trace 树中选择节点以审查详细上下文。")

# ============ TAB 3: 因果血缘图（辅助）============
with tab_causal:
    st.markdown("##### 🕵️ Agent 因果推理与数据血缘")
    st.caption(
        "节点：🎯目标/🛠️动作/📄产物/🔴错误（+👤人类/🧠思考）。"
        "边：6 类（驱动/生成/读取/导致/改写/then），跨 Stage 边加粗高亮。")

    graph_granularity = st.radio(
        "渲染粒度选择：",
        ["宏观 (Stage 边界)", "中观 (聚焦产物与报错 - 推荐)",
         "微观 (全量 Thought 与动作)"],
        horizontal=True,
    )

    mermaid_code = build_causal_mermaid(
        flat_events, record_cwd, granularity=graph_granularity)
    st.markdown(f"```mermaid\n{mermaid_code}\n```")