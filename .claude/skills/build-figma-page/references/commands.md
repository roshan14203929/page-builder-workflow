# Commands

Run from the kit root.

```bash
python scripts/kit.py init-project <project> "<name>"
python scripts/kit.py init-page <project> <page> "<name>"
python scripts/kit.py new-source <project> <page> --variant desktop=<url> --variant mobile=<url>
python scripts/kit.py new-source <project> <page> --from-source <source> --changed-node desktop=<node-id> --reason "<change>"
python scripts/kit.py source-budget <project> <page> <source>
python scripts/kit.py source-call <project> <page> <source> --operation <name> --status <SUCCESS|TRANSIENT_ERROR|AUTH_ERROR|RATE_LIMITED|FAILED> [--node <node-id>] [--retry-after <seconds>]
python scripts/kit.py source-patch <project> <page> <source> --file <patch.json>
python scripts/kit.py resolve-question <project> <page> <source> --question <id> --decision "<user decision>" --by user
python scripts/kit.py source-ready <project> <page> <source>
python scripts/kit.py spec-compact <project> <page> <source>
python scripts/kit.py inventory <project> <page> <source> --sections
python scripts/kit.py inventory <project> <page> <source> [--variant <label>] [--section <id>] [--kind <kind>] [--node <node-id>] [--id <item-id>] [--text <substring>] [--required] [--fields id,kind,text|all] [--limit <n>] [--offset <n>]
python scripts/kit.py source-fail <project> <page> <source> --message "<reason>"
python scripts/kit.py guidelines <project> <page> [--role builder|extractor|ui|content|accessibility|technical]
python scripts/kit.py new-run <project> <page> --source <source>
python scripts/kit.py transition <project> <page> <run> BUILDING
python scripts/kit.py new-candidate <project> <page> <run> --round 0 --scope full-page
python scripts/verify-output.py --root <candidate-dir> --inventory <inventory> --output <report>
python scripts/render-page.py --root <candidate-dir> --output <candidate.png> --width <width> --height <height> --full-page false
python scripts/browser-summary.py --report <desktop.png.json> --report <mobile.png.json> --output <browser-summary.json>
python scripts/visual-diff.py --reference <reference.png> --candidate <candidate.png> --output <visual-review.json>
python scripts/crop-bands.py --report <desktop-diff.json> --output <desktop-crops.json> [--regions 3] [--pad 40] [--min-difference 5]
python scripts/visual-summary.py --report <desktop-review.json> --report <mobile-review.json> --output <visual-summary.json>
python scripts/kit.py candidate-result <project> <page> <run> <candidate> --status accepted --static <static.json> --browser <browser-summary.json> --metrics <visual-summary.json>
python scripts/kit.py transition <project> <page> <run> VERIFYING
python scripts/kit.py qa-record <project> <page> <run> <kind> --file <qa.json>
python scripts/kit.py qa-summary <project> <page> <run>
python scripts/kit.py transition <project> <page> <run> REFINING
python scripts/kit.py next-repair <project> <page> <run>
python scripts/kit.py new-candidate <project> <page> <run> --round <N> --scope <section> --from-accepted
python scripts/kit.py release-check <project> <page> <run> --file <release-verdict.json>
python scripts/kit.py release <project> <page> <run>
python scripts/kit.py needs-review <project> <page> <run> --message "<reason>"
python scripts/kit.py fail <project> <page> <run> --message "<reason>"
python scripts/create-qa-docs.py <TICKET>
```

`create-qa-docs.py <TICKET>` generates four human-reviewer DOCX files under
`qa-reports/<TICKET>/`: `<TICKET>_overview-qa.docx` (Chapter 1 — project cover
sheet and sign-off), `<TICKET>_design-qa.docx` (Chapter 2 — WF vs Design diff),
`<TICKET>_content-qa.docx` (Chapter 3 — copy accuracy, Design vs HTML), and
`<TICKET>_coding-qa.docx` (Chapter 4 — typography metrics and guideline
compliance). Run this once at the start of the QA phase. Blank templates with the
`TICKET-ID` placeholder are kept at `qa-reports/` root for reference.

The browser summary has the same `{ "status": "PASS|FAIL" }` top-level shape
as a single render report and may aggregate several viewport render reports.
The `release` command requires the run to be `VERIFYING`, current-candidate
passing reports for all four QA kinds, a matching recorded release-verifier
verdict, and the exact generated payload: `images/`, `index.html`, `base.css`,
and `page.css`.

`guidelines` resolves the global, base, project, and page layers in precedence
order. With `--role` it includes only that role's file from `guidelines/base/`,
which is how every agent should read its guidelines. `new-run` still writes the
unscoped snapshot to `effective-guidelines.md`, so release evidence stays
complete.

`crop-bands.py` reads a `visual-diff.py` report, fuses its adjacent `worstBands`
into coherent regions, and writes native-resolution reference/candidate/diff
crops for the worst ones. Use it for pixel judgements; a full-page reference is
downscaled too far to read.

`source-ready` normalizes `spec/spec.json` and `spec/content-inventory.json`
losslessly and reports the byte change; `spec-compact` applies the same
normalization on demand. Prefer `inventory` slices over reading
`spec/content-inventory.json` in full, and never read `raw/figma-*.json`.
