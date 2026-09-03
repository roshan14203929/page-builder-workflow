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

## 5. Rules Shared with HTML5 — XHTML Deviations Only

Sections 2–10 of `html-coding-rules.md` (semantic HTML, accessibility, images,
fonts, HTML quality, CSS naming, CSS values, CSS architecture, CSS hygiene)
apply here, with the XHTML-specific modifications below.

### Structural elements

No semantic landmarks (`<main>`, `<section>`, `<article>`, `<nav>`, `<header>`,
`<footer>`, `<aside>`, `<figure>`, etc.) — use the `<div role="...">`
alternatives from the table in §4.

### Content model (HTML4, stricter than HTML5)

XHTML 1.0 Strict inherits the HTML4 content model:

- Block-level elements cannot be placed inside inline elements
  (e.g. `<div>` inside `<a>` is forbidden — HTML5 relaxes this):
  ```xml
  <!-- ❌ Invalid -->
  <a href="#"><div>block in inline</div></a>

  <!-- ✅ Correct -->
  <div class="link-block"><a href="#">...</a></div>
  ```
- `<a>` cannot be nested inside another `<a>`.
- `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`,
  `<button>`, `<form>`, or `<fieldset>`.
- `<label>` cannot be nested inside another `<label>`.
- `<form>` cannot be nested inside another `<form>`.

### Accessibility

- ARIA attributes (`role`, `aria-*`) cause DTD validation errors but are
  interpreted by browsers — continue using them.

### Images

- `<picture>` and `<source>` are unavailable. Wrap a single self-closing
  `<img />` in `<div class="img-wrapper">`.
- `loading`, `fetchpriority`, and `srcset` are outside the DTD but interpreted
  by modern browsers. Use per project policy.

### Fonts and script/link `type` attributes

- `<link rel="stylesheet">` requires `type="text/css"`; `<script>` requires
  `type="text/javascript"` (already covered in §3).
- Attribute minimization is prohibited — write `crossorigin="anonymous"`
  in full; never bare `crossorigin`.
- Place `<link rel="preconnect">` before the stylesheet `<link>` when using
  Google Fonts:
  ```xml
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css2?family=..." />
  ```

### HTML code quality

- Prefer numeric character references over named ones in XML mode
  (`application/xhtml+xml`), where the DTD is not loaded:
  - `&nbsp;` → `&#160;`
  - `&copy;` → `&#169;`
  - `&mdash;` → `&#8212;`

### CSS naming

- Use lowercase element names in CSS selectors — XML is case-sensitive.

### CSS architecture

- Scope every global element rule in `base.css` under `.cst-page`
  (e.g. `a { }` → `.cst-page a { }`). This prevents styles from leaking into
  header/footer regions managed by external systems.
- In `page.css`, class-alone selectors (specificity 10) lose to
  `.cst-page element` in `base.css` (specificity 11). Use `.cst-page .your-class`
  (specificity 20) to override:
  ```css
  /* ❌ specificity 10 — loses to base.css's 11 */
  .cst-my-link { color: red; }

  /* ✅ specificity 20 — beats base.css's 11 */
  .cst-page .cst-my-link { color: red; }
  ```
- `scroll-margin-top` for TOC anchors applies to `div[id]`, not `section[id]`
  (since `<section>` is unavailable):
  ```css
  div[id] {
    scroll-margin-top: 70px; /* match the actual fixed-header height */
  }
  ```

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
