from __future__ import annotations

import json
from pathlib import Path

from conftest import KIT, kit, run_kit


def write_json(path: Path, value: object) -> None:
    path.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")


def prepare_ready_source(source: dict[str, object], heading: str = "Hello") -> None:
    root = Path(str(source["root"]))
    write_json(root / "spec" / "spec.json", {
        "version": 1,
        "page": {"name": "Home", "language": "en"},
        "variants": [{"id": "desktop", "label": "desktop", "nodeId": "1:2", "width": 1440, "height": 900, "reference": "desktop.png"}],
        "tokens": {"colors": []},
        "sections": [{"id": "main", "role": "content", "sourceNodeIds": ["1:3"], "textItemIds": ["title"], "assetIds": [], "bounds": {}, "layout": {}, "visual": {}}],
        "assets": [], "openQuestions": [],
    })
    write_json(root / "spec" / "content-inventory.json", {
        "version": 1,
        "items": [{"id": "title", "kind": "heading", "text": heading, "required": True, "nodeId": "1:3", "sectionId": "main"}],
    })
    write_json(root / "asset-manifest.json", {"assets": []})
    (root / "reference" / "desktop.png").write_text("reference", encoding="utf-8")


def test_state_controller_has_no_personal_token_or_figma_rest_dependency() -> None:
    controller = KIT.read_text(encoding="utf-8")
    assert ".env.local" not in controller
    assert "FIGMA_ACCESS_TOKEN" not in controller
    assert "api.figma.com" not in controller


def test_new_source_deduplicates_canonical_variants_and_requires_force_reason(project_factory) -> None:
    project_id = "source-reuse-test"
    project_factory(project_id)
    kit("init-project", project_id, "Source reuse test")
    kit("init-page", project_id, "home", "Home")
    source = kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2&t=first")
    duplicate = run_kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2&t=second", check=False)
    assert duplicate.returncode != 0
    assert "already" in duplicate.stderr.lower() or "matching source" in duplicate.stderr.lower()
    prepare_ready_source(source)
    kit("source-ready", project_id, "home", str(source["sourceId"]))
    reused = kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2&t=second")
    assert reused["sourceId"] == source["sourceId"]
    assert reused["reused"] is True
    missing_reason = run_kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2", "--force-new", check=False)
    assert missing_reason.returncode != 0
    assert "requires --reason" in missing_reason.stderr.lower()
    forced = kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2", "--force-new", "--reason", "Figma changed outside the supplied node metadata")
    assert forced["sourceId"] != source["sourceId"]
    assert forced["created"] is True


