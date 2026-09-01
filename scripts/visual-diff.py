#!/usr/bin/env python3
"""Compare two PNGs with Pixelmatch and create the visual QA evidence."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2) + "\n"
    path.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)


def main() -> int:
    args = options(sys.argv[1:])
    if not args.get("reference") or not args.get("candidate") or not args.get("output"):
        raise ValueError("Usage: visual-diff.py --reference ref.png --candidate candidate.png --output visual-review.json [--threshold 5] [--peak-threshold 12]")
    reference_path, candidate_path, output = Path(args["reference"]).resolve(), Path(args["candidate"]).resolve(), Path(args["output"]).resolve()
    reference = Image.open(reference_path).convert("RGBA")
    candidate = Image.open(candidate_path).convert("RGBA")
    difference_threshold = float(args.get("threshold", "5"))
    peak_threshold = float(args.get("peak-threshold", "12"))
    if reference.size != candidate.size:
        # A size mismatch is a harness problem, not a visual regression. Reporting it
        # as a 100% difference would record a catastrophic QA failure for what is
        # really missing evidence: re-export the reference at 1x, or re-render the
        # candidate at the reference's width, height, and scale.
        report = {
            "status": "ERROR", "createdAt": now(), "reason": "dimension-mismatch",
            "detail": "Reference and candidate dimensions differ, so no comparison was performed.",
            "reference": {"width": reference.width, "height": reference.height},
            "candidate": {"width": candidate.width, "height": candidate.height},
            "thresholds": {"differenceThreshold": difference_threshold, "peakThreshold": peak_threshold},
        }
        write_report(output, report)
        return 3

    diff = Image.new("RGBA", reference.size)
    mismatched = pixelmatch(reference, candidate, diff, threshold=0.1, includeAA=False, diff_mask=True)
    width, height = reference.size
    total = width * height
    pixel_difference_percent = mismatched / total * 100
    band_height = max(40, min(100, round(height / 40)))
    raw_diff = diff.load()
    bands = []
    for start in range(0, height, band_height):
        end = min(height, start + band_height)
        changed = sum(1 for y in range(start, end) for x in range(width) if any(raw_diff[x, y][:3]))
        bands.append({"start": start, "end": end, "differencePercent": changed / ((end - start) * width) * 100})
    peak = max([0, *(band["differencePercent"] for band in bands)])
    diff_path = output.with_suffix(".png")
    report = {
        "status": "PASS" if pixel_difference_percent <= difference_threshold and peak <= peak_threshold else "FAIL",
        "createdAt": now(), "viewport": {"width": width, "height": height},
        "pixelDifferencePercent": pixel_difference_percent, "visualSimilarityPercent": 100 - pixel_difference_percent,
        "peakBandDifferencePercent": peak, "thresholds": {"differenceThreshold": difference_threshold, "peakThreshold": peak_threshold},
        "worstBands": sorted(bands, key=lambda band: band["differencePercent"], reverse=True)[:10],
        "files": {"reference": str(reference_path), "candidate": str(candidate_path), "diff": str(diff_path)},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    diff.save(diff_path)
    write_report(output, report)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
