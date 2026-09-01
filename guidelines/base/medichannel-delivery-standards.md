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
