from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ROOT


HOOK = ROOT / "scripts" / "log-agent-event.py"
STATE = ROOT / ".claude" / "state"
ARTIFACTS = ("active-run.json", "usage-cursors.json", "agent-events.jsonl", "hook-diagnostics.jsonl")


@pytest.fixture(autouse=True)
def clean_state():
    """The hook writes into the real .claude/state directory; keep it pristine."""
    saved = {name: (STATE / name).read_bytes() for name in ARTIFACTS if (STATE / name).exists()}
    for name in ARTIFACTS:
        (STATE / name).unlink(missing_ok=True)
    yield
    for name in ARTIFACTS:
        (STATE / name).unlink(missing_ok=True)
    for name, blob in saved.items():
        (STATE / name).write_bytes(blob)


def fire(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload),
        cwd=ROOT, capture_output=True, text=True,
    )


def transcript(tmp_path: Path, messages: list[tuple[str, dict]]) -> Path:
    path = tmp_path / "transcript.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for uuid, usage in messages:
            handle.write(json.dumps({"type": "assistant", "uuid": uuid, "message": {"usage": usage}}) + "\n")
        handle.write(json.dumps({"type": "user", "uuid": "u1"}) + "\n")  # ignored
    return path


def usage(inp: int = 0, out: int = 0, create: int = 0, read: int = 0) -> dict:
    return {"input_tokens": inp, "output_tokens": out,
            "cache_creation_input_tokens": create, "cache_read_input_tokens": read}


def events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_event_is_recorded_without_an_active_run(tmp_path: Path) -> None:
    # The previous implementation dropped the event entirely in this case.
    result = fire({"hook_event_name": "SubagentStop", "agent_id": "a1", "agent_type": "page-builder"})

    assert result.returncode == 0
    recorded = events(STATE / "agent-events.jsonl")
    assert len(recorded) == 1
    assert recorded[0]["agentType"] == "page-builder"
    assert recorded[0]["project"] is None


def test_event_is_routed_to_the_active_project(tmp_path: Path) -> None:
    (STATE / "active-run.json").write_text(json.dumps({
        "project": "medichannel", "page": "az-04-html-v1-0", "run": "run-002", "round": 1, "task": "footer",
    }), encoding="utf-8")

    result = fire({"hook_event_name": "SubagentStop", "agent_id": "a1", "agent_type": "repair-builder"})

    assert result.returncode == 0
    destination = ROOT / "projects" / "medichannel" / "events" / "agent-events.jsonl"
    try:
        recorded = events(destination)[-1]
        assert (recorded["project"], recorded["run"], recorded["round"]) == ("medichannel", "run-002", 1)
        assert recorded["task"] == "footer"
    finally:
        destination.unlink(missing_ok=True)


def test_usage_is_summed_from_the_transcript(tmp_path: Path) -> None:
    path = transcript(tmp_path, [
        ("m1", usage(inp=10, out=100, create=50, read=1000)),
        ("m2", usage(inp=5, out=200, create=0, read=2000)),
    ])

    fire({"hook_event_name": "SubagentStop", "agent_type": "page-builder", "transcript_path": str(path)})

    recorded = events(STATE / "agent-events.jsonl")[0]["usage"]
    assert recorded["input_tokens"] == 15
    assert recorded["output_tokens"] == 300
    assert recorded["cache_creation_input_tokens"] == 50
    assert recorded["cache_read_input_tokens"] == 3000
    assert recorded["cumulative_tokens"] == 3365
    # Peak context is the per-turn footprint, not the sum across turns.
    assert recorded["peak_context_tokens"] == 2005  # turn 2: 5 + 0 + 2000
    assert recorded["messages"] == 2


def session_with_subagent(tmp_path: Path, agent_id: str, session_msgs, agent_msgs):
    """Lay out a session transcript with a subagent transcript beside it."""
    session = transcript(tmp_path, session_msgs)
    nested = tmp_path / session.stem / "subagents"
    nested.mkdir(parents=True)
    path = nested / f"agent-{agent_id}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for uuid, block in agent_msgs:
            handle.write(json.dumps({"type": "assistant", "uuid": uuid, "message": {"usage": block}}) + "\n")
    return session, path


def test_the_subagents_own_transcript_is_preferred(tmp_path: Path) -> None:
    # transcript_path points at the SESSION transcript. Reading it attributes the
    # whole session to one subagent -- observed live as a ~2000x overstatement.
    session, _ = session_with_subagent(
        tmp_path, "abc123",
        session_msgs=[("s1", usage(out=500_000)), ("s2", usage(read=9_000_000))],
        agent_msgs=[("a1", usage(inp=4, out=110, create=12_982, read=11_770))],
    )

    fire({"hook_event_name": "SubagentStop", "agent_id": "abc123",
          "agent_type": "page-builder", "transcript_path": str(session)})

    recorded = events(STATE / "agent-events.jsonl")[0]
    assert recorded["usageScope"] == "subagent"
    assert recorded["usage"]["cumulative_tokens"] == 24_866  # the subagent, not the session
    assert recorded["usage"]["messages"] == 1
    assert recorded["transcriptPath"].endswith("subagents/agent-abc123.jsonl")


