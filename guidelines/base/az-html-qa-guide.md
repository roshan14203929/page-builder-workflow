# AZ HTML Production — QA Guide for the India Creative Team

> ⚠️ The instruction examples, URLs, commands, and specific numbers here are examples from my own environment. Check the latest in your own environment before using them.

---

## 0. Purpose & Approach

### 0-1. About this guide

A QA workflow for HTML production using Claude Code + Figma MCP. Two parts:
1. **How to connect Figma MCP** (Chapter 1)
2. **How to run Design QA / Content QA / Coding QA** (Chapters 2–4)

### 0-2. Where QA sits in the production flow

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

- **① Design QA** — diff between the WF and the design comp (text / numbers / reference-number mismatches, etc.)
- **② Content QA** — character-by-character copy verification: every visible string in the HTML matches the design comp exactly, and no placeholder copy remains.
- **③ Coding QA** — technical compliance: typography metrics (font-size / line-height) and XHTML / MediChannel guideline checks.

---

## 1. Setup

### 1-0. What MCP is (background)

**MCP (Model Context Protocol)** is a standard that lets AI tools like Claude Code talk directly to external services — here, Figma. With it, **Claude Code can read a Figma file's structure, text, colors, and sizes directly, without you opening the file**. All you need to remember: "connect Figma MCP → Claude Code can *read and operate on* your Figma design."

### 1-1. Open Claude Code and connect Figma MCP

> ⚠️ **To confirm:** whether Claude Code is already installed on the India CT machines is not confirmed. This assumes it's installed and covers startup → connection only. If it isn't installed, a separate setup step is needed.

**Steps:**

1. In the Claude Code chat box, type this line and press Enter (first time only):
   ```
   /plugin marketplace add anthropics/claude-plugins-official
   ```
2. Then type one more line and press Enter:
   ```
   /plugin install figma@claude-plugins-official
   ```
3. A browser opens with the Figma login screen. Log in with **your own Figma account** and approve the connection.
4. Back in Claude Code, just say (in English or Japanese) "check whether you're connected to Figma." If Claude Code returns your Figma account name via the `whoami` tool, the connection succeeded.

- ※ These plugin commands can change with Claude Code updates. If it won't connect, check the current install method.
- Once connected, just pasting a Figma link lets Claude Code read the design's contents (text / images / styles). You don't normally need to be aware of which tools run under the hood.

### 1-2. Launch Claude Code inside the target repository

The instruction examples in Chapters 2–4 point at local files like "this HTML file" or "this page.css". So Claude Code can read and write them, **launch Claude Code inside the folder of the cloned repository**.

### 1-3. Preview environment

Some checks (browser-rendered values such as font size / line height) need the page rendered — use your usual preview environment.

---

## 2. Design QA — WF vs Design diff

Detect mismatches between the WF (wireframe) and the design comps (PC/SP) built from it.

> This guide only shows the **instructions you give Claude Code**. If you ever want to know what's happening under the hood, just ask your own Claude Code "what steps did you use to check this?" and it will explain. You don't normally need to.

### 2-1. WF vs Design diff (ask for text + image comparison in one request)

Comparing WF and design is most efficient when you **ask for the text match and the image (graph/chart) visual comparison in a single request** — no need to split into two.

**Example instruction to Claude Code:**
```
Compare the Figma links below and check the diff between the WF and the design.

- WF:     <Figma link>
- Design: PC: <Figma link>   SP: <Figma link>

Check for:
1. Heading / body copy wording (missing additions, inconsistent notation)
2. Superscript / subscript / special characters
3. Content inside graph/chart images (footnote numbers, number mismatches) — compare via screenshots

For any diff, list it as "location / WF side / Design side".
```

- **Heading / body copy string matches** can be caught mechanically (missing text, notation drift).
- **Graphs/charts rendered as images** can't be caught by text comparison alone (the numbers and footnote references live inside the image), so have Claude Code take screenshots and compare them visually.
  - A huge parent frame captured in one shot shrinks too small to read. Tip: **split the links by section / panel.**
- **When it doesn't pick things up:** if it replies "can't find the text", ask Claude Code to confirm whether the target is really text (vs. embedded in an image or shape).

> ⚠️ **Note:** even within one session, if someone edits Figma directly in parallel, data fetched a moment ago can go stale. If "I fixed it but it's not reflected", just **ask Claude Code to "fetch the latest state again."** Don't assume caching — re-fetch and confirm on the spot.

### 2-2. Design guideline compliance

Design guidelines **differ by brand**. Check the guideline page in Figma that matches the project's brand.

Example: Breztri (BRZ) — the guideline page lives in the brand's Figma file. Ask the project lead for the current link.

