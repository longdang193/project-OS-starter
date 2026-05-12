---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: publication-policy-contract-implementation-plan
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-05-12-public-export-exclusion-policy-spec.md
targets:
  - repo_config/publication-config.json
  - scripts/validate_repo_config.py
  - scripts/publish_public_repo.ps1
  - scripts/validate_starter_kit.py
  - scripts/build_starter_kit.py
  - tests/
  - docs/operating_system/publication/public-repo-publication-policy.md
  - docs/operating_system/publication/public-repo-publishing.md
related_features: []
related_stages: []
---

# Implementation Plan: Public Export Exclusion Policy Contract

## Goal

Implement config-authoritative publication boundary enforcement that blocks never-publish paths and metadata-marked private content (`repo: private`) across public export and starter-kit validation flows.

## Key Deliverables

### Deliverable 1: Centralized policy contract in repo config

Publication config contains complete deny-path baseline plus metadata marker list, validated by repo config schema checks.

### Deliverable 2: Shared runtime enforcement in export validators

Publish and starter-kit validation paths consume policy-backed checks for denied surfaces and forbidden metadata markers with deterministic failure output.

### Deliverable 3: Verification coverage and governance alignment

Automated checks and docs updated so publication boundary behavior is testable, fail-closed, and source-of-truth documented.

## Task/Wave Breakdown

### Task 1: Finalize policy contract schema and baseline

**Purpose:**
- lock publication config shape and requested never-publish defaults

**Files:**
- Inspect: `repo_config/publication-config.json`
- Modify: `repo_config/publication-config.json`
- Modify: `scripts/validate_repo_config.py`
- Verify: `scripts/validate_repo_config.py`

**Preconditions:**
- spec decisions approved for path denylist + metadata markers

**Steps:**
- [ ] Step 1: Add/normalize deny-path baseline in publication config.
- [ ] Step 2: Add `forbiddenMetadataMarkers` list with `repo: private`.
- [ ] Step 3: Extend schema validation for required key and list-of-strings type.

**Verification:**
- [ ] `python scripts/validate_repo_config.py`

**Exit Criteria:**
- config validator passes and enforces new contract key.

### Task 2: Enforce metadata and path policy in public publish flow

**Purpose:**
- prevent private leakage in public export tree before publish

**Files:**
- Inspect: `scripts/publish_public_repo.ps1`
- Modify: `scripts/publish_public_repo.ps1`
- Verify: `scripts/publish_public_repo.ps1`

**Preconditions:**
- Task 1 complete

**Steps:**
- [ ] Step 1: Load metadata marker list from publication config.
- [ ] Step 2: Add export-tree scan for forbidden metadata markers.
- [ ] Step 3: Ensure violations fail run with clear diagnostics.

**Verification:**
- [ ] `pwsh -File scripts/publish_public_repo.ps1 -ExportRoot generated_exports/public-test`

**Exit Criteria:**
- publish dry-run fails on marker/path violations and passes on clean tree.

### Task 3: Align starter-kit validator with same policy semantics

**Purpose:**
- remove drift between starter-kit and public publish boundary checks

**Files:**
- Inspect: `scripts/validate_starter_kit.py`
- Inspect: `scripts/build_starter_kit.py`
- Modify: `scripts/validate_starter_kit.py`
- Verify: `scripts/validate_starter_kit.py`

**Preconditions:**
- Task 1 complete

**Steps:**
- [ ] Step 1: Introduce policy-backed metadata marker scanning in starter validator.
- [ ] Step 2: Keep existing forbidden token/path checks compatible.
- [ ] Step 3: Normalize error format for CI triage consistency.

**Verification:**
- [ ] `python scripts/validate_starter_kit.py --repo-root .`

**Exit Criteria:**
- starter-kit validation enforces `repo: private` and deny paths consistently.

### Task 4: Add regression coverage and docs contract update

**Purpose:**
- prove behavior and document canonical policy ownership

**Files:**
- Modify: `tests/` (publication/starter validation tests)
- Modify: `docs/operating_system/publication/public-repo-publication-policy.md`
- Modify: `docs/operating_system/publication/public-repo-publishing.md`
- Verify: `tests/`

**Preconditions:**
- Tasks 2-3 complete

**Steps:**
- [ ] Step 1: Add tests for denied paths, metadata markers, and fail-closed scenarios.
- [ ] Step 2: Add conflict test where allowlist includes denied path, expect deny.
- [ ] Step 3: Update docs to declare `repo_config/publication-config.json` as canonical policy source.

**Verification:**
- [ ] `pytest -q`
- [ ] `python scripts/validate_repo_config.py`

**Exit Criteria:**
- tests pass and docs reflect enforced contract.

## Verification

- `python scripts/validate_repo_config.py`
- `python scripts/validate_starter_kit.py --repo-root .`
- `pwsh -File scripts/publish_public_repo.ps1 -ExportRoot generated_exports/public-test`
- `pytest -q`

## Completion Criteria

1. policy denylist and metadata marker keys are config-authoritative and validated.
2. publish and starter validation both enforce `repo: private` exclusion.
3. failures are deterministic and actionable.
4. regression tests cover pass/fail/deny-precedence/fail-closed cases.
5. publication governance docs reference canonical config source.

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