def test_a_subagent_transcript_is_counted_whole_not_as_a_delta(tmp_path: Path) -> None:
    session, _ = session_with_subagent(
        tmp_path, "aaa", session_msgs=[("s1", usage(out=10))], agent_msgs=[("a1", usage(out=70))])
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    session2, _ = session_with_subagent(
        second_dir, "bbb", session_msgs=[("s1", usage(out=10))], agent_msgs=[("b1", usage(out=90))])

    fire({"hook_event_name": "SubagentStop", "agent_id": "aaa", "transcript_path": str(session)})
    fire({"hook_event_name": "SubagentStop", "agent_id": "bbb", "transcript_path": str(session2)})

    first, second = events(STATE / "agent-events.jsonl")
    # Each agent's own file is complete; no cursor should suppress the second.
    assert first["usage"]["output_tokens"] == 70
    assert second["usage"]["output_tokens"] == 90


def test_missing_subagent_transcript_falls_back_and_says_so(tmp_path: Path) -> None:
    session = transcript(tmp_path, [("s1", usage(out=42))])

    fire({"hook_event_name": "SubagentStop", "agent_id": "nope",
          "agent_type": "page-builder", "transcript_path": str(session)})

    recorded = events(STATE / "agent-events.jsonl")[0]
    assert recorded["usageScope"] == "session-delta"  # labelled, never conflated
    assert recorded["usage"]["output_tokens"] == 42
    notes = [json.loads(line) for line in (STATE / "hook-diagnostics.jsonl").read_text().splitlines() if line]
    assert any("No subagent transcript" in n["message"] for n in notes)


def test_agent_id_cannot_escape_the_subagents_directory(tmp_path: Path) -> None:
    session = transcript(tmp_path, [("s1", usage(out=5))])

    fire({"hook_event_name": "SubagentStop", "agent_id": "../../../etc/passwd",
          "transcript_path": str(session)})

    recorded = events(STATE / "agent-events.jsonl")[0]
    assert recorded["usageScope"] == "session-delta"
    assert recorded["transcriptPath"] == str(session)


def test_repeat_events_report_only_the_delta(tmp_path: Path) -> None:
    path = transcript(tmp_path, [("m1", usage(out=100))])
    payload = {"hook_event_name": "SubagentStop", "agent_type": "page-builder", "transcript_path": str(path)}
    fire(payload)

    # A second subagent finishes after two more messages land.
    with path.open("a", encoding="utf-8") as handle:
        for uuid, block in (("m2", usage(out=40)), ("m3", usage(out=60))):
            handle.write(json.dumps({"type": "assistant", "uuid": uuid, "message": {"usage": block}}) + "\n")
    fire(payload)

    first, second = events(STATE / "agent-events.jsonl")
    assert first["usage"]["output_tokens"] == 100
    assert second["usage"]["output_tokens"] == 100  # 40 + 60, not 200
    assert second["usage"]["messages"] == 2


def test_a_rotated_transcript_is_flagged_rather_than_misreported(tmp_path: Path) -> None:
    path = transcript(tmp_path, [("m1", usage(out=100))])
    payload = {"hook_event_name": "SubagentStop", "agent_type": "page-builder", "transcript_path": str(path)}
    fire(payload)
    # Simulate compaction: the cursor message no longer exists in the file.
    transcript(tmp_path, [("z9", usage(out=7))])
    fire(payload)

    second = events(STATE / "agent-events.jsonl")[1]
    assert second["usageCursorReset"] is True
    assert second["usage"]["output_tokens"] == 7


def test_failures_are_diagnosed_but_never_break_the_workflow(tmp_path: Path) -> None:
    missing = fire({"hook_event_name": "SubagentStop", "transcript_path": str(tmp_path / "absent.jsonl")})
    garbage = subprocess.run(
        [sys.executable, str(HOOK)], input="not json at all",
        cwd=ROOT, capture_output=True, text=True,
    )

    # Non-blocking: a hook must not fail the run.
    assert missing.returncode == 0 and garbage.returncode == 0
    # But the failure leaves a trace instead of vanishing silently.
    notes = [json.loads(line) for line in (STATE / "hook-diagnostics.jsonl").read_text().splitlines() if line]
    assert any("Transcript path" in n["message"] for n in notes)
    assert any("Unparsable" in n["message"] for n in notes)
    # The readable-payload case still produced an event despite the bad transcript.
    assert len(events(STATE / "agent-events.jsonl")) == 1


def test_malformed_project_id_falls_back_instead_of_writing_outside_projects() -> None:
    (STATE / "active-run.json").write_text(json.dumps({"project": "../../etc"}), encoding="utf-8")

    result = fire({"hook_event_name": "SubagentStop", "agent_type": "page-builder"})

    assert result.returncode == 0
    recorded = events(STATE / "agent-events.jsonl")
    assert len(recorded) == 1 and recorded[0]["project"] is None
