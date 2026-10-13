"""Hierarchical Skill-first trace board.

The module keeps parsing and graph logic import-safe. Streamlit is imported only
inside ``main`` so unit tests can exercise the model without a UI context.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class TraceNode:
    id: str
    kind: str
    label: str
    parent_id: Optional[str]
    start_index: int
    end_index: Optional[int] = None
    status: str = "open"
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceEdge:
    source: str
    target: str
    kind: str
    observed: bool = True
    derived: bool = False
    via: tuple[str, ...] = ()


@dataclass
class ArtifactVersion:
    artifact_key: str
    version: int
    node_id: str
    producer_skill_run_id: Optional[str]
    producer_task_id: Optional[str]
    producer_tool_call_id: Optional[str]
    created_index: int
    is_contract: bool


@dataclass
class TraceGraph:
    nodes: dict[str, TraceNode] = field(default_factory=dict)
    edges: list[TraceEdge] = field(default_factory=list)
    artifacts: dict[str, list[ArtifactVersion]] = field(default_factory=dict)
    session_summary: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BashClassification:
    classification: str
    subcommands: tuple[str, ...]


@dataclass
class GraphProjection:
    nodes: dict[str, TraceNode]
    edges: list[TraceEdge]
    level: str


class _GraphBuilder:
    def __init__(self) -> None:
        self.graph = TraceGraph()
        self._counter = 0
        self._edge_keys: set[tuple[Any, ...]] = set()

    def add_node(
        self,
        kind: str,
        label: str,
        parent_id: Optional[str],
        start_index: int,
        attrs: Optional[dict[str, Any]] = None,
    ) -> TraceNode:
        self._counter += 1
        node = TraceNode(
            id=f"N{self._counter}",
            kind=kind,
            label=label,
            parent_id=parent_id,
            start_index=start_index,
            attrs=attrs or {},
        )
        self.graph.nodes[node.id] = node
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        kind: str,
        *,
        observed: bool = True,
        derived: bool = False,
        via: tuple[str, ...] = (),
    ) -> Optional[TraceEdge]:
        if source not in self.graph.nodes or target not in self.graph.nodes:
            raise ValueError(f"Dangling edge {source} -[{kind}]-> {target}")
        if source == target:
            return None
        key = (source, target, kind, observed, derived, via)
        if key in self._edge_keys:
            return None
        self._edge_keys.add(key)
        edge = TraceEdge(source, target, kind, observed, derived, via)
        self.graph.edges.append(edge)
        return edge


def _iter_records(path: Path, diagnostics: list[str]):
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            try:
                yield index, json.loads(line)
            except json.JSONDecodeError as exc:
                diagnostics.append(f"line {index + 1}: {exc.msg}")


_CONTRACT_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".toml"}
_ERROR_PATTERNS = [
    ("Network", ("connection refused", "etimedout", "econnreset", "dns")),
    ("Timeout", ("timed out", "timeoutexpired", "deadline exceeded")),
    ("Permission", ("permission denied", "eacces", "eperm", "forbidden")),
    ("FileNotFound", ("no such file", "filenotfounderror", "enoent")),
    ("BuildError", ("syntaxerror", "indentationerror", "could not compile", "tsc error", "eslint")),
    ("GitError", ("conflict", "merge failed", "non-fast-forward", "fatal: pathspec")),
    ("TestFailure", ("assertionerror", "assertion failed", "test failed", "pytest")),
    ("EditError", ("string to replace not found", "file has not been read")),
    ("BashError", ("exit code", "tool_use_error")),
]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tool_result_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "")
            if item_type == "text":
                parts.append(str(item.get("text") or ""))
            elif item_type == "image":
                parts.append("[image omitted]")
            elif item.get("content") is not None:
                parts.append(str(item.get("content")))
            elif item_type:
                parts.append(f"[{item_type} omitted]")
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if content.get("type") == "image":
            return "[image omitted]"
        if content.get("text") is not None:
            return str(content["text"])
        return f"[{content.get('type', 'structured result')} omitted]"
    return str(content)


def _basename(path: Any) -> str:
    return str(path or "").replace("\\", "/").rstrip("/").split("/")[-1]


def _artifact_key(file_path: str, cwd: str) -> str:
    if not file_path:
        return ""
    normalized_cwd = os.path.normpath(cwd) if cwd else ""
    normalized_path = os.path.normpath(file_path)
    if normalized_cwd:
        full_path = normalized_path if os.path.isabs(normalized_path) else os.path.join(normalized_cwd, normalized_path)
        try:
            normalized_path = os.path.relpath(full_path, normalized_cwd)
        except ValueError:
            normalized_path = full_path
    return normalized_path.replace("\\", "/")


def _first_sentence(text: str, limit: int = 88) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "Execute task"
    sentence = re.split(r"(?<=[.!?。！？])\s+", cleaned, maxsplit=1)[0]
    return sentence[:limit] + ("…" if len(sentence) > limit else "")


def _split_shell_commands(command: str) -> tuple[str, ...]:
    parts: list[str] = []
    buffer: list[str] = []
    quote: Optional[str] = None
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            buffer.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\" and quote == '"':
            buffer.append(char)
            escaped = True
            index += 1
            continue
        if quote:
            buffer.append(char)
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue
        operator_length = 0
        if command.startswith("&&", index) or command.startswith("||", index):
            operator_length = 2
        elif char in {";", "|", "\n"}:
            operator_length = 1
        if operator_length:
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer.clear()
            index += operator_length
            continue
        buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return tuple(parts)


def _shell_tokens(command: str) -> list[str]:
    try:
        tokens = shlex.split(command, posix=False)
    except ValueError:
        tokens = command.split()
    normalized: list[str] = []
    for token in tokens:
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
            token = token[1:-1]
        normalized.append(token)
    tokens = normalized
    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens.pop(0)
    while tokens and _basename(tokens[0]).lower() in {"sudo", "env", "command"}:
        tokens.pop(0)
    return tokens


def _is_validation_script_name(name: str) -> bool:
    return bool(re.match(r"^(test|lint|check|verify|typecheck)(?:[:_-]|\.|$)", _basename(name).lower()))


def _is_validation_command(tokens: list[str]) -> bool:
    if not tokens:
        return False
    executable = _basename(tokens[0]).lower()
    executable = re.sub(r"\.(exe|cmd|bat)$", "", executable)
    args = [token.lower() for token in tokens[1:]]
    if executable in {"pytest", "ctest", "jest", "eslint", "stylelint", "mypy"}:
        return True
    if executable in {"npm", "pnpm", "yarn"}:
        return any(_is_validation_script_name(arg) for arg in args if arg not in {"run", "exec"})
    if executable == "npx":
        return bool(args and (_is_validation_script_name(args[0]) or _basename(args[0]) in {"jest", "eslint", "pytest"}))
    if executable in {"bash", "sh", "zsh"} and "-c" in args:
        command_index = args.index("-c")
        return _is_validation_command(_shell_tokens(args[command_index + 1])) if command_index + 1 < len(args) else False
    if executable in {"python", "python3", "node"}:
        if len(args) >= 2 and args[0] == "-m" and args[1] in {"pytest", "unittest"}:
            return True
        script_args = [arg for arg in args if not arg.startswith("-")]
        if script_args:
            script = _basename(script_args[0])
            return ".test." in script or _is_validation_script_name(script) or script in {"run_tests.py", "run-tests.py"}
    if executable in {"gradlew", "mvnw", "gradle", "mvn"}:
        return any(_is_validation_script_name(arg) or arg in {"test", "check", "verify"} for arg in args)
    if "hvigorw" in executable:
        return any(arg == "test" or arg.startswith("test@") or arg.endswith(":test") for arg in args)
    return False


def classify_bash_compound(command: str) -> BashClassification:
    subcommands = _split_shell_commands(command or "")
    classes: list[str] = []
    for part in subcommands:
        tokens = _shell_tokens(part)
        first = re.sub(r"\.(exe|cmd|bat)$", "", _basename(tokens[0]).lower()) if tokens else ""
        if first == "git":
            classes.append("VERSION_CONTROL")
        elif _is_validation_command(tokens):
            classes.append("VALIDATE")
        elif ">" in part or first in {"mkdir", "rm", "mv", "cp", "python", "python3", "node", "npm", "npx"}:
            classes.append("ACTION")
        elif first in {"cat", "head", "tail", "find", "grep", "rg", "ls", "tree", "wc", "which", "file", "stat"}:
            classes.append("INFO")
        elif first in {"cd", "pwd", "pushd", "popd"}:
            classes.append("NAV")
        else:
            classes.append("ACTION")
    for candidate in ("VALIDATE", "VERSION_CONTROL", "ACTION", "INFO", "NAV"):
        if candidate in classes:
            return BashClassification(candidate, subcommands)
    return BashClassification("ACTION", subcommands)


def _bash_target(command: str, classification: str) -> str:
    if classification == "VALIDATE":
        return "tests"
    if classification == "VERSION_CONTROL":
        return "repository"
    matches = re.findall(r"(?:^|\s)([^\s'\"]+\.[A-Za-z0-9]+)(?=\s|$)", command)
    return _basename(matches[-1]) if matches else "workspace"


def _classify_error(text: str) -> str:
    lowered = text.lower()
    for category, patterns in _ERROR_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return category
    return "UnknownError"


def _error_severity(category: str, tool: TraceNode) -> str:
    if category in {"TestFailure", "BuildError", "GitError", "Network", "Timeout", "Permission"}:
        return "important"
    if tool.attrs.get("tool_name") in {"Write", "Edit"}:
        return "important"
    return "minor"


def _semantic_signature(
    tool_name: str,
    inputs: dict[str, Any],
    thought: str,
    recovery_pending: bool,
) -> tuple[str, str, Optional[str], str, str]:
    explicit = re.search(r"\bstep\s*([0-9]+(?:\.[0-9]+)?)\b", thought, re.IGNORECASE)
    explicit_step = f"step{explicit.group(1)}" if explicit else None
    target = _basename(inputs.get("file_path"))
    bash = None
    if tool_name == "Bash":
        bash = classify_bash_compound(str(inputs.get("command", "")))
        target = _bash_target(str(inputs.get("command", "")), bash.classification)
        mode = {
            "VALIDATE": "validate",
            "VERSION_CONTROL": "version-control",
            "INFO": "inspect-input",
            "NAV": "inspect-input",
        }.get(bash.classification, "execute")
    elif tool_name in {"Read", "Glob", "Grep"}:
        mode = "inspect-input"
        target = target or str(inputs.get("pattern") or "workspace")
    elif tool_name == "Write":
        mode = "produce-artifact"
    elif tool_name == "Edit":
        mode = "modify-artifact"
    else:
        mode = "execute"
        target = target or tool_name

    if recovery_pending and mode in {"modify-artifact", "produce-artifact", "execute"}:
        mode = "recover-error"

    titles = {
        "inspect-input": f"Inspect {target}",
        "produce-artifact": f"Produce {target}",
        "modify-artifact": f"Modify {target}",
        "validate": "Validate changes",
        "version-control": "Update repository",
        "recover-error": f"Recover by updating {target}",
        "execute": f"Execute {target}",
    }
    confidence = "high" if explicit_step or mode in {"produce-artifact", "modify-artifact", "validate", "recover-error"} else "medium"
    reason = "explicit step and tool semantics" if explicit_step else "tool semantics and target"
    return mode, target or "workspace", explicit_step, titles[mode], confidence + ":" + reason


def parse_trace(jsonl_path: str | Path) -> TraceGraph:
    """Parse a Claude JSONL trace into a Skill-first base graph."""
    path = Path(jsonl_path)
    builder = _GraphBuilder()
    if not path.exists():
        builder.graph.diagnostics.append(f"Trace not found: {path}")
        return builder.graph

    skill_by_name: dict[str, TraceNode] = {}
    current_skill: Optional[TraceNode] = None
    current_task: dict[str, TraceNode] = {}
    pending_thought: dict[str, list[str]] = {}
    pending_tools: dict[str, TraceNode] = {}
    recovery_error: dict[str, list[str]] = {}
    recovery_linked: set[str] = set()
    explicit_tasks: dict[str, TraceNode] = {}
    pending_task_controls: dict[str, tuple[str, TraceNode, Optional[str]]] = {}
    last_result_by_skill: dict[str, Optional[str]] = {}
    last_index = 0
    last_cwd = ""
    goal = ""

    def switch_skill(attribution: str, index: int) -> None:
        nonlocal current_skill
        if attribution not in skill_by_name:
            return
        attributed = skill_by_name[attribution]
        if current_skill is attributed:
            return
        if current_skill and current_skill.attrs["activity_intervals"]:
            current_skill.attrs["activity_intervals"][-1][1] = index - 1
        current_skill = attributed
        current_skill.attrs["activity_intervals"].append([index, None])

    def attach_explicit_tasks(skill: TraceNode) -> None:
        for task in explicit_tasks.values():
            if task.parent_id is not None:
                continue
            if task.attrs.get("skill_hint") == skill.attrs.get("skill_name"):
                task.parent_id = skill.id
                task.attrs["skill_run_id"] = skill.id

    def create_task_control(block: dict[str, Any], index: int) -> Optional[TraceNode]:
        inputs = _safe_dict(block.get("input"))
        name = str(block.get("name") or "")
        if name == "TaskCreate":
            subject = str(inputs.get("subject") or "Unnamed task")
            description = str(inputs.get("description") or "")
            hint_match = re.search(
                r"\b((?:aid|rq|mod|harmonyos|tdd)-[a-z0-9-]+)\b",
                f"{subject} {description}".lower(),
            )
            task = builder.add_node(
                "Task",
                subject,
                None,
                index,
                {
                    "source": "explicit",
                    "external_task_id": None,
                    "subject": subject,
                    "description": description,
                    "skill_hint": hint_match.group(1) if hint_match else None,
                    "semantic_mode": "explicit",
                    "target_scope": "",
                    "task_key": ["explicit", subject, None],
                    "inference_confidence": "high",
                    "boundary_reason": "TaskCreate",
                    "raw_thought": "",
                    "tool_call_ids": [],
                    "lifecycle": [{"event": "pending", "status": "pending", "index": index}],
                },
            )
            explicit_tasks[task.id] = task
            if block.get("id"):
                pending_task_controls[str(block["id"])] = ("create", task, None)
            return task

        if name == "TaskUpdate":
            external_id = str(inputs.get("taskId") or "")
            status = str(inputs.get("status") or "updated")
            task = next(
                (item for item in explicit_tasks.values() if item.attrs.get("external_task_id") == external_id),
                None,
            )
            if task is None:
                task = next(
                    (item for item in explicit_tasks.values() if item.attrs.get("raw_external_id") == external_id),
                    None,
                )
            if task is None:
                for item in explicit_tasks.values():
                    if not item.attrs.get("external_task_id") and not item.attrs.get("raw_external_id"):
                        task = item
                        break
            if task is None:
                builder.graph.diagnostics.append(
                    f"event {index}: TaskUpdate references unknown task {external_id}"
                )
                return None
            task.attrs["raw_external_id"] = external_id
            if task.status in {"completed", "failed", "cancelled"} and status not in {"completed", "failed", "cancelled"}:
                return task
            task.attrs["status"] = status
            task.status = status
            task.attrs["lifecycle"].append({"event": status, "status": status, "index": index})
            if status in {"completed", "failed", "cancelled"}:
                task.end_index = index
            return task

        return None

    def finalize_task_create(tool_id: str, result_info: dict[str, Any], result_text: str) -> None:
        control = pending_task_controls.pop(tool_id, None)
        if not control or control[0] != "create":
            return
        task = control[1]
        task_data = _safe_dict(result_info.get("task"))
        match = re.search(r"Task\s+#?([A-Za-z0-9_-]+)", result_text)
        external_id = str(task_data.get("id") or (match.group(1) if match else ""))
        if external_id:
            task.attrs["external_task_id"] = external_id
            explicit_tasks[task.id] = task

    def create_skill(block: dict[str, Any], index: int) -> TraceNode:
        nonlocal current_skill
        inputs = _safe_dict(block.get("input"))
        skill_name = str(inputs.get("skill") or "unknown-skill")
        caller = current_skill
        invocation_reason = ""
        if caller:
            invocation_reason = "\n".join(pending_thought.setdefault(caller.id, [])).strip()
            pending_thought[caller.id].clear()
        node = builder.add_node(
            "SkillRun",
            skill_name,
            None,
            index,
            {
                "skill_name": skill_name,
                "tool_use_id": block.get("id"),
                "caller_skill_id": caller.id if caller else None,
                "activity_intervals": [],
                "args": inputs.get("args", ""),
                "invocation_reason": invocation_reason,
            },
        )
        skill_by_name[skill_name] = node
        pending_thought[node.id] = []
        recovery_error[node.id] = []
        last_result_by_skill[node.id] = None
        for task in explicit_tasks.values():
            if task.parent_id is None and task.attrs.get("skill_hint") == skill_name:
                task.parent_id = node.id
                task.attrs["skill_run_id"] = node.id
        if caller:
            builder.add_edge(caller.id, node.id, "invokes")
        if current_skill is None:
            current_skill = node
            node.attrs["activity_intervals"].append([index, None])
        return node

    def create_tool(block: dict[str, Any], index: int, cwd: str) -> None:
        tool_name = str(block.get("name") or "Unknown")
        if current_skill is None:
            builder.graph.diagnostics.append(
                f"event {index}: unattributed tool {tool_name} omitted before first SkillRun"
            )
            return
        inputs = _safe_dict(block.get("input"))
        thoughts = pending_thought.setdefault(current_skill.id, [])
        thought = "\n".join(thoughts).strip()
        mode, target, explicit_step, title, confidence_reason = _semantic_signature(
            tool_name, inputs, thought, bool(recovery_error.get(current_skill.id))
        )
        confidence, reason = confidence_reason.split(":", 1)
        identity_target = target
        if inputs.get("file_path"):
            identity_target = _artifact_key(str(inputs["file_path"]), cwd)
        task_key = (mode, identity_target, explicit_step)
        explicit_task = next(
            (
                item for item in explicit_tasks.values()
                if item.parent_id == current_skill.id
                and item.status not in {"completed", "failed", "cancelled"}
            ),
            None,
        )
        task = explicit_task or current_task.get(current_skill.id)
        if explicit_task:
            current_task[current_skill.id] = explicit_task
            explicit_task.attrs.setdefault("semantic_modes", set()).add(mode)
            if thought:
                existing = explicit_task.attrs.get("raw_thought", "")
                explicit_task.attrs["raw_thought"] = (existing + "\n" + thought).strip()
            task = explicit_task
        elif task is None or tuple(task.attrs["task_key"]) != task_key:
            previous_task = current_task.get(current_skill.id)
            if previous_task and previous_task.attrs.get("source") == "semantic":
                previous_task.status = "closed"
                previous_task.end_index = index - 1
            task = builder.add_node(
                "Task",
                title,
                current_skill.id,
                index,
                {
                    "source": "semantic",
                    "semantic_mode": mode,
                    "target_scope": target,
                    "explicit_step": explicit_step,
                    "task_key": list(task_key),
                    "inference_confidence": confidence,
                    "boundary_reason": reason,
                    "raw_thought": thought,
                    "tool_call_ids": [],
                },
            )
            current_task[current_skill.id] = task
            if mode == "recover-error":
                candidates = [
                    error_id
                    for error_id in reversed(recovery_error.get(current_skill.id, []))
                    if error_id not in recovery_linked
                ]
                if candidates:
                    error_id = candidates[0]
                    builder.add_edge(error_id, task.id, "triggers")
                    recovery_linked.add(error_id)
        elif thought:
            existing = task.attrs.get("raw_thought", "")
            task.attrs["raw_thought"] = (existing + "\n" + thought).strip()

        decision = None
        if thought:
            decision = builder.add_node(
                "Decision",
                _first_sentence(thought),
                task.id,
                index,
                {"raw_text": thought, "skill_run_id": current_skill.id},
            )

        bash_info = classify_bash_compound(str(inputs.get("command", ""))) if tool_name == "Bash" else None
        tool = builder.add_node(
            "ToolCall",
            f"{tool_name}: {target}",
            task.id,
            index,
            {
                "tool_use_id": block.get("id"),
                "tool_name": tool_name,
                "inputs": inputs,
                "cwd": cwd,
                "skill_run_id": current_skill.id,
                "task_id": task.id,
                "bash_class": bash_info.classification if bash_info else "",
                "bash_subcommands": list(bash_info.subcommands) if bash_info else [],
                "result": "",
                "is_error": None,
            },
        )
        task.attrs["tool_call_ids"].append(tool.id)
        if decision:
            previous_result = last_result_by_skill.get(current_skill.id)
            if previous_result:
                builder.add_edge(previous_result, decision.id, "informs")
            builder.add_edge(decision.id, tool.id, "drives")
            last_result_by_skill[current_skill.id] = None
        if block.get("id"):
            pending_tools[str(block["id"])] = tool
        thoughts.clear()

    def create_artifact_version(
        key: str,
        tool: TraceNode,
        index: int,
        *,
        external: bool = False,
    ) -> ArtifactVersion:
        versions = builder.graph.artifacts.setdefault(key, [])
        if external:
            version_number = 0
        else:
            existing_numbers = [item.version for item in versions]
            version_number = max(existing_numbers, default=0) + 1
        task = builder.graph.nodes.get(tool.parent_id or "")
        skill_id = tool.attrs.get("skill_run_id")
        artifact = ArtifactVersion(
            artifact_key=key,
            version=version_number,
            node_id="",
            producer_skill_run_id=None if external else skill_id,
            producer_task_id=None if external else (task.id if task else None),
            producer_tool_call_id=None if external else tool.id,
            created_index=index,
            is_contract=Path(key).suffix.lower() in _CONTRACT_EXTENSIONS,
        )
        node = builder.add_node(
            "ArtifactVersion",
            f"{_basename(key)} v{version_number}",
            skill_id,
            index,
            {
                "artifact_key": key,
                "version": version_number,
                "is_contract": artifact.is_contract,
                "external": external,
                "producer_skill_run_id": artifact.producer_skill_run_id,
                "producer_task_id": artifact.producer_task_id,
                "producer_tool_call_id": artifact.producer_tool_call_id,
            },
        )
        artifact.node_id = node.id
        previous = versions[-1] if versions else None
        versions.append(artifact)
        if not external:
            builder.add_edge(tool.id, node.id, "produces")
            if previous:
                builder.add_edge(previous.node_id, node.id, "supersedes")
        return artifact

    def latest_or_external(key: str, tool: TraceNode, index: int) -> ArtifactVersion:
        versions = builder.graph.artifacts.get(key)
        if versions:
            return versions[-1]
        return create_artifact_version(key, tool, index, external=True)

    def process_artifact_result(tool: TraceNode, index: int) -> None:
        tool_name = tool.attrs.get("tool_name")
        inputs = _safe_dict(tool.attrs.get("inputs"))
        file_path = str(inputs.get("file_path") or "")
        if not file_path or tool_name not in {"Read", "Write", "Edit"}:
            return
        key = _artifact_key(file_path, str(tool.attrs.get("cwd") or ""))
        if not key:
            return
        if tool_name in {"Read", "Edit"}:
            consumed = latest_or_external(key, tool, index)
            builder.add_edge(consumed.node_id, tool.id, "consumes")
        if tool_name in {"Write", "Edit"}:
            create_artifact_version(key, tool, index)

    for index, record in _iter_records(path, builder.graph.diagnostics):
        last_index = index
        message = _safe_dict(record.get("message"))
        role = message.get("role")
        content = message.get("content")
        cwd = str(record.get("cwd") or last_cwd)
        if cwd:
            last_cwd = cwd

        if role == "user" and not record.get("isMeta") and isinstance(content, str):
            if not goal:
                goal = content
            elif current_skill:
                builder.add_node(
                    "HumanInteraction",
                    _first_sentence(content),
                    current_skill.id,
                    index,
                    {
                        "interaction_type": "feedback",
                        "text": content,
                        "skill_run_id": current_skill.id,
                    },
                )

        attribution = record.get("attributionSkill")
        if attribution:
            switch_skill(str(attribution), index)

        if role == "assistant" and isinstance(content, list):
            for block in content:
                block_type = block.get("type")
                if block_type in {"thinking", "text"} and current_skill and not record.get("isMeta"):
                    text = str(block.get("thinking") or block.get("text") or "").strip()
                    if text:
                        pending_thought.setdefault(current_skill.id, []).append(text)
                elif block_type == "tool_use" and block.get("name") == "Skill":
                    create_skill(block, index)
                elif block_type == "tool_use" and block.get("name") in {"TaskCreate", "TaskUpdate"}:
                    create_task_control(block, index)
                elif block_type == "tool_use":
                    create_tool(block, index, cwd)
            continue

        if role == "user" and isinstance(content, list):
            for block in content:
                if block.get("type") != "tool_result":
                    continue
                tool_id = str(block.get("tool_use_id") or "")
                result_text = _tool_result_text(block.get("content"))
                result_info = _safe_dict(record.get("toolUseResult"))
                tool = pending_tools.pop(tool_id, None)
                if tool is None:
                    finalize_task_create(tool_id, result_info, result_text)
                    continue
                exit_code = result_info.get("exitCode")
                explicit_error = block.get("is_error") is True or result_info.get("is_error") is True
                is_error = bool(explicit_error or (exit_code is not None and str(exit_code) != "0"))
                tool.attrs["result"] = result_text
                tool.attrs["is_error"] = is_error
                tool.status = "failed" if is_error else "succeeded"
                tool.end_index = index
                result = builder.add_node(
                    "Result",
                    "Failed result" if is_error else "Successful result",
                    tool.id,
                    index,
                    {
                        "tool_call_id": tool.id,
                        "tool_use_id": tool.attrs.get("tool_use_id"),
                        "status": "failed" if is_error else "succeeded",
                        "content": result_text[:4000],
                        "exit_code": exit_code,
                    },
                )
                tool.attrs["result_node_id"] = result.id
                builder.add_edge(tool.id, result.id, "yields")
                last_result_by_skill[tool.attrs["skill_run_id"]] = result.id
                if is_error:
                    evidence = "\n".join(
                        part for part in (result_text, str(result_info.get("stderr") or "")) if part
                    )
                    category = _classify_error(evidence)
                    error = builder.add_node(
                        "Error",
                        f"{category}: {_first_sentence(evidence, 64)}",
                        result.id,
                        index,
                        {
                            "category": category,
                            "severity": _error_severity(category, tool),
                            "status": "failed",
                            "evidence": evidence,
                            "tool_call_id": tool.id,
                            "result_id": result.id,
                            "skill_run_id": tool.attrs["skill_run_id"],
                        },
                    )
                    builder.add_edge(result.id, error.id, "fails_with")
                    recovery_error.setdefault(tool.attrs["skill_run_id"], []).append(error.id)
                else:
                    process_artifact_result(tool, index)
                    if tool.attrs.get("bash_class") == "VALIDATE":
                        observation = builder.add_node(
                            "Observation",
                            "Validation passed",
                            result.id,
                            index,
                            {
                                "category": "ValidationResult",
                                "severity": "important",
                                "status": "passed",
                                "evidence": result_text,
                                "tool_call_id": tool.id,
                                "result_id": result.id,
                                "skill_run_id": tool.attrs["skill_run_id"],
                            },
                        )
                        builder.add_edge(result.id, observation.id, "observes")
                        open_errors = recovery_error.get(tool.attrs["skill_run_id"], [])
                        if open_errors:
                            resolved_error = open_errors.pop()
                            error_node = builder.graph.nodes[resolved_error]
                            error_node.attrs["resolved"] = True
                            builder.add_edge(observation.id, resolved_error, "resolves")

    for open_errors in recovery_error.values():
        for unresolved_error in open_errors:
            error_node = builder.graph.nodes[unresolved_error]
            error_node.attrs["severity"] = "critical"
            error_node.attrs["resolved"] = False

    if current_skill and current_skill.attrs["activity_intervals"]:
        current_skill.attrs["activity_intervals"][-1][1] = last_index
    for node in builder.graph.nodes.values():
        if node.kind in {"SkillRun", "Task"}:
            node.end_index = node.end_index if node.end_index is not None else last_index
            if node.attrs.get("status") in {"completed", "failed", "cancelled"}:
                continue
            node.status = "closed"
        if node.kind == "SkillRun":
            for interval in node.attrs["activity_intervals"]:
                if interval[1] is None:
                    interval[1] = last_index

    builder.graph.session_summary.update(
        {"goal": goal, "source": str(path), "event_count": last_index + 1, "base_cwd": last_cwd}
    )
    return builder.graph


def _visible_ancestor(graph: TraceGraph, node_id: str, visible: set[str]) -> tuple[Optional[str], tuple[str, ...]]:
    via: list[str] = []
    current_id: Optional[str] = node_id
    while current_id and current_id not in visible:
        via.append(current_id)
        node = graph.nodes.get(current_id)
        current_id = node.parent_id if node else None
    return current_id, tuple(via)


def project_graph(graph: TraceGraph, level: str) -> GraphProjection:
    """Create a consistent view by filtering nodes and rolling hidden endpoints up."""
    normalized = level.lower()
    if normalized not in {"macro", "meso", "micro"}:
        raise ValueError(f"Unknown projection level: {level}")

    if normalized == "micro":
        projection = GraphProjection(dict(graph.nodes), list(graph.edges), normalized)
        validate_graph(projection)
        return projection

    visible: set[str] = {
        node.id for node in graph.nodes.values() if node.kind in {"SkillRun", "Task"}
    }
    if normalized == "macro":
        for versions in graph.artifacts.values():
            contracts = [item for item in versions if item.is_contract]
            if contracts:
                visible.add(contracts[-1].node_id)
        visible.update(
            node.id
            for node in graph.nodes.values()
            if node.kind == "Error" and node.attrs.get("severity") in {"important", "critical"}
        )
    else:
        visible.update(
            node.id
            for node in graph.nodes.values()
            if node.kind in {"Decision", "Error", "Observation"}
        )
        visible.update(
            node.id
            for node in graph.nodes.values()
            if node.kind == "ArtifactVersion" and node.attrs.get("is_contract")
        )
        for node in graph.nodes.values():
            if node.kind != "ToolCall":
                continue
            bash_class = node.attrs.get("bash_class")
            if node.attrs.get("tool_name") in {"Write", "Edit"} or bash_class in {"VALIDATE", "VERSION_CONTROL", "ACTION"}:
                visible.add(node.id)

    projected_edges: list[TraceEdge] = []
    seen: set[tuple[Any, ...]] = set()
    for edge in graph.edges:
        source, source_via = _visible_ancestor(graph, edge.source, visible)
        target, target_via = _visible_ancestor(graph, edge.target, visible)
        if source is None or target is None or source == target:
            continue
        via = edge.via + source_via + target_via
        derived = edge.derived or source != edge.source or target != edge.target
        candidate = TraceEdge(
            source,
            target,
            edge.kind,
            observed=edge.observed,
            derived=derived,
            via=via,
        )
        key = (
            candidate.source,
            candidate.target,
            candidate.kind,
            candidate.observed,
            candidate.derived,
            candidate.via,
        )
        if key not in seen:
            seen.add(key)
            projected_edges.append(candidate)

    projection = GraphProjection(
        {node_id: graph.nodes[node_id] for node_id in visible},
        projected_edges,
        normalized,
    )
    validate_graph(projection)
    return projection


def _mermaid_text(text: Any, limit: int = 72) -> str:
    cleaned = re.sub(r"[\[\]{}()\"'`|<>]", " ", str(text or ""))
    cleaned = re.sub(r"#", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:limit] + ("…" if len(cleaned) > limit else "")


# Node kinds at each drill-down level. Level 1 is always visible; levels 2+3
# are hidden by default and revealed by clicking the parent node.
_LEVEL_BY_KIND: dict[str, int] = {
    "SkillRun": 1,
    "Task": 2,
    "ToolCall": 3,
    "Decision": 3,
    "Result": 3,
    "Error": 3,
    "Observation": 3,
    "HumanInteraction": 3,
}
_PARENTABLE_KINDS = {"SkillRun", "Task"}


def _build_parent_map(by_id: dict[str, "TraceNode"]) -> dict[str, list[str]]:
    """Build a logical parent→children mapping for drill-down.

    For a Skill node, its children are the Tasks whose ``parent_id`` points at
    the Skill. For a Task node, its children are any descendants whose nearest
    Skill/Task ancestor is this Task (so Error / Observation / Result that hang
    off a Result child still belong to the Task in the UI).
    """
    # Pre-compute nearest Skill/Task ancestor for each node.
    nearest_named: dict[str, Optional[str]] = {}

    def resolve(node_id: str) -> Optional[str]:
        if node_id in nearest_named:
            return nearest_named[node_id]
        node = by_id.get(node_id)
        if node is None or node.parent_id is None:
            nearest_named[node_id] = None
            return None
        parent = by_id.get(node.parent_id)
        if parent and parent.kind in _PARENTABLE_KINDS:
            nearest_named[node_id] = parent.id
            return parent.id
        ancestor = resolve(node.parent_id) if node.parent_id else None
        nearest_named[node_id] = ancestor
        return ancestor

    parent_map: dict[str, list[str]] = {}
    for node in by_id.values():
        if node.kind not in _PARENTABLE_KINDS:
            continue
        if node.kind == "SkillRun":
            children = [
                other.id
                for other in by_id.values()
                if other.parent_id == node.id and other.kind == "Task"
            ]
        else:
            children = [
                other.id
                for other in by_id.values()
                if other.id != node.id
                and resolve(other.id) == node.id
            ]
        if children:
            parent_map[node.id] = children
    return parent_map


def render_mermaid(
    projection: GraphProjection,
    skill_filter: Optional[set[str]] = None,
    collapse_tasks: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Render a projection with Skill and Task as nested Mermaid containers.

    Returns ``(mermaid_text, drilldown)`` where ``drilldown`` carries the
    parent→children map and level map the front-end JS uses for click-to-
    expand / click-to-collapse interaction.
    """
    drilldown: dict[str, Any] = {"parentMap": {}, "levelMap": {}}
    lines = [
        "%%{init: {"
        "'theme': 'base',"
        "'themeVariables': {"
        "'fontFamily': 'Arial, Helvetica, \"Microsoft YaHei\", \"Segoe UI\", sans-serif',"
        "'fontSize': '14px',"
        "'primaryColor': '#f7f7f4',"
        "'primaryBorderColor': '#898781',"
        "'primaryTextColor': '#0b0b0b',"
        "'lineColor': '#898781',"
        "'tertiaryColor': '#eef5ff'"
        "},"
        "'flowchart': {'useMaxWidth': false, 'htmlLabels': true, 'curve': 'basis', 'padding': 14, 'nodeSpacing': 50, 'rankSpacing': 60},"
        "'securityLevel': 'loose',"
        "'mindmap': {'padding': 20}"
        "}}%%",
        "graph LR",
    ]
    lines.extend(
        [
            "classDef skill fill:#e3f2fd,stroke:#2a78d6,stroke-width:2px,color:#0b0b0b;",
            "classDef task fill:#fff4e0,stroke:#d97706,stroke-width:1.5px,color:#0b0b0b;",
            "classDef decision fill:#e6e2f7,stroke:#4a3aa7,color:#0b0b0b;",
            "classDef tool fill:#d6f4e8,stroke:#1baf7a,color:#0b0b0b;",
            "classDef artifact fill:#fbe1d7,stroke:#eb6834,color:#0b0b0b;",
            "classDef error fill:#f7d8d8,stroke:#d03b3b,stroke-width:2px,color:#0b0b0b;",
            "classDef observation fill:#e8f5e9,stroke:#0ca30c,color:#0b0b0b;",
            "classDef human fill:#f3e5f5,stroke:#8e24aa,color:#0b0b0b;",
        ]
    )
    visible = set(projection.nodes)
    if skill_filter is not None:
        allowed = {str(item) for item in skill_filter}
        skill_ids_in_filter: set[str] = set()
        for node in projection.nodes.values():
            if node.kind != "SkillRun":
                continue
            if str(node.id) in allowed or node.attrs.get("skill_name") in allowed:
                skill_ids_in_filter.add(node.id)
        visible = {
            nid for nid in visible
            if projection.nodes[nid].kind != "SkillRun"
            or projection.nodes[nid].id in skill_ids_in_filter
            or projection.nodes[nid].attrs.get("skill_run_id") in skill_ids_in_filter
            or projection.nodes[nid].attrs.get("producer_skill_run_id") in skill_ids_in_filter
        }
    emitted: set[str] = set()
    skills = sorted(
        (node for node in projection.nodes.values()
         if node.kind == "SkillRun" and node.id in visible),
        key=lambda node: node.start_index,
    )
    for skill in skills:
        owned_tasks = [
            node for node in projection.nodes.values()
            if node.kind == "Task" and node.parent_id == skill.id and node.id in visible
        ]
        # Show Task count in the Skill title so the count is obvious even if the
        # boxes are tiny. The leading "▸" is the drill-down hint toggled by JS.
        skill_title = f"▸ 🧩 {_mermaid_text(skill.label)} · {len(owned_tasks)} task{'s' if len(owned_tasks) != 1 else ''}"
        lines.append(f'    subgraph SG_{skill.id}["{skill_title}"]')
        lines.append("        direction LR")
        lines.append(f'        {skill.id}["▸ 🧩 {_mermaid_text(skill.label)}"]:::skill')
        emitted.add(skill.id)
        if collapse_tasks:
            artifact_count = sum(
                1 for node in projection.nodes.values()
                if node.kind == "ArtifactVersion" and node.parent_id == skill.id
            )
            summary_label = f"{len(owned_tasks)} tasks / {artifact_count} artifacts"
            summary_id = f"SUMMARY_{skill.id}"
            lines.append(f'        {summary_id}["📦 {_mermaid_text(summary_label, 40)}"]:::task')
            emitted.add(summary_id)
        else:
            tasks = sorted(owned_tasks, key=lambda node: node.start_index)
            for task in tasks:
                # Decide flat vs nested based on whether this Task has visible
                # children in the current projection. With no children, drawing
                # a subgraph just produces a redundant label box around the
                # task node — flat rendering is much clearer.
                task_children = sorted(
                    (
                        node for node in projection.nodes.values()
                        if node.parent_id == task.id and node.id in visible
                        and node.id not in emitted
                    ),
                    key=lambda node: node.start_index,
                )
                if task_children:
                    lines.append(f'        subgraph TG_{task.id}["▸ 📌 {_mermaid_text(task.label)}"]')
                    lines.append("            direction TB")
                    lines.append(f'            {task.id}["▸ 📌 {_mermaid_text(task.label)}"]:::task')
                    emitted.add(task.id)
                    for child in task_children:
                        css = {
                            "Decision": "decision",
                            "ToolCall": "tool",
                            "Error": "error",
                            "Observation": "observation",
                            "Result": "tool",
                            "HumanInteraction": "human",
                        }.get(child.kind, "task")
                        icon = {
                            "Decision": "◇", "ToolCall": "🛠", "Error": "🔴",
                            "Observation": "✅", "Result": "📝", "HumanInteraction": "👤",
                        }.get(child.kind, "•")
                        lines.append(f'            {child.id}["{icon} {_mermaid_text(child.label)}"]:::{css}')
                        emitted.add(child.id)
                    lines.append("        end")
                else:
                    lines.append(f'        {task.id}["▸ 📌 {_mermaid_text(task.label)}"]:::task')
                    emitted.add(task.id)
        lines.append("    end")

    for node in sorted(
        (n for n in projection.nodes.values() if n.id not in emitted and n.id in visible),
        key=lambda item: item.start_index,
    ):
        css = {
            "ArtifactVersion": "artifact",
            "Error": "error",
            "Observation": "observation",
            "Decision": "decision",
            "ToolCall": "tool",
            "Task": "task",
            "SkillRun": "skill",
            "HumanInteraction": "human",
        }.get(node.kind, "task")
        icon = {
            "ArtifactVersion": "📄", "Error": "🔴", "Observation": "✅",
            "HumanInteraction": "👤",
        }.get(node.kind, "•")
        lines.append(f'    {node.id}["{icon} {_mermaid_text(node.label)}"]:::{css}')
        emitted.add(node.id)

    styles = {
        "invokes": ("-->", "#2a78d6"),
        "drives": ("-.->", "#4a3aa7"),
        "consumes": ("-.->", "#1baf7a"),
        "produces": ("-->", "#eb6834"),
        "supersedes": ("-->", "#898781"),
        "yields": ("==>", "#d03b3b"),
        "fails_with": ("==>", "#d03b3b"),
        "observes": ("==>", "#0ca30c"),
        "informs": ("-.->", "#898781"),
        "triggers": ("==>", "#4a3aa7"),
        "resolves": ("-->", "#0ca30c"),
    }
    for index, edge in enumerate(projection.edges):
        if edge.source not in visible or edge.target not in visible:
            continue
        arrow, color = styles.get(edge.kind, ("-->", "#898781"))
        label = edge.kind + (" · 汇总" if edge.derived else "")
        lines.append(f'    {edge.source} {arrow}|"{label}"| {edge.target}')
        width = "2.5px" if edge.derived or edge.kind in {"yields", "triggers", "fails_with", "observes"} else "1.5px"
        dash = ",stroke-dasharray:5 4" if edge.derived else ""
        lines.append(f"    linkStyle {index} stroke:{color},stroke-width:{width}{dash};")

    # Build drill-down metadata from the *visible* subgraph so the JS only ever
    # toggles nodes/edges that are actually in the diagram.
    visible_by_id: dict[str, TraceNode] = {nid: n for nid, n in projection.nodes.items() if nid in visible}
    level_map: dict[str, int] = {}
    for nid, node in visible_by_id.items():
        lvl = _LEVEL_BY_KIND.get(node.kind)
        if lvl is not None:
            level_map[nid] = lvl
    parent_map: dict[str, list[str]] = {}
    for parent_id, children in _build_parent_map(visible_by_id).items():
        kept = [c for c in children if c in level_map]
        if kept:
            parent_map[parent_id] = kept
    drilldown["levelMap"] = level_map
    drilldown["parentMap"] = parent_map

    return "\n".join(lines), drilldown


