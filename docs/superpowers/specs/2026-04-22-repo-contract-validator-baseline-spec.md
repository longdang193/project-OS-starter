---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/sync_architecture_docs.py
  - scripts/setup_hooks.ps1
  - scripts/setup_hooks.sh
  - tests/test_setup_hooks.py
  - tests/test_validate_repo_contracts.py
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/repo-governance.md
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/stage-lifecycle.md
related_features: []
related_stages: []
created_at: 2026-04-22T18:30:00+02:00
updated_at: 2026-04-22T18:30:00+02:00
---

# Repo Contract Validator Baseline Spec

## Goal

Add a canonical repo-contract validator to the starter so future repos inherit
one top-level validation command for:

- architecture sync freshness
- adoption-shape rules
- repo-config validation
- required metadata coverage
- partially generated `history.md` boundary validation

## Scope

The starter should:

- keep `scripts/sync_architecture_docs.py` as the regeneration-focused command
- add `scripts/validate_repo_contracts.py` as the broader repo-validation gate
- point setup hooks to the new validator in fast mode
- teach operating-system docs to distinguish sync from validate
- include focused tests for the new validator surface

## Invariants

- Starter validation should compose existing checks instead of replacing them.
- Adoption-shape validation remains part of the canonical validation story.
- Hook guidance, tests, and operating-system docs should all point to the same command.
- Partial-generated files should be validated as bounded mixed surfaces, not only regenerated opportunistically.
