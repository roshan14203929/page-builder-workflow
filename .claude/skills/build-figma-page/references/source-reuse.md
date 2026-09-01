# Source reuse and incremental extraction

## Decision rule

- CSS, HTML, interaction, responsive, or accessibility repairs create a new
  candidate in the same run. They never create a source.
- A fresh guideline snapshot or a terminal prior attempt creates a new run
  against the same READY source.
- Create a source only when Figma evidence changed or the stored extraction is
  defective.
- When the user supplies the changed node IDs, derive an incremental source
  from the current READY source instead of extracting every frame again.

## Duplicate protection

`new-source` canonicalizes supplied variants by file key, node ID, and label;
transient URL parameters such as `t` do not affect identity.

- An identical READY source is returned with `reused: true`; do not invoke an
  extractor.
- An identical EXTRACTING or FAILED source blocks accidental duplication.
- A deliberate repeat requires `--force-new --reason <text>`.

Do not use force-new to obtain another candidate or retry visual/CSS work.

## Incremental source workflow

Create a derived source with one or more changed nodes:

```bash
python scripts/kit.py new-source <project> <page> \
  --from-source source-001 \
  --changed-node desktop=8099:10395 \
  --reason "Safety section copy and color changed"
```

The controller clones the base artifacts locally, records source lineage, and
marks references for affected variants `STALE`. The extractor fetches only the
declared nodes plus the minimum parent, shared-variable, or asset evidence
needed to normalize them. It writes a version-1 patch matching
`schemas/source-patch.schema.json`, then the orchestrator applies it:

```bash
python scripts/kit.py source-patch <project> <page> <source> --file <patch.json>
```

The patch deterministically replaces changed sections and content, updates
assets and token groups, copies declared raw/asset/reference files, and records
call provenance. A genuinely new section must declare `insertBefore` or
`insertAfter`. Unchanged source records remain byte-identical.

## References and rate limits

Every visually affected supplied variant needs a refreshed full-frame
reference before the derived source can become READY. Prefer a user-supplied
reference when available; otherwise make at most one required render request
per affected variant. A targeted node screenshot may guide repair but does not
replace the release reference.

Run `source-budget` immediately before Figma work; when it returns
`allowed: false`, make no Figma call. Record every material Figma operation
with `source-call`. On `RATE_LIMITED`, record `retryAfterSeconds`, stop, and
leave the source EXTRACTING. Do not create
another source or retry before the recorded window. Authorization errors are
also non-retryable without an external access change.

Use the backend selected by `figma-extraction.md`. Prefer MCP when it satisfies
the required capabilities; otherwise API mode may load `FIGMA_ACCESS_TOKEN`
from the process environment or untracked `.env.local`. Never persist or log
the token, and never create a new source merely to change extraction backends.