def render_contract_mermaid(graph: TraceGraph) -> str:
    """Render Skill-to-contract lineage using only observed producer/consumer evidence."""
    lines = ["graph LR"]
    lines.extend(
        [
            "classDef skill fill:#e3f2fd,stroke:#2a78d6,stroke-width:2px,color:#0b0b0b;",
            "classDef artifact fill:#fbe1d7,stroke:#eb6834,color:#0b0b0b;",
        ]
    )
    skills = {node.id: node for node in graph.nodes.values() if node.kind == "SkillRun"}
    contract_versions: list[ArtifactVersion] = []
    rendered_versions: set[str] = set()
    for versions in graph.artifacts.values():
        contracts = [item for item in versions if item.is_contract]
        contract_versions.extend(contracts)
        rendered_versions.update(version.node_id for version in contracts)

    relevant_skills: set[str] = set()
    lineage: set[tuple[str, str, str]] = set()
    for edge in graph.edges:
        if edge.kind == "produces" and edge.target in rendered_versions:
            tool = graph.nodes.get(edge.source)
            skill_id = tool.attrs.get("skill_run_id") if tool else None
            if skill_id in skills:
                relevant_skills.add(skill_id)
                lineage.add((skill_id, edge.target, "produces"))
        elif edge.kind == "consumes" and edge.source in rendered_versions:
            tool = graph.nodes.get(edge.target)
            skill_id = tool.attrs.get("skill_run_id") if tool else None
            if skill_id in skills:
                relevant_skills.add(skill_id)
                lineage.add((edge.source, skill_id, "consumes"))

    for skill_id in sorted(relevant_skills, key=lambda item: skills[item].start_index):
        lines.append(f'    {skill_id}["🧩 {_mermaid_text(skills[skill_id].label)}"]:::skill')
    for artifact in sorted(contract_versions, key=lambda item: item.created_index):
        node = graph.nodes[artifact.node_id]
        lines.append(f'    {artifact.node_id}["📄 {_mermaid_text(node.label)}"]:::artifact')
    for source, target, kind in sorted(lineage):
        arrow = "-->" if kind == "produces" else "-.->"
        lines.append(f'    {source} {arrow}|"{kind}"| {target}')
    return "\n".join(lines)


