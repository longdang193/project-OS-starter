---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/sync_architecture_docs.py
  - scripts/validate_adoption_shape.py
  - scripts/validator_policy.py
  - docs/operating_system/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/project_templates/mode-a/
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

# Mode A Validator And Bootstrap Gap Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-24-mode-a-validator-and-bootstrap-gap-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Make `starter_method_only` validation and bootstrap behavior genuinely lighter and self-consistent, without dragging in the managed architecture toolchain by default.

**Architecture:** Move the canonical repo-contract flow to an adoption-mode-aware branch: Mode A runs only the validator layers that belong to starter-method repos, while managed mode keeps the full architecture sync/check path. Then align Mode A template requirements and operating-system docs so bootstrap expectations match the actual validator contract.

**Key Invariants:**
- `starter_method_only` remains a supported, lighter adoption mode.
- Managed mode remains the only mode that requires managed feature folders and generated architecture contracts.
- The canonical repo-contract command must stay canonical, but its steps must respect adoption mode.
- Mode A bootstrap requirements must be explicit and self-contained for Mode A itself.

**Rollout / Revert:**  
- rollback_trigger: Mode-aware branching weakens managed-mode checks or leaves Mode A unable to detect real starter drift.  
- rollback_method: Restore the previous repo-contract orchestration, keep the spec/plan, and retry with a narrower branching surface after isolating the failing assumption.

---

## Triage

Layer: operating_system
Feature type: MODIFY
Summary: Patch Mode A validator/bootstrap gaps by making the canonical validator flow mode-aware and aligning template/docs expectations with that lighter contract.
Reasoning: This is repo-method governance work. It is not product workstream behavior and should live in the operating-system layer.
Invariants:
  - Mode A must not require managed feature folders or non-empty generated architecture discovery.
  - Managed mode must keep the full sync/generator path.
  - Starter-only repos should not need local validator patches to stay aligned with upstream.
Dependencies:
  - `scripts/validate_repo_contracts.py`
  - `scripts/sync_architecture_docs.py`
  - `scripts/validate_adoption_shape.py`
  - `docs/project_templates/mode-a/`
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
  - `docs/superpowers/specs/2026-04-24-mode-a-validator-and-bootstrap-gap-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validate_repo_contracts.py
scripts/sync_architecture_docs.py
scripts/validate_adoption_shape.py
scripts/validator_policy.py
tests/test_validate_repo_contracts.py
tests/test_validate_adoption_shape.py
docs/operating_system/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/operating_system/project-adoption-migration-guide.md
docs/project_templates/mode-a/
docs/superpowers/specs/2026-04-24-mode-a-validator-and-bootstrap-gap-spec.md
```

## Scope Boundary

Implement only the Mode A contract cleanup:

1. make repo-contract orchestration adoption-mode-aware
2. keep sync/generator checks as managed-mode expectations
3. align Mode A template/documentation expectations with that branching
4. add regression coverage for starter-only and managed-mode behavior

Do not:

- redesign the managed architecture generator
- make `docs/features/` globally required
- collapse adoption modes together
- broaden this into a general validator refactor unrelated to Mode A

## Task 1: Make Repo-Contract Orchestration Adoption-Mode-Aware

**Files:**
- Modify: `scripts/validate_repo_contracts.py`
- Test: `tests/test_validate_repo_contracts.py`

- [x] Step 1: Add a small adoption-mode read helper or reuse existing mode parsing so repo-contract orchestration can branch by mode.
- [x] Step 2: In `starter_method_only`, skip the managed architecture sync/check path and keep only the mode-appropriate validator steps.
- [x] Step 3: In `managed_architecture_metadata`, preserve the full sync/check path.
- [x] Step 4: Keep fast-mode behavior canonical, but mode-aware.
- [x] Step 5: Add tests proving Mode A no longer routes through managed-only sync/generator steps while managed mode still does.

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_repo_contracts.py -q
```

## Task 2: Tighten Adoption-Shape Messaging For Mode A

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `scripts/validator_policy.py`
- Test: `tests/test_validate_adoption_shape.py`

- [x] Step 1: Review starter-only findings and warnings around `docs/features/`, `docs/stages/`, and `docs/generated/`.
- [x] Step 2: Keep feature metadata forbidden in Mode A, but make the validator language explicit that prose-only folders remain conditional.
- [x] Step 3: Add or adjust tests for:
  - starter-only repo with no `docs/features/`
  - starter-only repo with prose-only `docs/features/README.md`
  - starter-only repo without non-empty generated discovery

Suggested verification command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_adoption_shape.py -q
```

## Task 3: Align Mode A Template And Migration Guidance

**Files:**
- Modify: `docs/project_templates/mode-a/`
- Modify: `docs/operating_system/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`

- [x] Step 1: Update the migration guide to say plainly that Mode A is lighter and does not imply the full managed sync/generator toolchain.
- [x] Step 2: Update repo governance and doc-system lifecycle docs to reflect the same rule.
- [x] Step 3: Review Mode A template pack requirements and remove any implication that missing managed-only scripts are a bootstrap failure for starter-only repos.
- [x] Step 4: If any scripts remain required by the true Mode A validator path, state them explicitly in template docs.

## Task 4: End-To-End Verification

**Files:**
- Verify only

- [x] Step 1: Run focused validator tests after code changes land.
- [x] Step 2: Run the canonical repo-contract validator in starter-only mode on the starter repo.
- [x] Step 3: Run any managed-mode regression coverage needed to prove the full path still applies there.
- [x] Step 4: Run `git diff --check`.

Suggested verification commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_repo_contracts.py tests/test_validate_adoption_shape.py -q
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
git diff --check
```
