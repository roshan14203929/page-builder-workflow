#!/usr/bin/env python3
"""Perform deterministic static checks on generated HTML/CSS output."""

from __future__ import annotations

import html as html_module
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def is_within(root: Path, target: Path) -> bool:
    return target == root or root in target.parents


def visible_text(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style\b[^>]*>[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html_module.unescape(value).replace("\xa0", " ")).strip()


def main() -> int:
    args = options(sys.argv[1:])
    if not args.get("root"):
        raise ValueError("Usage: verify-output.py --root <generated-dir> [--inventory content-inventory.json] [--output report.json]")
    root = Path(args["root"]).resolve()
    # The default must NOT land inside root: this script enforces an exact-set
    # payload contract on root, so writing the report there makes the next run fail.
    default_output = root.parent / f"{root.name}-technical-report.json"
    output = Path(args.get("output", str(default_output))).resolve()
    if is_within(root, output):
        raise ValueError(f"--output must not be written inside the validated payload: {output}")
    findings: list[dict[str, object]] = []

    def add(identifier: str, severity: str, message: str, evidence: object = None) -> None:
        findings.append({"id": identifier, "severity": severity, "message": message, "section": None, "evidence": evidence, "suggestedFix": None})

    def text_of(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    index_path = root / "index.html"
    document = text_of(index_path)
    base_css, page_css = text_of(root / "base.css"), text_of(root / "page.css")
    css = f"{base_css}\n{page_css}"
    if not document:
        add("missing-index", "critical", "index.html is missing or empty.")
    if not base_css:
        add("missing-base-css", "critical", "base.css is missing or empty.")
    if not page_css:
        add("missing-page-css", "critical", "page.css is missing or empty.")
    if not (root / "images").is_dir():
        add("missing-images", "critical", "images/ is missing or is not a directory.")
    expected = ["base.css", "images", "index.html", "page.css"]
    try:
        found = sorted(entry.name for entry in root.iterdir() if entry.name != "candidate.json")
    except Exception:
        found = []
    if found != expected:
        add("invalid-output-structure", "critical", f"Deployable output must contain exactly: {', '.join(expected)}. Found: {', '.join(found)}.")
    if document and not re.match(r"^\s*<!doctype html>", document, flags=re.I):
        add("missing-doctype", "high", "Document is missing an HTML doctype.")
    if document and not re.search(r"<html\b[^>]*\blang=[\"'][^\"']+[\"']", document, flags=re.I):
        add("missing-lang", "high", "The html element has no language.")
    if document and not re.search(r"<title>\s*[^<]+\s*</title>", document, flags=re.I):
        add("missing-title", "high", "Document title is missing or empty.")
    if document and not re.search(r"<meta\b[^>]*name=[\"']viewport[\"']", document, flags=re.I):
        add("missing-viewport", "high", "Viewport metadata is missing.")
    if document and len(re.findall(r"<main\b", document, flags=re.I)) != 1:
        add("main-count", "high", "Document must contain exactly one main element.")
    if document and len(re.findall(r"<h1\b", document, flags=re.I)) != 1:
        add("h1-count", "high", "Document must contain exactly one h1.")
    if re.search(r"\sstyle\s*=", document, flags=re.I):
        add("inline-style", "medium", "Inline style attributes are not allowed.")
    if re.search(r"!important\b", css, flags=re.I):
        add("important", "medium", "CSS contains !important.")
    if re.search(r"(?:src|href)=[\"']https?://", document, flags=re.I) or re.search(r"url\(\s*[\"']?https?://", css, flags=re.I):
        add("remote-runtime", "high", "Generated output contains remote runtime resources.")
    if re.search(r"\b(lorem ipsum|todo|placeholder text|replace me)\b", document, flags=re.I):
        add("placeholder-content", "high", "Generated output contains placeholder content.")

    references = set(re.findall(r"(?:src|href)=[\"']([^\"'#?]+)[\"']", document, flags=re.I))
    references.update(re.findall(r"url\(\s*[\"']?([^\"')?#]+)[\"']?\s*\)", css, flags=re.I))
    for reference in references:
        if re.match(r"^(?:data:|mailto:|tel:|javascript:|//)", reference, flags=re.I) or reference.startswith("/"):
            continue
        target = (root / reference).resolve()
        if not is_within(root, target):
            add("unsafe-reference", "critical", f"Asset reference escapes generated root: {reference}")
        elif not target.exists():
            add("broken-reference", "high", f"Local asset does not exist: {reference}")

    if args.get("inventory"):
        inventory = json.loads(Path(args["inventory"]).resolve().read_text(encoding="utf-8"))
        text = visible_text(document)
        for item in inventory.get("items", []):
            required_text = str(item.get("text", ""))
            normalized = re.sub(r"\s+", " ", required_text).strip()
            if item.get("required") and required_text and normalized not in text:
                add(f"missing-content-{item.get('id')}", "critical", f"Required source content is missing: {required_text}", item.get("id"))

    try:
        files = sorted(file.name for file in root.iterdir())
    except Exception:
        files = []
    report = {"kind": "technical", "status": "FAIL" if findings else "PASS", "checkedAt": now(), "summary": f"{len(findings)} technical or content-integrity issue(s) found." if findings else "Static output checks passed.", "findings": findings, "files": files}
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2) + "\n"
    output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
