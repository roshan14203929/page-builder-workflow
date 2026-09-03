# MediChannel Delivery Coding Standards

All coding shall be done with high readability, taking maintainability and reusability into account.

---

## 4-1. HTML Coding

### General Coding Rules

All coding shall comply with web standards specifications.

- HTML shall only describe document structure (text, headings, tables, etc.); display styles (typeface, size, color, etc.) shall be separated using CSS.
- CSS and JavaScript shall be specified as external reference files.
- All HTML tag names shall be written in lowercase.
- Closing tags shall not be omitted, except for void elements.
- Spacer images and line breaks used for layout purposes shall not be used.
- The `<frame>` element shall not be used. To frame a portion of a page, use the `<iframe>` element.
- Do not specify styles directly on elements using the `style` attribute.
- Paths for images and links shall be written as document-root-relative paths starting with `"/"`, not file-relative paths such as `"../"`.
- Any externalized CSS or JavaScript files shall be loaded after the existing `desktop.css` and `script.css`.

### ② File Extensions

- All file names must include a file extension.
- If files of the same type are referenced with multiple extensions, unify them.
- HTML files shall use the `.html` extension.

### ③ Image Formats

- Acceptable image formats are GIF, JPEG, and PNG, with extensions `.gif`, `.jpg`, and `.png` respectively.
- Image resolution shall be 72 dpi.
- File sizes should be minimized as much as possible while maintaining quality, in consideration of low-bandwidth environments.

### ④ File Size

The total file size per page, including image files, shall be within 800 KB.

### ⑤ Template Usage

The distributed template (MediChannel_template) shall be used for production.

### ⑥ Removal of Unnecessary Files

Unnecessary files not used on the site (such as those listed below) shall be deleted and not included in the deliverable files.
(Thumb.db / .DS_Store / Files starting with "._" / _notes folder)

### ⑦ Document Type Declaration

The document type for MediChannel is XHTML 1.0 Strict. All coding shall conform to this document type.
Note: This is NOT HTML5.

### ⑧ Editable Area

HTML code shall only be written within the area directly below the comment "Body editable area starts here" and above "Body editable area ends here". Do not add HTML code outside this area.

```html
<!-- Body editable area starts here -->

Write content here

<!-- Body editable area ends here -->
```

### ⑨ Accessibility

From an accessibility perspective, at minimum the following shall be observed:

- All images shall have appropriate alternative text (`alt`) that specifically describes the image content.
- Whitespace characters shall not be used to adjust letter spacing.
- Platform-dependent characters must use character entity references. Examples: ①, ㈱, ㊤, Ⅲ, etc.

### ⑩ Validation

Validation must always be performed. Minor mistakes such as missing closing tags shall not occur, or measures to prevent them shall be in place.

---

## 4-2. CSS Coding

Use single-selector declarations as the basis, and keep specificity as low as possible.
Also, avoid element selectors where possible to minimize situations where HTML changes require CSS changes.

### CSS Format

- CSS declaration blocks must always be indented.
- Place one half-width space between the selector and `{`.
- Write the property followed immediately by `:`, then one half-width space, then the value.
- All declaration blocks must end with `;`.
- When listing multiple selectors separated by commas, place each selector on its own line.
- Aim for simple, clean code and avoid writing unused or non-functional styles.

```css
/* Not recommended */
.example {color: #FFFFFF; text-align: center;}

.example-a, example-b, example-c {
  margin-right:10px;
  font-weight:bold;
  margin:10px 0;
}


/* Recommended */
.example {
  color: #FFFFFF;
  text-align: center;
}

.example-a,
.example-b,
.example-c {
  font-weight: bold;
  margin: 10px 0;
}
```

### Value Specification

- Use shorthand notation as much as possible.
- Omit units for properties with a value of `0`. Example: `margin: 0;`
- Units should also be omitted for the `line-height` property in principle.
- **Use `px` for all size values** (font-size, dimensions, spacing, borders). Do not use `rem` or `em` — the page is embedded in a client template whose root font-size is outside our control.

### base.css Structure (overrides global builder defaults)

The following rules apply to MediChannel and override the global `builder.md` guidelines:

- Define all color, typography, and spacing tokens as `:root` CSS custom properties in `base.css`.
  Include `--font-size-*` and `--line-height-*` variables alongside color tokens.
- Use **semantic color variable names** (`--color-primary`, `--color-secondary`, `--color-bg`, `--color-text`,
  `--color-text-muted`, `--color-border`, `--color-bg-light`, `--color-tab-bar`) that match production naming.
- Set `max-width: 960px; margin: 0 auto;` on `.cst-page` for content containment — never `min-width`.
- **Never write bare unscoped element resets** such as `* { margin: 0; padding: 0; }`. All element resets
  must be scoped to `.cst-page` (e.g. `.cst-page *`, `.cst-page ul`, `.cst-page img`). An unscoped reset
  bleeds into the client template and causes `base.css` to override `page.css` component styles.
- The `scroll-margin-top` rule for anchor targets must be placed on `div[id]` (not on individual components)
  and must equal the fixed header height (typically `54px`).

```css
/* Correct `:root` token structure for MediChannel */
:root {
  --color-white: #ffffff;
  --color-black: #000000;
  --color-bg: #f5f3f1;
  --color-primary: #00b398;
  --color-primary-dark: #007260;
  --color-secondary: #ae2573;
  --color-secondary-dark: #881857;
  --color-heading: #333f48;
  --color-text: #333333;
  --color-text-muted: #666666;
  --color-text-annotation: #4d4d4d;
  --color-border: #dddddd;
  --color-bg-light: #f2f2f2;
  --color-tab-bar: #202020;

  --font-size-base: 16px;
  --font-size-sm: 14px;
  --font-size-xs: 12px;
  --line-height-tight: 1.3;
  --line-height-normal: 1.7;
}
```

### CSS3 Selectors and Properties

CSS3 usage is permitted. However, if display issues or accessibility problems are expected in legacy browsers, alternative solutions must be prepared.

### Validation

Validation must always be performed. Minor mistakes such as spelling errors or unnecessary styles shall not occur, or measures to prevent them shall be in place.

---

## 4-3. JavaScript Coding

JavaScript usage shall give full consideration to performance.

### Libraries

MediChannel loads jQuery 1.8.3 by default; this shall be used.
Loading other versions of jQuery or other libraries such as prototype.js is prohibited.

### Plugins

Plugin usage is permitted.
However, as stated above, loading other library versions to run plugins is prohibited.

### Validation

Validation must always be performed. Errors are not acceptable. (Code with errors may not be published.)

---

## 4-4. QA Scope Boundary — Client-Managed Zones

The following zones are owned and deployed by the client; they are **excluded from
all QA checks and must never be edited** in any deliverable:

| Zone | Scope note |
|------|------------|
| **Site header** | Global navigation bar, logo, login controls |
| **Breadcrumbs** | The `#breadcrumb` / `.breadcrumb` element and its links |
| **Site footer** | Copyright notice, site-wide links, legal disclaimers |

Changes to these areas ripple across the entire site and are outside the
India Creative Team's change control. If placeholder content (e.g. `/test.html`,
empty `<span>`) is observed in the breadcrumb, note it as **INFO** for the
client but do not raise it as a deliverable defect and do not attempt to fix it.