_MERMAID_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  /* Web-safe fonts FIRST so mermaid's text measurement never hits a missing
     font (PingFang SC is macOS-only and triggers the
     translate(undefined, NaN) layout error on Windows when used for
     measurement). */
  html, body { margin: 0; padding: 0; background: #fff;
    font-family: Arial, Helvetica, "Microsoft YaHei", "Segoe UI", sans-serif; }
  #wrap { width: 100%; min-height: HEIGHTpx; overflow: auto;
    border: 1px solid #e6e4df; border-radius: 10px; }
  #mermaid { width: 100%; cursor: grab; }
  #mermaid:active { cursor: grabbing; }
  /* Don't force `height: 100%` on the SVG — mermaid sizes itself; forcing a
     percentage height before the container is laid out produces NaN widths
     and the cascade of `translate(undefined, NaN)` errors. */
  #mermaid svg { display: block; max-width: 100%; height: auto !important; }
  .hint { position: absolute; right: 12px; bottom: 10px; font-size: 11px;
    color: #898781; background: rgba(255,255,255,.85); padding: 3px 8px;
    border-radius: 6px; pointer-events: none; letter-spacing: .02em; }
  #err { color: #b00020; padding: 16px; font-family: ui-monospace, monospace;
    font-size: 12px; white-space: pre-wrap; display: none; }
