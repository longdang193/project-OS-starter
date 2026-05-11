---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: strict-capability-linkage-policy-plan
parent_workstream: none
parent_spec: docs/superpowers/specs/metadata-linkage-governance-spec.md
targets:
  - docs/operating_system/rules/python-contracts-rule.md
  - .agents/skills/skill-doc-system-lifecycle/SKILL.md
  - docs/operating_system/workflows/workflow-live-run-preflight-check.md
  - scripts/validate_python_meta_headers.py
  - scripts/validate_repo_contracts.py
  - tests/test_validate_python_meta_headers.py
related_features: []
related_stages: []
---

## Goal

Define and implement strict, ownership-aware Python `@meta` capability linkage enforcement so feature-owned modules must declare upstream-resolved capability IDs, while infrastructure modules are governed by explicit exception policy rather than implicit skipping.

## Key Deliverables

### Ownership-classified capability linkage policy

Canonical governance surfaces define normative rules for `ownership` classification, mandatory capability linkage for feature-owned modules, and explicit exception boundaries for infrastructure modules.

### Strict validator contract with rollout-safe semantics

Python metadata validator and repo-contract integration enforce capability linkage in non-`starter_method_only` modes with deterministic failure messages, path/domain ownership handling, and tests covering success/failure matrices.

### Lifecycle-aligned execution and verification closure

Plan/context-pack state, preflight workflow checks, and validation commands are synchronized so execution can proceed by next-action gating without reintroducing downstream truth re-entry.

## Task/Wave Breakdown

### Task 1: Finalize policy wording and exception model

**Purpose:**
- Lock canonical policy language before validator hardening to prevent ambiguous enforcement.

**Files:**
- Inspect: `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- Modify: `docs/operating_system/rules/python-contracts-rule.md`
- Modify: `.agents/skills/skill-doc-system-lifecycle/SKILL.md`
- Modify: `docs/operating_system/workflows/workflow-live-run-preflight-check.md`
- Verify: `docs/operating_system/rules/python-contracts-rule.md`

**Preconditions:**
- Existing metadata-linkage governance patch applied.
- Source-of-truth chain requirement confirmed.

**Steps:**
- [x] Step 1: Add normative definitions for `ownership: feature | infrastructure` and strict capability requirements.
- [x] Step 2: Add explicit exception policy language for infrastructure/shared modules.
- [x] Step 3: Align lifecycle skill/workflow preflight checklists to the same terms and constraints.

**Verification:**
- [x] Manual policy consistency check across rule/skill/workflow wording.

**Exit Criteria:**
- Canonical rule, skill checklist, and preflight workflow use consistent ownership and strictness semantics.

### Task 2: Implement validator strict modes and enforcement matrix

**Purpose:**
- Enforce policy in executable validation logic with source-first linkage checks.

**Files:**
- Inspect: `scripts/validate_python_meta_headers.py`
- Modify: `scripts/validate_python_meta_headers.py`
- Modify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_python_meta_headers.py`

**Preconditions:**
- Task 1 complete.

**Steps:**
- [x] Step 1: Add strict ownership/capability flags and deterministic validation conditions.
- [x] Step 2: Enforce feature-owned capability presence + upstream resolution.
- [x] Step 3: Enforce explicit infrastructure exception handling and fail on implicit omissions.
- [x] Step 4: Wire strict mode invocation from repo-contract flow for eligible adoption modes.

**Verification:**
- [x] `py scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- Validator behavior matches policy matrix for feature-owned, infrastructure, and invalid-ownership cases.

### Task 3: Add regression tests and close verification gates

**Purpose:**
- Prove enforcement behavior and prevent policy regressions.

**Files:**
- Inspect: `tests/test_validate_python_meta_headers.py`
- Modify: `tests/test_validate_python_meta_headers.py`
- Verify: `tests/test_validate_python_meta_headers.py`

**Preconditions:**
- Task 2 complete.

**Steps:**
- [x] Step 1: Add tests for feature-owned missing capabilities failure.
- [x] Step 2: Add tests for unresolved capability failure.
- [x] Step 3: Add tests for infrastructure explicit-exception pass/fail boundaries.
- [x] Step 4: Add tests for unknown/missing ownership strict failure.

**Verification:**
- [x] `py -m pytest tests/test_validate_python_meta_headers.py -q`

**Exit Criteria:**
- Test suite covers strict matrix and passes.

### Task 4: Synchronize execution context and perform closeout checks

**Purpose:**
- Keep lifecycle state authoritative and verify closure readiness.

**Files:**
- Modify: `docs/superpowers/execution_context_packs/managed-surface-governance-reconciliation/latest.md`
- Modify: `docs/superpowers/plans/2026-05-11-16-55-metadata-linkage-governance-patch-plan.md`
- Verify: `docs/superpowers/execution_context_packs/managed-surface-governance-reconciliation/latest.md`

**Preconditions:**
- Tasks 1-3 complete.

**Steps:**
- [x] Step 1: Update plan progress and unresolved/closed items.
- [x] Step 2: Update canonical execution context pack with new enforcement status and evidence.
- [x] Step 3: Run closeout gate checks.

**Verification:**
- [x] `py scripts/validate_planning_lifecycle.py --strict`
- [x] `py scripts/validate_checkpoint_packs.py`
- [x] `py scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- Plan/context pack synchronized and closeout gate commands pass.

## Verification

- `py scripts/validate_planning_lifecycle.py --strict`
- `py scripts/validate_checkpoint_packs.py`
- `py scripts/validate_repo_contracts.py --fast`
- `py tools/docs/generate_architecture_metadata.py --check`

## Completion Criteria

1. Ownership-classified strict capability policy exists in canonical governance surfaces.
2. Validator/test enforcement matches approved strict matrix.
3. Execution context pack and plan state reflect final verified status.
4. Final verification commands pass without metadata-chain violations.
