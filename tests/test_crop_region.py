from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from conftest import ROOT


CROP = ROOT / "scripts" / "crop-region.py"
WIDTH = 120


def run_crop(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(CROP), *args], cwd=ROOT, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


@pytest.fixture
def reference(tmp_path: Path):
    def build(height: int) -> Path:
        image = Image.new("RGB", (WIDTH, height))
        # A distinct value per row, so a misaligned crop is detectable.
        for y in range(height):
            for x in range(WIDTH):
                image.putpixel((x, y), (y % 256, (y * 3) % 256, 7))
        path = tmp_path / "reference.png"
        image.save(path)
        return path

    return build


def test_crops_the_top_band_at_native_resolution(reference, tmp_path: Path) -> None:
    source = reference(4000)
    output = tmp_path / "above-fold.png"

    result = run_crop("--image", str(source), "--output", str(output), "--top", "900")

    assert (result["width"], result["height"]) == (WIDTH, 900)
    assert result["truncated"] is False
    crop = Image.open(output)
    assert crop.size == (WIDTH, 900)  # native width, no resampling
    assert list(crop.getdata()) == list(Image.open(source).crop((0, 0, WIDTH, 900)).getdata())


def test_a_short_image_is_truncated_rather_than_padded(reference, tmp_path: Path) -> None:
    # Padding would put synthetic fill against the candidate's real background and
    # register as a ~100% difference. The caller renders to `height` instead.
    source = reference(600)
    output = tmp_path / "above-fold.png"

    result = run_crop("--image", str(source), "--output", str(output), "--top", "900")

    assert (result["height"], result["requestedHeight"]) == (600, 900)
    assert result["truncated"] is True
    assert Image.open(output).size == (WIDTH, 600)


def test_start_offsets_the_region(reference, tmp_path: Path) -> None:
    source = reference(1000)
    output = tmp_path / "band.png"

    result = run_crop("--image", str(source), "--output", str(output), "--start", "200", "--top", "300")

    assert result["region"] == {"start": 200, "end": 500}
    crop = Image.open(output)
    assert list(crop.getdata()) == list(Image.open(source).crop((0, 200, WIDTH, 500)).getdata())


def test_a_sidecar_report_records_the_actual_height(reference, tmp_path: Path) -> None:
    source = reference(4000)
    output = tmp_path / "above-fold.png"

    run_crop("--image", str(source), "--output", str(output), "--top", "900")

    sidecar = json.loads((tmp_path / "above-fold.json").read_text(encoding="utf-8"))
    assert sidecar["height"] == 900
    assert sidecar["sourceSize"] == {"width": WIDTH, "height": 4000}


def test_a_start_past_the_image_is_rejected(reference, tmp_path: Path) -> None:
    source = reference(500)
    result = subprocess.run(
        [sys.executable, str(CROP), "--image", str(source),
         "--output", str(tmp_path / "x.png"), "--start", "500"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "past the end" in (result.stderr or result.stdout)
