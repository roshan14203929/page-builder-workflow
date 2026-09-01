#!/usr/bin/env python3
"""Generate, check, and query a deterministic workspace map.

This is the Python implementation of the codemap skill.  It intentionally has
no third-party dependencies so the skill is usable wherever Python 3.10+ is
available.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


TEXT_EXTENSIONS = {
    "", ".c", ".cc", ".cpp", ".css", ".go", ".h", ".html", ".java",
    ".js", ".jsx", ".json", ".md", ".mjs", ".cjs", ".py", ".rb",
    ".rs", ".scss", ".sh", ".sql", ".svg", ".toml", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml",
}
SKIP_DIRECTORIES = {
    ".git", ".hg", ".svn", ".codemap", "node_modules", "vendor", "dist",
    "build", "coverage", ".next", ".cache", "__pycache__", ".venv", "venv",
}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
SOURCE_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".css", ".scss", ".py"}
RESOLVE_EXTENSIONS = ["", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".json", ".css", ".scss", ".py"]


def json_text(value: Any, *, pretty: bool = False) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2 if pretty else None, separators=None if pretty else (",", ":"))


def stable_json(value: Any) -> str:
    """Match JSON.stringify-based stable serialization used by the Node tool."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def posix(value: str | Path) -> str:
    return str(value).replace("\\", "/").removeprefix("./")


def glob_regex(pattern: str) -> re.Pattern[str]:
    source = posix(pattern)
    output, index = "^", 0
    while index < len(source):
        char = source[index]
        if char == "*":
            if index + 1 < len(source) and source[index + 1] == "*":
                index += 1
                if index + 1 < len(source) and source[index + 1] == "/":
                    index += 1
                    output += "(?:.*/)?"
                else:
                    output += ".*"
            else:
                output += "[^/]*"
        elif char == "?":
            output += "[^/]"
        else:
            output += re.escape(char)
        index += 1
    return re.compile(f"{output}$")


def matches(file: str, patterns: list[str]) -> bool:
    return any(glob_regex(pattern).match(file) for pattern in patterns)


def fail(message: str) -> int:
    print(f"codemap: {message}", file=sys.stderr)
    return 1


def read_json(file: Path) -> dict[str, Any]:
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"cannot read {file}: {error}") from error