Typical items in a brand guideline (Breztri example):
- **Color** — Basic Color (black/white), Brand Color (Primary: Yellow / Teal / Dark Grey), Page Original Color (reference colors used within the design; as a rule don't create custom colors, reuse colors from reference materials)
- **Typography** — brand fonts (Gotham, Arial). Where they can't be used as device fonts, limit to image exports such as Hero.
- **Logo** — logo isolation (surrounding clear space) rules, and the naming convention for variations.

**Example instruction to Claude Code:**
```
Compare this design guideline (Figma link) with this design (Figma link) and check
whether the use of color, fonts, and logo complies with the guideline.

For anything that looks like a violation, report "location / guideline rule / actual value in the design".
```

- Swap the guideline page link per project brand each time.

---

## 3. Content QA — copy accuracy (Design vs Code)

Verify that every visible string in the coded HTML matches the design comp character-by-character. No layout or styling — text only. This phase can be run with just the HTML file and a Figma screenshot; a live Figma MCP connection is helpful but not required.

**The editable area is only inside `.cst-page`.** Don't touch header / footer / nav.

> This focuses on the **instructions you give Claude Code**. If you need the mechanism behind it, just ask your own Claude Code.

### 3-1. Design vs Code copy match

**Example instruction to Claude Code:**
```
Compare the design below with this HTML file (path).

- Design: PC: <Figma link>   SP: <Figma link>

Check for:
- Character-by-character differences in headings (H1/H2/H3/H4), body copy,
  footnotes, and reference numbers
  (including ®, superscript, subscript, half/full-width characters, presence of spaces)
- Full-width vs half-width numerals and punctuation (Japanese pages)
- Any visible string present in the HTML but missing from the design, or in the
  design but missing from the HTML

For any diff, list it as "location / Design side / implemented side".
```

### 3-2. Placeholder detection

Run this in the same session or as a follow-up. Placeholder copy that ships to production is a blocker.

**Example instruction to Claude Code:**
```
Read this HTML file (path) and check for any placeholder copy that was not
replaced before delivery. Look for:

- Breadcrumb links that still point to "/test.html" or contain " test" as visible text
- Approval code placeholders such as "JP-○○○○" in .cst-page-info or footer note elements
- Any other obviously temporary text (e.g. "Lorem", "TODO", "PLACEHOLDER", "ここに入る")

Report each hit with the element, line number, and the placeholder text found.
```

---

## 4. Coding QA — typography metrics & guideline compliance

Verify that the coded HTML/CSS complies with the XHTML / MediChannel guidelines and that typography metrics match the Figma spec.
**The editable area is only inside `.cst-page`.** Don't touch header / footer / nav (changes there ripple across the whole site).

> Copy and text accuracy is covered in Chapter 3 (Content QA). This chapter covers only technical and visual-metric compliance.

> **Assumption:** this chapter targets the **MediChannel** case. Non-MediChannel (3rd Party) cases have different editable areas and guidelines, so they're out of scope here (to be organized separately).

> As above, this focuses on the **instructions you give Claude Code**. If you need the mechanism behind it, just ask your own Claude Code.

### 4-1. Typography metrics (font size, line height)

Work that the formal guideline docs don't cover — **matching typography metrics against the Figma design**.

Check that the font-size and line-height values actually rendered in the browser match the values specified in the Figma design.

**Example instruction to Claude Code:**
```
Compare the design below with this HTML file (path) rendered in the browser.

- Design: PC: <Figma link>   SP: <Figma link>

Check for:
- Diffs between the specified font size / line height and the value actually rendered
  in the browser (PC and SP separately)

For any diff, list it as "location / Design side / implemented side".
```

Example from a real case (found on SP): H2 heading 20px (design was 24px), chart title 16px (20px), lead text 16px (20px). *(Illustrative — your numbers will differ.)*

### 4-2. Coding guideline compliance

This is not a Figma comparison but a check against the **existing formal guideline documents**. You don't need to invent checkpoints from scratch.

> ⚠️ **Note:** `guidelines/base/html-coding-rules.md` and the existing `/html-css-review` skill are rules/tools for **3rd Party (HTML5)** cases. MediChannel (XHTML) is different — don't use them for this guide. For MediChannel, refer only to the two below.

Formal documents to reference (in `guidelines/base/`):
- `xhtml-coding-rules.md` (rules specific to XHTML 1.0 Strict — also covers naming conventions, accessibility, CSS variables, etc.)
- `medichannel-delivery-standards.md` (MediChannel delivery rules: editable area, document type, file size, etc.)

**Example instruction to Claude Code:**
```
Read guidelines/base/xhtml-coding-rules.md and guidelines/base/medichannel-delivery-standards.md,
and check whether this index.html / base.css / page.css violates any of those rules.

For anything found, report "target file + line number / current code / corrected code / reason".
```

> **Finding granularity (add this to reduce noise):** check in the order "silent breakers (CSS variables, text) first, appearance last." Don't flag a CSS typo if no HTML element uses it (dead code). Don't flag a design-vs-implementation difference if Figma has it too (Figma is the source of truth). Split out "no real impact" items as Info.

> Diffs you find can be fixed by Claude Code directly — the instruction templates return "corrected code", so you can go from check to fix in one pass.

---

## 5. Future direction (concept)

In future I'd like to move beyond QA — toward generating HTML/CSS from the Figma design, and doing Figma/code edits, all within Claude Code + Figma MCP. The plan is to harden the QA side first, then feed the "types of design-vs-code drift" it surfaces back into generation as quality criteria. Direction only, for now.
