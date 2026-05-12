---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: consumer-adapter-sync-empty-mapping-plan
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-05-12-23-10-consumer-adapter-sync-empty-mapping-spec.md
targets:
  - scripts/sync_agent_adapters.py
  - tests/test_sync_agent_adapters.py
  - scripts/validate_agent_runtime_drift.py
related_features: []
related_stages: []
---

## Goal

Implement and verify role-aware empty-mapping handling in adapter sync checks so consumer-derived starter-kit repos pass default policy checks without shipping `adapters/`, while source-owner and explicit override checks remain strict.

## Key Deliverables

### Deliverable 1: Sync-script contract update

`sync_agent_adapters.py` implements deterministic consumer-derived skip behavior for default mode-policy selection when mappings are absent, with stable operator-facing messaging.

### Deliverable 2: Strictness boundaries preserved

Source-owner behavior and explicit platform override paths continue to fail closed on missing mappings.

### Deliverable 3: Regression coverage and validator compatibility

Targeted tests prove role/selection matrix behavior and confirm `validate_agent_runtime_drift.py` remains behaviorally aligned.

## Task/Wave Breakdown

### Task 1: Implement role-aware no-mapping decision gate in sync script

**Purpose:**
- Add bounded decision logic at empty-mapping branch without changing unrelated sync semantics.

**Files:**
- Inspect: `scripts/sync_agent_adapters.py`
- Modify: `scripts/sync_agent_adapters.py`
- Verify: `repo_config/adoption-mode.yaml`
- Verify: `repo_config/adapter-sync-policy.yaml`

**Preconditions:**
- Approved spec exists: `docs/superpowers/specs/2026-05-12-23-10-consumer-adapter-sync-empty-mapping-spec.md`
- Current no-mapping failure path is identified in sync script.

**Steps:**
- [x] Locate mapping discovery + empty-result failure branch.
- [x] Add guard predicate for consumer-derived + default mode-policy selection + no mappings.
- [x] Emit explicit skip message and return success for guarded case.
- [x] Preserve existing failure behavior for source-owner and explicit override paths.

**Verification:**
- [x] Manual inspection confirms only empty-mapping branch changed and strict paths preserved.

**Exit Criteria:**
- Sync script contains deterministic skip/fail branching per spec decisions.

### Task 2: Add regression tests for role and selection matrix

**Purpose:**
- Prevent future regressions in consumer/source-owner and override behavior.

**Files:**
- Inspect: `tests/test_sync_agent_adapters.py`
- Modify: `tests/test_sync_agent_adapters.py`
- Verify: `scripts/sync_agent_adapters.py`

**Preconditions:**
- Task 1 complete.

**Steps:**
- [x] Add test: consumer-derived + default selection + no mappings => success/skip.
- [x] Add test: source-owner + default selection + no mappings => failure.
- [x] Add test: consumer-derived + `--platform` + no mappings => failure.
- [x] Add test: consumer-derived + `--all-platforms` + no mappings => failure.

**Verification:**
- [x] `py -3 -m pytest tests/test_sync_agent_adapters.py`

**Exit Criteria:**
- New and existing sync adapter tests pass with clear assertions on outcomes/messages.

### Task 3: Validate downstream compatibility and closure evidence

**Purpose:**
- Ensure runtime drift validator flow remains consistent after sync behavior update.

**Files:**
- Inspect: `scripts/validate_agent_runtime_drift.py`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_agent_runtime_drift.py`

**Preconditions:**
- Task 2 complete with passing sync tests.

**Steps:**
- [x] Run targeted drift validator check path.
- [x] Run fast repo contract gate to ensure no collateral governance regression.
- [x] Capture command outputs for closure evidence.

**Verification:**
- [x] `py -3 scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- Validator flows pass with updated sync contract and no new failures.

## Verification

- `py -3 -m pytest tests/test_sync_agent_adapters.py`
- `py -3 scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 scripts/validate_planning_lifecycle.py --strict`

## Completion Criteria

1. all Key Deliverables are satisfied.
2. consumer-derived default no-mapping path returns success with explicit skip message.
3. source-owner and explicit override no-mapping paths fail closed.
4. targeted tests and validator commands pass with evidence captured.
