#!/usr/bin/env python3
"""Claude SubagentStop hook: append the active run's audit event with token usage.

The hook payload carries no usage statistics, but transcripts record a per-message
`usage` block. Crucially, `transcript_path` points at the *parent session*
transcript, not the subagent's -- reading it attributes the whole session's spend
to one subagent, overstating it by orders of magnitude. A subagent writes its own
transcript alongside the session's, at:

    <dir>/<session-id>/subagents/agent-<agent-id>.jsonl

Prefer that file and count it whole: it is exactly one subagent's usage. Fall back
to a cursor-tracked delta on the session transcript only when it is missing, and
label the result so the two are never confused.

Never fails the workflow: every error is recorded to the diagnostics log and the
hook still exits 0. Silence is not the same as success, so a dropped event leaves
a trace instead of vanishing.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".claude" / "state"
ACTIVE = STATE / "active-run.json"
CURSORS = STATE / "usage-cursors.json"
FALLBACK = STATE / "agent-events.jsonl"
DIAGNOSTICS = STATE / "hook-diagnostics.jsonl"
PROJECT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COUNTED = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
# What the model had to read on a single turn. Cache reads recur every turn, so
# summing them across a long agent inflates the total by orders of magnitude and
# makes turn count -- not context size -- look like the thing to optimize. Peak
# context is the figure that tracks context-reduction work, and it is what the
# host reports as a subagent's token count.
CONTEXT = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def note(message: str, **detail: object) -> None:
    """Record a diagnostic. A hook that fails quietly is worse than one that fails."""
    try:
        DIAGNOSTICS.parent.mkdir(parents=True, exist_ok=True)
        with DIAGNOSTICS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": now(), "message": message, **detail}, separators=(",", ":")) + "\n")
    except Exception:
        pass
    print(f"[layerlift-hook] {message}", file=sys.stderr)


def read_json(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except Exception as error:
        note("Unreadable JSON; using default.", path=str(path), error=str(error))
        return default


def subagent_transcript(session: Path, agent_id: object) -> Path | None:
    """Locate this subagent's own transcript beside the session's, if it exists."""
    if not isinstance(agent_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", agent_id):
        return None
    candidate = session.parent / session.stem / "subagents" / f"agent-{agent_id}.jsonl"
    return candidate if candidate.is_file() else None


def usage_since(transcript: Path, cursor: str | None) -> tuple[dict[str, int], str | None, bool]:
    """Sum assistant-message usage recorded after `cursor`.

    Returns (totals, new cursor, whether the cursor was missing from the file).
    A missing cursor means the transcript was compacted or rotated, so the whole
    file is counted and the caller is told the figure is not a clean delta.
    """
    records: list[tuple[str | None, dict]] = []
    with transcript.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if entry.get("type") != "assistant":
                continue
            usage = (entry.get("message") or {}).get("usage")
            if isinstance(usage, dict):
                records.append((entry.get("uuid"), usage))

    start, reset = 0, False
    if cursor is not None:
        matches = [index for index, (uuid, _) in enumerate(records) if uuid == cursor]
        if matches:
            start = matches[-1] + 1
        else:
            reset = True

    totals = {key: 0 for key in COUNTED}
    window = 0
    for _, usage in records[start:]:
        for key in COUNTED:
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] += value
        # Context footprint for this turn: everything the model read to produce it.
        window = max(window, sum(usage.get(key) or 0 for key in CONTEXT))
    totals["cumulative_tokens"] = sum(totals[key] for key in COUNTED)
    totals["peak_context_tokens"] = window
    totals["messages"] = len(records) - start
    return totals, (records[-1][0] if records else cursor), reset


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception as error:
        note("Unparsable hook payload.", error=str(error))
        return

    event = {
        "at": now(),
        "event": payload.get("hook_event_name", "unknown"),
        "sessionId": payload.get("session_id"),
        "agentId": payload.get("agent_id"),
        "agentType": payload.get("agent_type"),
    }

    # Run context is best-effort: an event without it is still worth recording.
    state = read_json(ACTIVE, {})
    project = str(state.get("project", "")) if isinstance(state, dict) else ""
    if isinstance(state, dict):
        event.update({key: state.get(key) for key in ("page", "run", "round", "task")})
    if not PROJECT_ID.fullmatch(project):
        if project:
            note("Ignoring malformed project id in active-run state.", project=project)
        project = ""
    event["project"] = project or None

    transcript_path = payload.get("transcript_path")
    if transcript_path:
        session = Path(transcript_path)
        agent = subagent_transcript(session, payload.get("agent_id"))
        transcript = agent or session
        event["transcriptPath"] = str(transcript)
        event["usageScope"] = "subagent" if agent else "session-delta"
        if agent is None:
            note("No subagent transcript; falling back to a session delta.",
                 session=str(session), agentId=payload.get("agent_id"))
        if transcript.is_file():
            try:
                if agent is not None:
                    # A subagent transcript is single-use: count it whole.
                    event["usage"] = usage_since(transcript, None)[0]
                else:
                    cursors = read_json(CURSORS, {})
                    cursors = cursors if isinstance(cursors, dict) else {}
                    key = str(transcript.resolve())
                    totals, cursor, reset = usage_since(transcript, cursors.get(key))
                    event["usage"] = totals
                    if reset:
                        event["usageCursorReset"] = True
                    cursors[key] = cursor
                    CURSORS.parent.mkdir(parents=True, exist_ok=True)
                    temporary = CURSORS.with_suffix(".json.tmp")
                    temporary.write_text(json.dumps(cursors, separators=(",", ":")), encoding="utf-8")
                    temporary.replace(CURSORS)
            except Exception as error:
                note("Could not derive usage from transcript.", path=str(transcript), error=str(error))
        else:
            note("Transcript path is not a readable file.", path=str(transcript))
    else:
        note("Hook payload carried no transcript_path; usage unavailable.")

    destination = (ROOT / "projects" / project / "events" / "agent-events.jsonl") if project else FALLBACK
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    except Exception as error:
        note("Could not append the audit event.", path=str(destination), error=str(error))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # a hook must never break the workflow
        note("Unhandled hook failure.", error=str(error))
    sys.exit(0)
