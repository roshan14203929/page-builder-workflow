from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import ROOT


CODEMAP = ROOT / ".claude" / "skills" / "codemap" / "scripts" / "codemap.py"


def run_codemap(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(CODEMAP), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


def fixture(root: Path) -> Path:
    (root / ".codemap").mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("from .util import value\nprint(value)\n", encoding="utf-8")
    (root / "src" / "util.py").write_text("value = 1\n", encoding="utf-8")
    (root / ".codemap" / "config.json").write_text(json.dumps({
        "version": 1,
        "project": "Fixture",
        "description": "Codemap fixture.",
        "entryPoints": ["src/main.py"],
        "modules": [
            {"id": "app", "label": "App", "layer": "Runtime", "description": "Runs the fixture.", "paths": ["src/main.py"], "entryPoints": ["src/main.py"]},
            {"id": "utility", "label": "Utility", "layer": "Runtime", "description": "Provides a value.", "paths": ["src/util.py"]},
        ],
    }, indent=2) + "\n", encoding="utf-8")
    return root


def test_codemap_build_is_deterministic_and_infers_python_dependencies(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    run_codemap("build", "--root", str(root))
    first = (root / ".codemap" / "map.json").read_text(encoding="utf-8")
    run_codemap("build", "--root", str(root))
    second = (root / ".codemap" / "map.json").read_text(encoding="utf-8")
    assert first == second
    workspace_map = json.loads(first)
    app = next(module for module in workspace_map["modules"] if module["id"] == "app")
    utility = next(module for module in workspace_map["modules"] if module["id"] == "utility")
    assert app["dependencies"] == ["utility"]
    assert app["inferredDependencies"] == ["utility"]
    assert utility["usedBy"] == ["app"]
    assert workspace_map["uncoveredFiles"] == []
    assert workspace_map["overlaps"] == []
    assert "<script>" in (root / ".codemap" / "workspace-map.html").read_text(encoding="utf-8")


def test_codemap_check_detects_drift_without_rewriting_map(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    run_codemap("build", "--root", str(root))
    map_path = root / ".codemap" / "map.json"
    before = map_path.read_text(encoding="utf-8")
    (root / "src" / "util.py").write_text("value = 2\n", encoding="utf-8")
    result = run_codemap("check", "--root", str(root), check=False)
    assert result.returncode == 2
    assert json.loads(result.stdout)["changed"] == ["src/util.py"]
    assert map_path.read_text(encoding="utf-8") == before


def test_codemap_rejects_paths_outside_the_repository(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    result = run_codemap("build", "--root", str(root), "--config", "../escape/config.json", check=False)
    assert result.returncode == 1
    assert "must stay inside" in result.stderr


def test_codemap_query_returns_module_and_file_ownership(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    run_codemap("build", "--root", str(root))
    module = json.loads(run_codemap("query", "--root", str(root), "--module", "app").stdout)
    assert module["id"] == "app"
    assert module["dependencies"] == ["utility"]
    file = json.loads(run_codemap("query", "--root", str(root), "--file", "src/main.py").stdout)
    assert file["file"]["modules"] == ["app"]
    assert [item["id"] for item in file["modules"]] == ["app"]
    search = json.loads(run_codemap("query", "--root", str(root), "--search", "value").stdout)
    assert [item["id"] for item in search] == ["utility"]


def test_codemap_help_exits_successfully() -> None:
    result = run_codemap("--help", check=False)
    assert result.returncode == 0
    assert result.stdout.startswith("usage: codemap.py")
