#!/usr/bin/env python3
"""Combine per-viewport visual comparison reports."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for index in range(0, len(values), 2):
        name = values[index].removeprefix("--") if index < len(values) else ""
        value = values[index + 1] if index + 1 < len(values) else None
        if not name or not value:
            raise ValueError("Options must be provided as --name value pairs.")
        if name == "report":
            result.setdefault("report", []).append(value)  # type: ignore[union-attr]
        else:
            result[name] = value
    return result


def main() -> int:
    args = options(sys.argv[1:])
    report_paths = args.get("report")
    if not report_paths or not args.get("output"):
        raise ValueError("Usage: visual-summary.py --report <viewport.json> [--report <viewport.json> ...] --output <summary.json>")
    reports = []
    for name in report_paths:  # type: ignore[union-attr]
        file = Path(str(name)).resolve()
        reports.append({"file": str(file), **json.loads(file.read_text(encoding="utf-8"))})
    # An ERROR report means no comparison happened (e.g. reference and candidate
    # dimensions differ). That is missing evidence, not a visual regression, and it
    # must not be averaged into the metrics as a 100% difference.
    errored = [report for report in reports if report.get("status") == "ERROR"]
    failed = [report for report in reports if report.get("status") not in {"PASS", "ERROR"}]
    measured = [report for report in reports if report.get("status") in {"PASS", "FAIL"}]
    summary = {
        "status": "ERROR" if errored else ("PASS" if not failed else "FAIL"),
        "checkedAt": now(),
        "viewportCount": len(reports),
        "failed": [report["file"] for report in failed],
        "errored": [report["file"] for report in errored],
        "pixelDifferencePercent": max((float(report.get("pixelDifferencePercent", 100)) for report in measured), default=None),
        "peakBandDifferencePercent": max((float(report.get("peakBandDifferencePercent", 100)) for report in measured), default=None),
        "reports": reports,
    }
    if errored:
        summary["reason"] = "Visual evidence is unavailable: " + "; ".join(
            sorted({str(report.get("reason") or "comparison error") for report in errored})
        )
    output = Path(str(args["output"])).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(summary, indent=2) + "\n"
    output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if summary["status"] == "PASS" else (3 if summary["status"] == "ERROR" else 2)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
