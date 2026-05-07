---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - tests/test_validate_adoption_shape.py
  - docs/superpowers/specs/2026-04-24-mode-a-missing-surface-discovery-spec.md
related_features: []
related_stages: []
---

# Mode A Missing-Surface Discovery Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-mode-a-missing-surface-discovery-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add warning-only Mode A discovery checks so growing starter-only repos can notice missing lightweight doc anchors before opting into managed metadata.

**Architecture:** Extend `validate_adoption_shape.py` with a small starter-only discovery pass driven by centralized policy constants in `validator_policy.py`. Keep the pass heuristic and warning-only, focusing on product-surface anchors that are currently invisible to the validator. Because `docs/pipeline.md` is already globally required, the new implementation will concentrate on missing `docs/features/README.md` and `docs/api.md` warnings rather than duplicating the existing required-root-doc rule.

**Key Invariants:**
- `starter_method_only` stays lighter than managed mode.
- The new checks emit warnings, not errors.
- Managed feature/stage metadata is still not required in Mode A.
- Required root-doc enforcement stays separate from missing-surface discovery.

**Rollout / Revert:**  
- rollback_trigger: the new heuristics warn on tiny starter repos or create noisy false positives on clearly non-API projects.  
- rollback_method: remove the starter-only discovery pass, keep the spec/plan/docs, and retry with narrower heuristics or higher thresholds.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Add Mode A warning-level discovery rules for missing lightweight doc anchors in non-trivial starter-only repos.
Reasoning: This is repo-method validator behavior and starter guidance, not product workstream logic.
Invariants:
  - Mode A warnings must not require managed metadata.
  - `docs/pipeline.md` remains enforced by the existing required-root-doc rule.
  - Missing feature-index and optional API doc warnings should rely on objective file-tree evidence.
Dependencies:
  - `scripts/validate_adoption_shape.py`
  - `scripts/validator_policy.py`
  - `tests/test_validate_adoption_shape.py`
Affected stages:
  - none
Affected features:
  - none
Primary lens: cross-cutting
Affected docs:
  feature_source: none
  feature_yaml: none
  feature_lineage: none
  feature_history: none
  stage_source: none
  stage_contract: none
  feature_docs:
    - none
  cross_cutting_docs:
    - none
  operating_system_docs:
    - `docs/operating_system/repo-governance.md`
    - `docs/operating_system/skill-doc-system-lifecycle.md`
    - `docs/operating_system/project-adoption-migration-guide.md`
  readme: none
  generated:
    - none
Generated refresh required: no
Capability IDs:
  - none
Invariant IDs:
  - none
Spec needed: yes
Plan needed: yes

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
  - `docs/operating_system/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/project_templates/mode-a/README.md`
  - `docs/superpowers/specs/2026-04-24-mode-a-missing-surface-discovery-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validate_adoption_shape.py
scripts/validator_policy.py
tests/test_validate_adoption_shape.py
docs/operating_system/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/project-adoption-migration-guide.md
docs/project_templates/mode-a/README.md
docs/superpowers/specs/2026-04-24-mode-a-missing-surface-discovery-spec.md
```

## Scope Boundary

Implement only Phase 1 warning-level discovery:

1. centralize starter-only heuristic thresholds and path hints
2. add a warning for missing `docs/features/README.md` in non-trivial Mode A repos
3. add a warning for missing `docs/api.md` in API-heavy Mode A repos
4. document the new behavior plainly
5. verify it against both tiny and non-trivial starter-only fixtures

Do not:

- require managed feature folders in Mode A
- auto-infer per-feature IDs from code
- convert warnings into errors
- duplicate the existing `docs/pipeline.md` required-root-doc rule

## Task 1: Add Failing Starter-Only Discovery Tests

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add a fixture for a non-trivial starter-only repo that has runtime surface but no `docs/features/README.md`.
- [x] Step 2: Add a fixture for an API-heavy starter-only repo without `docs/api.md`.
- [x] Step 3: Assert these cases return success with `WARN` output, not failure.
- [x] Step 4: Add passing counterparts proving the warnings disappear once the anchor docs exist.

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -k "starter_method_only and (feature_index or api_doc)" -q
```

## Task 2: Implement The Discovery Pass

**Files:**
- Modify: `scripts/validator_policy.py`
- Modify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Add centralized Mode A discovery policy constants for code-file suffixes, thresholds, and path hints.
- [x] Step 2: Add helper functions that detect non-trivial runtime surface and likely API surface from the repo tree.
- [x] Step 3: Call the new starter-only discovery pass from `validate_starter_method_only()`.
- [x] Step 4: Keep messages explicit that these are prose-anchor warnings, not managed-metadata obligations.

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -q
```

## Task 3: Align Mode A Guidance

**Files:**
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/project_templates/mode-a/README.md`
- Modify: `docs/superpowers/specs/2026-04-24-mode-a-missing-surface-discovery-spec.md`

- [x] Step 1: Document that Mode A now warns on missing lightweight doc anchors as projects grow.
- [x] Step 2: Say plainly that `docs/pipeline.md` is already required separately, so the new discovery pass focuses on missing feature/API anchors.
- [x] Step 3: Mark the spec completed once implementation and verification finish.

## Task 4: Verify Against Starter And Downstream Shapes

**Files:**
- Verify only

- [x] Step 1: Run the full adoption-shape test file.
- [x] Step 2: Run `scripts/validate_adoption_shape.py` on the starter repo.
- [x] Step 3: Run the adoption-shape validator on `fitcv-langgraph` and confirm whether the new warning surfaces there.
- [x] Step 4: Run `git diff --check`.

Suggested verification commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -q
.\.venv\Scripts\python.exe scripts/validate_adoption_shape.py
.\.venv\Scripts\python.exe C:\Users\HOANG PHI LONG DANG\repos\fitcv-langgraph\scripts\validate_adoption_shape.py --repo-root C:\Users\HOANG PHI LONG DANG\repos\fitcv-langgraph
git diff --check
```
