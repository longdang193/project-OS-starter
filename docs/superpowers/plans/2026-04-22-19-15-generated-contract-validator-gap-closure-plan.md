---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/doc-system-lifecycle.md
  - docs/operating_system/feature-lifecycle.md
  - docs/operating_system/stage-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
related_features: []
related_stages: []
---

# Generated Contract Validator Gap Closure Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`
**Type:** modify  
**Plan Layer:** operating_system
**Plan Status:** active

> **For agentic workers:** Use `executing-plans` or `subagent-driven-development` to implement task-by-task.

**Goal:** Extend adoption-shape validation so it enforces the remaining generated contract schemas that the starter generator and docs already treat as canonical.

**Architecture:** The work stays centered in `scripts/validate_adoption_shape.py`, adding schema validators for generated stage contracts, generated feature contracts, managed `history.md` boundaries, and generated discovery files. Tests should live in `tests/test_validate_adoption_shape.py`, while operating-system docs should be tightened only enough to say these generated surfaces are validator-enforced managed contracts.

**Key Invariants:**
- Human-owned source files remain the upstream truth; generated artifacts stay generated-only.
- Adoption-shape validation should enforce schema, not reimplement the full generator semantics.
- New checks should catch older drifted shapes like nested stage contracts without making the validator brittle to harmless empty generated discovery.

**Rollout / Revert:**  
- rollback_trigger: The new validator rejects the current starter repo or obviously valid managed fixtures.  
- rollback_method: Revert the new schema validators and their tests, then reintroduce narrower checks one artifact family at a time.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: `docs/stages/*.yaml` contract shape documented in `docs/operating_system/stage-lifecycle.md`
- Feature history: `docs/features/<feature_id>/history.md` contract shape documented in `docs/operating_system/feature-lifecycle.md`
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/operating_system/feature-lifecycle.md`
  - `docs/operating_system/stage-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
- README: none
- Generated discovery: `docs/generated/capability_lineage.yaml`, `docs/generated/architecture_dag.yaml`

---

## Files To Modify

- `scripts/validate_adoption_shape.py`
- `tests/test_validate_adoption_shape.py`
- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/feature-lifecycle.md`
- `docs/operating_system/stage-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`

## Tests To Add Or Update

- Add adoption-shape tests for:
  - valid generated stage contract shape
  - rejection of nested legacy stage contract shape
  - valid generated feature contract shape
  - rejection of malformed managed `history.md`
  - valid minimal generated discovery shape
  - rejection of malformed generated discovery shape
- Keep tests focused on schema, not generator business logic.

## Verification Commands

- `python -m py_compile scripts/validate_adoption_shape.py tests/test_validate_adoption_shape.py`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_adoption_shape.py -q`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python scripts/validate_adoption_shape.py`
- `$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python scripts/validate_adoption_shape.py --repo-root 'C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT'`

---

## Tasks

### Task 1: Add failing adoption-shape tests for the missing generated artifact schemas

1. Extend `tests/test_validate_adoption_shape.py` with fixtures/helpers for:
   - canonical generated feature contract
   - canonical generated stage contract
   - canonical generated discovery files
2. Add failing tests that prove current gaps:
   - nested legacy stage contract is rejected
   - malformed generated feature contract is rejected
   - malformed `history.md` without generated markers / `## Human Notes` is rejected
   - malformed generated discovery files are rejected
3. Run the targeted pytest slice and confirm the new tests fail for the expected reasons.

### Task 2: Implement generated stage and feature contract schema validation

1. Add helper validators in `scripts/validate_adoption_shape.py` for:
   - generated stage contracts under `docs/stages/*.yaml`
   - generated feature contracts under `docs/features/*/<feature_id>.yaml`
2. Enforce:
   - generated-file header
   - top-level mapping shape
   - required keys
   - string-list ref fields
   - rejection of nested legacy stage contract wrappers
3. Re-run the targeted tests and make them green.

### Task 3: Implement managed history and generated discovery schema validation

1. Add minimal managed `history.md` boundary checks:
   - generated start marker
   - generated end marker
   - `## Human Notes`
2. Add generated discovery validators for:
   - `docs/generated/capability_lineage.yaml`
   - `docs/generated/architecture_dag.yaml`
3. Keep discovery checks schema-level and friendly to empty generated outputs.
4. Re-run the targeted tests and make them green.

### Task 4: Update operating-system docs to say these surfaces are validator-enforced

1. Update:
   - `docs/operating_system/stage-lifecycle.md`
   - `docs/operating_system/feature-lifecycle.md`
   - `docs/operating_system/doc-system-lifecycle.md`
   - `docs/operating_system/project-adoption-migration-guide.md`
2. Clarify which generated artifact schemas are now adoption-validator enforced.
3. Keep wording consistent with the canonical source-of-truth model and migration-target language.

### Task 5: Verify against starter and downstream drift

1. Run:
   - `python -m py_compile ...`
   - targeted pytest for `tests/test_validate_adoption_shape.py`
   - `python scripts/validate_adoption_shape.py`
2. Run the starter validator against `JOB-PROJECT`.
3. Confirm it now catches:
   - legacy nested stage contracts such as `docs/stages/enrich.yaml`
   - any additional generated-contract drift surfaced by the new checks
4. Review diff for focused scope and doc/code sync.
