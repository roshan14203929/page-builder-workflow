# AZ HTML Production — QA Guide for the India Creative Team

> ⚠️ Examples, URLs, commands, and numbers here are from my own environment. Verify in yours before use.

---

## Purpose & Approach

### About this guide

QA workflow for HTML production using Claude Code + Figma MCP. Three QA phases:
1. **Design QA** — WF vs design diff
2. **Content QA** — copy accuracy (Design vs Code)
3. **Coding QA** — typography metrics and guideline compliance

### Where QA sits in the production flow

```
WF (Figma wireframe)
   ↓
Design (Figma PC/SP)        ← ① Design QA: WF vs Design
   ↓
Coding (XHTML/CSS)          ← ② Content QA: copy accuracy (Design vs Code, text only)
                            ← ③ Coding QA: technical compliance (XHTML / guidelines)
   ↓
Publish (MediChannel)
```

- **① Design QA** — diff between WF and design comp (text / numbers / reference-number mismatches)
- **② Content QA** — character-by-character copy verification: every visible string in HTML matches design; no placeholder copy remains
- **③ Coding QA** — technical compliance: typography metrics (font-size / line-height) and XHTML / MediChannel guideline checks

---

## Design QA — WF vs Design diff

Detect mismatches between the WF and design comps (PC/SP).

> This guide shows only **instructions you give Claude Code**. To understand what's happening under the hood, ask Claude Code "what steps did you use to check this?"

### WF vs Design diff

Ask for text match and image (graph/chart) comparison in one request — no need to split.

**Example instruction:**
```
Compare the Figma links below and check the diff between the WF and the design.

- WF:     <Figma link>
- Design: PC: <Figma link>   SP: <Figma link>

Check for:
1. Heading / body copy wording (missing additions, inconsistent notation)
2. Superscript / subscript / special characters
3. Content inside graph/chart images (footnote numbers, number mismatches) — compare via screenshots

For any diff, list as "location / WF side / Design side".
```

- String matches are caught mechanically. Graph/chart numbers live inside images — Claude Code takes screenshots to compare visually.
- Large parent frames shrink too small to read. **Split links by section / panel.**
- If it replies "can't find the text", ask Claude Code to confirm whether the target is text or embedded in an image/shape.

> ⚠️ If someone edits Figma in parallel, fetched data goes stale. If "I fixed it but it's not reflected" — ask Claude Code to **"fetch the latest state again."** Re-fetch and confirm on the spot.

### Design guideline compliance

Guidelines **differ by brand**. Use the guideline page in Figma matching the project's brand. Ask the project lead for the current link.

Typical items (Breztri/BRZ example):
- **Color** — Basic Color (black/white), Brand Color (Primary: Yellow / Teal / Dark Grey), Page Original Color (reuse reference colors; don't create custom ones)
- **Typography** — brand fonts (Gotham, Arial). Where unavailable as device fonts, limit to image exports (e.g. Hero)
- **Logo** — clear space rules and naming convention for variations

**Example instruction:**
```
Compare this design guideline (Figma link) with this design (Figma link) and check
whether color, fonts, and logo comply with the guideline.

For any violation, report "location / guideline rule / actual value in design".
```

---

## Content QA — copy accuracy (Design vs Code)

Verify every visible string in the HTML matches the design comp character-by-character. Text only — no layout or styling. A live Figma MCP connection is helpful but not required.

**Editable area: only inside `.cst-page`.** Don't touch header / footer / nav.

### Design vs Code copy match

**Example instruction:**
```
Compare the design below with this HTML file (path).

- Design: PC: <Figma link>   SP: <Figma link>

Check for:
- Character-by-character differences in headings (H1–H4), body copy, footnotes,
  and reference numbers (including ®, superscript, subscript, half/full-width, spaces)
- Full-width vs half-width numerals and punctuation (Japanese pages)
- Strings in HTML missing from design, or in design missing from HTML

For any diff, list as "location / Design side / implemented side".
```

### Placeholder detection

Run in the same session or as a follow-up. Placeholder copy shipping to production is a blocker.

**Example instruction:**
```
Read this HTML file (path) and check for unreplaced placeholder copy:

- Breadcrumb links pointing to "/test.html" or containing " test" as visible text
- Approval code placeholders like "JP-○○○○" in .cst-page-info or footer note elements
- Other obviously temporary text (e.g. "Lorem", "TODO", "PLACEHOLDER", "ここに入る")

Report each hit with element, line number, and placeholder text.
```

---

## Coding QA — typography metrics & guideline compliance

Verify HTML/CSS complies with XHTML / MediChannel guidelines and typography metrics match the Figma spec.
**Editable area: only inside `.cst-page`.** Don't touch header / footer / nav.

> Copy accuracy is covered in Content QA. This chapter covers only technical and visual-metric compliance.

> **Assumption:** targets the **MediChannel** case. Non-MediChannel (3rd Party) has different editable areas and guidelines — out of scope here.

### Typography metrics (font size, line height)

Check that font-size and line-height rendered in the browser match the Figma spec.

**Example instruction:**
```
Compare the design below with this HTML file (path) rendered in the browser.

- Design: PC: <Figma link>   SP: <Figma link>

Check diffs between specified and actually rendered font size / line height (PC and SP separately).

For any diff, list as "location / Design side / implemented side".
```

Example from a real case (SP): H2 heading 20px (design: 24px), chart title 16px (20px), lead text 16px (20px). *(Illustrative — your numbers will differ.)*

### Coding guideline compliance

A check against **existing formal guideline documents**, not a Figma comparison.

> ⚠️ `guidelines/base/html-coding-rules.md` covers shared HTML/CSS rules but targets 3rd Party (HTML5). For MediChannel (XHTML), **prefer the two files below**.

Formal documents in `guidelines/base/`:
- `xhtml-coding-rules.md` — XHTML 1.0 Strict rules, naming conventions, accessibility, CSS variables
- `medichannel-delivery-standards.md` — editable area, document type, file size, delivery rules

**Example instruction:**
```
Read guidelines/base/xhtml-coding-rules.md and guidelines/base/medichannel-delivery-standards.md,
and check whether index.html / base.css / page.css violates any rules.

For anything found, report "file + line number / current code / corrected code / reason".
```

> **Reduce noise:** check in order "silent breakers (CSS variables, text) first, appearance last." Don't flag dead CSS (no element uses it). Don't flag design-vs-implementation diffs that also exist in Figma (Figma is source of truth). Split "no real impact" items as Info.

> Diffs can be fixed by Claude Code directly — instruction templates return "corrected code", so check and fix in one pass.