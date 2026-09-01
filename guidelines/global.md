# Global workflow and quality guidelines

## Precedence

Resolve instructions in this order: this file, the matching file under
`guidelines/base/`, project guidelines, then page guidelines. Later rules may
override earlier rules only when they address the same requirement explicitly.
Write the resolved source list and SHA-256 hash into every run.

## Figma extraction

- Prefer the authenticated Figma MCP connection when it satisfies the required
  extraction capabilities. Use the read-only Figma REST API when MCP is
  unavailable, incomplete for the source, or explicitly required by the user.
- In API mode, load `FIGMA_ACCESS_TOKEN` only from the process environment or
  untracked `.env.local`; never print, persist, or pass it as a command argument.
- Reuse an identical READY source. Do not create sources for HTML, CSS,
  interaction, responsive, or accessibility repairs; those changes belong in
  candidates. New runs normally reuse the selected READY source.
- When the user identifies changed Figma nodes, derive an incremental source
  and fetch only those nodes plus the minimum dependent parent, variable, or
  asset evidence. Require an explicit reason and preserve base-source lineage.
- Record material Figma operations in the source call ledger. On a Figma rate
  limit, persist the retry window and stop without creating another source or
  retrying inside that window.
- Fetch each top-level frame once for extraction. Parse descendants locally.
- Fetch variables/styles once per file when the selected backend exposes them.
- Collect asset node identifiers during the tree walk and export assets in one
  bounded pass when supported.
- Export one reference screenshot for every supplied viewport variant.
- Persist the raw backend response, extraction-method record, normalized spec,
  content inventory, asset manifest, reference images, and extraction warnings
  in a new source folder.
- Treat supplied frames as the complete fidelity scope. Infer variant roles
  from explicit labels, frame names, dimensions, and matching content—not URL
  count alone—and record the classification with confidence and evidence.
- A single clearly wide frame is normally a desktop-only fidelity target; do
  not invent a mobile counterpart. For related wide and narrow frames,
  normally classify the widest as desktop and the narrowest as mobile.
- Never invent a missing value. Record ambiguity only in
  `spec/spec.json.openQuestions`; record user-approved resolutions in
  `spec/spec.json.decisions` through the state controller.

## Run immutability

