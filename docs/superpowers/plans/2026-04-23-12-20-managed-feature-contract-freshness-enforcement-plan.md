---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/lifecycle/feature-lifecycle.md
  - docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md
  - docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md
related_features: []
related_stages: []
---

# Managed Feature Contract Freshness Enforcement Implementation Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-23-managed-feature-contract-freshness-enforcement-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make managed generated feature contracts fail validation unless they include `revision`, `latest_change_id`, and `last_updated_at`.

**Architecture:** `scripts/validate_adoption_shape.py` owns adoption-shape schema checks. The validator should require freshness metadata directly from every managed generated feature contract instead of deriving that requirement from sibling lineage timeline contents. Operating-system docs and prior specs should describe the tightened contract plainly.

**Key Invariants:**

- Freshness metadata belongs in generated `<feature_id>.yaml`, not `feature.source.yaml`.
- `timeline: []` must not exempt a managed generated feature contract from the freshness schema.
- The validator checks presence and type, not semantic correctness of timestamps or change IDs.
- Existing unrelated generator/test working-tree changes must remain untouched.

**Rollout / Revert:**
- rollback_trigger: Focused validator tests fail in a way unrelated to freshness enforcement.
- rollback_method: Revert the validator freshness block, the added tests, and the docs wording changes from this plan.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/adoption/project-adoption-migration-guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/lifecycle/feature-lifecycle.md`
  - `docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md`
  - `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`
- README: none
- Generated discovery: none

## Task 1: Add Failing Validator Coverage

**Files:**

- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add a test where a managed feature contract omits freshness metadata and sibling `lineage.generated.yaml` has `timeline: []`.
- [x] Step 2: Assert the validator fails with the required freshness metadata message.
- [x] Step 3: Add a partial-freshness test where only one freshness key is present.
- [x] Step 4: Add an invalid-type test for non-integer `revision` and empty string freshness values.
- [x] Step 5: Run:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_adoption_shape.py -k "freshness or rich_lineage" -q
```

- [x] Step 6: Confirm the current validator allowed the drift with direct JOB-PROJECT validation before changing production validator code.

## Task 2: Tighten Validator Freshness Enforcement

**Files:**

- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`

- [x] Step 1: In `validate_generated_feature_contract_schema()`, compute missing freshness keys unconditionally for each managed generated feature contract.
- [x] Step 2: Emit an error when any of `revision`, `latest_change_id`, or `last_updated_at` is missing.
- [x] Step 3: Keep or tighten existing type checks:
  - `revision` must be an integer.
  - `latest_change_id` must be a non-empty string.
  - `last_updated_at` must be a non-empty string.
- [x] Step 4: Remove the sibling-lineage `timeline` condition for missing freshness metadata.
- [x] Step 5: Run the focused tests from Task 1 and confirm they pass.

## Task 3: Align Guidance And Specs

**Files:**

- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Modify: `docs/superpowers/specs/2026-04-22-feature-contract-freshness-metadata-spec.md`
- Modify: `docs/superpowers/specs/2026-04-22-generated-contract-validator-gap-closure-spec.md`

- [x] Step 1: Replace soft conditional wording that says freshness metadata is required only when completed-plan metadata or completed lineage exists.
- [x] Step 2: State that current managed generated feature contracts require `revision`, `latest_change_id`, and `last_updated_at`.
- [x] Step 3: State that `timeline: []` does not exempt generated feature contracts from the freshness schema.
- [x] Step 4: Preserve the ownership boundary: freshness metadata remains generated and does not belong in `feature.source.yaml`.

## Task 4: Verify And Review

**Files:**

- Test: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Run focused validator tests:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_adoption_shape.py -k "freshness or rich_lineage" -q
```

- [x] Step 2: Run the full adoption-shape test file:

```powershell
$env:PYTHONPATH=(Resolve-Path '.tmp-tests\pytest-deps').Path; python -m pytest tests/test_validate_adoption_shape.py -q
```

- [x] Step 3: Run starter validation:

```powershell
.venv\Scripts\python.exe scripts\validate_repo_contracts.py --fast
```

- [x] Step 4: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 5: Review `git diff` and confirm unrelated pre-existing changes were not modified.

## Execution Notes

- Focused validator tests passed: `4 passed, 38 deselected`.
- Full adoption-shape validator tests passed: `42 passed`.
- The pre-fix drift was reproduced with direct validation of JOB-PROJECT; the
  local pytest entrypoint was unavailable until `uv run` was approved.
- Direct starter adoption-shape validation passed.
- `tools/docs/generate_architecture_metadata.py --check` reported generated outputs are current.
- `git diff --check` passed with line-ending warnings only.
- `scripts/validate_repo_contracts.py --fast` and `scripts/sync_architecture_docs.py --check` both passed their pre-pytest checks but could not complete the bundled pytest phase because `.tmp-tests/architecture-pytest` is permission-blocked on this Windows checkout.
