"""
annotated_to_agentdebug.py — 把 annotate_skill_sections.py 的产物转成 AgentDebugX 的 AgentTrajectory

关键点:
- event.module = attributionSkill:attributionSkillSection (细粒度)
- 父→子 skill 链通过 module 字符串表达
- metadata 字段塞 attribution* 全字段供 AgentDebugX 消费
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 把 AgentDebugX src 加进 path
AGENTDEBUGX_SRC = Path(r"D:\tmp_agentdebugx\AgentDebugX\src")
sys.path.insert(0, str(AGENTDEBUGX_SRC))

from agentdebug.schema.models import (  # noqa: E402
    AgentEvent,
    AgentTrajectory,
    EventType,
    new_id,
)
from agentdebug.ingest.adapters.importers import _module_for_event_type  # noqa: E402


def iso_to_datetime(ts: str) -> datetime:
    """ISO 8601 → datetime"""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def event_type_from_record(record: dict) -> tuple[EventType, str]:
    """从 annotated JSONL 行推断 AgentDebugX EventType 和 agent_name"""
    rec_type = record.get("type")
    msg = record.get("message", {})

    # 工具调用:从 tool_use 块的 name 字段
    content = msg.get("content", [])
    if isinstance(content, list):
        for blk in content:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                tool_name = blk.get("name", "agent")
                if tool_name == "Bash":
                    return EventType.TOOL_CALL, "Bash"
                if tool_name == "Skill":
                    return EventType.HANDOFF, "Skill"  # Skill 调用算 handoff
                if tool_name in ("Read", "Write", "Edit", "Glob", "Grep"):
                    return EventType.TOOL_CALL, tool_name
                if tool_name in ("TaskCreate", "TaskUpdate"):
                    return EventType.PLAN, tool_name
                return EventType.TOOL_CALL, tool_name
            if isinstance(blk, dict) and blk.get("type") == "thinking":
                return EventType.REFLECTION, "claude-code"
            if isinstance(blk, dict) and blk.get("type") == "text":
                return EventType.AGENT_STEP, "claude-code"

    # tool_result user 行
    if rec_type == "user":
        if isinstance(content, list):
            for blk in content:
                if isinstance(blk, dict) and blk.get("type") == "tool_result":
                    return EventType.TOOL_RESULT, "tool-result"
        return EventType.OBSERVATION, "user"

    # attachment 行
    if rec_type == "attachment":
        att_type = record.get("attachment", {}).get("type", "")
        if att_type == "skill_listing":
            return EventType.PLAN, "skill-listing"
        if att_type == "task_reminder":
            return EventType.REFLECTION, "task-reminder"
        return EventType.OBSERVATION, "attachment"

    # queue-operation
    if rec_type == "queue-operation":
        return EventType.RUN_START, "queue"

    # last-prompt
    if rec_type == "last-prompt":
        return EventType.REFLECTION, "last-prompt"

    return EventType.AGENT_STEP, "claude-code"


def convert(jsonl_path: Path, output_path: Path) -> AgentTrajectory:
    """annotated jsonl → AgentTrajectory"""
    session_id = jsonl_path.stem.replace(".annotated", "")
    events: list[AgentEvent] = []
    parent_map: dict[str, str] = {}
    step_counter = 0
    skill_counter = 0

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            rec_uuid = rec.get("uuid") or f"line-{line_no}"
            parent_uuid = rec.get("parentUuid")
            event_type, agent_name = event_type_from_record(rec)

            # ── 核心:从 annotated 字段构建 module 字符串 ──
            skill = rec.get("attributionSkill")
            section = rec.get("attributionSkillSection")
            section_title = rec.get("attributionSkillSectionTitle")
            sub_skill = rec.get("attributionSubSkill")
            method = rec.get("attributionInferenceMethod", "fallback")
            conf = rec.get("attributionInferenceConfidence", 0.0)

            # module 字符串(skill:section),无 section 时只填 skill
            if skill and section:
                module = f"{skill}:{section}"
            elif skill:
                module = f"{skill}"
            else:
                module = _module_for_event_type(event_type)

            metadata: dict[str, Any] = {
                "attributionSkill": skill,
                "attributionSkillSection": section,
                "attributionSkillSectionTitle": section_title,
                "attributionSubSkill": sub_skill,
                "attributionInferenceMethod": method,
                "attributionInferenceConfidence": conf,
                "source_format": "claude_code",
                "claude_code_version": rec.get("version"),
                "cwd": rec.get("cwd"),
                "gitBranch": rec.get("gitBranch"),
                "isSidechain": rec.get("isSidechain"),
                "isMeta": rec.get("isMeta"),
                "attributionSkillSectionTitle": section_title,
                "userType": rec.get("userType"),
                "entrypoint": rec.get("entrypoint"),
                "source_line": line_no,
            }
            # 去掉 None 值
            metadata = {k: v for k, v in metadata.items() if v is not None}

            # input/output
            inp = None
            out = None
            error = None
            content = rec.get("message", {}).get("content", [])
            if isinstance(content, list):
                tool_inputs = []
                tool_outputs = []
                thinking_text = ""
                text_blocks = []
                for blk in content:
                    if not isinstance(blk, dict):
                        continue
                    if blk.get("type") == "tool_use":
                        tool_inputs.append({"name": blk.get("name"), "input": blk.get("input")})
                    elif blk.get("type") == "tool_result":
                        tool_outputs.append({"tool_use_id": blk.get("tool_use_id"), "content": blk.get("content"), "is_error": blk.get("is_error")})
                    elif blk.get("type") == "thinking":
                        thinking_text += blk.get("thinking", "")
                    elif blk.get("type") == "text":
                        text_blocks.append(blk.get("text", ""))
                if tool_inputs:
                    inp = tool_inputs
                elif thinking_text:
                    inp = thinking_text[:8000]
                elif text_blocks:
                    inp = "\n".join(text_blocks)[:8000]
                if tool_outputs:
                    out = tool_outputs
            elif isinstance(content, str):
                inp = content[:8000]

            # error 字段
            tool_use_result = rec.get("toolUseResult")
            if isinstance(tool_use_result, dict) and tool_use_result.get("interrupted"):
                error = "interrupted"
            if isinstance(tool_use_result, dict) and tool_use_result.get("is_error"):
                error = tool_use_result.get("stderr") or "tool_error"

            # timestamp
            ts_str = rec.get("timestamp")
            if ts_str:
                try:
                    ts_dt = iso_to_datetime(ts_str)
                except Exception:
                    ts_dt = datetime.now(timezone.utc)
            else:
                ts_dt = datetime.now(timezone.utc)

            evt = AgentEvent(
                event_id=rec_uuid,
                trace_id=session_id,
                parent_event_id=parent_uuid,
                agent_name=agent_name,
                event_type=event_type,
                module=module,
                step_index=step_counter,
                timestamp=ts_dt,
                input=inp,
                output=out,
                error=error,
                metadata=metadata,
            )
            events.append(evt)
            parent_map[rec_uuid] = parent_uuid or ""
            step_counter += 1

    trajectory = AgentTrajectory(
        trace_id=session_id,
        task_id=session_id,
        framework="claude_code",
        started_at=events[0].timestamp if events else datetime.now(timezone.utc),
        ended_at=events[-1].timestamp if events else None,
        events=events,
        metadata={
            "source_format": "claude_code",
            "claude_code_version": "2.1.165",
            "annotated_by": "annotate_skill_sections.py",
            "module_source": "attributionSkill:attributionSkillSection",
            "cwd": events[0].metadata.get("cwd") if events else None,
        },
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(trajectory.model_dump_json(indent=2), encoding="utf-8")
    return trajectory


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="annotated jsonl path")
    p.add_argument("output", type=Path, help="output trajectory json")
    args = p.parse_args()

    traj = convert(args.input, args.output)
    print(f"OK: {len(traj.events)} events written to {args.output}")
    # 统计 module 分布
    from collections import Counter
    mod_counter = Counter(ev.module for ev in traj.events)
    print(f"Distinct modules: {len(mod_counter)}")
    for m, c in mod_counter.most_common(15):
        print(f"  {m!r}: {c}")
