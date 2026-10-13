"""
Hermes Agent session -> Claude Code JSONL converter
====================================================

Reads Hermes session exports (one JSON object per file from
``D:\\huawei\\my_sessions\\*.jsonl``) and emits Claude Code JSONL streams
that ``claude-code-viewer`` (CCV) understands.

Output layout mirrors CCV's expected directory structure::

    <userprofile>/.claude/projects/<encoded-cwd>/<uuid>.jsonl

Each Hermes session becomes a single CCV session file. The encoded project
folder matches how Claude Code itself stores sessions::

    D:\\huawei\\my_ai_company  ->  D--huawei-my_ai_company

Run with ``--help`` for usage.

Why this lives in ``dev/`` (and not at the project root): the project's
CLAUDE.md / AGENTS.md direct scratch helpers into scratch dirs;
``dev/`` is the agreed-on spot, see MEMORY.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CONVERTER_TAG = "hermes-to-ccv/1.0"


# ---------------------------------------------------------------------------
# Schema emission
# ---------------------------------------------------------------------------


def to_iso(ts: float | int | str | None) -> str:
    """Best-effort Unix epoch (seconds) -> ISO 8601 UTC string."""
    if ts is None:
        # Fall back to now so we always have a valid timestamp
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        epoch = float(ts)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def encode_cwd(cwd: str) -> str:
    """``D:\\foo\\bar`` -> ``D--foo-bar`` (matches Claude Code's project id)."""
    if not cwd:
        return "unknown"
    s = cwd.replace("\\", "/").replace(":", "-")
    # Lowercase the drive letter only (Claude Code keeps it lowercased)
    parts = s.split("/")
    if parts and len(parts[0]) >= 2 and parts[0][1] == "-":
        parts[0] = parts[0][0].lower() + parts[0][1:]
    return "-".join(p for p in parts if p)


def parse_tool_args(arguments: Any) -> dict[str, Any]:
    """Hermes stores tool args as a JSON string; CCV wants a dict."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str) and arguments:
        try:
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else {"raw": parsed}
        except json.JSONDecodeError:
            return {"raw": arguments}
    return {}


def normalize_tool_content(content: Any) -> Any:
    """CCV accepts ``str`` or a list of typed blocks for tool_result.content."""
    if content is None:
        return ""
    if isinstance(content, (str, list)):
        return content
    # dict / scalar -> JSON string keeps it inspectable
    try:
        return json.dumps(content, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(content)


def text_block(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text or ""}


def tool_use_block(tool_call: dict[str, Any]) -> dict[str, Any]:
    fn = tool_call.get("function") or {}
    return {
        "type": "tool_use",
        "id": tool_call.get("id") or tool_call.get("call_id") or str(uuid.uuid4()),
        "name": fn.get("name", "unknown_tool"),
        "input": parse_tool_args(fn.get("arguments")),
    }


def tool_result_block(tool_msg: dict[str, Any]) -> dict[str, Any]:
    """Build a ``tool_result`` content block from a Hermes role='tool' message."""
    raw = tool_msg.get("content", "")
    is_error = False
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed.get("success") is False:
                is_error = True
        except json.JSONDecodeError:
            pass
    return {
        "type": "tool_result",
        "tool_use_id": tool_msg.get("tool_call_id") or tool_msg.get("tool_name", ""),
        "content": normalize_tool_content(raw),
        **({"is_error": True} if is_error else {}),
    }


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------


def convert_messages(
    messages: list[dict[str, Any]],
    *,
    session_id: str,
    cwd: str,
    started_at: float | int | None,
) -> Iterable[dict[str, Any]]:
    """Yield CCV-shaped entry dicts for a Hermes messages list."""
    # Establish the chain of uuids; parentUuid traces back through the chain
    prev_uuid: str | None = None
    # Use a stable epoch anchored at session start; fall back to msg ts
    base_epoch = started_at
    for idx, msg in enumerate(messages):
        role = msg.get("role")
        msg_ts = msg.get("timestamp") or base_epoch
        # Advance base_epoch so later messages don't repeat the same stamp
        if isinstance(msg_ts, (int, float)) and base_epoch is not None:
            base_epoch = msg_ts
        elif base_epoch is None:
            base_epoch = idx

        current_uuid = str(uuid.uuid4())

        if role == "user":
            content = msg.get("content") or ""
            entry = {
                "type": "user",
                "message": {"role": "user", "content": content},
            }
        elif role == "assistant":
            blocks: list[dict[str, Any]] = []
            reasoning = msg.get("reasoning_content") or msg.get("reasoning")
            text = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []

            # Hermes keeps its reasoning as a separate field; keep it visible
            if reasoning:
                blocks.append(
                    {"type": "thinking", "thinking": reasoning, "signature": ""}
                )
            if text or not tool_calls:
                blocks.append(text_block(text))
            for tc in tool_calls:
                blocks.append(tool_use_block(tc))

            entry = {
                "type": "assistant",
                "message": {
                    "id": msg.get("id") or str(uuid.uuid4()),
                    "type": "message",
                    "role": "assistant",
                    "model": "",  # filled in by caller; Hermes sessions vary
                    "content": blocks,
                    "stop_reason": msg.get("finish_reason") or "end_turn",
                },
            }
        elif role == "tool":
            # CCV packages tool results as a user-role entry carrying a tool_result block
            entry = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [tool_result_block(msg)],
                },
            }
        else:
            # System / developer / unknown -> emit as a system entry (CCV keeps these)
            entry = {
                "type": "system",
                "message": {
                    "role": role or "system",
                    "content": msg.get("content", ""),
                },
            }

        # Common base fields
        is_sidechain = bool(msg.get("is_sidechain")) or role in {"system"}
        entry.update(
            {
                "isSidechain": is_sidechain,
                "userType": "external",
                "cwd": cwd,
                "sessionId": session_id,
                "version": CONVERTER_TAG,
                "uuid": current_uuid,
                "timestamp": to_iso(msg_ts),
                "parentUuid": prev_uuid,
            }
        )
        prev_uuid = current_uuid
        yield entry


def convert_session(session: dict[str, Any]) -> list[dict[str, Any]]:
    sid = session.get("id") or session.get("session_id") or str(uuid.uuid4())
    cwd = session.get("cwd") or ""
    model = session.get("model") or "unknown"
    started = session.get("started_at")
    messages = session.get("messages") or []

    entries = []
    for entry in convert_messages(
        messages, session_id=sid, cwd=cwd, started_at=started
    ):
        # Backfill model on assistant entries
        if entry.get("type") == "assistant":
            entry["message"]["model"] = model
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Filesystem wiring
# ---------------------------------------------------------------------------


def is_full_snapshot(path: Path) -> bool:
    """Decide if ``path`` is the canonical ``_end`` snapshot for its session.

    Hermes stores multiple files per session::

        <sid>_start.jsonl     -- empty / first turn (smallest)
        <sid>_turn<N>.jsonl   -- incremental snapshots per turn
        <sid>_end.jsonl       -- final, full snapshot (always largest)
        <sid>_manual.jsonl    -- user-saved checkpoint

    The ``_end`` file is the most complete; we treat it as canonical by
    default to avoid creating duplicate CCV sessions from the same Hermes
    session id.
    """
    return path.stem.endswith("_end")


def iter_hermes_files(
    source: Path, *, all_snapshots: bool
) -> Iterable[tuple[Path, dict[str, Any]]]:
    """Yield (path, parsed_session) for every parseable Hermes file."""
    if all_snapshots:
        candidates = sorted(source.glob("*.jsonl"))
    else:
        # Default: keep only ``_end`` snapshots; fall back to ``_manual``
        # if no ``_end`` exists for a session. Then keep ``_start`` if it's
        # the only thing we have.
        grouped: dict[str, list[Path]] = {}
        for path in source.glob("*.jsonl"):
            # session id = filename minus the trailing snapshot tag
            stem = path.stem
            sid = stem.rsplit("_", 1)[0] if not stem.endswith("_end") else stem[: -len("_end")]
            # ``_turn<N>`` files share the same prefix; collapse them
            if "_turn" in stem and stem.rsplit("_", 1)[1].startswith("turn"):
                sid = stem.rsplit("_", 1)[0]
            # Re-derive the canonical sid (always 23 chars: YYYYMMDD_HHMMSS_x)
            sid = sid[:23] if len(sid) >= 23 else sid
            grouped.setdefault(sid, []).append(path)
        candidates = []
        for sid, paths in grouped.items():
            end_files = [p for p in paths if is_full_snapshot(p)]
            manual = [p for p in paths if p.stem.endswith("_manual")]
            start = [p for p in paths if p.stem.endswith("_start")]
            if end_files:
                candidates.append(end_files[0])  # there should be only one
            elif manual:
                # Manual checkpoints often capture later state than _start
                candidates.append(max(manual, key=lambda p: p.stat().st_size))
            elif start:
                candidates.append(start[0])
            else:
                # No labelled snapshot — fall back to largest file for the sid
                candidates.append(max(paths, key=lambda p: p.stat().st_size))
        candidates = sorted(candidates)

    for path in candidates:
        try:
            with path.open(encoding="utf-8") as f:
                line = f.readline()
                if not line.strip():
                    continue
                yield path, json.loads(line)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[warn] skip {path.name}: {exc}", file=sys.stderr)


def output_path_for(
    session: dict[str, Any], *, claude_dir: Path, overwrite: bool
) -> tuple[Path, str]:
    """Compute the destination path for a session."""
    cwd = session.get("cwd") or ""
    encoded = encode_cwd(cwd)
    project_dir = claude_dir / "projects" / encoded
    project_dir.mkdir(parents=True, exist_ok=True)
    target = project_dir / f"{uuid.uuid4()}.jsonl"
    return target, encoded


def write_session(entries: list[dict[str, Any]], target: Path) -> None:
    with target.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False))
            f.write("\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert Hermes session exports into Claude Code JSONL "
        "streams that claude-code-viewer can render."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(r"D:\huawei\my_sessions"),
        help="Directory containing Hermes *.jsonl session exports",
    )
    parser.add_argument(
        "--claude-dir",
        type=Path,
        default=None,
        help="Override <claude-dir> root (defaults to %%USERPROFILE%%/.claude)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Convert only the first N sessions (useful for smoke-testing)",
    )
    parser.add_argument(
        "--all",
        dest="all_snapshots",
        action="store_true",
        help="Convert every snapshot (incl. _turnN); default keeps only _end",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print destination paths without writing files",
    )
    args = parser.parse_args(argv)

    if not args.source.is_dir():
        print(f"[error] source not found: {args.source}", file=sys.stderr)
        return 2

    claude_dir = args.claude_dir or (
        Path.home() / ".claude" if Path.home().exists() else None
    )
    if claude_dir is None:
        print("[error] cannot resolve ~/.claude; pass --claude-dir", file=sys.stderr)
        return 2

    converted = 0
    skipped = 0
    for path, session in iter_hermes_files(args.source, all_snapshots=args.all_snapshots):
        if args.limit is not None and converted >= args.limit:
            break
        # Hermes uses ``id`` for the session; tolerate either spelling
        if not session.get("id") and not session.get("session_id"):
            print(f"[warn] {path.name}: no session id, skip", file=sys.stderr)
            skipped += 1
            continue
        try:
            entries = convert_session(session)
        except Exception as exc:  # defensive: keep the loop alive on bad rows
            print(f"[warn] {path.name}: conversion failed: {exc}", file=sys.stderr)
            skipped += 1
            continue
        if not entries:
            skipped += 1
            continue
        target, encoded = output_path_for(session, claude_dir=claude_dir, overwrite=True)
        cwd = session.get("cwd", "")
        sid = session.get("id") or session.get("session_id")
        print(
            f"  {path.name}  ({len(entries)} entries) -> "
            f"projects/{encoded}/<uuid>.jsonl  [cwd={cwd!r} sid={sid}]"
        )
        if args.dry_run:
            converted += 1
            continue
        write_session(entries, target)
        converted += 1

    print(f"\nDone: {converted} converted, {skipped} skipped -> {claude_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
