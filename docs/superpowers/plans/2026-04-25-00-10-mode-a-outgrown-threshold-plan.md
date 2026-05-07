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
  - docs/superpowers/specs/2026-04-24-mode-a-outgrown-threshold-spec.md
related_features: []
related_stages: []
---

# Mode A Outgrown-Threshold Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-mode-a-outgrown-threshold-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Add a second warning tier that detects when a `starter_method_only` repo has likely outgrown lightweight anchors and should plan migration to `managed_architecture_metadata`.

**Architecture:** Reuse the existing starter-only discovery helpers, add one stricter maturity heuristic in `validator_policy.py`, and emit a new warning from `validate_starter_method_only()` only after the repo has crossed the lightweight-anchor threshold. Keep the heuristic additive and warning-only. Then align Mode A docs to explain the second-tier signal clearly.

**Key Invariants:**
- Existing missing-anchor warnings remain unchanged.
- The new outgrown-threshold signal is warning-only.
- Small starter-only repos stay clean.
- The outgrown-threshold warning explicitly points to `managed_architecture_metadata`.

**Rollout / Revert:**  
- rollback_trigger: the new heuristic warns on obviously small repos or creates noisy false positives on repos that are still comfortably Mode A.  
- rollback_method: remove the outgrown-threshold helper and warning, keep the spec/plan/docs, and recalibrate thresholds in a narrower follow-up.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Add a warning-only maturity threshold so Mode A repos that have grown beyond lightweight anchors are nudged to plan migration to managed metadata.
Reasoning: This is validator and repo-governance behavior in the operating-system layer.
Invariants:
  - Mode A remains valid for early-stage repos.
  - Feature-index warnings continue to handle the first threshold.
  - The new warning only appears after lightweight-anchor expectations are already met.
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

## Files To Modify

```text
scripts/validate_adoption_shape.py
scripts/validator_policy.py
tests/test_validate_adoption_shape.py
docs/operating_system/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/project-adoption-migration-guide.md
docs/project_templates/mode-a/README.md
docs/superpowers/specs/2026-04-24-mode-a-outgrown-threshold-spec.md
```

## Task 1: Add Failing Maturity-Threshold Tests

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Add a mature starter-only fixture with broader runtime/test surface than the existing non-trivial fixture.
- [x] Step 2: Add a test showing first-threshold repos with `docs/features/README.md` do not yet trigger the new outgrown warning.
- [x] Step 3: Add a test showing mature repos with the anchor docs do trigger the new outgrown warning.

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -k "starter_method_only and (outgrown or feature_index)" -q
```

## Task 2: Implement The Outgrown-Threshold Helper

**Files:**
- Modify: `scripts/validator_policy.py`
- Modify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Add centralized thresholds for mature runtime/test breadth.
- [x] Step 2: Add helper logic that computes whether a repo has likely outgrown lightweight anchors.
- [x] Step 3: Emit the new warning only when the first-threshold anchor is already present and the stricter maturity heuristic is satisfied.
- [x] Step 4: Keep the warning explicit that migration should be planned, not forced immediately.

## Task 3: Align Mode A Docs

**Files:**
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/project_templates/mode-a/README.md`
- Modify: `docs/superpowers/specs/2026-04-24-mode-a-outgrown-threshold-spec.md`

- [x] Step 1: Document the second warning tier and its purpose.
- [x] Step 2: Explain that some repos can stay in Mode A for a while, but mature repos should plan the migration.
- [x] Step 3: Mark the spec completed after verification.

## Task 4: Verify

**Files:**
- Verify only

- [x] Step 1: Run the targeted tests.
- [x] Step 2: Run the full adoption-shape suite.
- [x] Step 3: Run the updated starter validator against `fitcv-langgraph` and record whether it is still on tier 1 or would move toward tier 2 after adding the feature index.
- [x] Step 4: Run `git diff --check`.
