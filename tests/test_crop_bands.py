from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from conftest import ROOT


CROP = ROOT / "scripts" / "crop-bands.py"
WIDTH, HEIGHT = 120, 900


def run_crop(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(CROP), *args], cwd=ROOT, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


@pytest.fixture
def diff_report(tmp_path: Path):
    def build(bands: list[dict[str, float]]) -> Path:
        files = {}
        for index, layer in enumerate(("reference", "candidate", "diff")):
            image = Image.new("RGB", (WIDTH, HEIGHT))
            # A distinct value per row per layer, so a misaligned crop is detectable.
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    image.putpixel((x, y), (y % 256, (y * 3) % 256, index))
            path = tmp_path / f"{layer}.png"
            image.save(path)
            files[layer] = str(path)
        report = tmp_path / "desktop-diff.json"
        report.write_text(json.dumps({
            "status": "FAIL", "viewport": {"width": WIDTH, "height": HEIGHT},
            "peakBandDifferencePercent": max((b["differencePercent"] for b in bands), default=0),
            "worstBands": bands, "files": files,
        }), encoding="utf-8")
        return report

    return build


def test_crops_are_native_resolution_and_aligned_to_the_band(diff_report, tmp_path: Path) -> None:
    report = diff_report([{"start": 400, "end": 500, "differencePercent": 90.0}])
    output = tmp_path / "crops.json"

    result = run_crop("--report", str(report), "--output", str(output), "--pad", "0")

    assert result["status"] == "FAIL"
    assert len(result["regions"]) == 1
    region = result["regions"][0]
    assert (region["start"], region["end"]) == (400, 500)

    source = Image.open(tmp_path / "reference.png")
    crop = Image.open(region["files"]["reference"])
    assert crop.size == (WIDTH, 100)  # native width, exact band height - no downscale
    assert list(crop.getdata()) == list(source.crop((0, 400, WIDTH, 500)).getdata())
    assert set(region["files"]) == {"reference", "candidate", "diff"}


def test_adjacent_bands_merge_into_one_region(diff_report, tmp_path: Path) -> None:
    # visual-diff.py emits fixed-height slivers; a tall failure spans several.
    report = diff_report([
        {"start": 100, "end": 200, "differencePercent": 80.0},
        {"start": 200, "end": 300, "differencePercent": 95.0},
        {"start": 300, "end": 400, "differencePercent": 70.0},
        {"start": 800, "end": 900, "differencePercent": 60.0},
    ])
    output = tmp_path / "crops.json"

    result = run_crop("--report", str(report), "--output", str(output), "--pad", "0")

    regions = result["regions"]
    assert len(regions) == 2
    merged = next(r for r in regions if r["start"] == 100)
    assert (merged["end"], merged["mergedBands"]) == (400, 3)
    assert merged["differencePercent"] == 95.0  # region carries its worst band


def test_padding_adds_context_and_clamps_to_the_image(diff_report, tmp_path: Path) -> None:
    report = diff_report([{"start": 0, "end": 100, "differencePercent": 90.0},
                          {"start": 850, "end": 900, "differencePercent": 88.0}])
    output = tmp_path / "crops.json"

    result = run_crop("--report", str(report), "--output", str(output), "--pad", "40")

    spans = sorted((r["start"], r["end"]) for r in result["regions"])
    assert spans == [(0, 140), (810, 900)]  # clamped at both edges, padded inward


def test_quiet_bands_produce_no_crops(diff_report, tmp_path: Path) -> None:
    report = diff_report([{"start": 100, "end": 200, "differencePercent": 1.5}])
    output = tmp_path / "crops.json"

    result = run_crop("--report", str(report), "--output", str(output), "--min-difference", "5")

    assert result["status"] == "PASS"
    assert result["regions"] == []
    assert not list(tmp_path.glob("crops-*.png"))


def test_region_limit_keeps_the_worst_regions(diff_report, tmp_path: Path) -> None:
    report = diff_report([
        {"start": 0, "end": 50, "differencePercent": 20.0},
        {"start": 200, "end": 250, "differencePercent": 95.0},
        {"start": 400, "end": 450, "differencePercent": 60.0},
        {"start": 600, "end": 650, "differencePercent": 80.0},
    ])
    output = tmp_path / "crops.json"

    result = run_crop("--report", str(report), "--output", str(output), "--regions", "2", "--pad", "0")

    assert [r["differencePercent"] for r in result["regions"]] == [95.0, 80.0]
