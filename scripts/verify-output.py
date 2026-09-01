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
    # Accessible text carried in attributes (image alt, aria-label, title) is real
    # page content. Collect it before tags are stripped so an inventory item that
    # is rendered only as image alt text is not falsely reported missing. This is
    # required for XHTML/MediChannel figures whose description lives in alt="".
    attrs = re.findall(r"(?:\balt|\baria-label|\btitle)\s*=\s*\"([^\"]*)\"", value, flags=re.I)
    attrs += re.findall(r"(?:\balt|\baria-label|\btitle)\s*=\s*'([^']*)'", value, flags=re.I)
    # Named inline phrasing elements (span, em, strong, etc.) used for rich-text
    # emphasis do not introduce visual word gaps. When such a tag is surrounded
    # on BOTH sides by visible text (non-whitespace, non-tag-boundary chars),
    # remove it silently so inventory substring checks still pass.
    # Tags at block boundaries (preceded by whitespace/">" or followed by "<"),
    # and void/block elements like <br> and <img>, are left for the next sub
    # which converts them to spaces — correctly handling adjacent-span heading
    # patterns where the tag provides the only word separator.
    _inline_phrasing = (
        r"a|span|em|strong|b|i|u|s|abbr|acronym|cite|code|dfn|kbd|mark|q|samp"
        r"|small|sub|sup|time|var|bdi|bdo|data|ruby|rb|rt|rtc|rp|wbr"
    )
    value = re.sub(
        rf"(?<=[^\s>])</?(?:{_inline_phrasing})\b[^>]*>(?=[^\s<])",
        "", value, flags=re.I,
    )
    value = re.sub(r"<[^>]+>", " ", value)
    value = value + " " + " ".join(attrs)
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
        # candidate.json is lifecycle metadata and structural-check/ is
        # pre-acceptance diagnostic evidence (per the artifact contract, both live
        # in the candidate dir). Neither is part of the deployable payload.
        found = sorted(entry.name for entry in root.iterdir() if entry.name not in ("candidate.json", "structural-check"))
    except Exception:
        found = []
    if found != expected:
        add("invalid-output-structure", "critical", f"Deployable output must contain exactly: {', '.join(expected)}. Found: {', '.join(found)}.")
    # Accept the HTML5 shorthand (<!doctype html>) and the full XHTML 1.0 Strict
    # DOCTYPE, which may be preceded by an <?xml ...?> declaration. MediChannel
    # deliveries are XHTML 1.0 Strict, not HTML5.
    if document and not re.match(r"^\s*(?:<\?xml\b[^>]*\?>\s*)?<!doctype\s+html\b", document, flags=re.I):
        add("missing-doctype", "high", "Document is missing an HTML doctype.")
    if document and not re.search(r"<html\b[^>]*\blang=[\"'][^\"']+[\"']", document, flags=re.I):
        add("missing-lang", "high", "The html element has no language.")
    if document and not re.search(r"<title>\s*[^<]+\s*</title>", document, flags=re.I):
        add("missing-title", "high", "Document title is missing or empty.")
    if document and not re.search(r"<meta\b[^>]*name=[\"']viewport[\"']", document, flags=re.I):
        add("missing-viewport", "high", "Viewport metadata is missing.")
    # Count main landmarks as either a literal <main> element or an element
    # carrying role="main". XHTML 1.0 Strict has no <main>, so MediChannel uses
    # <div id="main" role="main">. Subtract the overlap so <main role="main">
    # is not double-counted.
    main_elements = len(re.findall(r"<main\b", document, flags=re.I))
    role_main = len(re.findall(r"role\s*=\s*[\"']main[\"']", document, flags=re.I))
    main_overlap = len(re.findall(r"<main\b[^>]*role\s*=\s*[\"']main[\"']", document, flags=re.I))
    if document and (main_elements + role_main - main_overlap) != 1:
        add("main-count", "high", "Document must contain exactly one main landmark (<main> or role=\"main\").")
    if document and len(re.findall(r"<h1\b", document, flags=re.I)) != 1:
        add("h1-count", "high", "Document must contain exactly one h1.")
    if re.search(r"\sstyle\s*=", document, flags=re.I):
        add("inline-style", "medium", "Inline style attributes are not allowed.")
    if re.search(r"!important\b", css, flags=re.I):
        add("important", "medium", "CSS contains !important.")
    # Remote-runtime: flag resource-loading attributes (src on any element; href on
    # non-anchor elements like <link>, <base>). Regular <a href="https://..."> hyperlinks
    # are valid external navigation and must not be flagged as remote resources.
    has_remote_src = bool(re.search(r"\bsrc=[\"']https?://", document, flags=re.I))
    has_remote_link = bool(re.search(r"<link\b[^>]*\bhref=[\"']https?://", document, flags=re.I))
    has_remote_css_url = bool(re.search(r"url\(\s*[\"']?https?://", css, flags=re.I))
    if has_remote_src or has_remote_link or has_remote_css_url:
        add("remote-runtime", "high", "Generated output contains remote runtime resources.")
    if re.search(r"\b(lorem ipsum|todo|placeholder text|replace me)\b", document, flags=re.I):
        add("placeholder-content", "high", "Generated output contains placeholder content.")

    references = set(re.findall(r"(?:src|href)=[\"']([^\"'#?]+)[\"']", document, flags=re.I))
    references.update(re.findall(r"url\(\s*[\"']?([^\"')?#]+)[\"']?\s*\)", css, flags=re.I))
    for reference in references:
        # Skip non-local schemes (external URLs, data URIs, mailto, tel, etc.)
        if re.match(r"^(?:https?:|data:|mailto:|tel:|javascript:|//)", reference, flags=re.I) or reference.startswith("/"):
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
