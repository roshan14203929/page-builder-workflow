# XHTML 1.0 Strict vs HTML5 — Reference

---

## DOCTYPE & Root Element

| | XHTML 1.0 Strict | HTML5 |
|---|---|---|
| DOCTYPE | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">` | `<!DOCTYPE html>` |
| Root element | `<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">` | `<html lang="ja">` |
| XML namespace | Required | Not used |
| `xml:lang` | Required alongside `lang` | Not used |

**Note:** XHTML is an XML application — any single malformed tag breaks the entire page. HTML5 recovers from errors gracefully.

---

## Syntax Rules

| Rule | XHTML 1.0 Strict | HTML5 |
|---|---|---|
| Tag case | Lowercase only — `<DIV>` is invalid | Case-insensitive |
| Closing tags | All required | Many optional (`</p>`, `</li>`, etc.) |
| Void elements | Self-close required — `<br />`, `<img />` | Slash optional |
| Attribute values | Must be quoted | Unquoted allowed |
| Boolean attributes | `disabled="disabled"`, `checked="checked"` | `disabled`, `checked` |

---

## Script and Style

```xml
<!-- XHTML: CDATA wrapper required for inline scripts -->
<script type="text/javascript">
//<![CDATA[
  if (a < b && c > d) { ... }
//]]>
</script>
```

- `type="text/javascript"` and `type="text/css"` required in XHTML; optional in HTML5
- `async` / `defer` cause DTD validation errors in XHTML; standard in HTML5

---

## Meta Charset

- XHTML: `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />`
- HTML5: `<meta charset="UTF-8">` — must be the first element inside `<head>`

`<meta charset="UTF-8">` is invalid in XHTML.

---

## HTML5 Elements Unavailable in XHTML

Use `<div role="...">` equivalents in XHTML:

| HTML5 element | XHTML replacement | ARIA role |
|---|---|---|
| `<main>` | `<div role="main">` | `main` |
| `<nav>` | `<div role="navigation">` | `navigation` |
| `<header>` | `<div role="banner">` | `banner` |
| `<footer>` | `<div role="contentinfo">` | `contentinfo` |
| `<aside>` | `<div role="complementary">` | `complementary` |
| `<article>` | `<div role="article">` | `article` |
| `<section>` | `<div role="region" aria-label="...">` | `region` |
| `<figure>` | `<div role="figure">` | — |

Other unavailable elements: `<video>`, `<audio>`, `<picture>`, `<canvas>`, `<details>`, `<summary>`, `<dialog>`, `<template>`, `<datalist>`, `<progress>`, `<meter>`, `<ruby>`, `<wbr>`.

HTML5 input types (`email`, `url`, `number`, `date`, `range`, etc.) and form attributes (`placeholder`, `required`, `autofocus`, `pattern`, etc.) cause DTD validation errors in XHTML — browsers handle them gracefully but validators reject them.

---

## Content Model

Block inside inline is illegal in XHTML Strict:
- ❌ `<a href="#"><div>...</div></a>`
- ✅ HTML5 allows this via the transparent content model

Removed in XHTML Strict: `<font>`, `<center>`, `<strike>`, `<big>`, `<basefont>`, `<frame>`, `<frameset>`, `<noframes>`.

Nesting prohibitions:
- `<a>` cannot contain `<a>`
- `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`
- `<label>` cannot contain `<label>`
- `<form>` cannot contain `<form>`
- `<pre>` cannot contain `<img>`, `<big>`, `<small>`, `<sub>`, `<sup>`

---

## Ampersand & Entities

- `&` must always be `&amp;` — including in URLs: `<a href="?a=1&amp;b=2">`
- In XML mode, only the five predefined XML entities are safe without a DTD:
  `&lt;` `&gt;` `&amp;` `&quot;` `&apos;`
- Use numeric refs for all others: `&nbsp;` → `&#160;`, `&copy;` → `&#169;`, `&mdash;` → `&#8212;`
- `&apos;` is valid in XHTML; use `&#39;` if HTML4 compatibility is needed

---

## `id` vs `name`

- `name` is deprecated on `<a>`, `<form>`, `<img>` in XHTML — use `id`
- `id` must start with a letter or underscore in XHTML — leading digits are forbidden

---

## `lang` / `xml:lang`

- XHTML: both required, values must match — `xml:lang` takes precedence
- HTML5: `lang` only

---

## CSS: `<tbody>` Must Be Explicit

In XML parsing mode, `<tbody>` is not auto-inferred. Write it explicitly in every table or `table > tbody > tr` selectors will break.

---

## Quick Reference

```html
<!-- XHTML invalid — HTML5 allows -->
<INPUT type="hidden" value="foo">     <!-- uppercase tag -->
<br>                                   <!-- no self-close -->
<img src="x.gif">                     <!-- no self-close, no alt -->
<input disabled>                      <!-- minimized boolean -->
<td rowspan=3>                        <!-- unquoted attribute -->
<a href="?a=1&b=2">                   <!-- bare & -->
<p>First<p>Second                     <!-- unclosed p -->
<a href="#"><div>block</div></a>      <!-- block in inline -->

<!-- HTML5 valid — XHTML would not allow -->
<!DOCTYPE html>
<meta charset="UTF-8">
<script>...</script>
<input required>
<input type="email">
<video src="movie.mp4" controls></video>
<article><section>...</section></article>
```
