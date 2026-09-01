@AGENTS.md

Use `/build-figma-page` to run the workflow. The main Claude session is the
orchestrator. It must invoke the configured subagents itself because subagents
must not coordinate or recursively delegate. Keep all writes scoped to the
selected project, page, source, and run.

