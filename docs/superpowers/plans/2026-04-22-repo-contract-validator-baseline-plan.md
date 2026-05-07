---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/sync_architecture_docs.py
  - scripts/setup_hooks.ps1
  - scripts/setup_hooks.sh
  - tests/test_setup_hooks.py
  - tests/test_validate_repo_contracts.py
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/lifecycle/feature-lifecycle.md
  - docs/operating_system/lifecycle/stage-lifecycle.md
related_features: []
related_stages: []
created_at: 2026-04-22T18:32:00+02:00
updated_at: 2026-04-22T18:32:00+02:00
spec_refs:
  - docs/superpowers/specs/2026-04-22-repo-contract-validator-baseline-spec.md
---

# Repo Contract Validator Baseline Plan

## Goal

Promote repo validation in the starter from an architecture-only hook target to
a top-level repo-contract validator that future projects can inherit directly.

## Tasks

1. Add `scripts/validate_repo_contracts.py` as the canonical validation entrypoint.
2. Keep `scripts/sync_architecture_docs.py` as the narrower regeneration workflow.
3. Point setup hooks to `validate_repo_contracts.py --fast`.
4. Add focused tests for boundary validation and hook wiring.
5. Update operating-system docs so sync and validate are clearly separated.
