# MediChannel Delivery Coding Standards

All coding shall prioritize readability, maintainability, and reusability.

---

## HTML Coding

### General Rules

- HTML = structure only. Styles → CSS. No inline `style` attributes.
- CSS and JS → external files, loaded after `desktop.css` and `script.css` within the designated template comment markers.
- All tag names lowercase. No omitted closing tags (except void elements).
- No spacer images or layout line breaks. No `<frame>`.
- Paths → document-root-relative (e.g. `/img/foo.jpg`), not relative (`../`).

### File Extensions

- All files must have extensions. HTML → `.html`. Unify if mixed.

### Image Formats

- Allowed: GIF (`.gif`), JPEG (`.jpg`), PNG (`.png`). SVG allowed on content pages.
- WebP **not permitted**.
- Resolution: 72 dpi. `&` in URLs → `&amp;`. Minimize file size while maintaining quality.

### File Size

Total per page (including images): **≤ 800 KB**.

### Template

Use the distributed `MediChannel_template`.

### Unnecessary Files

Delete before delivery: `Thumb.db`, `.DS_Store`, files starting with `._`, `_notes` folder.

### Document Type

**XHTML 1.0 Strict.** Not HTML5.

### Editable Area

Write HTML only between:
```html
<!-- Body editable area starts here -->

Write content here

<!-- Body editable area ends here -->
```

### Accessibility

- All `<img>` → meaningful `alt` text describing the image content.
- No whitespace for letter-spacing adjustment.
- Platform-dependent characters → character entity references (e.g. ①, ㈱, Ⅲ).

### Meta Tags & Page Title

- `<meta name="keywords">` → present, `content=""`.
- `<meta name="description">` → omit on login-required pages.
- `<title>` format: `[Page Name] | [Site Suffix]` (e.g. `製品情報 | MediChannel`).
- `<title>` must match `<h1>`.

### Validation

Always validate. Missing closing tags are not acceptable.

---

## CSS Coding

Use single-selector declarations. Keep specificity low. Avoid element selectors where possible.

### Format

```css
/* Not recommended */
.example {color: #FFFFFF; text-align: center;}

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

### Values

- Use shorthand. Omit units for `0` values. `line-height` → unitless.
- **All sizes in `px`** (font-size, dimensions, spacing, borders). No `rem` or `em` — root font-size is outside our control.

### base.css Rules (overrides global builder defaults)

- Define all color, typography, and spacing tokens as `:root` CSS custom properties in `base.css`.
- Use **semantic color names** (`--color-primary`, `--color-bg`, `--color-text`, etc.).
- `.cst-page` → `max-width: 960px; margin: 0 auto;`. Never `min-width`.
- **No bare unscoped resets** (`* { margin: 0; padding: 0; }`). Scope all resets to `.cst-page` (e.g. `.cst-page *`, `.cst-page ul`).
- `scroll-margin-top` for anchor targets → on `div[id]`, equal to fixed header height (typically `54px`).

```css
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

### CSS3

Permitted. Prepare fallbacks if legacy browser issues are expected.

### Validation

Always validate. No spelling errors or unnecessary styles.

---

## JavaScript Coding

### Libraries

MediChannel loads **jQuery 1.8.3** by default — use it. Do not load other versions or libraries (e.g. prototype.js).

### Plugins

Permitted, but no additional library versions to support them.

### Validation

Always validate. Errors are not acceptable (code with errors may not publish).

---

## QA Scope Boundary — Client-Managed Zones

The following are **excluded from all QA checks and must never be edited**:

| Zone | Scope note |
|------|------------|
| **Site header** | Global nav, logo, login controls |
| **Breadcrumbs** | `#breadcrumb` / `.breadcrumb` element and links |
| **Site footer** | Copyright, site-wide links, legal disclaimers |

If placeholder content (e.g. `/test.html`) appears in the breadcrumb, note as **INFO** for the client — do not raise as a defect or attempt to fix.