</style>
</head>
<body>
<div id="wrap">
  <div id="mermaid" class="mermaid-root"></div>
  <div class="hint">🖱 滚轮缩放 · 拖拽平移 · 点 Skill/Task 标题 ▸ 展开 / 折叠子图</div>
</div>
__DRILLDOWN_BLOCK__
<script id="mermaid-source" type="application/json">__SOURCE_JSON__</script>
__INITIAL_LEVEL_SCRIPT__
"""
_MERMAID_HTML_TEMPLATE_TAIL = """
<script>
  (function () {
    var errEl = document.getElementById('err');
    function log(msg) {
      errEl.style.display = 'block';
      errEl.textContent = msg;
      console.error('[mermaid]', msg);
    }
    function loadScript(src) {
      return new Promise(function (resolve, reject) {
        var s = document.createElement('script');
        s.src = src;
        s.onload = function () { resolve(src); };
        s.onerror = function () { reject(new Error('failed to load ' + src)); };
        document.head.appendChild(s);
      });
    }
    var cdns = [
      'https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js',
      'https://unpkg.com/mermaid@10.9.1/dist/mermaid.min.js',
      'https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js',
      'https://cdn.bootcdn.net/ajax/libs/mermaid/10.9.1/mermaid.min.js',
      'https://lib.baomitu.com/mermaid/10.9.1/mermaid.min.js',
    ];

    (async function () {
      var loaded = null, lastErr = null;
      for (var i = 0; i < cdns.length; i++) {
        try {
          await loadScript(cdns[i]);
          if (typeof window.mermaid !== 'undefined') { loaded = cdns[i]; break; }
        } catch (e) { lastErr = e; }
      }
      if (!loaded) {
        log('All CDNs failed to load mermaid.js.\\nLast error: '
          + (lastErr ? lastErr.message : 'unknown')
          + '\\nNetwork diagnostics: open DevTools -> Network. If all cdn.* requests returned 0 / net::ERR, your network blocks public CDNs - download mermaid.min.js locally and edit the script list.');
        return;
      }
      try {
        var srcEl = document.getElementById('mermaid-source');
        var source = srcEl ? JSON.parse(srcEl.textContent) : '';
        window.mermaid.initialize({
          startOnLoad: false,
          securityLevel: 'loose',
          theme: 'base',
          themeVariables: {
            fontFamily: 'Arial, Helvetica, "Microsoft YaHei", "Segoe UI", sans-serif',
            fontSize: '14px',
          },
          flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
        });
        await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });
        var out = await window.mermaid.render('mermaid-svg', source);
        document.getElementById('mermaid').innerHTML = out.svg;
        var svg = document.getElementById('mermaid').querySelector('svg');
        if (svg) svg.style.cursor = 'grab';
        errEl.style.display = 'none';
        if (typeof window.__drilldownInit === 'function') {
          window.__drilldownInit(__INITIAL_LEVEL__);
        }
      } catch (e) {
        log('mermaid render failed: ' + e.message + '\\n\\nSource (first 2000 chars):\\n'
          + String(source).slice(0, 2000));
      }
    })();
  })();
