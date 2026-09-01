# XHTML 1.0 Strict vs. Modern HTML5 — Comprehensive Issues & Conflicts Reference

> **Source references:** W3C XHTML 1.0 Specification (https://www.w3.org/TR/xhtml1/), WHATWG HTML Living Standard (https://html.spec.whatwg.org/multipage/xhtml.html), MDN Web Docs (https://developer.mozilla.org/en-US/docs/Glossary/XHTML)  
> **Status note:** XHTML 1.0 was superseded on 27 March 2018. The W3C now recommends the [HTML Living Standard](https://www.w3.org/TR/html/) for all new implementations.

---

## 1. DOCTYPE & Document Declaration

| Aspect | XHTML 1.0 Strict | Modern HTML5 |
|---|---|---|
| DOCTYPE | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">` | `<!DOCTYPE html>` |
| Root element | `<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">` | `<html lang="ja">` |
| XML namespace | Required (`xmlns` attribute) | Not applicable |
| `xml:lang` | Required alongside `lang` | Not used |
| XML declaration | Recommended (`<?xml version="1.0" encoding="UTF-8"?>`) | Not used |

**Conflict:** The long DOCTYPE triggers "quirks mode" in some older parsers. Modern HTML5 uses the short `<!DOCTYPE html>` which always triggers standards mode.

---

## 2. Parsing Model — The Critical Difference

This is the most important conflict when mixing XHTML rules with modern content:

- **XHTML** is an **XML application**. Browsers that receive it as `application/xhtml+xml` use a strict XML parser. **Any single malformed tag causes the entire page to fail** with a yellow error screen (XML parse error).
- **Modern HTML5** uses a **fault-tolerant HTML parser** that recovers gracefully from errors.
- **The catch:** This file (and most XHTML sites) is served as `text/html`, so browsers parse it with the HTML parser anyway — but the XHTML doctype creates a false expectation of XML strictness that can confuse developers and tools.

**Conflict:** You cannot add HTML5-specific constructs (e.g. `<template>`, inline `<svg>`) into a document served as `application/xhtml+xml` without ensuring they are XML-namespace-well-formed, or the entire page will break.

---

## 3. Syntax Rules — Strict vs. Lenient

### 3.1 Well-formedness (Required in XHTML, optional in HTML5)

In XHTML, documents must be **well-formed XML**. All of the following violations are fatal errors in XML mode:

- Elements must not overlap:
  - ❌ XHTML: `<b><i>text</b></i>` (overlapping — illegal)
  - ✅ XHTML: `<b><i>text</i></b>` (properly nested)
  - ✅ HTML5: Tolerates overlapping tags (parser auto-corrects)

### 3.2 Tag Case Sensitivity

- **XHTML:** All element and attribute names **must be lowercase** (XML is case-sensitive).
  - ❌ `<DIV>`, `<P>`, `<INPUT TYPE="text">`
  - ✅ `<div>`, `<p>`, `<input type="text">`
- **HTML5:** Case-insensitive — `<DIV>` and `<div>` are identical.

### 3.3 End Tags — All Required in XHTML

- **XHTML:** All non-empty elements must have a closing tag.
  - ❌ `<p>First paragraph<p>Second paragraph`
  - ✅ `<p>First paragraph</p><p>Second paragraph</p>`
- **HTML5:** Many closing tags are optional (`</p>`, `</li>`, `</td>`, `</tr>`, `</th>`, `</dt>`, `</dd>`, `</colgroup>`, `</tbody>`, `</thead>`, `</tfoot>`, `</html>`, `</head>`, `</body>`).

### 3.4 Self-Closing (Void) Elements

- **XHTML:** Void elements must use self-closing syntax:
  - ✅ `<br />`, `<hr />`, `<img src="..." alt="..." />`, `<input />`, `<link />`, `<meta />`
  - ❌ `<br>`, `<hr>`, `<img src="...">`
- **HTML5:** The trailing slash on void elements is **optional and ignored** — both `<br>` and `<br/>` are valid.
- **Important:** The W3C recommends including a space before `/>` for compatibility: `<br />` not `<br/>`.

### 3.5 Attribute Quoting

- **XHTML:** All attribute values **must be quoted** (single or double quotes).
  - ❌ `<td rowspan=3>`
  - ✅ `<td rowspan="3">`
- **HTML5:** Attribute values may be unquoted if they contain no spaces or special characters.

### 3.6 Attribute Minimization (Boolean Attributes)

- **XHTML:** Attribute minimization is **forbidden**. Boolean attributes must have explicit values.
  - ❌ `<input disabled>`, `<option selected>`, `<dl compact>`
  - ✅ `<input disabled="disabled">`, `<option selected="selected">`, `<dl compact="compact">`
- **HTML5:** Boolean attributes can be written in minimized form:
  - ✅ `disabled`, `checked`, `selected`, `readonly`, `multiple`, `required`, `autofocus`, `autoplay`, `controls`, `defer`, `ismap`, `loop`, `multiple`, `open`, `reversed`, `scoped`, `seamless`

**Conflict:** Adding modern HTML5 form attributes like `required`, `autofocus` without values is invalid XHTML.

---

## 4. Script and Style Elements

### 4.1 CDATA Sections Required in XHTML

In XHTML served as XML, `<script>` and `<style>` content is treated as **parsed character data (#PCDATA)**. Characters like `<`, `>`, `&`, `]]>` will be interpreted as XML markup and cause parse errors.

The XHTML-correct approach requires wrapping script/style content in `CDATA` sections:

```xml
<!-- XHTML-correct -->
<script type="text/javascript">
//<![CDATA[
  if (a < b && c > d) { ... }
//]]>
</script>
```

```xml
<!-- HTML5-correct (no CDATA needed) -->
<script>
  if (a < b && c > d) { ... }
</script>
```

### 4.2 `type` Attribute on Scripts

- **XHTML:** `type="text/javascript"` was conventionally required.
- **HTML5:** The `type` attribute on `<script>` defaults to `text/javascript` and is **optional** (unless using modules: `type="module"`).

### 4.3 `type` Attribute on Stylesheets

- **XHTML/HTML4:** `type="text/css"` was conventionally required on `<link>` and `<style>`.
- **HTML5:** Defaults to `text/css` — **optional**.

### 4.4 `async` and `defer` on `<script>`

- **XHTML 1.0 Strict:** `async` and `defer` are not defined in the DTD. Using them causes DTD validation errors.
- **HTML5:** Both are standard attributes for controlling script loading and execution:
  - `defer`: Script executes after HTML parsing completes, in document order.
  - `async`: Script executes as soon as it downloads, potentially out of order.
  - `type="module"` scripts are deferred by default.

---

## 5. `<meta>` Charset Declaration

- **XHTML approach (used in this file):** `<meta name="content-type" content="text/html; charset=UTF-8"/>`
- **HTML5 approach:** `<meta charset="UTF-8">` — simplified, not valid in XHTML 1.0 Strict.
- **Also valid in HTML5:** `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">`

**Conflict:** The simplified `<meta charset="UTF-8">` syntax is **invalid in XHTML** but is the standard in HTML5 and should appear as the **first element in `<head>`** for HTML5 documents.

---

## 6. HTML5 Elements Not Available in XHTML 1.0 Strict

The following elements **do not exist** in the XHTML 1.0 Strict DTD. Using them causes DTD validation failure and may cause unexpected rendering:

### 6.1 Semantic Structural Elements
| Element | Purpose |
|---|---|
| `<article>` | Self-contained content unit |
| `<section>` | Thematic grouping |
| `<aside>` | Tangentially related content (sidebar) |
| `<nav>` | Navigation block |
| `<header>` | Introductory content for a section |
| `<footer>` | Footer for a section or page |
| `<main>` | Primary content of the document |
| `<figure>` | Self-contained figure with optional caption |
| `<figcaption>` | Caption for a `<figure>` |
| `<hgroup>` | Groups heading elements |
| `<mark>` | Highlighted/marked text |
| `<time>` | Machine-readable date/time |
| `<address>` (redefined) | Extended semantics in HTML5 |

### 6.2 Media Elements
| Element | Purpose |
|---|---|
| `<video>` | Embedded video |
| `<audio>` | Embedded audio |
| `<source>` | Media source for `<video>`/`<audio>` |
| `<track>` | Text tracks (subtitles, captions) |
| `<embed>` | Plugin/external content embedding |
| `<picture>` | Responsive image container |

### 6.3 Form Elements (New in HTML5)
| Element | Purpose |
|---|---|
| `<datalist>` | Autocomplete suggestion list |
| `<output>` | Calculation result |
| `<progress>` | Progress indicator |
| `<meter>` | Scalar measurement |

### 6.4 Interactive / Scripting Elements
| Element | Purpose |
|---|---|
| `<details>` | Disclosure widget |
| `<summary>` | Summary for `<details>` |
| `<dialog>` | Modal/non-modal dialog |
| `<canvas>` | 2D/3D graphics surface |
| `<template>` | Inert HTML template (**⚠ in XHTML/XML mode, content is parsed directly into the live DOM — the inert `DocumentFragment` behavior is lost entirely**) |
| `<slot>` | Web Components slot |

### 6.5 Inline SVG & MathML
In HTML5, `<svg>` and `<math>` can be embedded directly inline. In XHTML 1.0 Strict this requires explicit namespace declarations and the document must be served as XML.

### 6.6 Text-Level and Other Elements
| Element | Purpose |
|---|---|
| `<ruby>` | Ruby annotation container (East Asian typography) |
| `<rt>` | Ruby text annotation |
| `<rp>` | Ruby fallback parenthesis |
| `<wbr>` | Word break opportunity hint |

---

## 7. HTML5 Input Types Not Available in XHTML 1.0 Strict

The `type` attribute of `<input>` only accepted a fixed set of values in XHTML. In HTML5, many new types were added:

| New Type | Purpose |
|---|---|
| `email` | Email address input with validation |
| `url` | URL input with validation |
| `number` | Numeric input with spin controls |
| `range` | Slider control |
| `date` | Date picker |
| `time` | Time picker |
| `datetime-local` | Combined date+time picker |
| `month` | Month picker |
| `week` | Week picker |
| `search` | Search field |
| `color` | Color picker |
| `tel` | Telephone number |

**Conflict:** Using these in XHTML 1.0 Strict context causes DTD validation errors. Browsers handle them gracefully, but XHTML validators will reject them.

---

## 8. HTML5 Form Attributes Not Available in XHTML 1.0 Strict

| Attribute | Element | Purpose |
|---|---|---|
| `placeholder` | `input`, `textarea` | Placeholder text |
| `required` | form elements | Client-side required validation |
| `autofocus` | form elements | Auto-focus on load |
| `autocomplete` | `form`, `input` | Browser autocomplete control |
| `pattern` | `input` | Regex validation pattern |
| `min` / `max` | `input` | Value range constraints |
| `step` | `input` | Stepping interval |
| `multiple` | `input[type=file]`, `select` | Multiple values |
| `novalidate` | `form` | Disables built-in validation |
| `formaction` | `button`, `input[type=submit]` | Override form action |
| `list` | `input` | Links to a `<datalist>` |
| `formmethod` | `button`, `input[type=submit]` | Override form method |
| `formenctype` | `button`, `input[type=submit]` | Override form encoding type |
| `formnovalidate` | `button`, `input[type=submit]` | Disable form validation for this submit |
| `formtarget` | `button`, `input[type=submit]` | Override form target |

**Note:** The `action` attribute on `<form>` was required in XHTML 1.0 Strict (inherited from HTML 4). In HTML5 it is optional — it defaults to the current page URL.

---

## 9. Content Model Violations (Nesting Rules)

XHTML 1.0 Strict has a strict content model inherited from HTML 4:

### 9.1 Block elements inside inline elements (illegal in XHTML Strict)
- ❌ `<a href="#"><div>...</div></a>` — block inside inline
- ✅ HTML5 allows this via the **transparent content model** (`<a>` can wrap block content)

### 9.2 Deprecated/Removed Presentational Elements
These were already removed from XHTML 1.0 Strict (they existed in Transitional):
- `<font>`, `<center>`, `<strike>`, `<u>` (as presentational), `<big>`, `<basefont>`, `<applet>`, `<frame>`, `<frameset>`, `<noframes>`, `<isindex>`

HTML5 removed or redefined most of these. Some (`<u>`, `<s>`, `<small>`, `<b>`, `<i>`) were given new **semantic** meanings.

### 9.3 Element Prohibitions (XHTML-specific)
These nesting rules from the XHTML DTD are not expressible in XML and must be honored manually:
- `<a>` must **not** contain other `<a>` elements
- `<pre>` must **not** contain `<img>`, `<object>`, `<big>`, `<small>`, `<sub>`, `<sup>`
- `<button>` must **not** contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`, `<iframe>`
- `<label>` must **not** contain other `<label>` elements
- `<form>` must **not** contain other `<form>` elements

HTML5 enforces similar rules but through its parsing model, not a DTD.

---

## 10. Ampersand Handling

- **XHTML/XML:** The `&` character **must always** be escaped as `&amp;` everywhere, including in URLs:
  - ❌ `<a href="?a=1&b=2">` (invalid XHTML)
  - ✅ `<a href="?a=1&amp;b=2">` (valid XHTML)
- **HTML5:** Still recommended to escape `&` in attribute values, but the HTML parser is more forgiving.

---

## 11. `id` vs `name` Attributes

- **XHTML:** The `name` attribute on `<a>`, `<form>`, `<img>`, `<map>`, `<iframe>`, `<applet>` is **deprecated** in favor of `id`. Fragment identifiers (`#foo`) only work with `id` in XML.
- **HTML5:** `name` on `<a>` is fully obsolete. Use `id` for fragment targets.

**Recommended practice (for backward compatibility):** Use both during transition:
```html
<a id="section1" name="section1">...</a>
```

**Important change — `id` naming rules:** XHTML (XML) requires `id` values to be valid XML Names — they must start with a letter or underscore, and leading digits are forbidden. HTML5 only requires that the value be non-empty and contain no spaces, so leading digits and other characters are now valid. This is a common migration gotcha when moving markup to HTML5.

---

## 12. `lang` vs `xml:lang`

- **XHTML:** Both `lang` and `xml:lang` attributes must be used together. `xml:lang` takes precedence:
  - `<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">`
- **HTML5:** Only `lang` is needed:
  - `<html lang="ja">`

---

## 13. `javascript:void(0)` in href

- Not strictly an XHTML vs HTML5 issue, but `href="javascript:void(0);"` is present in this file and is considered poor practice in modern HTML. Prefer `<button>` elements or `href="#"` with `event.preventDefault()`.

---

## 14. White Space and Character Handling

- **XHTML/XML:** Formfeed character (U+000C) is **illegal** in XML — it is treated as whitespace in HTML.
- **XHTML/XML:** Attribute value white space is normalized (leading/trailing stripped, multiple spaces collapsed to one).
- **HTML5:** More permissive white space handling, aligns with historical browser behavior.
- **`<textarea>` / `<pre>` initial newline:** The HTML parser strips the first newline character immediately following the opening `<textarea>` or `<pre>` tag. The XML parser does not. This is a polyglot authoring requirement:
  ```html
  <textarea>
  hello</textarea>
  <!-- HTML mode: value is "hello" / XML mode: value is "\nhello" -->
  ```

---

## 15. Named Character Reference `&apos;`

- **XHTML/XML:** `&apos;` (apostrophe, U+0027) is a valid XML entity.
- **HTML5/HTML4:** `&apos;` is **not defined in HTML 4**. For maximum compatibility, use `&#39;` instead.

---

## 16. DOM and CSS Implications

### 16.1 Element/Attribute Name Case in DOM
- **XHTML served as `application/xhtml+xml`:** DOM returns element/attribute names in **lowercase** (XML DOM).
- **XHTML served as `text/html`:** DOM returns element/attribute names in **uppercase** (HTML DOM: `element.tagName === "DIV"`).
- **HTML5:** DOM always returns names in **uppercase** for HTML elements.

**Conflict:** JavaScript that checks `element.tagName` may behave differently depending on how the document is served.

### 16.2 CSS `<tbody>` Inference
- **HTML parser** (HTML5 mode): Automatically infers `<tbody>` inside `<table>` if omitted.
- **XML parser** (XHTML mode): Does **not** infer `<tbody>`.

**Conflict:** CSS selectors like `table > tbody > tr` will break in XML mode if `<tbody>` is not explicitly written.

### 16.3 CSS Element Name Case
- CSS selectors for XHTML should use **lowercase** element names (XML is case-sensitive).
- In HTML5 mode, CSS selectors are case-insensitive for HTML elements.

---

## 17. Security Implications

### 17.1 XSS via MIME Type Confusion
- If a document is served as `application/xhtml+xml` but contains user-generated content, XML parsing can expose additional attack vectors (e.g., XML entity expansion attacks — "Billion Laughs").
- HTML5 documents served as `text/html` are not vulnerable to XML-specific attacks.

### 17.2 External Entity Injection (XXE)
- XML documents can reference external entities via the DOCTYPE, which can lead to server-side request forgery (SSRF) or data exfiltration if user input affects the document structure.
- HTML5 documents ignore DTD entity declarations entirely.

---

## 18. Accessibility Implications

HTML5 introduces native ARIA landmark roles through semantic elements:

| HTML5 Element | Implicit ARIA Role |
|---|---|
| `<main>` | `main` |
| `<nav>` | `navigation` |
| `<header>` (in body) | `banner` |
| `<footer>` (in body) | `contentinfo` |
| `<aside>` | `complementary` |
| `<article>` | `article` |
| `<section>` (with accessible name) | `region` |

In XHTML 1.0 Strict, these roles must be added manually via `role="..."` attributes (ARIA), which are themselves not part of the XHTML 1.0 Strict DTD.

---

## 19. XML Processing Instructions

- **XHTML (served as XML):** Processing instructions (PIs) like `<?xml-stylesheet type="text/css" href="styles.css"?>` are fully supported as distinct node types and are preserved in the DOM.
- **HTML5:** Processing instructions do not exist. In HTML parsing, `<?...>` is treated as a **comment that closes on the first `>`**, not on `?>`. The PI content is silently discarded or corrupted:
  - `<?xml-stylesheet type="text/css" href="styles.css"?>` becomes a comment that ends immediately after `<?xml-stylesheet type`, leaving `="text/css" href="styles.css"?>` as stray text in the document.
- **Conflict:** If your XHTML document uses `<?xml-stylesheet?>` or any other processing instructions and is migrated to HTML5 (or served as `text/html`), those PIs are silently lost.

---

## 20. Named Character Entities Without DTD

- **XHTML 1.0 Strict** defines a rich set of named character entities (`&nbsp;`, `&copy;`, `&eacute;`, `&mdash;`, etc.) via its DTD.
- **In true XML mode** (`application/xhtml+xml`), the XML parser is **not guaranteed** to load or process the external DTD. If the DTD is not loaded, any named entity other than the five predefined XML entities causes a **fatal XML parse error**:
  - ✅ Always safe: `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`
  - ❌ Unsafe without DTD: `&nbsp;`, `&copy;`, `&eacute;`, `&mdash;`, etc.
- **Workaround in XHTML:** Use numeric character references: `&#160;` (non-breaking space), `&#169;` (©), `&#8212;` (—).
- **HTML5:** Supports a large set of named character references natively, without any DOCTYPE or DTD.

**Conflict:** Many real-world XHTML documents that use `&nbsp;` extensively will crash with XML parse errors when switched from `text/html` to `application/xhtml+xml` delivery.

---

## 21. `<noscript>` Behavior in XML Mode

- **HTML5:** `<noscript>` works as expected — its content is rendered only when scripting is disabled and hidden when scripting is enabled. The HTML parser handles this through a scripting-flag–dependent parsing mode.
- **XHTML (served as XML):** `<noscript>` has **no effect**. XML does not allow conditional parsing based on runtime state. The `<noscript>` element's children are always parsed and always appear in the DOM, regardless of whether JavaScript is enabled.
- **`<noscript>` is forbidden in XHTML5 polyglot markup** for this reason.

**Conflict:** XHTML documents that rely on `<noscript>` for progressive enhancement or fallback content will silently show that content to **all** users (including those with JavaScript enabled) when served as `application/xhtml+xml`.

---

## 22. DOM Scripting Differences

### 22.1 `document.write()` and `document.writeln()`
- **XHTML (XML mode):** Completely non-functional. `document.write()` has no defined behavior for XML documents and will throw errors or silently do nothing.
- **HTML5:** Functions normally (though discouraged in modern code).

### 22.2 `innerHTML`
- **XHTML (XML mode):** `innerHTML` must contain **well-formed XML**. Assigning malformed markup throws a parse error.
- **HTML5:** Uses the HTML fragment parsing algorithm with error recovery — malformed markup is silently corrected.

### 22.3 Namespace-Aware DOM Methods
In XHTML/XML mode, DOM Level 1 methods that ignore namespaces can silently fail when used with SVG, MathML, or namespaced elements:

| HTML5 (namespace-unaware) | XHTML/XML (correct equivalent) |
|---|---|
| `document.createElement("svg")` | `document.createElementNS("http://www.w3.org/2000/svg", "svg")` |
| `element.getAttribute("xlink:href")` | `element.getAttributeNS("http://www.w3.org/1999/xlink", "href")` |
| `element.setAttribute("xlink:href", val)` | `element.setAttributeNS("http://www.w3.org/1999/xlink", "href", val)` |
| `document.getElementsByTagName("rect")` | `document.getElementsByTagNameNS("http://www.w3.org/2000/svg", "rect")` |

**Conflict:** JavaScript libraries and frameworks that use DOM Level 1 methods may silently fail to create or query namespaced elements in true XML mode.

### 22.4 Third-Party Scripts
Scripts from Google AdSense, social media share buttons, and payment widgets commonly use `document.write()`. They will fail completely in documents served as `application/xhtml+xml`, causing XML parse errors that halt page rendering entirely.

---

## 23. `xml:base` and `xml:space`

### 23.1 `xml:base`
- **XHTML (XML mode):** The `xml:base` attribute can be placed on any element to change the base URI for relative URL resolution within that subtree — a powerful XML feature.
  ```xml
  <div xml:base="https://example.com/images/">
    <img src="logo.png"/>  <!-- resolves to https://example.com/images/logo.png -->
  </div>
  ```
- **HTML5:** `xml:base` is **not supported**. The only mechanism for changing the base URL is the `<base href="...">` element in `<head>`, which applies to the entire document.

### 23.2 `xml:space`
- **XHTML (XML mode):** The `xml:space="preserve"` attribute instructs the XML processor to preserve all whitespace within that element's subtree.
- **HTML5:** `xml:space` is not recognized. Whitespace handling is controlled via CSS (`white-space: pre`, `white-space: pre-wrap`, etc.).
- **`xml:space` is forbidden in polyglot markup** (except inside SVG or MathML subtrees).

---

## 24. Declarative Shadow DOM

- **HTML5:** The `<template shadowrootmode="open">` pattern allows shadow roots to be declared directly in HTML markup. The browser creates a real shadow root and moves template content into it during parsing.
  ```html
  <div id="host">
    <template shadowrootmode="open">
      <style>p { color: red; }</style>
      <p>This is in the shadow DOM</p>
    </template>
  </div>
  ```
- **XHTML (XML mode):** The `shadowrootmode` attribute is ignored. The `<template>` element remains in the DOM as a regular element, and its content is parsed directly into the live DOM (not into a shadow root). No shadow root is created.
- This is a known incompatibility tracked in Mozilla Bug [#1887436](https://bugzilla.mozilla.org/show_bug.cgi?id=1887436).

**Conflict:** Any component library or design system using declarative shadow DOM will produce incorrect output when documents are served as `application/xhtml+xml`.

---

## 25. Migration Summary — XHTML 1.0 Strict → HTML5

| Change Required | Priority |
|---|---|
| Replace DOCTYPE with `<!DOCTYPE html>` | High |
| Remove `xmlns` from `<html>`, keep only `lang` | High |
| Remove `xml:lang` attribute | High |
| Change `<meta name="content-type" ...>` to `<meta charset="UTF-8">` | High |
| Remove `type="text/javascript"` from `<script>` | Medium |
| Remove `type="text/css"` from `<link rel="stylesheet">` | Medium |
| Fix uppercase element names (e.g. `<INPUT>` → `<input>`) | Medium |
| Quote all unquoted attribute values (e.g. `maxlength=50` → `maxlength="50"`) | Medium |
| Escape `&` as `&amp;` in URLs and text | Medium |
| Wrap inline script/style with `<![CDATA[...]]>` if serving as XML | Low (if text/html) |
| Replace `name` anchors with `id` anchors | Low |
| Add semantic HTML5 elements (`<nav>`, `<main>`, `<header>`, `<footer>`) | Optional |
| Add native ARIA landmarks | Recommended |

---

## 26. Quick Reference — Validity Comparison

```html
<!-- XHTML 1.0 Strict — INVALID examples that HTML5 allows -->

<INPUT type="hidden" value="foo">         <!-- uppercase tag = XHTML invalid -->
<br>                                       <!-- no self-close = XHTML invalid -->
<img src="x.gif">                         <!-- no self-close, no alt = XHTML invalid -->
<input disabled>                          <!-- minimized boolean = XHTML invalid -->
<td rowspan=3>                            <!-- unquoted attribute = XHTML invalid -->
<a href="?a=1&b=2">                       <!-- bare & = XHTML invalid -->
<p>First<p>Second                         <!-- unclosed p = XHTML invalid -->
<a href="#"><div>block in inline</div></a><!-- block in inline = XHTML Strict invalid -->

<!-- HTML5 — VALID but XHTML Strict would not allow -->

<!DOCTYPE html>                           <!-- simple doctype = HTML5 only -->
<meta charset="UTF-8">                    <!-- simplified charset = HTML5 only -->
<script>...</script>                      <!-- no type attr needed = HTML5 only -->
<input required>                          <!-- boolean attr = HTML5 valid -->
<input type="email">                      <!-- new input type = HTML5 only -->
<video src="movie.mp4" controls></video>  <!-- video element = HTML5 only -->
<article><section>...</section></article> <!-- semantic elements = HTML5 only -->
```
