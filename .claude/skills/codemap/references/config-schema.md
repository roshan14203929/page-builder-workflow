# Codemap configuration

Store the configuration at `.codemap/config.json` by default.

```json
{
  "version": 1,
  "project": "Example project",
  "description": "One sentence describing the repository.",
  "maxFileBytes": 2097152,
  "exclude": ["vendor/**", "generated/**"],
  "entryPoints": ["src/main.py", "scripts/cli.py"],
  "modules": [
    {
      "id": "runtime",
      "label": "Runtime",
      "layer": "Application",
      "description": "Coordinates the primary application flow.",
      "paths": ["src/runtime/**", "src/main.py"],
      "dependencies": ["contracts"],
      "entryPoints": ["src/main.py"]
    }
  ]
}
```

## Fields

- `version`: must be `1`.
- `project`: human-readable project name.
- `description`: concise repository purpose.
- `maxFileBytes`: optional per-file scan limit, defaulting to 2 MiB. Larger
  text files are hashed and line-counted in chunks without loading their full
  content; import inference is skipped and a warning is recorded.
- `exclude`: optional repository-relative glob patterns added to the built-in
  exclusions. Built-ins cover dependency folders, VCS data, caches, common
  build output, `.codemap/`, binary media, and OS metadata.
- `entryPoints`: optional repository-level entry points.
- `modules`: non-empty array of functional modules.

Each module requires:

- `id`: unique lowercase kebab-case identifier.
- `label`: short display name.
- `layer`: architectural band used to group the visual map.
- `description`: one sentence stating responsibility, not implementation.
- `paths`: one or more repository-relative globs. A file should normally match
  exactly one module.

Optional module fields:

- `dependencies`: explicit module IDs. These are merged with dependencies
  inferred from relative JavaScript, TypeScript, CSS, and Python imports.
- `entryPoints`: module-specific entry points.

## Module design

Prefer stable capabilities such as `state-controller`, `artifact-contracts`,
`visual-validation`, or `agent-guidance`. Avoid nodes for individual helper
files unless that file is independently operated or is a true entry point.

The generator reports:

- `uncoveredFiles`: files that match no module;
- `overlaps`: files claimed by multiple modules; and
- unresolved relative imports in each file record.

Resolve overlaps by tightening patterns. Either assign uncovered source files
or explicitly exclude intentional noise. Generated project artifacts may be
represented by one lifecycle module rather than enumerated by run.
