# XHTML 1.0 Strict Coding Rules

> **Base:** Created by applying the differences from `xhtml-vs-html5-reference.md` to `html-coding-rules.md` (HTML5 rules).
> **Scope:** Rules for coding directly in XHTML 1.0 Strict. Applies to MediChannel deliveries.

---

## 1. Document Structure

### DOCTYPE and Root Element

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
```

- Include the `<?xml ...?>` declaration on the very first line.
- Use the full DOCTYPE for XHTML 1.0 Strict (do not use the HTML5 shorthand `<!DOCTYPE html>`).
- The `<html>` element must always include all three attributes: `xmlns`, `xml:lang`, and `lang`. The values of `xml:lang` and `lang` must be identical.

### charset Declaration

```xml
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
```

- The HTML5 shorthand `<meta charset="UTF-8">` is invalid in XHTML 1.0 Strict. Use the form above.
- Place it as the first element inside `<head>`.

### `<title>`

- Always fill in. Content must be unique and descriptive (45–65 characters).
- Match the content to the page's `<h1>`. If they differ, revise to match `<h1>`.

### Main Content Area

XHTML 1.0 Strict does not have a `<main>` element. Use a `<div>` with `role="main"` as an alternative:

```xml
<div id="main" role="main">
  …
</div>
```

### Container Placement

Place `.container` inside the block that acts as a `<section>` equivalent (`<div class="content-section">`):

```xml
<!-- Correct -->
<div class="content-section">
  <div class="container">…</div>
</div>
```

---

## 2. XHTML Syntax Rules (Key Differences from HTML5)

These are mandatory requirements for XHTML 1.0 Strict. Violations cause XML parse errors.

### 2.1 All Tag and Attribute Names Must Be Lowercase

XML is case-sensitive; write everything in lowercase.

```xml
<!-- ❌ Invalid -->
<DIV CLASS="wrapper"><INPUT TYPE="text"></DIV>

<!-- ✅ Correct -->
<div class="wrapper"><input type="text" /></div>
```

### 2.2 All Elements Must Be Closed

Void elements must be self-closed with `/>`, and non-void elements must have a closing tag. Include a space before `/>`.

```xml
<!-- ❌ Invalid -->
<br>
<img src="..." alt="...">
<p>First paragraph<p>Second paragraph

<!-- ✅ Correct -->
<br />
<img src="..." alt="..." />
<p>First paragraph</p><p>Second paragraph</p>
```

Common self-closing elements: `<br />` `<hr />` `<img />` `<input />` `<link />` `<meta />`

### 2.3 All Attribute Values Must Be Quoted

```xml
<!-- ❌ Invalid -->
<td rowspan=3>

<!-- ✅ Correct -->
<td rowspan="3">
```

### 2.4 Boolean Attributes Must Have an Explicit Value

Attribute minimization is prohibited in XHTML.

```xml
<!-- ❌ Invalid -->
<input disabled>
<option selected>

<!-- ✅ Correct -->
<input disabled="disabled" />
<option selected="selected">
```

### 2.5 Elements Must Be Properly Nested

Elements must be closed in the correct order (overlapping is prohibited).

```xml
<!-- ❌ Invalid -->
<b><i>text</b></i>

<!-- ✅ Correct -->
<b><i>text</i></b>
```

### 2.6 `&` Must Always Be Escaped

Escape all `&` characters as `&amp;`, including those in URLs.

```xml
<!-- ❌ Invalid -->
<a href="?a=1&b=2">

<!-- ✅ Correct -->
<a href="?a=1&amp;b=2">
```

### 2.7 Naming Rules for `id` Attributes

In XHTML (XML), `id` values must begin with a letter or underscore. Leading digits are not permitted.

```xml
<!-- ❌ Invalid -->
<div id="1st-section">

<!-- ✅ Correct -->
<div id="section-1">
<div id="_anchor">
```

---

## 3. `<script>` and `<style>` Usage

### `type` Attribute Is Required

The `type` attribute cannot be omitted in XHTML.

```xml
<script type="text/javascript" src="app.js"></script>
<link rel="stylesheet" type="text/css" href="style.css" />
<style type="text/css">…</style>
```

### CDATA Wrapping for Inline `<script>` / `<style>`

If inline scripts or styles contain `<`, `>`, or `&`, they will cause XML parse errors. Wrap them in a CDATA section.

```xml
<script type="text/javascript">
//<![CDATA[
  if (a < b && c > d) { /* ... */ }
//]]>
</script>

