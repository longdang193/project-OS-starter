---
layer: operating_system
artifact_type: plan
status: active
template_id: implementation-plan
name: managed-surface-governance-reconciliation
parent_workstream: none
parent_spec: none
targets:
  - scripts/validator_policy.py
  - scripts/validate_adoption_shape.py
  - repo_config/adoption-mode.yaml
  - docs/project_templates/mode-a/repo_config/adoption-mode.yaml
  - docs/operating_system/adoption/project-adoption-migration-guide.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/governance/feature-routing-guide.md
  - tests/test_validate_adoption_shape.py
related_features: []
related_stages: []
---

## Goal

Reconcile adoption-governance drift by enforcing one managed architecture surface contract across repos, while splitting source authority via explicit repo role instead of shape-based mode separation.

## Key Deliverables

### Managed-surface contract enforcement

Validator policy and adoption-shape checks enforce managed architecture surfaces as required contract behavior, with no permissive starter-mode gaps for managed/stage/discovery metadata surfaces.

### Role-based authority model

Adoption config supports explicit `repo_role` (`source_owner` vs `consumer_derived`) so source authority and sync/drift policy split by role while metadata shape remains consistent.

### Documentation and alias reconciliation

Operating-system governance/adoption docs use canonical alias wording and aligned policy language matching validator behavior.

### Verification coverage

Validator tests cover `repo_role` parsing/validation and strict stage-surface behavior; repo contract validation passes on patched surfaces.

## Task/Wave Breakdown

### Task 1: Triage contract and map enforcement delta

**Purpose:**
- Lock exact drift boundaries between current docs, policy, and validator behavior.

**Files:**
- Inspect: `scripts/validator_policy.py`
- Inspect: `scripts/validate_adoption_shape.py`
- Inspect: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Inspect: `docs/operating_system/governance/repo-governance.md`
- Inspect: `docs/operating_system/governance/feature-routing-guide.md`
- Verify: `repo_config/adoption-mode.yaml`

**Preconditions:**
- Worktree baseline established.
- Plan approved for execution.

**Steps:**
- [x] Compare canonical mode/alias rules against validator dispatch and error/warn paths.
- [x] Confirm strictness target: missing/forbidden managed surfaces should fail under reconciled policy.
- [x] Record concrete line-level patch points for policy + docs alignment.

**Verification:**
- [x] Drift table prepared inline in execution notes with file/line references.

**Exit Criteria:**
- Patch boundaries are explicit and implementation-ready.

### Task 2: Implement validator policy and adoption-shape enforcement

**Purpose:**
- Enforce managed-surface contract and role split in code.

**Files:**
- Modify: `scripts/validator_policy.py`
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `repo_config/adoption-mode.yaml`
- Modify: `docs/project_templates/mode-a/repo_config/adoption-mode.yaml`

**Preconditions:**
- Task 1 complete.

**Steps:**
- [x] Add canonical `repo_role` policy constants and valid values.
- [x] Parse/validate `repo_role` from adoption config.
- [x] Tighten starter legacy checks where still present so stage source/contracts are error-level.
- [x] Ensure alias normalization remains deterministic and canonical.
- [x] Update config examples/templates to include `repo_role`.

**Verification:**
- [x] `py scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- Validator behavior matches reconciled contract and config examples parse cleanly.

### Task 3: Reconcile governance/adoption docs to enforcement truth

**Purpose:**
- Remove wording drift and alias corruption so docs match validator behavior.

**Files:**
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/governance/feature-routing-guide.md`

**Preconditions:**
- Task 2 complete.

**Steps:**
- [x] Replace nested alias text with canonical single-alias form.
- [x] Replace shape-split language with role-split language where policy now requires full managed surface.
- [x] Add concise rule clarity so mode/role expectations are unambiguous.

**Verification:**
- [x] `py scripts/validate_repo_contracts.py --fast`
- [x] `py scripts/validate_adoption_shape.py`

**Exit Criteria:**
- Docs and validator policy no longer conflict on expected managed surfaces.

### Task 4: Add regression tests and finalize verification

**Purpose:**
- Lock new contract behavior with focused tests and final checks.

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_repo_contracts.py`

**Preconditions:**
- Tasks 2–3 complete.

**Steps:**
- [x] Add/adjust tests for `repo_role` parsing and invalid-role failure path.
- [x] Add/adjust tests for strict stage-surface handling in legacy starter path.
- [x] Run targeted tests and repo contract gate.

**Verification:**
- [x] `pytest tests/test_validate_adoption_shape.py`
- [x] `py scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- Targeted tests pass and contract validator passes for patched scope.

## Verification

- `py scripts/validate_repo_contracts.py --fast`
- `pytest tests/test_validate_adoption_shape.py`

## Completion Criteria

1. [x] Key Deliverables complete and reflected in committed file changes.
2. [x] Validator and docs show aligned managed-surface contract semantics.
3. [x] Role split (`source_owner`/`consumer_derived`) enforced via adoption config and tests.
4. [x] Final verification commands pass on patched scope.