def test_incremental_sources_merge_changed_nodes_and_preserve_lineage(project_factory) -> None:
    project_id = "source-patch-test"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Source patch test")
    kit("init-page", project_id, "home", "Home")
    base = kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2")
    prepare_ready_source(base)
    kit("source-ready", project_id, "home", str(base["sourceId"]))
    derived = kit("new-source", project_id, "home", "--from-source", str(base["sourceId"]), "--changed-node", "desktop=1:3", "--changed-node", "desktop=1:4", "--reason", "Heading changed and a section was added")
    assert derived["baseSourceId"] == base["sourceId"]
    assert derived["extractionMode"] == "INCREMENTAL"
    premature = run_kit("source-ready", project_id, "home", str(derived["sourceId"]), check=False)
    assert premature.returncode != 0
    assert "stale reference" in premature.stderr.lower()

    patch_root = project_root / "patch-input"
    (patch_root / "reference").mkdir(parents=True)
    (patch_root / "reference" / "desktop.png").write_text("updated-reference", encoding="utf-8")
    patch_file = patch_root / "patch.json"
    write_json(patch_file, {
        "version": 1, "sourceId": derived["sourceId"],
        "sections": [
            {"id": "main", "role": "content", "sourceNodeIds": ["1:3"], "textItemIds": ["title"], "assetIds": [], "bounds": {}, "layout": {}, "visual": {"color": "#123456"}},
            {"section": {"id": "details", "role": "content", "sourceNodeIds": ["1:4"], "textItemIds": ["details-heading"], "assetIds": [], "bounds": {}, "layout": {}, "visual": {}}, "insertAfter": "main"},
        ],
        "replaceContentForSections": ["main"],
        "contentItems": [
            {"id": "title", "kind": "heading", "text": "Updated", "required": True, "nodeId": "1:3", "sectionId": "main"},
            {"id": "details-heading", "kind": "heading", "text": "Details", "required": True, "nodeId": "1:4", "sectionId": "details"},
        ],
        "specAssets": [], "manifestAssets": [], "refreshedVariants": ["desktop"],
        "files": {"assets": [], "references": [{"from": "reference/desktop.png", "to": "desktop.png"}], "raw": []},
        "calls": [{"operation": "get-design-context", "nodeId": "1:3", "status": "SUCCESS"}, {"operation": "get-design-context", "nodeId": "1:4", "status": "SUCCESS"}],
    })
    applied = kit("source-patch", project_id, "home", str(derived["sourceId"]), "--file", str(patch_file))
    assert applied["staleReferences"] == []
    kit("source-ready", project_id, "home", str(derived["sourceId"]))
    root = Path(str(derived["root"]))
    inventory = json.loads((root / "spec" / "content-inventory.json").read_text(encoding="utf-8"))
    assert inventory["items"][0]["text"] == "Updated"
    assert inventory["items"][1]["sectionId"] == "details"
    spec = json.loads((root / "spec" / "spec.json").read_text(encoding="utf-8"))
    assert [section["id"] for section in spec["sections"]] == ["main", "details"]
    run = kit("new-run", project_id, "home", "--source", str(derived["sourceId"]))
    kit("transition", project_id, "home", str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, "home", str(run["runId"]), "--round", "0")
    candidate_record = json.loads((Path(str(candidate["root"])) / "candidate.json").read_text(encoding="utf-8"))
    assert candidate_record["sourceId"] == derived["sourceId"]
    assert candidate_record["baseSourceId"] == base["sourceId"]


def test_rate_limit_calls_are_recorded_without_creating_another_source(project_factory) -> None:
    project_id = "source-rate-limit-test"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Source rate limit test")
    kit("init-page", project_id, "home", "Home")
    source = kit("new-source", project_id, "home", "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2")
    kit("source-call", project_id, "home", str(source["sourceId"]), "--operation", "get-screenshot", "--node", "1:2", "--status", "RATE_LIMITED", "--retry-after", "3600", "--message", "Figma returned HTTP 429")
    record = json.loads((Path(str(source["root"])) / "source.json").read_text(encoding="utf-8"))
    assert len(record["callLedger"]) == 1
    assert record["rateLimit"]["retryAfterSeconds"] == 3600
    budget = kit("source-budget", project_id, "home", str(source["sourceId"]))
    assert budget["allowed"] is False
    assert budget["retryAfterSeconds"] > 0
    entries = sorted(path.name for path in (project_root / "pages" / "home" / "sources").iterdir())
    assert entries == [source["sourceId"]]


def test_legacy_sources_without_a_stored_fingerprint_are_still_reused(project_factory) -> None:
    project_id, page_id = "legacy-fp", "home"
    project_factory(project_id)
    kit("init-project", project_id)
    kit("init-page", project_id, page_id)
    url = "https://www.figma.com/design/FILEKEY1/Doc?node-id=10-20"
    source = kit("new-source", project_id, page_id, "--variant", f"desktop={url}")
    prepare_ready_source(source)
    kit("source-ready", project_id, page_id, str(source["sourceId"]))

    # Simulate a legacy record written before fingerprints existed.
    source_file = Path(str(source["root"])) / "source.json"
    record = json.loads(source_file.read_text(encoding="utf-8"))
    record.pop("fingerprint", None)
    write_json(source_file, record)

    repeat = kit("new-source", project_id, page_id, "--variant", f"desktop={url}")
    assert repeat["reused"] is True
    assert repeat["sourceId"] == source["sourceId"]
    assert repeat["created"] is False


