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
- Keep each semantic section's HTML independently replaceable for focused
  repairs: self-contained `<section>` blocks with clear IDs. Shared CSS
  component classes may span sections — section isolation applies to the HTML,
  not the CSS.
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

## CSS component architecture

- HTML sections are independently replaceable DOM units for repair targeting.
  CSS components are shared classes used across multiple sections. These are
  separate concerns — do not confuse them.
- Before writing any section HTML, define shared component classes in `page.css`
  first: buttons, cards, tags, typography utilities, and any pattern that
  appears in more than one section.
- Express per-section differences as BEM modifiers on the component, not as
  descendant selectors: `.btn` defines the base and `.btn--hero` adjusts its
  size, rather than `.hero .btn`. This keeps selectors shallow and keeps the
  component readable on its own.
- Do not copy a component's full ruleset into a section block. Reference the
  shared component class and add a modifier only where the section genuinely
  differs; a modifier declares only the properties that change.
- Open `page.css` with a comment block listing the component vocabulary, so the
  next agent can see the intended shared classes before reading any selector.
  Keep it accurate — it is the one comment exempt from the deletion rule below,
  and every repair that adds or renames a component class updates it.

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
  the code they describe. The component-vocabulary block at the top of
  `page.css` is required: correct it rather than deleting it.