</script>
</body>
</html>
"""


def _mermaid_html(
    mermaid_source: str,
    drilldown: dict[str, Any],
    height: int = 720,
    initial_level: int = 1,
) -> str:
    """Build a self-contained HTML page that renders the mermaid source
    inside a CDN-waterfall iframe and wires up the drill-down interaction.

    The mermaid source is serialised as JSON inside a
    ``<script type="application/json">`` block, so HTML-significant
    characters (``</script>``, ``<script>``, backticks, etc.) cannot break
    the surrounding parser regardless of what the trace contains.
    """
    import json as _json

    source_json = _json.dumps(mermaid_source, ensure_ascii=False)
    drilldown_block = _drilldown_html(drilldown)
    return (
        _MERMAID_HTML_TEMPLATE
        .replace("HEIGHT", str(height))
        .replace("__DRILLDOWN_BLOCK__", drilldown_block)
        .replace("__SOURCE_JSON__", source_json)
        .replace(
            "__INITIAL_LEVEL_SCRIPT__",
            "<script>window.__drilldownVisibleLevels=" + str(initial_level) + ";</script>",
        )
        + _MERMAID_HTML_TEMPLATE_TAIL.replace("__INITIAL_LEVEL__", str(initial_level))
    )


def _safe_artifact_content(graph: TraceGraph, artifact_key: str, max_bytes: int = 1_000_000) -> Optional[str]:
    base_cwd = str(graph.session_summary.get("base_cwd") or "")
    if not base_cwd:
        return None
    base = Path(base_cwd).resolve()
    candidate = (base / artifact_key).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if not candidate.is_file() or candidate.stat().st_size > max_bytes:
        return None
    for encoding in ("utf-8", "gbk"):
        try:
            return candidate.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            continue
    return None


def _mermaid_live_pako_url(source: str) -> str:
    """Encode mermaid source for a mermaid.live URL fragment (pako + url-safe base64)."""
    import base64
    import zlib

    # mermaid.live uses pako.deflate (zlib format, wbits=15) and then base64url.
    compressor = zlib.compressobj(9, zlib.DEFLATED, 15)
    payload = compressor.compress(source.encode("utf-8")) + compressor.flush()
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _drilldown_html(drilldown: dict[str, Any]) -> str:
    """Render the inline <script> + <style> block that wires click-to-expand.

    Designed to work whether the SVG was produced by mermaid.js (iframe path)
    or by a remote service like kroki / mermaid.ink (inline path). Both emit
    the same node and edge DOM shape, so the same selector logic applies.

    Critical: click handlers must be attached AFTER the SVG is rendered —
    mermaid.render() is async, so attaching handlers eagerly at script-load
    time finds zero nodes. The render script calls ``__drilldownInit(N)``
    once the SVG is in the DOM; we use that hook to (a) walk the visible
    parentMap and attach click listeners, then (b) apply initial visibility.
    """
    import json as _json

    payload = _json.dumps(drilldown, ensure_ascii=False)
    return (
        "<style>"
        ".mermaid-root g.node.drilldown-parent{cursor:pointer;}"
        ".mermaid-root g.node.drilldown-parent:hover rect,"
        ".mermaid-root g.node.drilldown-parent:hover polygon,"
        ".mermaid-root g.node.drilldown-parent:hover .basic label{filter:brightness(0.94);}"
        "</style>"
        f"<script id=\"drilldown-data\" type=\"application/json\">{payload}</script>"
        "<script>"
        "(function(){try{"
        "var dataEl=document.getElementById('drilldown-data');"
        "var data=dataEl?JSON.parse(dataEl.textContent):{parentMap:{},levelMap:{}};"
        "var root=document.querySelector('.mermaid-root')||document.body;"
        # Escape regex metacharacters in node IDs (mermaid IDs are alphanumeric,
        # but user data could contain dashes/underscores which are already safe).
        "function esc(s){return s.replace(/[-/\\\\^$*+?.()|[\\]{}]/g,'\\\\$&');}"
        # Find a node by its declared ID. mermaid emits IDs like
        # ``flowchart-N1-0``; kroki sometimes emits just ``N1``. We accept both.
        "function findNode(id){"
        "if(!id)return null;"
        "var pat=new RegExp('^(?:flowchart-)?'+esc(id)+'(?:-[0-9]+)?$');"
        "var nodes=root.querySelectorAll('g.node[id],g[id^=\"flowchart-\"],g[id^=\"N\"],g[id]');"
        "for(var i=0;i<nodes.length;i++){var n=nodes[i];if(pat.test(n.id||''))return n;}"
        # Last-resort: match any <g> whose text content begins with the
        # truncated label (only used as a fallback for edge cases).
        "var fallback=root.querySelectorAll('g.node');"
        "for(var j=0;j<fallback.length;j++){var g=fallback[j];if((g.id||'').indexOf(id)>=0)return g;}"
        "return null;"
        "}"
        "function findEdges(srcId,tgtId){var out=[];"
        "root.querySelectorAll('g.edgePath, .flowchart-link, g[class*=\"edge\"]').forEach(function(e){"
        "var id=e.id||'';var pat=new RegExp('_'+esc(srcId)+'_'+esc(tgtId)+'_');"
        "if(pat.test(id))out.push(e);"
        "});return out;"
        "}"
        "function setIcon(parent,open){"
        "var lbl=parent.querySelector('foreignObject, .nodeLabel, g.label, text');"
        "if(!lbl)return;"
        "var cur=lbl.textContent||'';"
        "if(open){if(cur.indexOf('▸')===0)lbl.textContent='▾'+cur.substring(1);}"
        "else{if(cur.indexOf('▾')===0)lbl.textContent='▸'+cur.substring(1);}"
        "}"
        "function attachHandlers(){"
        "var keys=Object.keys(data.parentMap||{});"
        "console.log('[drilldown] attaching click handlers for',keys.length,'parents');"
        "keys.forEach(function(parentId){"
        "var parent=findNode(parentId);"
        "if(!parent){console.warn('[drilldown] parent node not found:',parentId);return;}"
        "if(parent._drilldownReady)return;"
        "parent._drilldownReady=true;"
        "parent.classList.add('drilldown-parent');"
        "parent.setAttribute('data-drilldown-parent',parentId);"
        "var children=data.parentMap[parentId];"
        "parent.addEventListener('click',function(ev){"
        "ev.stopPropagation();"
        "var allHidden=children.every(function(cid){var c=findNode(cid);return c&&c.style.display==='none';});"
        "var next=allHidden?'':'none';"
        "children.forEach(function(cid){"
        "var c=findNode(cid);if(c)c.style.display=next;"
        "findEdges(parentId,cid).forEach(function(e){e.style.display=next;});"
        "});"
        "setIcon(parent,allHidden);"
        "});"
        "});"
        "}"
        "function applyVisibility(){"
        "var visible=window.__drilldownVisibleLevels||1;"
        "Object.keys(data.levelMap||{}).forEach(function(id){"
        "var lvl=data.levelMap[id];"
        "if(lvl>visible){var n=findNode(id);if(n)n.style.display='none';}"
        "});"
        "}"
        "window.__drilldownInit=function(extraLevels){"
        "extraLevels=extraLevels||1;"
        "var prev=window.__drilldownVisibleLevels||1;"
        "window.__drilldownVisibleLevels=Math.max(prev,extraLevels);"
        "attachHandlers();"
        "applyVisibility();"
        "};"
        "}catch(err){console.error('[drilldown]',err);}"
        "})();"
        "</script>"
    )


try:
    import streamlit as st  # type: ignore
    _REMOTE_CACHE = st.cache_data(show_spinner=False, max_entries=64)
except Exception:  # pragma: no cover - Streamlit not installed (unit tests)
    def _REMOTE_CACHE(func):
        return func


@_REMOTE_CACHE
def _render_mermaid_remote(source: str) -> Optional[str]:
    """Render mermaid source to SVG by calling a public render service.

    This is the most reliable path when the iframe/CDN route is blocked: the
    remote service handles all of mermaid.js + font measurement + layout, and
    returns a static SVG that Streamlit can drop straight into the page.
    Returns ``None`` if every endpoint fails (network blocked, timeout, etc).
    Cached by source string so switching back and forth between skills does
    not re-hit the network.
    """
    import requests

    # Kroki accepts text/plain POST and is generally accessible; it returns the
    # SVG body directly. Try the public instance first, then a few mirrors.
    kroki_hosts = ["https://kroki.io", "https://kroki.tonycrane.tech"]
    for host in kroki_hosts:
        try:
            resp = requests.post(
                f"{host}/mermaid/svg",
                data=source.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=8,
            )
            if resp.ok and "svg" in resp.headers.get("content-type", "").lower():
                return resp.text
        except Exception:
            continue
    # mermaid.ink JSON API; sometimes reachable when kroki is not.
    try:
        resp = requests.post(
            "https://mermaid.ink/api/render",
            json={"code": source, "format": "svg"},
            timeout=8,
        )
        if resp.ok:
            return resp.text
    except Exception:
        pass
    # mermaid.ink static SVG URL (no API call, just a GET to a pako-encoded
    # path); returns the same SVG that mermaid.live uses.
    try:
        encoded = _mermaid_live_pako_url(source)
        resp = requests.get(f"https://mermaid.ink/svg/{encoded}", timeout=8)
        if resp.ok and "svg" in resp.headers.get("content-type", "").lower():
            return resp.text
    except Exception:
        pass
    return None


def validate_graph(graph: TraceGraph | GraphProjection) -> None:
    for edge in graph.edges:
        if edge.source not in graph.nodes or edge.target not in graph.nodes:
            raise ValueError(f"Dangling edge: {edge}")


def main() -> None:
    import streamlit as st
    import streamlit_antd_components as sac

    st.set_page_config(
        page_title="Agent Trace Board v2",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1rem; max-width: 100%;}
        h1 {font-size: 1.55rem !important; margin-bottom: .1rem !important;}
        .trace-note {color:#52514e; font-size:.88rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🧩 Agent Skill Trace Board v2")
    st.caption("一级 SkillRun · 二级 SemanticTask · Decision / ToolCall / Error / .md 契约产物")

    default_trace = os.environ.get(
        "TRACE_JSONL_PATH", "264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl"
    )
    with st.sidebar:
        st.header("⚙️ Trace 设置")
        trace_path = st.text_input("JSONL 路径", value=default_trace)
        level_label = st.radio(
            "显示粒度",
            ["宏观：Skill + Task + 重要证据", "中观：展开决策与关键工具", "微观：全部原始节点"],
            index=0,
        )
        minimum_error = st.select_slider(
            "最低 Error 级别",
            options=["minor", "important", "critical"],
            value="important",
        )
        allow_file_preview = st.checkbox(
            "允许读取 trace cwd 下的产物内容",
            value=False,
            help="仅对可信 JSONL 开启；trace 中的 cwd 和 file_path 会决定本地读取范围。",
        )

    path = Path(trace_path)
    if not path.exists():
        st.warning("请输入有效的 JSONL 路径。")
        st.stop()

    @st.cache_data(show_spinner="正在解析 Skill 层级与产物血缘…")
    def load_graph(path_text: str, modified_ns: int) -> TraceGraph:
        del modified_ns
        return parse_trace(path_text)

    graph = load_graph(str(path), path.stat().st_mtime_ns)
    if not graph.nodes:
        st.warning("Trace 中没有识别到 Skill 调用。")
        st.stop()

    if level_label.startswith("宏观"):
        level = "macro"
    elif level_label.startswith("中观"):
        level = "meso"
    else:
        level = "micro"
    projection = project_graph(graph, level)
    severity_rank = {"minor": 0, "important": 1, "critical": 2}
    threshold = severity_rank[minimum_error]
    visible_nodes = {
        node_id: node
        for node_id, node in projection.nodes.items()
        if node.kind != "Error" or severity_rank.get(str(node.attrs.get("severity")), 0) >= threshold
    }
    projection = GraphProjection(
        visible_nodes,
        [edge for edge in projection.edges if edge.source in visible_nodes and edge.target in visible_nodes],
        projection.level,
    )
    validate_graph(projection)

    counts = {kind: sum(node.kind == kind for node in graph.nodes.values()) for kind in (
        "SkillRun", "Task", "Decision", "ToolCall", "Error", "ArtifactVersion"
    )}
    cols = st.columns(6)
    for column, (kind, count) in zip(cols, counts.items()):
        column.metric(kind, count)

    if graph.diagnostics:
        st.warning(f"解析诊断共 {len(graph.diagnostics)} 条；可能包含格式异常或 Skill 前未归属的工具调用。")
        with st.expander("查看解析诊断"):
            for diagnostic in graph.diagnostics:
                st.code(diagnostic, language="text")

    tab_tree, tab_causal, tab_contract = st.tabs(
        ["🌳 Skill 层级", "🕸️ Skill 因果图", "📄 契约产物"]
    )

    with tab_tree:
        left, right = st.columns([4, 6], gap="large")
        label_to_id: dict[str, str] = {}

        def node_label(node: TraceNode) -> str:
            icons = {
                "SkillRun": "🧩", "Task": "📌", "Decision": "◇", "ToolCall": "🛠️",
                "Error": "🔴", "Observation": "✅", "ArtifactVersion": "📄",
                "Result": "📝", "HumanInteraction": "👤",
            }
            label = f"{icons.get(node.kind, '•')} {node.kind}: {node.label}  [{node.id}]"
            label_to_id[label] = node.id
            return label

        def select_node(label: str) -> Optional[TraceNode]:
            node_id = label_to_id.get(label)
            return graph.nodes.get(node_id) if node_id else None

        def task_children(task: TraceNode):
            children = [
                node for node in graph.nodes.values()
                if node.parent_id == task.id
            ]
            children.extend(
                node for node in graph.nodes.values()
                if node.kind == "ArtifactVersion" and node.attrs.get("producer_task_id") == task.id
            )
            children.sort(key=lambda node: node.start_index)
            return [sac.TreeItem(label=node_label(node)) for node in children]

        tree_items = []
        for skill in sorted(
            (node for node in graph.nodes.values() if node.kind == "SkillRun"),
            key=lambda node: node.start_index,
        ):
            tasks = sorted(
                (node for node in graph.nodes.values() if node.kind == "Task" and node.parent_id == skill.id),
                key=lambda node: node.start_index,
            )
            task_items = [
                sac.TreeItem(label=node_label(task), children=task_children(task) or None)
                for task in tasks
            ]
            tree_items.append(sac.TreeItem(label=node_label(skill), children=task_items or None))

        with left:
            st.markdown("##### SkillRun → SemanticTask")
            with st.container(height=720, border=True):
                selected = sac.tree(
                    items=tree_items,
                    index=0,
                    open_all=False,
                    size="sm",
                    show_line=True,
                    return_index=False,
                )
        with right:
            st.markdown("##### 节点详情")
            with st.container(height=720, border=True):
                node = select_node(selected) if selected else None
                if node is None:
                    st.info("从左侧选择 Skill、Task 或证据节点。")
                else:
                    st.markdown(f"### {node.kind} · {node.label}")
                    st.caption(f"{node.id} · events {node.start_index}–{node.end_index}")
                    if node.kind == "Task":
                        c1, c2, c3 = st.columns(3)
                        c1.metric("语义模式", node.attrs.get("semantic_mode", "-"))
                        c2.metric("推断置信度", node.attrs.get("inference_confidence", "-"))
                        c3.metric("工具数", len(node.attrs.get("tool_call_ids", [])))
                        st.markdown(f"**边界依据：** {node.attrs.get('boundary_reason', '-')}")
                        with st.expander("查看 Task 原始 Thought", expanded=True):
                            st.text(node.attrs.get("raw_thought") or "无")
                    elif node.kind == "ToolCall":
                        st.markdown(f"**工具：** `{node.attrs.get('tool_name')}`")
                        st.json(node.attrs.get("inputs", {}), expanded=True)
                        if node.attrs.get("bash_subcommands"):
                            st.markdown("**Compound Bash 子命令：**")
                            for command in node.attrs["bash_subcommands"]:
                                st.code(command, language="bash")
                        st.markdown("**结果：**")
                        st.code(str(node.attrs.get("result") or "尚无结果"))
                    elif node.kind == "Error":
                        st.error(
                            f"{node.attrs.get('severity', '').upper()} · {node.attrs.get('category')}"
                        )
                        st.code(str(node.attrs.get("evidence") or ""))
                    elif node.kind == "ArtifactVersion":
                        key = str(node.attrs.get("artifact_key") or "")
                        st.markdown(f"**路径：** `{key}`")
                        st.markdown(
                            f"**版本：** v{node.attrs.get('version')} · "
                            f"**契约：** {'是' if node.attrs.get('is_contract') else '否'}"
                        )
                        if allow_file_preview:
                            content = _safe_artifact_content(graph, key)
                            if content is not None:
                                with st.expander("查看当前文件内容"):
                                    st.code(content, language="markdown" if key.endswith(".md") else None)
                        else:
                            st.caption("文件内容预览已关闭；可在侧边栏显式开启。")
                    else:
                        st.json(node.attrs, expanded=True)

    with tab_causal:
        st.markdown(f"##### {level_label}")

        skill_runs = sorted(
            (node for node in graph.nodes.values() if node.kind == "SkillRun"),
            key=lambda node: node.start_index,
        )
        skill_options = ["🌐 全部 Skills"] + [
            f"🧩 {node.attrs.get('skill_name') or node.label}  ·  {len(node.attrs.get('activity_intervals', []))} 段"
            for node in skill_runs
        ]
        skill_name_to_id = {
            node.attrs.get("skill_name") or node.label: node.id for node in skill_runs
        }

        ctrl_left, ctrl_right = st.columns([2, 3], gap="medium")
        with ctrl_left:
            depth_choice = st.radio(
                "📐 折叠 / 展开层级",
                options=["skills", "tasks", "full"],
                format_func=lambda value: {
                    "skills": "1️⃣ 仅 Skill（最高层）",
                    "tasks": "2️⃣ Skill + Task + 关键证据",
                    "full": "3️⃣ Skill + Task + 完整 Decision/Tool 详情",
                }[value],
                index={"macro": 1, "meso": 1, "micro": 2}[level],
                key="causal_depth",
                horizontal=False,
                help="切换层级后,记得在画布上**点击 Skill/Task 的标题**折叠子图。",
            )
            chosen_skill = st.selectbox(
                "🎯 只看某一个 Skill 的因果图",
                options=skill_options,
                index=0,
                key="causal_single_skill",
                help="选单个 Skill 时,只渲染该 Skill 及其下属节点 + 跨 Skill 边。",
            )

        with ctrl_right:
            st.markdown(
                """
                **画布操作**
                - 🖱 **滚轮** = 缩放 · **拖拽空白** = 平移
                - ▸ **点击 Skill / Task 标题** = 展开 / 折叠其下属子图（嵌套可叠加）
                - 🔍 **悬停节点** = 看 hover 详情
                - 🧭 **右上角控件** = 回到中心 / 切换方向 / 全屏
                """
            )
            st.caption(
                f"当前投影节点 {len(projection.nodes)} 个,边 {len(projection.edges)} 条 · "
                "基于 mermaid.js v10 渲染,子图折叠 + pan/zoom 都是 native 能力。"
            )

        selected_skill_filter: Optional[set[str]] = None
        if chosen_skill != skill_options[0]:
            raw_skill_label = chosen_skill.split("  ·  ")[0]
            skill_label = raw_skill_label[2:] if raw_skill_label.startswith("🧩 ") else raw_skill_label
            skill_id = skill_name_to_id.get(skill_label)
            if skill_id:
                selected_skill_filter = {skill_id}

        if depth_choice == "full" and len(projection.nodes) > 500:
            st.warning(
                f"当前投影含 {len(projection.nodes)} 个节点(深度=完整详情),"
                "渲染会比较慢;可切回 2️⃣ Skill+Task 加快速度。"
            )

        mermaid_text, drilldown = render_mermaid(
            projection,
            skill_filter=selected_skill_filter,
            # Drill-down needs every level to be present in the rendered SVG so
            # clicking a Skill can reveal its Tasks. The depth_choice radio
            # therefore only controls which levels are *initially visible*,
            # not which levels are emitted.
            collapse_tasks=False,
        )

        # depth_choice now sets the initial visibility only — all three levels
        # are always rendered so click-to-expand works.
        initial_level = {"skills": 1, "tasks": 2, "full": 3}.get(depth_choice, 1)

        # Quick stats — visible even if the iframe below fails to render.
        skill_n = sum(1 for n in projection.nodes.values() if n.kind == "SkillRun")
        task_n = sum(1 for n in projection.nodes.values() if n.kind == "Task")
        st.caption(
            f"📊 投影统计 · Skill {skill_n} 个 · Task {task_n} 个 · "
            f"总节点 {len(projection.nodes)} · 总边 {len(projection.edges)} · "
            f"本次 Mermaid 文本 {len(mermaid_text.splitlines())} 行"
        )

        graph_height = 760 if depth_choice == "full" else 600 if depth_choice == "tasks" else 460

        # Render path 1: ask a remote service (kroki / mermaid.ink) to render
        # the mermaid source to SVG. This is the most reliable path on networks
        # where public CDNs are flaky — no browser-side JS or iframe sandboxing
        # involved at all.
        svg_text: Optional[str] = None
        render_source = "remote (kroki / mermaid.ink)"
        with st.spinner("🛰 正在尝试远程渲染 mermaid…"):
            svg_text = _render_mermaid_remote(mermaid_text)

        if svg_text:
            # Drop the SVG directly into the page. Streamlit sanitises by
            # default, so we explicitly opt out for inline SVG. The trailing
            # script wires up click handlers + initial visibility (the script
            # in ``_drilldown_html`` itself only sets up the IIFE and waits).
            wrapped_svg = (
                f"<div class='mermaid-root' style='overflow:auto; max-height:{graph_height}px; "
                f"border:1px solid #e6e4df; border-radius:10px; background:#fff;'>{svg_text}</div>"
                + _drilldown_html(drilldown)
                + f"<script>window.__drilldownInit({initial_level});</script>"
            )
            st.markdown(wrapped_svg, unsafe_allow_html=True)
        else:
            # Render path 2: bundle mermaid.js inside an iframe via srcdoc and
            # try a CDN waterfall. This is the local fallback when the remote
            # service is also blocked.
            render_source = "iframe + CDN waterfall (local)"
            st.info("远程渲染未连通，改用浏览器内 mermaid.js 渲染…")
            html = _mermaid_html(
                mermaid_text,
                drilldown,
                height=graph_height,
                initial_level=initial_level,
            )
            import streamlit.components.v1 as components

            components.html(html, height=graph_height + 20, scrolling=False)

        st.caption(
            f"渲染路径：{render_source} · 当前默认展开层级 = {initial_level}（点击 Skill/Task 标题 ▸ 可继续展开/折叠）"
        )

        # Always show the raw source + a link to open it in mermaid.live, so
        # the user has a path to the diagram even if every render route fails.
        with st.expander("🧾 查看 / 复制 Mermaid 源码（外链 mermaid.live）", expanded=False):
            st.code(mermaid_text, language="text")
            st.markdown(
                f"[🌐 在 mermaid.live 打开](https://mermaid.live/edit#pako:"
                f"{_mermaid_live_pako_url(mermaid_text)})",
                help="在新标签页中渲染当前 Mermaid 源码",
            )

    with tab_contract:
        contracts = [
            version
            for versions in graph.artifacts.values()
            for version in versions
            if version.is_contract
        ]
        if not contracts:
            st.info("没有发现契约产物。")
        else:
            st.markdown("##### Skill 与契约产物血缘")
            st.markdown(f"```mermaid\n{render_contract_mermaid(graph)}\n```")
            rows = []
            for version in sorted(contracts, key=lambda item: item.created_index):
                skill = graph.nodes.get(version.producer_skill_run_id or "")
                task = graph.nodes.get(version.producer_task_id or "")
                rows.append(
                    {
                        "产物": version.artifact_key,
                        "版本": version.version,
                        "生产 Skill": skill.label if skill else "external",
                        "生产 Task": task.label if task else "external input",
                        "事件": version.created_index,
                    }
                )
            st.dataframe(rows, width="stretch", hide_index=True)
            keys = sorted({version.artifact_key for version in contracts})
            selected_key = st.selectbox("选择产物查看版本链", keys)
            selected_versions = graph.artifacts[selected_key]
            def _producer_label(graph: TraceGraph, version: ArtifactVersion) -> str:
                skill_id = version.producer_skill_run_id
                if skill_id in graph.nodes:
                    return graph.nodes[skill_id].label
                return "external"

            st.markdown(
                " → ".join(
                    f"**v{version.version}** ({_producer_label(graph, version)})"
                    for version in selected_versions
                )
            )


if __name__ == "__main__":
    main()
