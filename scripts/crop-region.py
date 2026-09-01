#!/usr/bin/env python3
"""Crop a fixed region from a PNG at native resolution for the structural check."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


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
    if not args.get("image") or not args.get("output"):
        raise ValueError(
            "Usage: crop-region.py --image <source.png> --output <crop.png> [--top 900] [--start 0]"
        )
    image_path, output = Path(args["image"]).resolve(), Path(args["output"]).resolve()
    start = int(args.get("start", "0"))
    requested = int(args.get("top", "900"))
    if start < 0 or requested <= 0:
        raise ValueError("--start must be >= 0 and --top must be > 0.")

    image = Image.open(image_path)
    if start >= image.height:
        raise ValueError(f"--start {start} is past the end of a {image.height}px-tall image.")

    # Crop only what exists. Padding a short image would put a synthetic fill
    # against the candidate's real page background, and that band alone can
    # register as a ~100% difference — a false structural failure. The caller
    # renders the candidate to `height` instead.
    end = min(image.height, start + requested)
    height = end - start
    output.parent.mkdir(parents=True, exist_ok=True)
    image.crop((0, start, image.width, end)).save(output)

    write_report(output.with_suffix(".json"), {
        "status": "OK",
        "createdAt": now(),
        "source": str(image_path),
        "sourceSize": {"width": image.width, "height": image.height},
        "region": {"start": start, "end": end},
        "requestedHeight": requested,
        "width": image.width,
        "height": height,
        "truncated": height < requested,
        "output": str(output),
    })
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
