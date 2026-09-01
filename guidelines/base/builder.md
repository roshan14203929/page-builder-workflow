# Builder defaults

- Produce exactly `images/`, `index.html`, `base.css`, and `page.css` as the deployable output.
- Keep global element and token rules in `base.css`; keep page and component rules in `page.css`.
- Use semantic HTML and native controls before ARIA.
- Use CSS custom properties for repeated source tokens.
- Use Grid and Flexbox based on the extracted layout rather than absolute
  positioning except where the source genuinely requires layering.
- Keep selectors shallow and component-scoped.
- Store local assets in `images/` and use relative URLs.
- Implement responsive behavior from supplied variants; interpolate
  conservatively between them without hiding required content.
- When only one variant is supplied, preserve that variant's source intent and
  add only a conservative technical baseline. Do not invent an unsupplied
  mobile or desktop composition. A fixed-layout document may preserve a
  readable source canvas within a contained scroller instead of shrinking or
  redesigning its content.
- Do not use inline styles, `!important`, remote scripts, trackers, frameworks,
  or fabricated placeholder copy.
- Keep each semantic section independently replaceable for focused repairs.
- Use `design-taste-frontend` only when the orchestrator routes it for a landing
  page, portfolio, marketing/editorial page, or redesign. State a one-line
  Design Read and apply it only to choices the source leaves unspecified.
- Exact Figma copy, geometry, tokens, assets, variants, user decisions, and
  these effective guidelines override Taste guidance. Taste must not introduce
  dependencies, remote resources, generated assets, or fabricated content.

## CSS naming and values

- Use BEM class naming: `.block`, `.block__element`, and `.block--modifier`.
- Use hyphens rather than underscores in block and element names.
- Do not encode position or surrounding context in a class name.
- For pages embedded in an external template or CMS, prefix every authored
  class with `cst-` to avoid selector collisions.
- Define colors as `:root` custom properties; do not hardcode hex colors outside
  `:root`.
- Use padding for space between content and its own box edges; use margin for
  space between sibling boxes.
- Use `:root` spacing variables for structural padding, margin, and layout gap.
  Small one-off fine-tuning values do not require variables.
- Use `rem` for font sizes. Do not use `clamp()` for font sizing; use explicit
  breakpoints for viewport-specific sizes.
- Use unitless `line-height` values.
- Remove an earlier declaration when the same property is declared twice in a
  selector.
- Do not use `!important`; remove the conflicting inline style or cascade issue
  that made it appear necessary.

## CSS architecture and hygiene

- Put global element rules such as `img`, `ul`, and `body` in `base.css`, not a
  page-specific stylesheet, when the project uses that split.
- Do not duplicate selectors. Consolidate the rules and remove earlier
  overridden declarations.
- In media-query overrides, include only properties whose values change; do
  not repeat the complete base rule.
- Merge overlapping media queries that assign the same values.
- Give every section used as a table-of-contents or in-page anchor target a
  `scroll-margin-top` equal to the actual fixed-header height so the target is
  not obscured after navigation.
- Delete commented-out CSS and remove or correct comments that no longer match
  the code they describe.
