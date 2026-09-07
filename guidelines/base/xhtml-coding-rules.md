# XHTML 1.0 Strict Coding Rules

> **Base:** `html-coding-rules.md` + diffs from `xhtml-vs-html5-reference.md`.
> **Scope:** MediChannel deliveries coded directly in XHTML 1.0 Strict.

---

## Document Structure

### DOCTYPE and Root Element

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
```

- `<?xml ...?>` on the very first line.
- Full XHTML 1.0 Strict DOCTYPE — not `<!DOCTYPE html>`.
- `<html>` must have all three: `xmlns`, `xml:lang`, `lang` (values must match).

### charset

```xml
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
```

First element inside `<head>`. `<meta charset="UTF-8">` is invalid here.

### `<title>`

Unique, descriptive, 45–65 chars. Must match `<h1>`.

### Main Content Area

No `<main>` in XHTML 1.0 Strict. Use:
```xml
<div id="main" role="main">…</div>
```

### Container Placement

`.container` inside the section-equivalent `<div>`, not on it:
```xml
<div class="content-section">
  <div class="container">…</div>
</div>
```

---

## XHTML Syntax Rules

Violations cause XML parse errors.

### Lowercase Everything

```xml
<!-- ❌ --> <DIV CLASS="wrapper">
<!-- ✅ --> <div class="wrapper">
```

### All Elements Must Be Closed

Void elements → self-close with space before `/>`.

```xml
<!-- ❌ --> <br>  <img src="..." alt="...">
<!-- ✅ --> <br />  <img src="..." alt="..." />
```

Common void elements: `<br />` `<hr />` `<img />` `<input />` `<link />` `<meta />`

### All Attribute Values Must Be Quoted

```xml
<!-- ❌ --> <td rowspan=3>
<!-- ✅ --> <td rowspan="3">
```

### Boolean Attributes Need Explicit Values

```xml
<!-- ❌ --> <input disabled>
<!-- ✅ --> <input disabled="disabled" />
```

### Proper Nesting

```xml
<!-- ❌ --> <b><i>text</b></i>
<!-- ✅ --> <b><i>text</i></b>
```

### Escape All `&`

```xml
<!-- ❌ --> <a href="?a=1&b=2">
<!-- ✅ --> <a href="?a=1&amp;b=2">
```

### `id` Values Must Start with Letter or Underscore

```xml
<!-- ❌ --> <div id="1st-section">
<!-- ✅ --> <div id="section-1">
```

---

## `<script>` and `<style>`

### `type` Attribute Required

```xml
<script type="text/javascript" src="app.js"></script>
<link rel="stylesheet" type="text/css" href="style.css" />
```

### CDATA Wrapping for Inline Blocks

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

### No `async` / `defer`

Not in XHTML 1.0 Strict DTD. Control load order by placing `<script>` at end of `<body>`.

---

## Available Structural Elements

| HTML5 | XHTML Alternative |
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

**Prohibited (no alternative):** `<picture>` `<source>` `<video>` `<audio>` `<canvas>` `<details>` `<summary>` `<dialog>` `<datalist>` `<output>` `<progress>` `<meter>` `<template>`

---

## Deviations from `html-coding-rules.md`

Sections 2–10 of `html-coding-rules.md` apply, with these XHTML-specific overrides:

**Structural elements** — Use `<div role="...">` alternatives from table above. No semantic landmarks.

**Content model** — Stricter than HTML5:
- Block elements inside inline elements forbidden (`<div>` inside `<a>` invalid).
- No nested `<a>`, `<label>`, or `<form>`.
- `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`.

**Accessibility** — `role` and `aria-*` cause DTD errors but are interpreted by browsers — use them anyway.

**Images** — No `<picture>` or `<source>`. Use `<div class="img-wrapper"><img /></div>`. `loading`, `fetchpriority`, `srcset` are outside DTD but supported by modern browsers — use per project policy.

**Fonts** — `crossorigin` must be written in full (`crossorigin="anonymous"`). Preconnect before stylesheet:
```xml
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
<link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css2?family=..." />
```

**Character references** — In XML mode, prefer numeric refs over named ones:
- `&nbsp;` → `&#160;` · `&copy;` → `&#169;` · `&mdash;` → `&#8212;`

**CSS naming** — Lowercase element names in selectors (XML is case-sensitive).

**CSS architecture:**
- Scope all global element rules in `base.css` under `.cst-page` (e.g. `.cst-page a {}`).
- In `page.css`, use `.cst-page .your-class` (specificity 20) to beat `base.css`'s `.cst-page element` (specificity 11):
  ```css
  /* ❌ specificity 10 — loses */
  .cst-my-link { color: red; }

  /* ✅ specificity 20 — wins */
  .cst-page .cst-my-link { color: red; }
  ```
- TOC anchor offset on `div[id]` (not `section[id]`):
  ```css
  div[id] { scroll-margin-top: 70px; }
  ```

---

## Checklist

| Item | ✓ |
|---|---|
| Full XHTML 1.0 Strict DOCTYPE | |
| `<html>` has `xmlns`, `xml:lang`, `lang` (values match) | |
| charset via `<meta http-equiv="Content-Type" ...>` | |
| All tag/attribute names lowercase | |
| All void elements self-closed with ` />` | |
| All attribute values quoted | |
| Boolean attributes have explicit values | |
| All `&` escaped as `&amp;` | |
| Inline `<script>`/`<style>` wrapped in CDATA | |
| `<script>` has `type="text/javascript"` | |
| `<link rel="stylesheet">` has `type="text/css"` | |
| No HTML5-only elements | |
| `id` values start with letter or underscore | |
| No block elements inside inline elements | |