---
thread_id: starter-adoption-experience.adoption-prompt-discoverability-without-duplication
status: dropped
drop_reason: Existing prompt ladder and adoption migration guide already provide sufficient discoverability coverage for current scope; no bounded duplicate-reduction change is required now.
drop_approved_by: Antigravity
dropped_at: 2026-05-08T12:27:00Z
---

# Adoption Prompt Discoverability Without Duplication

## Goal

Keep adoption, migration, and managed-update prompts easy to find without
repeating the same lifecycle explanation across too many docs.

## Why Now

The prompt pack now covers many adjacent adoption flows, so the repo risks
drifting into duplicated README, governance, and prompt wording if
discoverability is not treated as its own bounded slice.

## Dependencies

- current prompt taxonomy should stay stable enough to organize cleanly

## Shared Surfaces

- `docs/operating_system/prompt_templates/README.md`
- `docs/operating_system/adoption/project-adoption-migration-guide.md`
- `docs/operating_system/governance/repo-governance.md`

## Notes

- this may be solvable through docs-only refinement without validator work
- keep it separate from prompt metadata so the repo can advance the two slices independently
