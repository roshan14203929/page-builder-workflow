#!/usr/bin/env python3
"""Crop the worst-differing bands from a visual diff for native-resolution review."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


LAYERS = ("reference", "candidate", "diff")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pretty = json.dumps(report, indent=2) + "\n"
    compact = json.dumps(report, separators=(",", ":")) + "\n"
    path.write_text(pretty, encoding="utf-8")
    sys.stdout.write(compact)


def merge(bands: list[dict[str, float]], pad: int, height: int) -> list[dict[str, float]]:
    """Pad each band, then fuse overlapping or abutting ones into single regions.

    `visual-diff.py` reports fixed-height bands, so a tall failure arrives as
    several adjacent slivers. Reviewing them separately wastes reads and hides
    the shape of the failure, so fuse them back into one region.
    """
    regions: list[dict[str, float]] = []
    for band in sorted(bands, key=lambda item: item["start"]):
        start = max(0, int(band["start"]) - pad)
        end = min(height, int(band["end"]) + pad)
        worst = float(band["differencePercent"])
        if regions and start <= regions[-1]["end"]:
            regions[-1]["end"] = max(regions[-1]["end"], end)
            regions[-1]["differencePercent"] = max(regions[-1]["differencePercent"], worst)
            regions[-1]["bands"] += 1
        else:
            regions.append({"start": start, "end": end, "differencePercent": worst, "bands": 1})
    return regions


def main() -> int:
    args = options(sys.argv[1:])
    if not args.get("report") or not args.get("output"):
        raise ValueError(
            "Usage: crop-bands.py --report <diff.json> --output <crops.json> "
            "[--regions 3] [--pad 40] [--min-difference 5]"
        )
    report_path, output = Path(args["report"]).resolve(), Path(args["output"]).resolve()
    limit = int(args.get("regions", "3"))
    pad = int(args.get("pad", "40"))
    minimum = float(args.get("min-difference", "5"))

    source = json.loads(report_path.read_text(encoding="utf-8"))
    files = source.get("files") or {}
    bands = [band for band in source.get("worstBands") or [] if band["differencePercent"] >= minimum]
    if not bands:
        write_report(output, {
            "status": "PASS", "createdAt": now(), "report": str(report_path),
            "reason": f"No band differs by at least {minimum}%.", "regions": [],
        })
        return 0

    images = {}
    for layer in LAYERS:
        path = files.get(layer)
        if path and Path(path).exists():
            images[layer] = Image.open(Path(path))
    if "reference" not in images:
        raise ValueError(f"Reference image is unavailable: {files.get('reference')}")

    height = min(image.height for image in images.values())
    regions = sorted(
        merge(bands, pad, height), key=lambda region: region["differencePercent"], reverse=True
    )[:limit]

    written = []
    for region in sorted(regions, key=lambda item: item["start"]):
        start, end = int(region["start"]), int(region["end"])
        crops = {}
        for layer, image in images.items():
            crop = image.crop((0, start, image.width, min(end, image.height)))
            destination = output.parent / f"{output.stem}-{start}-{end}-{layer}.png"
            crop.save(destination)
            crops[layer] = str(destination)
        written.append({
            "start": start, "end": end, "height": end - start,
            "mergedBands": region["bands"],
            "differencePercent": region["differencePercent"],
            "files": crops,
        })

    write_report(output, {
        "status": "FAIL", "createdAt": now(), "report": str(report_path),
        "viewport": source.get("viewport"),
        "peakBandDifferencePercent": source.get("peakBandDifferencePercent"),
        "note": "Crops are native resolution. Review these for pixel judgements; "
                "use the full-page render only for layout, ordering, and rhythm.",
        "regions": written,
    })
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
