#!/usr/bin/env python3
"""Combine one or more render diagnostics into the browser QA report."""

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
        raise ValueError("Usage: browser-summary.py --report <render.png.json> [--report <render.png.json> ...] --output <summary.json>")
    reports = []
    for name in report_paths:  # type: ignore[union-attr]
        file = Path(str(name)).resolve()
        report = json.loads(file.read_text(encoding="utf-8"))
        reports.append({"file": str(file), **report})
    failed = [report for report in reports if report.get("status") != "PASS"]
    summary = {
        "status": "PASS" if not failed else "FAIL",
        "checkedAt": now(),
        "viewportCount": len(reports),
        "failed": [report["file"] for report in failed],
        "reports": reports,
    }
    output = Path(str(args["output"])).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    pretty = json.dumps(summary, indent=2) + "\n"
    compact = json.dumps(summary, separators=(",", ":")) + "\n"
    output.write_text(pretty, encoding="utf-8")
    sys.stdout.write(compact)
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
