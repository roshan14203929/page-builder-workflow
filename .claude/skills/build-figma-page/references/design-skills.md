# Design skill routing

These project-local skills supplement the Figma workflow. They do not create
new state transitions or QA kinds, and they cannot weaken the source contract,
effective guidelines, deterministic checks, or release gates.

## Design Taste during construction

The `taste-skill` is not available in this project. Skip Design Taste routing.
The page builder proceeds directly from the normalized spec and effective
guidelines without a Design Read step.

## Web Interface Guidelines during QA

UI and accessibility reviewers use the base guideline files (`ui-qa.md`,
`accessibility-qa.md`) directly. No external fetch is required and no
`webInterfaceGuidelines` provenance object is expected.
