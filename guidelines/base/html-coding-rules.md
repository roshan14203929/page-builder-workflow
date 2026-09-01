# HTML & CSS Rules

> **Prettier** and **html-validate** handle formatting, tag closing, doctype, charset, attribute quoting, and void elements automatically. These rules cover everything they miss.

> **Project-specific notes (MediChannel deliveries)**
> - **Template workflow:** Treat the template as read-only. Build and iterate in a separate file; copy only finished code into the template's designated editable area. Never run a formatter over the whole template file.
> - **XHTML output:** When the final deliverable must be XHTML, use a GenAI tool to convert the finished HTML5 file as a final step. Review the output manually against the XHTML-vs-HTML5 reference before submitting.

---

## 1. Document Structure

- `<html>` must have a `lang` attribute matching the page language (`lang="en"`, `lang="ja"`, etc.).
- `<title>` must be filled in — unique and descriptive (45–65 characters).
- `<title>` must match the page's `<h1>` content. If they differ, align `<title>` to the `<h1>`.
- Include exactly one `<main>` per page, wrapping the primary content.
- Always place `.container` on a `<div>` inside the `<section>`, never on the `<section>` itself:
  ```html
  <!-- correct -->
  <section class="content-section">
    <div class="container">…</div>
  </section>

  <!-- wrong -->
  <section class="content-section container">…</section>
  ```

---

## 2. Semantic HTML

- Use heading elements (`<h2>`, `<h3>`) for section titles. Never use a styled `<div>` as a heading.
- One `<h1>` per page. Do not skip heading levels (e.g. `<h1>` → `<h3>`).
- Use HTML tags for their semantic meaning, not their visual appearance. If only styling is needed, use CSS instead. When emphasis is semantically meaningful, use `<strong>` (not `<b>`) or `<em>` (not `<i>`).
- No spacer `<div>` elements (e.g. `<div style="height:20px">`). Use `margin` or `padding` in CSS.
- No empty elements (`<p></p>`) and no empty or whitespace-only class attributes (`class=""` or `class=" "`).

---

## 3. Accessibility

- Every `<img>` must have an `alt` attribute. Content images need a meaningful description; decorative images use `alt=""`.
- `alt` text must describe **what the image shows**, not its location or role ("製品ビジュアル", not "hero image for desktop").
- For PNG content images, base the `alt` text on the **nearest preceding `<h3>` or `<h4>` heading**. Verify each PNG's `alt` matches that heading's text; if `alt` is missing or unrelated, derive it from the nearest heading.
- `aria-label` values must be in the **page language**. An English label on a Japanese page breaks the screen reader experience.
- Never remove focus outlines without providing an equally visible replacement.
- Use `:focus-visible` for keyboard focus styles. Do not combine `:hover` and `:focus` in the same rule — they serve different input methods.

---

## 4. Images

- Every `<img>` must have explicit `width` and `height` attributes to prevent layout shift (CLS).
- Do **not** use `<picture>` or `<source>`. Wrap content images in a `<div class="img-wrapper">` with a single `<img>` inside — no `<picture>` element. The full template with CSS is at `.claude/template/index.html`.
- Use `loading="lazy"` on below-fold images. Use `loading="eager"` + `fetchpriority="high"` on the LCP (hero) image.

**Standard (single image):**
```html
<div class="img-wrapper">
  <img
    src="img/image.jpg"
    alt="Use the nearest preceding h3 or h4 heading text"
    loading="lazy"
    width="960"
    height="540"
  >
</div>
```

**With retina / HiDPI assets:**
```html
<div class="img-wrapper">
  <img
    src="img/image.jpg"
    srcset="
      img/image.jpg    1x,
      img/image@2x.jpg 2x
    "
    alt="Use the nearest preceding h3 or h4 heading text"
    loading="lazy"
    width="960"
    height="540"
  >
</div>
```

---

## 5. Fonts

For CSS and HTML font setup, use the provided templates. One rule applies regardless of template:

- Add `<link rel="preconnect">` **before** the Google Fonts `<link>`:
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  ```

---

## 6. HTML Code Hygiene

- No inline `style="..."` attributes. Move all values to a CSS class. Inline styles override the stylesheet and force `!important` into media queries to compensate.
- No commented-out HTML blocks. Delete unused code. If a section is intentionally excluded, leave a `<!-- TODO: reason -->` comment instead of the full block.

---

## 7. CSS — Naming

- Use BEM: `.block`, `.block__element`, `.block--modifier`.
- Block and element names use **hyphens**, not underscores: `.site-header`, not `.site_header`.
- Do not encode position or context in class names: `.references--footer`, not `.references__item_section_1`.
- When writing CSS for a page that sits inside an external template or CMS, prefix **all** class names with `cst-` (e.g. `.cst-hero`, `.cst-section__title`) to prevent collisions with the template's own selectors.

---

## 8. CSS — Variables & Values

- All colors must use `:root` variables. No hardcoded hex values outside `:root`.
- **Padding** is for inner space — between an element's content and its own edges. **Margin** is for outer space — between an element and its surrounding siblings. Use `padding` on a container to separate content from the box edges; use `margin-bottom` on elements to create vertical rhythm between sibling blocks.
- Use `:root` spacing variables for structural values (padding, margin, gap on layout elements). Small one-off values for fine-tuning (e.g. `4px` item gap, `5px` decorative padding) do not need a variable.
- Use `rem` for font sizes, not `px`. Do not use `clamp()` for font sizes — use breakpoints to set different sizes per viewport instead.
- Use a **number without a unit** for `line-height` (e.g. `1.5`, not `30px`).
- If a property is declared twice in the same selector, remove the first (overridden) one.
- No `!important`. It is almost always caused by an inline `style="..."` attribute overriding the stylesheet. Remove the inline style and the `!important` in the media query becomes unnecessary.

---

## 9. CSS — Architecture

- Global element rules (`img`, `ul`, `body`, etc.) belong in `base.css`, not `page.css`.
- Do not duplicate rules for the same selector. Remove the earlier, overridden one.
- In media query overrides, only include the properties that actually change. Do not repeat the full ruleset.
- Do not write overlapping media query breakpoints that set the same value. Merge them into one.
- Any `<section>` used as a TOC anchor target (i.e. it has an `id`) must have `scroll-margin-top` set to the header height, so the fixed header does not cover the section on scroll:
  ```css
  section[id] {
    scroll-margin-top: 70px; /* match the actual header height */
  }
  ```

---

## 10. CSS — Code Hygiene

- No commented-out CSS. Delete unused rules entirely.
- Fix or remove comments that no longer match the code they describe.
