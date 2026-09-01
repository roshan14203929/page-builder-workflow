# Orchestration

## State machine

Use `scripts/kit.py` for every state transition.

```text
source: EXTRACTING -> READY | FAILED
run: CREATED -> BUILDING -> VERIFYING -> COMPLETED
                           -> REFINING -> VERIFYING
                           -> NEEDS_REVIEW | FAILED
```

`COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal. Start a new run instead
of reopening one.

## Delegation sequence

1. Apply `source-reuse.md`. Request the source with one
   `--variant <label>=<url>` per supplied frame. If the controller returns
   `reused: true`, do not invoke extraction. When the user identifies changed
   nodes, create an incremental source from the current READY source and invoke
   `figma_extractor` / `figma-extractor` only for those nodes. For a genuinely
   new source, it owns only that source directory. Require it to record
   `page.variantScope`; supplied frames define fidelity scope and missing
   counterparts are not inferred.
2. Apply the routing rules in `design-skills.md` to the normalized source. Tell
   the builder whether Design Taste is applicable and why.
3. Create a run and a candidate. Invoke `page_builder` / `page-builder` alone.
   When routed, explicitly invoke `design-taste-frontend` in its handoff. It
   owns only that candidate directory.
4. Run deterministic static validation, browser rendering, and visual metrics.
5. Accept or reject the candidate. Copying into `generated/` is performed by
   `candidate-result`, not by a reviewer.
6. Fetch the Web Interface Guidelines source once for the run, then invoke
   content, UI, accessibility, and technical reviewers. Pass that single
   fetched document and its provenance to the UI and accessibility reviewers
   as described in `design-skills.md`; they must not fetch it themselves.
   Reuse the same fetch across repair rounds. Include `page.variantScope` in
   each handoff so unsupplied widths remain diagnostic unless explicitly
   required. They are
   read-only and return one QA JSON object each. The main agent records them.
7. Invoke `release_verifier` / `release-verifier` after the summary passes and
   record its verdict with `release-check`.
8. On failure, create a new candidate with `--from-accepted`, then invoke
   `repair_builder` / `repair-builder` with only failed
   findings, the current accepted output, reference evidence, and affected
   sections. It owns only a new candidate directory.

## Parallelism

Parallelize independent read-heavy reviewers. Wait for every reviewer before
aggregating. Do not parallelize builders that would modify the same candidate,
generated directory, page record, or run record. If sections are built in
parallel, give every worker a separate candidate subdirectory and let the main
agent assemble them deterministically.

## Candidate decision

Reject a candidate when static validation fails, required content is missing,
the browser reports console/network/overflow failures, or visual metrics are
unavailable. `candidate-result --status accepted` mechanically requires
passing static, browser, and aggregate visual reports.

For a repair candidate, compare it with the last accepted candidate:

- Reject if full-page difference regresses by more than 0.10 percentage points.
- Reject if peak-band difference regresses by more than 0.10 points.
- After repair round one, require at least 0.20 points of improvement in
  full-page or peak-band difference unless the targeted nonvisual failure is
  demonstrably fixed without visual regression.
- Preserve the previous accepted output byte-for-byte after rejection.

## Stop conditions

Stop and request user input when Figma is ambiguous, guidelines conflict with
the source, source variants contradict one another, essential assets are
unavailable, or changing copy/design intent is required.

Stop automatically and mark `NEEDS_REVIEW` when the configured repair cap is
reached, two consecutive candidates yield no meaningful improvement, a
required reviewer is unavailable, or an unresolved critical/high finding
remains.