def test_ported_controller_commands_are_dispatchable(project_factory) -> None:
    project_id, page_id = "ported-cmds", "home"
    project_factory(project_id)
    kit("init-project", project_id)
    kit("init-page", project_id, page_id)

    # status works with and without a page argument
    assert kit("status", project_id)["project"]["id"] == project_id
    assert kit("status", project_id, page_id)["page"]["id"] == page_id

    url = "https://www.figma.com/design/FILEKEY2/Doc?node-id=30-40"
    doomed = kit("new-source", project_id, page_id, "--variant", f"desktop={url}")
    assert kit("source-fail", project_id, page_id, str(doomed["sourceId"]), "--message", "unreachable")["status"] == "FAILED"
    # a FAILED source is immutable
    assert run_kit("source-fail", project_id, page_id, str(doomed["sourceId"]), check=False).returncode != 0

    source = kit("new-source", project_id, page_id, "--variant", f"desktop={url}", "--force-new", "--reason", "retry")
    root = Path(str(source["root"]))
    prepare_ready_source(source)
    spec_file = root / "spec" / "spec.json"
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    spec["openQuestions"] = [{"id": "q-1", "essential": True, "question": "Which PDF?"}]
    write_json(spec_file, spec)
    resolved = kit("resolve-question", project_id, page_id, str(source["sourceId"]), "--question", "q-1", "--decision", "Use the 2026 insert", "--by", "user")
    assert resolved["remaining"] == 0
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    assert spec["decisions"][0]["decision"] == "Use the 2026 insert"
    assert run_kit("resolve-question", project_id, page_id, str(source["sourceId"]), "--question", "q-1", "--decision", "again", check=False).returncode != 0

    kit("source-ready", project_id, page_id, str(source["sourceId"]))
    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    run_id = str(run["runId"])
    kit("transition", project_id, page_id, run_id, "BUILDING")

    # next-repair increments, and is capped
    kit("transition", project_id, page_id, run_id, "VERIFYING")
    kit("transition", project_id, page_id, run_id, "REFINING")
    for expected in (1, 2, 3):
        assert kit("next-repair", project_id, page_id, run_id)["round"] == expected
    capped = run_kit("next-repair", project_id, page_id, run_id, check=False)
    assert capped.returncode != 0 and "cap reached" in capped.stderr.lower()

    # needs-review records the reason and is terminal
    terminal = kit("needs-review", project_id, page_id, run_id, "--message", "blocked on source content")
    assert terminal["status"] == "NEEDS_REVIEW"
    run_record = json.loads((Path(str(run["root"])) / "run.json").read_text(encoding="utf-8"))
    assert run_record["events"][-1]["message"] == "blocked on source content"
    assert json.loads((Path(str(run["root"])).parents[1] / "page.json").read_text(encoding="utf-8"))["status"] == "NEEDS_REVIEW"
    assert run_kit("next-repair", project_id, page_id, run_id, check=False).returncode != 0


def test_verify_output_never_writes_its_report_into_the_payload(tmp_path) -> None:
    import subprocess, sys as _sys
    root = Path(__file__).resolve().parents[1]
    payload = tmp_path / "candidate-001"
    (payload / "images").mkdir(parents=True)
    (payload / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>T</title>'
        '<link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css">'
        "</head><body><main><h1>Hi</h1></main></body></html>", encoding="utf-8")
    (payload / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (payload / "page.css").write_text("main{display:block}", encoding="utf-8")

    # default run must leave the payload untouched and still be a clean PASS
    subprocess.run([_sys.executable, str(root / "scripts" / "verify-output.py"), "--root", str(payload)],
                   cwd=root, check=True, capture_output=True, text=True)
    assert sorted(p.name for p in payload.iterdir()) == ["base.css", "images", "index.html", "page.css"]
    report = tmp_path / "candidate-001-technical-report.json"
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "PASS"

    # and an explicit --output inside the payload is refused outright
    bad = subprocess.run(
        [_sys.executable, str(root / "scripts" / "verify-output.py"), "--root", str(payload),
         "--output", str(payload / "technical-report.json")],
        cwd=root, check=False, capture_output=True, text=True)
    assert bad.returncode != 0
    assert "must not be written inside" in (bad.stderr + bad.stdout)
