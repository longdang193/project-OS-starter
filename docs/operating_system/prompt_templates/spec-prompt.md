# Spec Prompt

Use this when the problem is known and you want a design spec.

If the roadmap thread or workstream is still unclear, use
`roadmap-to-workstream-prompt.md` or `workstream-to-spec-prompt.md` first.

```text
Draft a spec for this change.

Change idea:
- problem:
- desired outcome:
- affected area:
- constraints:
- what should stay true:
- roadmap thread this follows (use a valid ID from `docs/intent/workstreams/`, or `none` if this is operating_system work):
- if `none`, why:

Please:
1. classify the work as intent, operating_system, workstream, or change
2. identify the owning docs and targets
3. state how this follows the master roadmap or why `parent_workstream: none` is intentional
4. draft the spec in docs/superpowers/specs/
5. call out the recommended next implementation step after the spec
```

Expected output:
- a spec in `docs/superpowers/specs/`
