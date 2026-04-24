# Prompt Templates

Use these prompts when you want to guide an agent through the repo process in
a consistent way.

Lifecycle order:

1. `intent-prompt.md`
2. `spec-prompt.md`
3. `plan-prompt.md`
4. `execute-prompt.md`
5. `validate-or-drift-prompt.md`
6. `mode-migration-prompt.md`

Use the smallest prompt that matches the step you actually want.

- use an intent prompt when the project purpose or direction is still fuzzy
- use a spec prompt when the design needs to be written down
- use a plan prompt when the spec is approved and you want execution steps
- use an execution prompt when a plan already exists
- use a validation/drift prompt when you want to find gaps or missing surfaces
- use a mode-migration prompt when you want to assess or plan
  `starter_method_only -> managed_architecture_metadata`

These are guidance files, not required repo artifacts.

When the work is product-direction work, name the roadmap thread it follows.
When it is true operating-system work, say why it should remain
`parent_workstream: none`.
