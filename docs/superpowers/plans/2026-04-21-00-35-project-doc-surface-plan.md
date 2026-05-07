---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - README.md
  - docs/setup.md
  - docs/configuration.md
  - docs/usage.md
  - docs/pipeline.md
  - docs/architecture.md
  - docs/adoption_guide.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/governance/repo-governance.md
  - scripts/validate_adoption_shape.py
  - scripts/sync_architecture_docs.py
  - scripts/setup_hooks.ps1
  - scripts/setup_hooks.sh
  - .github/workflows/repo-hooks.yml
  - tests/test_validate_adoption_shape.py
  - tests/test_setup_hooks.py
related_features: []
related_stages: []
---

# Project Documentation Surface Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-21-project-doc-surface-spec.md`  
**Type:** add  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Define the required root documentation set under `docs/`, add starter placeholders for the required docs, and enforce the required set through the repo validation and hook path.

**Architecture:** The work is cross-cutting operating-system governance. It updates the human-facing guidance in `README.md` and `docs/operating_system/*.md`, adds the required starter doc files under `docs/`, and extends `scripts/validate_adoption_shape.py` plus hook/CI wiring so missing required docs fail the normal validation path.

**Key Invariants:**
- `README.md` remains a summary and navigation layer rather than absorbing all detailed project docs.
- The required root docs are machine-checkable and must be enforced through the existing validation flow.
- Optional docs are documented but do not fail validation when absent.
- Feature/stage/source-of-truth ownership rules remain unchanged.

**Rollout / Revert:**  
- rollback_trigger: validation or hook updates create noisy false failures for the starter repo  
- rollback_method: remove the required-doc validator block and its tests, keep prose-only guidance, and restore prior hook/CI behavior

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/adoption_guide.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/governance/repo-governance.md`
- Operating-system docs:
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/governance/repo-governance.md`
- README: `README.md`
- Generated discovery: none

---

### Task 1: Add Required Root Doc Placeholders

**Files:**
- Create: `docs/setup.md`
- Create: `docs/configuration.md`
- Create: `docs/usage.md`
- Create: `docs/pipeline.md`
- Create: `docs/architecture.md`
- Docs: `README.md`

- [x] Step 1: Create the five required root docs with concise starter-safe placeholders that describe intended scope.
- [x] Step 2: Update `README.md` bootstrap guidance so it points projects to the standard root doc set under `docs/`.
- [x] Step 3: Verify the new files use consistent naming and are clearly cross-cutting rather than feature-local.

### Task 2: Update Governance And Adoption Docs

**Files:**
- Modify: `docs/adoption_guide.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Docs: exact entries above

- [x] Step 1: Update the adoption guide to name the required and optional root doc set.
- [x] Step 2: Update doc-system lifecycle guidance so `docs/*.md` explicitly includes the standard root project docs.
- [x] Step 3: Update repo governance to state that the required root docs are part of the enforced repo doc surface.
- [x] Step 4: Check that the guidance remains consistent with the no-double-entry and ownership model.

### Task 3: Enforce Required Docs In Validation And Hooks

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `scripts/sync_architecture_docs.py`
- Modify: `scripts/setup_hooks.ps1`
- Modify: `scripts/setup_hooks.sh`
- Modify: `.github/workflows/repo-hooks.yml`
- Test: `tests/test_validate_adoption_shape.py`
- Test: `tests/test_setup_hooks.py`

- [x] Step 1: Write a failing validator test for missing required root docs.
- [x] Step 2: Implement the smallest validator rule that fails when required root docs are absent.
- [x] Step 3: Update hook/CI wiring or tests as needed so the required-doc check is part of the normal validation path.
- [x] Step 4: Update hook tests to assert the required-doc validation path is covered.
- [x] Step 5: Run focused tests for validator/hook behavior and confirm green.

### Task 4: Run Final Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-04-21-00-35-project-doc-surface-plan.md`

- [x] Step 1: Run `python scripts/validate_adoption_shape.py`.
- [x] Step 2: Run `python scripts/sync_architecture_docs.py --check`.
- [x] Step 3: Run `git diff --check`.
- [x] Step 4: Review diffs for consistency across README, docs, validator, and tests.
- [x] Step 5: Mark the plan complete once verification evidence is clean.
