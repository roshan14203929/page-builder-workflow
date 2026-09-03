#!/usr/bin/env python3
"""Token usage report by agent and run.

Reads projects/<project>/events/agent-events.jsonl written by the
SubagentStop hook (scripts/log-agent-event.py) and prints a per-run,
per-agent summary with cache efficiency stats.

Usage:
  python scripts/report-usage.py <project>
  python scripts/report-usage.py <project> --run run-001
  python scripts/report-usage.py <project> --page fsn-hes-article03
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COLS = {
    "agent":   28,
    "in":       7,
    "out":      7,
    "create":  12,
    "hit":      9,
    "total":    8,
    "scope":   12,
}
HEADER = (
    f"{'Agent':<{COLS['agent']}} "
    f"{'In':>{COLS['in']}} "
    f"{'Out':>{COLS['out']}} "
    f"{'CacheCreate':>{COLS['create']}} "
    f"{'CacheHit':>{COLS['hit']}} "
    f"{'Total':>{COLS['total']}} "
    f"Scope"
)
SEP = (
    f"{'-'*COLS['agent']} "
    f"{'-'*COLS['in']} "
    f"{'-'*COLS['out']} "
    f"{'-'*COLS['create']} "
    f"{'-'*COLS['hit']} "
    f"{'-'*COLS['total']}"
)
WIDTH = 70


def fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def load_events(project: str, run: str | None, page: str | None) -> list[dict]:
    path = ROOT / "projects" / project / "events" / "agent-events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if not e.get("usage"):
            continue
        if run and e.get("run") != run:
            continue
        if page and e.get("page") != page:
            continue
        events.append(e)
    return events


def report(events: list[dict]) -> None:
    by_run: dict[tuple, list] = defaultdict(list)
    for e in events:
        key = (e.get("at", ""), e.get("page", "?"), e.get("run", "?"))
        by_run[key].append(e)

    has_delta = False

    for (at, page, run), run_events in sorted(by_run.items()):
        print(f"\n{'=' * WIDTH}")
        print(f"Page: {page}   Run: {run}")
        print(f"{'=' * WIDTH}")
        print(HEADER)
        print(SEP)

        totals: dict[str, int] = defaultdict(int)
        for e in run_events:
            u = e.get("usage", {})
            agent = (e.get("agentType") or e.get("agentId") or "?")[:COLS["agent"]]
            scope = e.get("usageScope", "?")
            if scope == "session-delta":
                has_delta = True

            inp    = u.get("input_tokens", 0)
            out    = u.get("output_tokens", 0)
            create = u.get("cache_creation_input_tokens", 0)
            hit    = u.get("cache_read_input_tokens", 0)
            total  = u.get("cumulative_tokens", 0)

            for key, val in (("input", inp), ("output", out),
                             ("create", create), ("hit", hit), ("total", total)):
                totals[key] += val

            print(
                f"{agent:<{COLS['agent']}} "
                f"{fmt(inp):>{COLS['in']}} "
                f"{fmt(out):>{COLS['out']}} "
                f"{fmt(create):>{COLS['create']}} "
                f"{fmt(hit):>{COLS['hit']}} "
                f"{fmt(total):>{COLS['total']}} "
                f"{scope}"
            )

        print(SEP)
        print(
            f"{'TOTAL':<{COLS['agent']}} "
            f"{fmt(totals['input']):>{COLS['in']}} "
            f"{fmt(totals['output']):>{COLS['out']}} "
            f"{fmt(totals['create']):>{COLS['create']}} "
            f"{fmt(totals['hit']):>{COLS['hit']}} "
            f"{fmt(totals['total']):>{COLS['total']}}"
        )

        cache_pool = totals["hit"] + totals["create"]
        if cache_pool > 0:
            hit_rate = totals["hit"] / cache_pool * 100
            print(
                f"\nCache hit rate: {hit_rate:.1f}%"
                f"  (reads={fmt(totals['hit'])}, creates={fmt(totals['create'])})"
            )

    if has_delta:
        print(
            "\n* One or more rows are labelled 'session-delta': the subagent "
            "transcript was not found, so the figure is a delta from the parent "
            "session transcript and includes orchestrator work. It overstates the "
            "individual subagent's spend."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Token usage report by agent and run."
    )
    parser.add_argument("project", help="Project ID (e.g. medichannel)")
    parser.add_argument("--run",  help="Filter to a specific run (e.g. run-001)")
    parser.add_argument("--page", help="Filter to a specific page slug")
    args = parser.parse_args()

    events = load_events(args.project, run=args.run, page=args.page)
    if not events:
        print("No usage events found.")
        return
    report(events)


if __name__ == "__main__":
    main()
