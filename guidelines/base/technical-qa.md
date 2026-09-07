# Technical QA defaults

- Validate document structure, local asset references, console output, local
  request failures, viewport overflow, CSS loading, and JavaScript errors.
- Reject unresolved placeholders, missing files, remote runtime dependencies,
  and paths that escape the generated directory.
- Verify the page works from the included local server without the agent host.
- Keep reports machine-readable and include exact evidence.

## General Rendering

- Page renders without console errors in target browsers.
- **MediChannel targets:** Win11 Edge, Win11 Chrome, macOS Safari, and mobile
  simulation (iPhone/Safari, Android/Chrome, iPad/Safari).
- **M3 targets:** Win11 Edge, Win11 Chrome, Win11 Firefox, macOS Safari, and
  mobile simulation (iPhone/Safari).
- Page displays correctly at 1280px (desktop) and 375px (mobile).
- No unwanted horizontal scroll at any viewport width.

## Delivery

- Total page file size including all images must not exceed 800 KB.
- All files stored with correct naming convention per project delivery requirements.
