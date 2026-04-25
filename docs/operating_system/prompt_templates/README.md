# Prompt Templates

Use these prompts when you want to guide an agent through the repo process in
a consistent way.

Lifecycle order:

1. `intent-prompt.md`
2. `roadmap-to-workstream-prompt.md`
3. `workstream-to-spec-prompt.md`
4. `spec-prompt.md`
5. `plan-prompt.md`
6. `execute-prompt.md`
7. `validate-or-drift-prompt.md`
8. `managed-metadata-update-prompt.md`
9. `mode-migration-prompt.md`
10. `workstream-alignment-review-prompt.md`
11. `roadmap-gap-prompt.md`
12. `roadmap-vs-execution-divergence-prompt.md`

Use the smallest prompt that matches the step you actually want.

- use an intent prompt when the project purpose or direction is still fuzzy
- use a roadmap-to-workstream prompt when you are translating intent or a
  roadmap thread into the right delivery branch
- use a workstream-to-spec prompt when the workstream is known and you want the
  next bounded design slice
- use a spec prompt when the design needs to be written down
- use a plan prompt when the spec is approved and you want execution steps
- use an execution prompt when a plan already exists
- use a validation/drift prompt when you want to find gaps or missing surfaces
- use a managed-metadata update prompt when the repo is already in
  `managed_architecture_metadata` and you want to update or repair managed
  metadata surfaces in place
- use a mode-migration prompt when you want to assess or plan
  `starter_method_only -> managed_architecture_metadata`
- use a workstream-alignment review prompt when you want to sanity-check
  whether a proposed change actually belongs to the named workstream
- use a roadmap-gap prompt when you think the master roadmap may be missing a
  durable thread
- use a roadmap-vs-execution divergence prompt when you want to compare
  upstream roadmap/workstream intent against specs, plans, and execution so far

These are guidance files, not required repo artifacts.

The practical ladder is:

`intent -> roadmap/workstream choice -> spec -> plan -> execution`

with `operating_system` remaining a parallel branch when the work is really
about repo method rather than product delivery.

When the work is product-direction work, name the roadmap thread it follows.
When it is true operating-system work, say why it should remain
`parent_workstream: none`.

When naming a real workstream, use a valid ID from `docs/intent/workstreams/`.
