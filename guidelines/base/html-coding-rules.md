# HTML & CSS Rules

> Prettier + html-validate handle formatting, closing tags, doctype, charset, quoting, void elements.

> **MediChannel:** Template = read-only. Build in separate file; copy finished code into template's editable area. Never format the whole template. For XHTML output, convert finished HTML5 as final step; review manually before submitting.

---

## Document Structure
- `<html lang="…">` must match page language.
- `<title>` unique, descriptive, 45–65 chars, matches `<h1>`.
- Exactly one `<main>` per page.
- `.container` on `<div>` inside `<section>`, never on `<section>` itself.

## Semantic HTML
- Use `<h2>`/`<h3>` for section titles. Never styled `<div>` as heading.
- One `<h1>`. No skipped heading levels.
- Tags for meaning, not appearance. Meaningful emphasis → `<strong>`/`<em>`, not `<b>`/`<i>`.
- No spacer `<div>`. No empty elements or blank `class` attributes.

## Accessibility
- Every `<img>` needs `alt`. Content → descriptive; decorative → `alt=""`.
- `alt` describes what image shows, not its role. For PNGs, derive from nearest preceding `<h3>`/`<h4>`.
- `aria-label` in page language.
- Never remove focus outlines without visible replacement.
- Use `:focus-visible` for keyboard styles. Don't combine `:hover` and `:focus` in one rule.

## Images
- All `<img>` need explicit `width` + `height` attributes (prevents CLS — sets
  the intrinsic size hint for the browser before the image loads).
- CSS must keep images fluid: `.img-wrapper img { max-width: 100%; height: auto; }`.
  Never set a fixed CSS `width` or `height` on an image — it breaks layout at
  other viewport sizes and causes horizontal scroll.
- No `<picture>`/`<source>`. Wrap in `<div class="img-wrapper">`.
- Below-fold → `loading="lazy"`. LCP/hero → `loading="eager" fetchpriority="high"`.

```html
<!-- standard -->
<div class="img-wrapper">
  <img src="img/image.jpg" alt="nearest h3/h4 text" loading="lazy" width="960" height="540">
</div>

<!-- retina -->
<div class="img-wrapper">
  <img src="img/image.jpg" srcset="img/image.jpg 1x, img/image@2x.jpg 2x"
    alt="nearest h3/h4 text" loading="lazy" width="960" height="540">
</div>
```

## Fonts
Always place `<link rel="preconnect">` before Google Fonts `<link>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

## HTML Hygiene
- No inline `style="…"`. Move to CSS class.
- No commented-out blocks. Delete unused code; use `<!-- TODO: reason -->` for intentional omissions.
- No `href="javascript:void(0)"`. Use `<button>` for actions, or `href="#"` + `preventDefault()`.

## CSS — Naming
- BEM: `.block`, `.block__element`, `.block--modifier`. Hyphens, not underscores.
- No position/context in class names (`.references--footer` ✓, `.references__item_section_1` ✗).
- Inside external template/CMS: prefix all classes with `cst-` (e.g. `.cst-hero`).

## CSS — Variables & Values
- All colors via `:root` variables. No hardcoded hex outside `:root`.
- `padding` = inner space; `margin` = outer space between siblings.
- Use `:root` spacing variables for layout; small one-off values (4px, 5px) don't need variables.
- Font sizes in `rem`, not `px`. No `clamp()` — use breakpoints instead.
- `line-height` unitless (e.g. `1.5`).
- Duplicate property in same selector → remove first.
- No `!important`. Fix by removing inline `style`.

## CSS — Architecture
- Global element rules → `base.css`, not `page.css`.
- No duplicate selectors. No repeated full rulesets in media queries — only changed properties.
- No overlapping breakpoints setting same value — merge them.
- Sections with `id` (TOC anchors) need `scroll-margin-top` matching header height:
```css
section[id] { scroll-margin-top: 70px; }
```

## CSS — Hygiene
- No commented-out CSS. Delete unused rules.
- Remove or fix stale comments.