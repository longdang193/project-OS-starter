---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/operating_system/lifecycle/feature-lifecycle.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Managed Feature Folder Validator Alignment Plan

**Feature Source:** `none`
**Feature Contract:** `none`
**Spec:** `docs/superpowers/specs/2026-04-22-managed-feature-folder-validator-alignment-spec.md`
**Type:** modify
**Plan Layer:** operating_system
**Plan Status:** active

**Goal:** Align managed-mode validation with the documented required feature-folder shape.

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
  - `docs/operating_system/lifecycle/feature-lifecycle.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
- README: none
- Generated discovery: none

### Task 1: Tighten Validator Enforcement

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Docs: `docs/operating_system/lifecycle/feature-lifecycle.md`, `docs/operating_system/skill-doc-system-lifecycle.md`

- [ ] Step 1: Require `<feature_id>.yaml`, `lineage.generated.yaml`, and `history.md` in managed mode.
- [ ] Step 2: Keep validator messages explicit about whether the fix is create vs regenerate.
- [ ] Step 3: Update operating-system docs so required vs optional folder members match enforcement.

### Task 2: Expand Test Coverage

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`

- [ ] Step 1: Add a reusable managed-feature fixture helper with the full required folder shape.
- [ ] Step 2: Add failing cases for missing `feature.source.yaml`, `<feature_id>.yaml`, `lineage.generated.yaml`, and `history.md`.
- [ ] Step 3: Keep at least one managed-mode passing fixture.

### Task 3: Verify

**Files:**
- Test: `tests/test_validate_adoption_shape.py`

- [ ] Step 1: Run `python scripts/validate_adoption_shape.py`.
- [ ] Step 2: Run `python -m pytest tests/test_validate_adoption_shape.py -q`.
- [ ] Step 3: Summarize remaining environment limits if any.
