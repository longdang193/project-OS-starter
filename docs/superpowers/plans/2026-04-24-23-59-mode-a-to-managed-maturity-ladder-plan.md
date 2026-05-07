---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_adoption_shape.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/README.md
  - tests/test_validate_adoption_shape.py
  - docs/superpowers/specs/2026-04-24-mode-a-to-managed-maturity-ladder-spec.md
related_features: []
related_stages: []
---

# Mode A To Managed Maturity Ladder Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-mode-a-to-managed-maturity-ladder-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Clarify that `starter_method_only` is the starting mode, lightweight anchors are an early waypoint, and `managed_architecture_metadata` is the intended mature destination for repos with durable product surface.

**Architecture:** Keep the existing warning triggers and severity unchanged, but tighten the wording in validator findings and Mode A docs so they express an explicit maturity ladder instead of a dead-end minimum. Add focused tests that verify the new messaging mentions `managed_architecture_metadata`.

**Key Invariants:**
- `starter_method_only` remains a supported lightweight mode.
- Current warnings remain warnings, not errors.
- `docs/features/README.md` remains a useful early anchor.
- The wording must clearly name `managed_architecture_metadata` as the mature destination.

**Rollout / Revert:**  
- rollback_trigger: the new wording sounds like forced immediate migration rather than staged guidance.  
- rollback_method: restore the previous warning/doc phrasing and retry with narrower language.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Update Mode A warning language and docs to express the maturity ladder from `starter_method_only` toward `managed_architecture_metadata`.
Reasoning: This is governance and validator messaging work in the operating-system layer.
Invariants:
  - warning triggers stay the same
  - warning severity stays the same
  - the mature target is named plainly
Dependencies:
  - `scripts/validate_adoption_shape.py`
  - `tests/test_validate_adoption_shape.py`
  - `docs/operating_system/*.md`
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
tests/test_validate_adoption_shape.py
docs/operating_system/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/project-adoption-migration-guide.md
docs/project_templates/mode-a/README.md
docs/superpowers/specs/2026-04-24-mode-a-to-managed-maturity-ladder-spec.md
```

## Task 1: Tighten Warning Assertions First

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Update the feature-index warning test to assert that the output mentions `managed_architecture_metadata`.
- [x] Step 2: Update the API warning test to assert that the output frames the doc as an early step rather than the whole mature answer.

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -k "starter_method_only and (feature_index or api_doc)" -q
```

## Task 2: Update Validator Wording

**Files:**
- Modify: `scripts/validate_adoption_shape.py`

- [x] Step 1: Reword the `docs/features/README.md` warning so it says to add the index now and treat it as a migration signal toward `managed_architecture_metadata`.
- [x] Step 2: Reword the API warning so it says the doc is an early anchor and does not imply Mode A is the mature end-state.
- [x] Step 3: Keep behavior unchanged apart from wording.

## Task 3: Align Mode A Docs

**Files:**
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/project_templates/mode-a/README.md`
- Modify: `docs/superpowers/specs/2026-04-24-mode-a-to-managed-maturity-ladder-spec.md`

- [x] Step 1: Add the explicit ladder `starter_method_only -> lightweight anchors -> managed_architecture_metadata`.
- [x] Step 2: Say plainly that lightweight anchors are waypoints, not the mature destination.
- [x] Step 3: Mark the spec completed after verification.

## Task 4: Verify

**Files:**
- Verify only

- [x] Step 1: Run the targeted warning tests.
- [x] Step 2: Run the full adoption-shape test file.
- [x] Step 3: Run the updated starter validator against `fitcv-langgraph` and confirm the warning now mentions the maturity path.
- [x] Step 4: Run `git diff --check`.
