# Layerlift Agent Kit workspace map

A local, multi-agent Figma-to-HTML workflow with immutable run state and four independent release gates.

Fingerprint: `4bb87e0ebfa4749c` · 10 modules · 80 files · 8698 lines

## Start here

- `.claude/skills/build-figma-page/SKILL.md`
- `scripts/kit.py`
- `scripts/serve.py`
- `scripts/validate-kit.py`

## Module graph

### Instructions

#### Governance and guidance (`governance`)

Defines repository purpose, commands, security boundaries, and guideline precedence.

- Owns: 20 files, 2228 lines
- Paths: `AGENTS.md`, `CLAUDE.md`, `README.md`, `PROJECT_REFERENCE.md`, `guidelines/**`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`, `.mcp.json`
- Depends on: none
- Used by: `artifact-contracts`, `codemap-skill`, `figma-workflow-skill`, `frontend-design-skills`, `project-workspaces`, `state-controller`
- Entry points: `AGENTS.md`, `README.md`

### Agent workflow

#### Figma workflow skill (`figma-workflow-skill`)

Orchestrates Figma extraction, candidate construction, independent QA, repair, and release.

- Owns: 10 files, 835 lines
- Paths: `.claude/skills/build-figma-page/**`
- Depends on: `artifact-contracts`, `frontend-design-skills`, `governance`, `host-adapters`, `render-and-qa`, `state-controller`, `validation-and-tests`
- Used by: `host-adapters`, `project-workspaces`, `validation-and-tests`
- Entry points: `.claude/skills/build-figma-page/SKILL.md`

#### Codemap skill (`codemap-skill`)

Builds and queries the durable workspace map used for repository orientation.

- Owns: 4 files, 588 lines
- Paths: `.claude/skills/codemap/**`
- Depends on: `governance`
- Used by: `validation-and-tests`
- Entry points: `.claude/skills/codemap/SKILL.md`, `.claude/skills/codemap/scripts/codemap.py`
- External packages: `__future__`, `argparse`, `hashlib`, `html`, `json`, `os`, `pathlib`, `re`, `sys`, `typing`

#### Frontend design skills (`frontend-design-skills`)

Provides optional design-direction guidance and Vercel interface-review rules for matching frontend tasks.

- Owns: 2 files, 1247 lines
- Paths: `.claude/skills/taste-skill/**`, `.claude/skills/web-design-guidelines/**`
- Depends on: `governance`
- Used by: `figma-workflow-skill`, `validation-and-tests`
- Entry points: `.claude/skills/taste-skill/SKILL.md`, `.claude/skills/web-design-guidelines/SKILL.md`

#### Claude adapter (`host-adapters`)

Configures Claude subagent roles and skills.

- Owns: 10 files, 252 lines
- Paths: `.claude/agents/**`, `.claude/settings.json`, `.claude/state/**`
- Depends on: `figma-workflow-skill`
- Used by: `figma-workflow-skill`, `validation-and-tests`
- Entry points: `.claude/settings.json`

### Deterministic runtime

#### Lifecycle state controller (`state-controller`)

Creates and transitions projects, pages, sources, runs, candidates, QA records, and releases.

- Owns: 2 files, 608 lines
- Paths: `scripts/kit.py`, `scripts/log-agent-event.py`
- Depends on: `artifact-contracts`, `governance`
- Used by: `figma-workflow-skill`, `project-workspaces`, `render-and-qa`, `validation-and-tests`
- Entry points: `scripts/kit.py`
- External packages: `__future__`, `copy`, `datetime`, `json`, `os`, `pathlib`, `re`, `sys`, `urllib.parse`

#### Artifact contracts (`artifact-contracts`)

Defines machine-readable schemas and example structures for sources, runs, specifications, content, and QA.

- Owns: 10 files, 416 lines
- Paths: `schemas/**`, `templates/**`
- Depends on: `governance`
- Used by: `figma-workflow-skill`, `project-workspaces`, `render-and-qa`, `state-controller`, `validation-and-tests`

#### Rendering and QA evidence (`render-and-qa`)

Serves and renders candidates, measures browser output, compares pixels, verifies accepted evidence, and generates the four human-reviewer QA DOCX deliverables (overview, design, content, coding).

- Owns: 9 files, 1284 lines
- Paths: `scripts/render-page.py`, `scripts/serve.py`, `scripts/browser-summary.py`, `scripts/visual-diff.py`, `scripts/visual-summary.py`, `scripts/verify-output.py`, `scripts/measure-footer.py`, `scripts/crop-bands.py`, `scripts/create-qa-docs.py`, `qa-reports/**`
- Depends on: `artifact-contracts`, `state-controller`
- Used by: `figma-workflow-skill`, `validation-and-tests`
- Entry points: `scripts/create-qa-docs.py`, `scripts/render-page.py`, `scripts/serve.py`, `scripts/verify-output.py`
- External packages: `PIL`, `__future__`, `asyncio`, `datetime`, `docx`, `docx.enum.text`, `docx.oxml`, `docx.oxml.ns`, `docx.shared`, `html`, `http.server`, `json`, `mimetypes`, `os`, `pathlib`, `pixelmatch.contrib.PIL`, `playwright.async_api`, `re`, `render_page`, `sys`, `threading`, `typing`, `urllib.parse`

### Verification

#### Validation and tests (`validation-and-tests`)

Checks repository integrity and exercises lifecycle invariants and mapping behavior.

- Owns: 13 files, 1240 lines
- Paths: `scripts/validate-kit.py`, `tests/**`
- Depends on: `artifact-contracts`, `codemap-skill`, `figma-workflow-skill`, `frontend-design-skills`, `host-adapters`, `render-and-qa`, `state-controller`
- Used by: `figma-workflow-skill`
- Entry points: `scripts/validate-kit.py`
- External packages: `PIL`, `__future__`, `conftest`, `datetime`, `hashlib`, `json`, `pathlib`, `pytest`, `shutil`, `subprocess`, `sys`

### Mutable artifacts

#### Project workspaces (`project-workspaces`)

Provides the versioned template for project-local guideline workspaces while runtime project state remains outside the architecture map.

- Owns: 0 files, 0 lines
- Paths: `projects/_template/**`
- Depends on: `artifact-contracts`, `figma-workflow-skill`, `governance`, `state-controller`
- Used by: none

## Coverage

Every mapped file has exactly one module owner.

## Agent navigation

Use the module IDs above to query `.codemap/map.json`, then open source files for exact implementation details. Refresh the map after structural changes.