def validate_config(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise ValueError("config.version must be 1")
    if not isinstance(config.get("project"), str) or not config["project"]:
        raise ValueError("config.project is required")
    modules = config.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ValueError("config.modules must be non-empty")
    ids: set[str] = set()
    for module in modules:
        identifier = module.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
            raise ValueError(f"invalid module id: {identifier}")
        if identifier in ids:
            raise ValueError(f"duplicate module id: {identifier}")
        ids.add(identifier)
        for key in ("label", "layer", "description"):
            if not isinstance(module.get(key), str) or not module[key]:
                raise ValueError(f"module {identifier} requires {key}")
        if not isinstance(module.get("paths"), list) or not module["paths"]:
            raise ValueError(f"module {identifier} requires paths")
    for module in modules:
        for dependency in module.get("dependencies", []):
            if dependency not in ids:
                raise ValueError(f"module {module['id']} references unknown dependency {dependency}")
            if dependency == module["id"]:
                raise ValueError(f"module {module['id']} cannot depend on itself")


def walk(root: Path, excludes: list[str]) -> list[str]:
    files: list[str] = []
    for directory, names, filenames in os.walk(root, topdown=True, followlinks=False):
        directory_path = Path(directory)
        names[:] = sorted(
            (name for name in names if name not in SKIP_DIRECTORIES and not matches(posix((directory_path / name).relative_to(root)) + "/", excludes)),
            key=str.casefold,
        )
        for name in sorted(filenames, key=str.casefold):
            file = directory_path / name
            relative = posix(file.relative_to(root))
            if file.is_symlink() or name in SKIP_FILES or matches(relative, excludes):
                continue
            if file.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            files.append(relative)
    return files


def file_info(root: Path, relative: str, maximum: int) -> dict[str, Any]:
    file = root / relative
    size = file.stat().st_size
    digest = hashlib.sha256()
    if size > maximum:
        newlines = 0
        with file.open("rb") as handle:
            while chunk := handle.read(64 * 1024):
                digest.update(chunk)
                newlines += chunk.count(b"\n")
        return {"path": relative, "bytes": size, "lines": newlines + 1 if size else 0, "hash": digest.hexdigest()[:16], "content": None, "oversized": True}
    raw = file.read_bytes()
    content = raw.decode("utf-8")
    digest.update(raw)
    return {
        "path": relative, "bytes": len(raw), "lines": 0 if not content else len(re.split(r"\r?\n", content)),
        "hash": digest.hexdigest()[:16], "content": content, "oversized": False,
    }


def extract_imports(content: str, extension: str) -> list[str]:
    if extension not in SOURCE_EXTENSIONS:
        return []
    found: set[str] = set()
    patterns = (
        r"\b(?:import|export)\s+(?:[^\"']+?\s+from\s+)?[\"']([^\"']+)[\"']",
        r"\brequire\(\s*[\"']([^\"']+)[\"']\s*\)",
        r"\bimport\(\s*[\"']([^\"']+)[\"']\s*\)",
        r"@(?:import|use|forward)\s+(?:url\()?\s*[\"']([^\"']+)[\"']",
        r"^\s*(?:from\s+([.A-Za-z_][\w.]*)\s+import|import\s+([.A-Za-z_][\w.]*))",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            found.update(value for value in match.groups() if value)
    return sorted(found)


def normalize_relative(base: str) -> str:
    normalized = str(PurePosixPath(base))
    while normalized.startswith("../"):
        normalized = normalized[3:]
    return normalized.removeprefix("./")


def resolve_import(source: str, specifier: str, known_files: set[str]) -> dict[str, str]:
    if not specifier.startswith("."):
        parts = specifier.split("/")
        return {"external": "/".join(parts[:2]) if specifier.startswith("@") else parts[0]}
    # Python relative imports use dots rather than file-system separators:
    # ``from .util import value`` resolves beside the importing module, while
    # ``from ..shared import value`` resolves one package higher.
    if "/" not in specifier and re.fullmatch(r"\.+(?:[A-Za-z_][\w.]*)?", specifier):
        leading = len(specifier) - len(specifier.lstrip("."))
        parent = PurePosixPath(source).parent
        for _ in range(max(leading - 1, 0)):
            parent = parent.parent
        remainder = specifier[leading:].replace(".", "/")
        base = normalize_relative(str(parent / remainder))
    else:
        base = normalize_relative(str(PurePosixPath(source).parent / specifier))
    candidates = [f"{base}{extension}" for extension in RESOLVE_EXTENSIONS]
    candidates += [f"{base}/index{extension}" for extension in RESOLVE_EXTENSIONS[1:]]
    target = next((candidate for candidate in candidates if candidate in known_files), None)
    return {"target": target} if target else {"unresolved": specifier}


def create_snapshot(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    excludes = config.get("exclude", []) if isinstance(config.get("exclude", []), list) else []
    maximum = config.get("maxFileBytes", 2 * 1024 * 1024)
    if not isinstance(maximum, int) or maximum < 1024 or maximum > 64 * 1024 * 1024:
        raise ValueError("config.maxFileBytes must be between 1024 and 67108864")
    paths = walk(root, excludes)
    known_files = set(paths)
    details = [file_info(root, path, maximum) for path in paths]
    membership: dict[str, list[str]] = {}
    uncovered: list[str] = []
    overlaps: list[dict[str, Any]] = []
    for detail in details:
        owners = [module["id"] for module in config["modules"] if matches(detail["path"], module["paths"])]
        membership[detail["path"]] = owners
        if not owners:
            uncovered.append(detail["path"])
        if len(owners) > 1:
            overlaps.append({"path": detail["path"], "modules": owners})
    inferred = {module["id"]: set() for module in config["modules"]}
    external = {module["id"]: set() for module in config["modules"]}
    records: list[dict[str, Any]] = []
    for detail in details:
        imports = [] if detail["content"] is None else extract_imports(detail["content"], Path(detail["path"]).suffix.lower())
        resolved = [{"specifier": item, **resolve_import(detail["path"], item, known_files)} for item in imports]
        owners = membership[detail["path"]]
        if len(owners) == 1:
            owner = owners[0]
            for item in resolved:
                if "target" in item:
                    target_owners = membership.get(item["target"], [])
                    if len(target_owners) == 1 and target_owners[0] != owner:
                        inferred[owner].add(target_owners[0])
                elif "external" in item:
                    external[owner].add(item["external"])
        records.append({key: detail[key] for key in ("path", "bytes", "lines", "hash", "oversized")} | {"modules": owners, "imports": resolved})
    records.sort(key=lambda item: item["path"])
    known_modules = {module["id"] for module in config["modules"]}
    modules: list[dict[str, Any]] = []
    for module in config["modules"]:
        owned = [record for record in records if module["id"] in record["modules"]]
        explicit = sorted(set(module.get("dependencies", [])))
        inferred_dependencies = sorted(inferred[module["id"]])
        dependencies = sorted((set(explicit) | set(inferred_dependencies)) - {module["id"]})
        modules.append({
            "id": module["id"], "label": module["label"], "layer": module["layer"], "description": module["description"], "paths": module["paths"],
            "entryPoints": sorted(set(module.get("entryPoints", []))), "dependencies": [item for item in dependencies if item in known_modules],
            "explicitDependencies": explicit, "inferredDependencies": inferred_dependencies, "usedBy": [], "externalDependencies": sorted(external[module["id"]]),
            "fileCount": len(owned), "lines": sum(record["lines"] for record in owned), "files": sorted(record["path"] for record in owned),
        })
    for module in modules:
        module["usedBy"] = sorted(candidate["id"] for candidate in modules if module["id"] in candidate["dependencies"])
    config_hash = hashlib.sha256(stable_json(config).encode()).hexdigest()
    fingerprint_input = "\n".join([f"config\0{config_hash}", *(f"{record['path']}\0{record['hash']}" for record in records)])
    return {
        "version": 1, "project": config["project"], "description": config.get("description", ""), "configHash": config_hash,
        "fingerprint": hashlib.sha256(fingerprint_input.encode()).hexdigest(),
        "totals": {"files": len(records), "lines": sum(record["lines"] for record in records), "modules": len(modules), "uncovered": len(uncovered), "overlaps": len(overlaps)},
        "entryPoints": sorted(set(config.get("entryPoints", []))), "modules": modules, "uncoveredFiles": sorted(uncovered), "overlaps": overlaps,
        "warnings": [{"path": detail["path"], "reason": f"content exceeds {maximum} bytes; imports not inspected"} for detail in details if detail["oversized"]], "files": records,
    }


def markdown_text(value: Any) -> str:
    return re.sub(r"[\r\n]+", " ", str(value).replace("<", "&lt;").replace(">", "&gt;"))


def code_text(value: Any) -> str:
    return str(value).replace("`", "\\`")


def markdown(snapshot: dict[str, Any]) -> str:
    totals = snapshot["totals"]
    lines = [f"# {markdown_text(snapshot['project'])} workspace map", "", markdown_text(snapshot["description"]), "", f"Fingerprint: `{snapshot['fingerprint'][:16]}` · {totals['modules']} modules · {totals['files']} files · {totals['lines']} lines", "", "## Start here", ""]
    lines += [f"- `{code_text(item)}`" for item in snapshot["entryPoints"]] or ["- No repository entry points declared."]
    lines += ["", "## Module graph", ""]
    for layer in dict.fromkeys(module["layer"] for module in snapshot["modules"]):
        lines += [f"### {markdown_text(layer)}", ""]
        for module in (item for item in snapshot["modules"] if item["layer"] == layer):
            deps = ", ".join(f"`{item}`" for item in module["dependencies"]) or "none"
            used_by = ", ".join(f"`{item}`" for item in module["usedBy"]) or "none"
            lines += [f"#### {markdown_text(module['label'])} (`{code_text(module['id'])}`)", "", markdown_text(module["description"]), "", f"- Owns: {module['fileCount']} files, {module['lines']} lines", f"- Paths: {', '.join(f'`{code_text(item)}`' for item in module['paths'])}", f"- Depends on: {deps}", f"- Used by: {used_by}"]
            if module["entryPoints"]:
                lines.append(f"- Entry points: {', '.join(f'`{item}`' for item in module['entryPoints'])}")
            if module["externalDependencies"]:
                lines.append(f"- External packages: {', '.join(f'`{item}`' for item in module['externalDependencies'])}")
            lines.append("")
    lines += ["## Coverage", ""]
    if not snapshot["uncoveredFiles"] and not snapshot["overlaps"]:
        lines += ["Every mapped file has exactly one module owner.", ""]
    if snapshot["uncoveredFiles"]:
        lines += [f"### Uncovered files ({len(snapshot['uncoveredFiles'])})", "", *(f"- `{item}`" for item in snapshot["uncoveredFiles"]), ""]
    if snapshot["overlaps"]:
        lines += [f"### Overlapping ownership ({len(snapshot['overlaps'])})", "", *(f"- `{item['path']}`: {', '.join(f'`{name}`' for name in item['modules'])}" for item in snapshot["overlaps"]), ""]
    lines += ["## Agent navigation", "", "Use the module IDs above to query `.codemap/map.json`, then open source files for exact implementation details. Refresh the map after structural changes.", ""]
    return "\n".join(lines)


def html_document(snapshot: dict[str, Any]) -> str:
    data = json_text(snapshot).replace("<", "\\u003c")
    title = html.escape(str(snapshot["project"]))
    description = html.escape(str(snapshot["description"]))
    totals = snapshot["totals"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>{title} workspace map</title><style>
:root{{color-scheme:dark;--bg:#0b1020;--panel:#121a2e;--line:#51617f;--text:#edf2ff;--muted:#9cabca;--accent:#7dd3fc}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 ui-sans-serif,system-ui,sans-serif}}header{{position:sticky;top:0;z-index:5;padding:20px 24px;background:#0b1020ee;border-bottom:1px solid #24304a}}h1{{margin:0;font-size:22px}}header p{{margin:5px 0;color:var(--muted)}}input{{width:min(440px,100%);margin-top:10px;padding:9px 12px;border:1px solid #354461;border-radius:8px;background:#0f172a;color:var(--text)}}main{{position:relative;padding:24px;overflow:auto}}.layers{{position:relative;z-index:2;display:flex;gap:18px;min-width:max-content}}.layer{{width:280px}}.layer h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}.node{{width:100%;margin:10px 0;padding:14px;border:1px solid #34425f;border-radius:10px;background:var(--panel);color:var(--text);text-align:left;cursor:pointer}}.node:hover,.node:focus{{border-color:var(--accent)}}.node strong{{display:block}}.node small{{color:var(--muted)}}svg{{position:absolute;inset:24px;z-index:1;overflow:visible;pointer-events:none}}aside{{position:fixed;right:20px;bottom:20px;width:min(420px,calc(100vw - 40px));max-height:55vh;overflow:auto;padding:16px;border:1px solid #405171;border-radius:12px;background:#10182b}}aside[hidden]{{display:none}}aside button{{float:right;background:none;border:0;color:var(--text);font-size:20px;cursor:pointer}}code{{color:#bae6fd}}</style></head><body><header><h1>{title} workspace map</h1><p>{description} · {totals['modules']} modules · {totals['files']} files · {totals['lines']} lines</p><input id="search" aria-label="Filter modules" placeholder="Filter modules, paths, or descriptions"></header><main><svg id="edges" aria-hidden="true"></svg><div class="layers" id="layers"></div></main><aside id="detail" hidden><button id="close" aria-label="Close details">×</button><div id="detailBody"></div></aside><script>
const map={data},layers=document.querySelector('#layers'),detail=document.querySelector('#detail'),body=document.querySelector('#detailBody'),search=document.querySelector('#search');
function show(m){{body.textContent='';for(const [label,values] of [['Module',[m.id]],['Paths',m.paths],['Dependencies',m.dependencies.length?m.dependencies:['none']],['Used by',m.usedBy.length?m.usedBy:['none']],['Files',m.files]]){{const p=document.createElement('p'),b=document.createElement('b');b.textContent=label;p.append(b,document.createElement('br'));values.forEach((v,i)=>{{if(i)p.append(document.createElement('br'));const c=document.createElement('code');c.textContent=v;p.append(c)}});body.append(p)}}detail.hidden=false}}
function draw(){{const svg=document.querySelector('#edges'),main=document.querySelector('main').getBoundingClientRect();svg.textContent='';for(const m of map.modules){{const a=document.querySelector('[data-id="'+CSS.escape(m.id)+'"]');if(!a)continue;for(const id of m.dependencies){{const b=document.querySelector('[data-id="'+CSS.escape(id)+'"]');if(!b)continue;const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect(),line=document.createElementNS('http://www.w3.org/2000/svg','path'),x1=ar.right-main.left,y1=ar.top+ar.height/2-main.top,x2=br.left-main.left,y2=br.top+br.height/2-main.top;line.setAttribute('d','M '+x1+' '+y1+' C '+(x1+x2)/2+' '+y1+', '+(x1+x2)/2+' '+y2+', '+x2+' '+y2);line.setAttribute('fill','none');line.setAttribute('stroke','#51617f');line.setAttribute('stroke-width','1.5');svg.append(line)}}}}
function render(q=''){{layers.textContent='';const n=q.toLowerCase();for(const layer of [...new Set(map.modules.map(m=>m.layer))]){{const col=document.createElement('section');col.className='layer';const h=document.createElement('h2');h.textContent=layer;col.append(h);for(const m of map.modules.filter(x=>x.layer===layer)){{if(n&&![m.id,m.label,m.description,...m.paths,...m.files].join(' ').toLowerCase().includes(n))continue;const b=document.createElement('button');b.className='node';b.dataset.id=m.id;const strong=document.createElement('strong'),small=document.createElement('small');strong.textContent=m.label;small.textContent=m.id+' · '+m.fileCount+' files · '+m.lines+' lines';b.append(strong,small);b.onclick=()=>show(m);col.append(b)}}if(col.children.length>1)layers.append(col)}}requestAnimationFrame(draw)}}
search.oninput=()=>render(search.value);document.querySelector('#close').onclick=()=>detail.hidden=true;addEventListener('resize',draw);render();</script></body></html>'''


def write_atomic(file: Path, content: str) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_name(file.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(file)


def paths_for(root: Path, config_arg: str | None) -> tuple[Path, Path, Path, Path]:
    config = (root / (config_arg or ".codemap/config.json")).resolve()
    try:
        config.relative_to(root)
    except ValueError as error:
        raise ValueError("config and generated outputs must stay inside the repository root") from error
    return config, config.parent / "map.json", config.parent / "WORKSPACE_MAP.md", config.parent / "workspace-map.html"


def load(root: Path, args: argparse.Namespace) -> tuple[tuple[Path, Path, Path, Path], dict[str, Any]]:
    locations = paths_for(root, args.config)
    config = read_json(locations[0])
    validate_config(config)
    return locations, create_snapshot(root, config)


def build(root: Path, args: argparse.Namespace) -> int:
    locations, snapshot = load(root, args)
    write_atomic(locations[1], json_text(snapshot, pretty=True) + "\n")
    write_atomic(locations[2], markdown(snapshot))
    write_atomic(locations[3], html_document(snapshot))
    print(json_text({"status": "built", "fingerprint": snapshot["fingerprint"], "totals": snapshot["totals"], "outputs": [str(path) for path in locations[1:]]}, pretty=True))
    return 0


def check(root: Path, args: argparse.Namespace) -> int:
    locations, snapshot = load(root, args)
    if not locations[1].exists():
        raise ValueError(f"map does not exist: {locations[1]}")
    previous = read_json(locations[1])
    before = {item["path"]: item["hash"] for item in previous.get("files", [])}
    after = {item["path"]: item["hash"] for item in snapshot["files"]}
    result = {"status": "current" if previous.get("fingerprint") == snapshot["fingerprint"] else "stale", "added": sorted(after.keys() - before.keys()), "changed": sorted(item for item in after if item in before and after[item] != before[item]), "removed": sorted(before.keys() - after.keys()), "uncoveredFiles": snapshot["uncoveredFiles"], "overlaps": snapshot["overlaps"]}
    print(json_text(result, pretty=True))
    return 2 if result["status"] == "stale" or result["uncoveredFiles"] or result["overlaps"] else 0


def query(root: Path, args: argparse.Namespace) -> int:
    locations = paths_for(root, args.config)
    if not locations[1].exists():
        raise ValueError(f"map does not exist: {locations[1]}")
    snapshot = read_json(locations[1])
    if args.module:
        item = next((module for module in snapshot["modules"] if module["id"] == args.module), None)
        if not item: raise ValueError(f"unknown module: {args.module}")
        output: Any = item
    elif args.file:
        requested = posix(args.file)
        item = next((file for file in snapshot["files"] if file["path"] == requested), None)
        if not item: raise ValueError(f"file is not mapped: {requested}")
        output = {"file": item, "modules": [module for module in snapshot["modules"] if module["id"] in item["modules"]]}
    elif args.entry_points:
        output = {"repository": snapshot["entryPoints"], "modules": [{"id": module["id"], "entryPoints": module["entryPoints"]} for module in snapshot["modules"] if module["entryPoints"]]}
    elif args.search:
        needle = args.search.lower()
        output = [module for module in snapshot["modules"] if needle in " ".join([module["id"], module["label"], module["layer"], module["description"], *module["paths"], *module["files"]]).lower()]
    else:
        output = [{key: module[key] for key in ("id", "label", "layer", "description", "dependencies", "fileCount", "lines")} for module in snapshot["modules"]]
    print(json_text(output, pretty=True))
    return 0


class CodemapArgumentParser(argparse.ArgumentParser):
    """Keep CLI misuse on the tool's documented exit-code-1 error path."""

    def error(self, message: str) -> None:
        raise ValueError(message)


def main() -> int:
    usage = "codemap.py <build|check|query> --root <repository> [--config path] [--module id|--file path|--entry-points|--search keyword]"
    parser = CodemapArgumentParser(prog="codemap.py", usage=usage)
    parser.add_argument("command", nargs="?", choices=("build", "check", "query"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--config")
    parser.add_argument("--module")
    parser.add_argument("--file")
    parser.add_argument("--search")
    parser.add_argument("--entry-points", action="store_true")
    args = parser.parse_args()
    if not args.command:
        raise ValueError(f"usage: {usage}")
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise ValueError(f"root is not a directory: {root}")
    return {"build": build, "check": check, "query": query}[args.command](root, args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(fail(str(error)))