<style type="text/css">
/*<![CDATA[*/
  .foo > .bar { color: red; }
/*]]>*/
</style>
```

### Do Not Use `async` / `defer`

These are not defined in the XHTML 1.0 Strict DTD and will cause DTD validation errors. Control script load order by placing `<script>` elements at the end of `<body>`.

---

## 4. Available Structural Elements

HTML5 elements that do not exist in XHTML 1.0 Strict cannot be used. Use alternatives instead.

| HTML5 Element | XHTML Alternative |
|---|---|
| `<main>` | `<div id="main" role="main">` |
| `<section>` | `<div class="section" role="region">` |
| `<article>` | `<div class="article" role="article">` |
| `<nav>` | `<div class="nav" role="navigation">` |
| `<header>` | `<div class="header" role="banner">` |
| `<footer>` | `<div class="footer" role="contentinfo">` |
| `<aside>` | `<div class="aside" role="complementary">` |
| `<figure>` | `<div class="figure">` |
| `<figcaption>` | `<p class="figcaption">` |
| `<mark>` | `<span class="mark">` |
| `<time>` | `<span class="time">` |

Prohibited elements (no alternative): `<picture>` `<source>` `<video>` `<audio>` `<canvas>` `<details>` `<summary>` `<dialog>` `<datalist>` `<output>` `<progress>` `<meter>` `<template>`

---

## 5. Semantic Markup

- Use heading elements (`<h2>`, `<h3>`, etc.) for section titles. Do not use `<div>` as a heading for styling purposes.
- Use `<h1>` only once per page. Do not skip heading levels (e.g., jumping from `<h1>` to `<h3>` is not allowed).
- Use `<strong>` for semantic emphasis (not `<b>`), and `<em>` for stress emphasis (not `<i>`).
- Spacer `<div>` elements (e.g., `<div style="height:20px">`) are not allowed. Use CSS `margin` / `padding` instead.
- Empty elements (`<p></p>`) and empty class attributes (`class=""`, `class=" "`) are not allowed.

---

## 6. Accessibility

- All `<img />` elements must have an `alt` attribute. Content images should have a meaningful description; decorative images should use `alt=""`.
- `alt` text should describe what the image shows (not the file name or placement).
- For PNG content images, set the `alt` value based on the immediately preceding `<h3>` or `<h4>` heading text.
- `aria-label` values should be written in the language of the page (Japanese for Japanese pages).
- If focus outlines are hidden, provide an equally visible alternative style.
- Use `:focus-visible` to define keyboard focus styles. Do not combine `:hover` and `:focus` into the same rule.
- ARIA attributes are not defined in the XHTML 1.0 Strict DTD, but `role` and `aria-*` attributes can still be written (they cause DTD validation errors but are interpreted by browsers).

---

## 7. Images

- All `<img />` elements must explicitly specify `width` and `height` attributes (to prevent layout shift).
- `<picture>` is not available in XHTML 1.0 Strict. Place a single `<img />` inside `<div class="img-wrapper">`.
- `loading`, `fetchpriority`, and `srcset` are not defined in the XHTML 1.0 Strict DTD but can be written (they cause DTD validation errors but are interpreted by modern browsers). Use based on project policy.

**Standard (single image):**
```xml
<div class="img-wrapper">
  <img
    src="img/image.jpg"
    alt="Heading text from the preceding h3 or h4"
    width="960"
    height="540"
  />
</div>
```

**Retina-ready (`srcset` — outside DTD validation):**
```xml
<div class="img-wrapper">
  <img
    src="img/image.jpg"
    srcset="img/image.jpg 1x, img/image@2x.jpg 2x"
    alt="Heading text from the preceding h3 or h4"
    width="960"
    height="540"
  />
</div>
```

---

## 8. Fonts

When using a Google Fonts `<link>`, place `<link rel="preconnect">` elements before it. The `type="text/css"` attribute is required.

```xml
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" />
<link
  rel="stylesheet"
  type="text/css"
  href="https://fonts.googleapis.com/css2?family=..."
