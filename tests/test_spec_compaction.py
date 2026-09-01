from __future__ import annotations

import json
from pathlib import Path

from conftest import kit, run_kit


STYLE_A = {"fontFamily": "Noto Sans JP", "fontSize": 18, "fontWeight": 700}
STYLE_B = {"fontFamily": "Meiryo", "fontSize": 16, "fontWeight": 400}


def build_source(project_factory, project_id: str) -> tuple[str, str, Path]:
    page_id = "home"
    project_factory(project_id)
    kit("init-project", project_id, "Compaction test")
    kit("init-page", project_id, page_id, "Home")
    source = kit(
        "new-source", project_id, page_id,
        "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2",
        "--variant", "mobile=https://www.figma.com/design/example?node-id=2-3",
    )
    root = Path(str(source["root"]))
    write(root / "spec" / "spec.json", {
        "version": 1,
        "page": {"name": "Home"},
        "variants": [
            {"id": "desktop", "label": "desktop", "width": 1440, "height": 900, "reference": "desktop.png"},
            {"id": "mobile", "label": "mobile", "width": 375, "height": 812, "reference": "mobile.png"},
        ],
        "sections": [{"id": "hero", "role": "banner"}],
        "tokens": {
            "colors": [
                {"value": {"r": 230 / 255, "g": 230 / 255, "b": 230 / 255, "a": 1},
                 "uses": ["1:1", "1:2", "1:3"], "count": 3},
                {"value": {"r": 0, "g": 179 / 255, "b": 152 / 255, "a": 0.5},
                 "uses": ["1:4"], "count": 1},
            ],
            "typography": [
                {"value": {"fontFamily": "Noto Sans JP", "fontSize": 18}, "uses": ["1:1"], "count": 1},
            ],
            # The other extractor shape: `nodeIds` provenance and pre-rendered
            # CSS colour strings.
            "radii": [{"id": "radius-01", "count": 67, "nodeIds": ["1:1", "1:2"],
                       "evidence": {"role": "cornerRadius", "value": "4px"}}],
            "spacing": [{"value": {"paddingLeft": 14}, "uses": ["1:1"], "count": 1}],
            "shadows": [],
        },
    })
    items = []
    for index in range(12):
        variant = "desktop" if index % 2 == 0 else "mobile"
        items.append({
            "id": f"content-{index}",
            "kind": "heading" if index < 4 else "paragraph",
            "text": f"Copy {index}",
            "required": index % 3 == 0,
            "nodeId": f"1:{index}",
            "sectionId": "hero" if index < 6 else "body",
            "variant": variant,
            "style": STYLE_A if index % 2 == 0 else STYLE_B,
        })
    write(root / "spec" / "content-inventory.json", {"version": 1, "items": items})
    write(root / "asset-manifest.json", {"version": 1, "assets": []})
    (root / "reference").mkdir(parents=True, exist_ok=True)
    for name in ("desktop.png", "mobile.png"):
        (root / "reference" / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    return project_id, page_id, root


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")


def resolve(inventory: dict) -> list[dict]:
    styles = inventory.get("styles", {})
    resolved = []
    for item in inventory["items"]:
        item = dict(item)
        if isinstance(item.get("style"), str):
            item["style"] = styles[item["style"]]
        resolved.append(item)
    return resolved


def test_spec_compact_is_lossless_and_shrinks_the_artifacts(project_factory) -> None:
    project_id, page_id, root = build_source(project_factory, "spec-compact-test")
    inventory_path = root / "spec" / "content-inventory.json"
    before = json.loads(inventory_path.read_text(encoding="utf-8"))
    before_bytes = inventory_path.stat().st_size

    result = kit("spec-compact", project_id, page_id, "source-001")

    reports = {entry["file"]: entry for entry in result["normalized"]}
    assert reports["spec/spec.json"]["bytesAfter"] < reports["spec/spec.json"]["bytesBefore"]
    assert reports["spec/content-inventory.json"]["bytesAfter"] < before_bytes

    after = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert set(after["styles"]) == {"s0", "s1"}
    assert resolve(after) == before["items"]


def test_spec_compact_normalizes_design_tokens(project_factory) -> None:
    project_id, page_id, root = build_source(project_factory, "token-normalize-test")
    spec_path = root / "spec" / "spec.json"
    before = json.loads(spec_path.read_text(encoding="utf-8"))

    kit("spec-compact", project_id, page_id, "source-001")
    tokens = json.loads(spec_path.read_text(encoding="utf-8"))["tokens"]

    # Opaque colours become hex; translucent ones keep their alpha as rgba().
    assert [entry["value"] for entry in tokens["colors"]] == ["#e6e6e6", "rgba(0,179,152,0.5)"]
    # Both provenance shapes are dropped; `count` survives as the ranking signal.
    assert not any(
        {"uses", "nodeIds"} & set(entry) for group in tokens.values() for entry in group
    )
    assert [entry["count"] for entry in tokens["colors"]] == [3, 1]
    # A group using the other extractor shape keeps its id, count, and evidence.
    assert tokens["radii"][0] == {
        "id": "radius-01", "count": 67,
        "evidence": {"role": "cornerRadius", "value": "4px"},
    }
    # Non-colour groups keep their structured values, and empty groups survive.
    assert tokens["typography"][0]["value"] == {"fontFamily": "Noto Sans JP", "fontSize": 18}
    assert tokens["spacing"][0]["value"] == {"paddingLeft": 14}
    assert tokens["shadows"] == []
    # Everything outside `tokens` is untouched.
    after = json.loads(spec_path.read_text(encoding="utf-8"))
    assert {k: v for k, v in after.items() if k != "tokens"} == {
        k: v for k, v in before.items() if k != "tokens"
    }


def test_token_colours_round_trip_to_their_eight_bit_values(project_factory) -> None:
    project_id, page_id, root = build_source(project_factory, "token-precision-test")
    original = json.loads((root / "spec" / "spec.json").read_text(encoding="utf-8"))["tokens"]["colors"]

    kit("spec-compact", project_id, page_id, "source-001")
    converted = json.loads((root / "spec" / "spec.json").read_text(encoding="utf-8"))["tokens"]["colors"]

    for source, result in zip(original, converted):
        channels = [round(source["value"][key] * 255) for key in "rgb"]
        alpha = source["value"].get("a", 1)
        if alpha >= 0.999:
            assert result["value"] == "#%02x%02x%02x" % tuple(channels)
        else:
            assert result["value"] == f"rgba({channels[0]},{channels[1]},{channels[2]},{round(alpha, 3)})"


def test_spec_compact_is_idempotent(project_factory) -> None:
    project_id, page_id, root = build_source(project_factory, "spec-compact-idempotent-test")
    inventory_path = root / "spec" / "content-inventory.json"

    kit("spec-compact", project_id, page_id, "source-001")
    first = inventory_path.read_text(encoding="utf-8")
    kit("spec-compact", project_id, page_id, "source-001")

    assert inventory_path.read_text(encoding="utf-8") == first


def test_source_ready_normalizes_the_spec_artifacts(project_factory) -> None:
    project_id, page_id, root = build_source(project_factory, "source-ready-compaction-test")
    inventory_path = root / "spec" / "content-inventory.json"
    before_bytes = inventory_path.stat().st_size

    ready = kit("source-ready", project_id, page_id, "source-001")

    assert ready["status"] == "READY"
    assert any(entry["file"] == "spec/spec.json" for entry in ready["normalized"])
    assert inventory_path.stat().st_size < before_bytes
    assert "\n " not in inventory_path.read_text(encoding="utf-8").strip()


def test_inventory_query_filters_and_projects_fields(project_factory) -> None:
    project_id, page_id, _ = build_source(project_factory, "inventory-query-test")
    kit("source-ready", project_id, page_id, "source-001")

    everything = kit("inventory", project_id, page_id, "source-001", "--fields", "all")
    assert everything["total"] == 12
    assert everything["matched"] == 12

    desktop = kit("inventory", project_id, page_id, "source-001", "--variant", "desktop")
    assert desktop["matched"] == 6
    assert all(item["variant"] == "desktop" for item in desktop["items"])
    assert all("style" not in item and "bounds" not in item for item in desktop["items"])

    headings = kit("inventory", project_id, page_id, "source-001", "--kind", "heading")
    assert headings["matched"] == 4

    hero = kit("inventory", project_id, page_id, "source-001", "--section", "hero")
    assert hero["matched"] == 6

    required = kit("inventory", project_id, page_id, "source-001", "--required")
    assert required["matched"] == 4

    text_only = kit("inventory", project_id, page_id, "source-001", "--fields", "id,text")
    assert set(text_only["items"][0]) == {"id", "text"}


def test_inventory_query_resolves_styles_and_paginates(project_factory) -> None:
    project_id, page_id, _ = build_source(project_factory, "inventory-style-test")
    kit("source-ready", project_id, page_id, "source-001")

    scoped = kit(
        "inventory", project_id, page_id, "source-001",
        "--section", "hero", "--variant", "desktop", "--fields", "all",
    )
    assert scoped["matched"] == 3
    assert set(scoped["styles"]) == {"s0"}
    assert scoped["styles"]["s0"] == STYLE_A

    page_one = kit("inventory", project_id, page_id, "source-001", "--limit", "5")
    assert page_one["returned"] == 5 and page_one["matched"] == 12
    page_two = kit("inventory", project_id, page_id, "source-001", "--offset", "5", "--limit", "5")
    assert page_two["returned"] == 5
    assert page_one["items"][0]["id"] != page_two["items"][0]["id"]

    sections = kit("inventory", project_id, page_id, "source-001", "--sections")
    assert {entry["sectionId"] for entry in sections["sections"]} == {"hero", "body"}
    assert sum(entry["items"] for entry in sections["sections"]) == 12