- A source snapshot is immutable after it becomes `READY`.
- A run may change only while its status is nonterminal.
- `COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal.
- Start a new run for every fresh attempt or user-approved alternative.
- Preserve every generated candidate and record acceptance or rejection.

## QA gates

- Maximum automatic repair rounds: 3.
- Full-page maximum pixel difference: 5%.
- Maximum localized horizontal-band difference: 12%.
- Candidate regression tolerance: 0.10 percentage points.
- Meaningful improvement required after the first repair: 0.20 percentage
  points in either full-page or peak-band difference.
- Required checks: `content`, `ui`, `accessibility`, and `technical`.
- A missing or unavailable required check is not a pass.
- Do not average independent checks into a passing score. Every gate must pass.

## Candidate acceptance

- Validate HTML, CSS, asset references, and required content before rendering.
- Accept a repair only if it fixes its targeted failure without exceeding the
  regression tolerance elsewhere.
- Reject malformed or regressing candidates and preserve the last accepted
  artifact exactly.
- Stop when all gates pass, the repair cap is reached, no meaningful
  improvement occurs, required Figma data is unavailable, or a user decision
  is necessary.

## Content fidelity

- Preserve every required visible string exactly, including punctuation,
  capitalization, numerals, labels, legal copy, and calls to action.
- Do not add marketing copy, links, testimonials, prices, claims, or features
  not present in the source or explicitly requested.
- Do not omit visually present content because it appears repetitive.
- Record source text in `content-inventory.json` and verify the output against
  it mechanically before semantic review.

## UI fidelity

- Match hierarchy, geometry, spacing, alignment, typography, colors, borders,
  radii, shadows, opacity, gradients, imagery, and stacking.
- Render and inspect every supplied reference viewport.
- Perform blocking visual-fidelity and responsive-intent checks only at
  supplied variant widths. The 320, 375, 768, 1024, and 1440 pixel matrix is a
  baseline diagnostic for unsupplied widths unless the user or page guidelines
  explicitly require those widths; do not treat an absent mobile or desktop
  design as an implicit variant.
- At diagnostic-only widths, block only concrete technical or accessibility
  failures that are independent of an invented layout, such as unreachable
  controls, page-level accidental overflow, or hidden essential content. Do
  not fail UI solely because a desktop-only fixed-layout or image-document page
  preserves its source canvas instead of reflowing like a mobile design.
- Verify hover, focus-visible, active, disabled, menu, modal, and form states
  when those states exist.

## Accessibility and technical quality

- Use semantic landmarks and exactly one page-level `h1`.
- Preserve logical heading order and keyboard operation.
- Give controls accessible names and inputs associated labels.
- Provide useful alternative text for informative images and empty alt text for
  decorative images.
- Describe what an informative image shows, not its location or implementation
  role. For PNG content figures, use the nearest preceding `h3` or `h4` as the
  basis for the alternative text and verify that the result describes the
  figure accurately.
- Keep every `aria-label` in the page language.
- Never remove a focus outline without providing an equally visible
  replacement. Use `:focus-visible` for keyboard focus styles; do not combine
  `:hover` and `:focus` into one rule because they represent different input
  methods.
- Respect reduced-motion preferences and maintain visible focus indicators.
- Reserve media dimensions and prevent avoidable layout shifts.
- Reject broken local assets, console errors, failed local network requests,
  horizontal overflow, invalid document structure, and placeholder content.

## HTML and template delivery

- Treat delivery templates as read-only. Build and iterate in a separate file,
  then copy only finished code into the template's designated editable area.
  Never run a formatter over an entire delivery template.
- When available, rely on Prettier and `html-validate` for formatting, tag
  closing, doctype, charset, attribute quoting, and void-element validation;
  apply the rules below to requirements those tools do not cover.
- When XHTML is explicitly required, convert the completed HTML only as the
  final local step and manually compare the result with the project's
  XHTML-versus-HTML reference. Do not introduce an external model API for the
  conversion.
- Set the root `html[lang]` to the page language.
- Provide a unique, descriptive `title` of 45–65 characters and align it with
  the page `h1` content.
- Include exactly one `main` element containing the primary page content.
- Put a `.container` on a `div` inside a `section`, never on the `section`
  itself.

## Semantic HTML hygiene

- Use heading elements such as `h2` and `h3` for section titles; never style a
  `div` to act as a heading.
- Use exactly one `h1` and do not skip heading levels.
- Choose elements for semantic meaning rather than visual appearance. Use
  `strong` and `em` when emphasis is meaningful instead of `b` and `i`.
- Do not create spacer `div` elements; use CSS margin or padding.
- Do not leave empty elements, empty `class` attributes, or whitespace-only
  `class` attributes.
- Do not use inline `style` attributes. Move declarations into CSS classes.
- Delete commented-out HTML. If content is intentionally excluded, retain only
  a short explanatory HTML comment stating why instead of the full block.

## Image markup and loading

- Give every `img` explicit intrinsic numeric `width` and `height` attributes
  to reserve its aspect ratio and prevent cumulative layout shift. Use CSS for
  responsive sizing such as `width: 100%` and `height: auto`.
- Do not use `picture` or `source` for delivery content images. Wrap a single
  `img` in an `.img-wrapper` element and express supported responsive or HiDPI
  variants with `srcset` on that image.
- Use `loading="lazy"` for below-the-fold images. Use `loading="eager"` and
  `fetchpriority="high"` for the LCP or hero image.
- For retina assets, provide explicit `1x` and `2x` `srcset` candidates while
  retaining `src`, alternative text, loading mode, width, and height.
- Follow the provided local font templates. If an explicitly authorized
  template already uses Google Fonts, place preconnect links for
  `fonts.googleapis.com` and `fonts.gstatic.com` before its stylesheet link;
  do not introduce remote fonts when the workflow requires local-only output.

## Release

- Only the primary orchestrator may create `releases/v-###`.
- Release the exact accepted generated directory; do not rewrite it while
  copying.
- Include the run record, guideline snapshot, final QA summary, and checksums.

## Platform guidelines

Confirm the platform at ticket intake. MediChannel and HTML5 (M3, CareNet) have
mutually exclusive coding standards — building under the wrong ruleset means a
complete rebuild.

**MediChannel (XHTML 1.0 Strict, internal, 960 px)**

Apply all three of the following base guidelines together:

- `guidelines/base/xhtml-coding-rules.md` — XHTML 1.0 Strict syntax and CSS rules
- `guidelines/base/medichannel-delivery-standards.md` — file size, template,
  editable area, jQuery version, and delivery requirements
- `guidelines/base/xhtml-vs-html5-reference.md` — reference for any XHTML/HTML5
  conflicts encountered during build or QA

The QA workflow for MediChannel (Design QA, Content QA, and Coding QA) is
documented in `guidelines/base/az-html-qa-guide.md`.

Do not apply `html-coding-rules.md` to MediChannel work.

**M3.com / MedPeer and CareNet (HTML5, external)**

Apply:

- `guidelines/base/html-coding-rules.md` — HTML5 coding and CSS rules

Do not apply XHTML rules or MediChannel delivery requirements to these projects.