/>
```

- In XHTML, when adding the `crossorigin` attribute to a self-closing element, include an explicit value: `crossorigin="anonymous"` (attribute minimization is prohibited).

---

## 9. Content Model (Nesting Rules)

XHTML 1.0 Strict strictly inherits the HTML4 content model.

- Placing block elements inside inline elements is prohibited:
  ```xml
  <!-- ❌ Invalid -->
  <a href="#"><div>block in inline</div></a>

  <!-- ✅ Correct -->
  <div class="link-block"><a href="#">...</a></div>
  ```
- `<a>` elements cannot be nested inside another `<a>`.
- Inside a `<button>`, the following are not allowed: `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`.
- `<label>` elements cannot be nested inside another `<label>`.
- `<form>` elements cannot be nested inside another `<form>`.

---

## 10. HTML Code Quality

- Do not use inline `style="..."` attributes. Move all values to CSS classes.
- Do not leave commented-out HTML blocks. Delete unnecessary code. For intentionally excluded sections, leave a `<!-- TODO: reason -->` comment.
- Character references: When using named character references such as `&nbsp;`, it is safer to use numeric references in XML mode (`application/xhtml+xml`) where the DTD is not loaded:
  - `&nbsp;` → `&#160;`
  - `&copy;` → `&#169;`
  - `&mdash;` → `&#8212;`

---

## 11. CSS — Naming Conventions

- Use BEM: `.block`, `.block__element`, `.block--modifier`.
- Block and element names use hyphens: `.site-header` (not `site_header`).
- Do not include position or context in class names: `.references--footer` (not `.references__item_section_1`).
- When writing CSS in external templates or CMS pages, prefix all class names with `cst-` (e.g., `.cst-hero`, `.cst-section__title`).

---

## 12. CSS — Variables and Values

- Use `:root` variables for all colors. Hardcoded hex values outside `:root` are not allowed.
- `padding` is for inner spacing (between content and its own edge); `margin` is for outer spacing (between sibling elements).
- Use `:root` spacing variables for structural values of layout elements (padding, margin, gap). Small fine-tuning values (e.g., a `4px` gap) do not require variables.
- Use `rem` for font sizes (not `px`). Do not use `clamp()` for font sizes; switch values at breakpoints instead.
- Use unitless numbers for `line-height` (e.g., `1.5`, not `30px`).
- If a property is declared twice within the same selector, delete the first (overridden) declaration.
- Do not use `!important`.

---

## 13. CSS — Architecture

- Place global element rules (`img`, `ul`, `body`, etc.) in `base.css`. Do not write them in `page.css`.
- Scope all global element rules in `base.css` under `.cst-page` (e.g., `a { }` → `.cst-page a { }`). This prevents styles from leaking into the header, footer, and other areas managed by external systems.
- In `page.css`, if the styled element is one of `<a>` / `<ul>` / `<ol>` / `<img>` / `<picture>` / `<video>` / `<em>` / `<i>` / `<cite>`, a class alone (specificity 10) loses to `base.css`'s `.cst-page element` selector (specificity 11). Use the `.cst-page .your-class` form (specificity 20) instead:
  ```css
  /* ❌ Specificity 10 — loses to base.css's 11 */
  .cst-my-link { color: red; }

  /* ✅ Specificity 20 — beats base.css's 11 */
  .cst-page .cst-my-link { color: red; }
  ```
- Do not duplicate rules for the same selector. Delete the overridden one.
- In media query overrides, write only the properties that actually change. Do not repeat the entire ruleset.
- Add `scroll-margin-top` to `<div id="...">` elements used as TOC anchors to prevent them from being hidden behind a fixed header:
  ```css
  div[id] {
    scroll-margin-top: 70px; /* Adjust to the actual header height */
  }
  ```
- Use lowercase element names in CSS selectors (XHTML/XML is case-sensitive).

---

## 14. CSS — Code Quality

- Do not leave commented-out CSS. Delete unnecessary rules completely.
- Revise or delete comments that no longer match the code.

---

## Appendix: XHTML 1.0 Strict Checklist

Verify the following before submitting code:

| Checklist Item | Confirmed |
|---|---|
| DOCTYPE is in the full XHTML 1.0 Strict format | |
| `<html>` has all three attributes: `xmlns`, `xml:lang`, and `lang` | |
| charset is declared via `<meta http-equiv="Content-Type" ...>` | |
| All tag and attribute names are lowercase | |
| All void elements are self-closed with `/>` (with a space) | |
| All attribute values are enclosed in quotes | |
| Boolean attributes have an explicit value (e.g., `disabled="disabled"`) | |
| All `&` characters are escaped as `&amp;` | |
| Inline `<script>`/`<style>` blocks are wrapped in CDATA | |
| `<script>` elements include `type="text/javascript"` | |
| `<link rel="stylesheet">` elements include `type="text/css"` | |
| HTML5-only elements (`<section>`, `<main>`, etc.) are not used | |
| `id` attribute values begin with a letter or underscore | |
| Block elements are not placed inside inline elements | |
