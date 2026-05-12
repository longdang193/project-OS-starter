---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: kit-classification-contract-plan
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-05-12-12-16-kit-classification-contract-spec.md
targets:
  - repo_config/starter-kit-manifest.json
  - scripts/validate_repo_contracts.py
  - scripts/validate_env_gitignore_contract.py
  - scripts/publish_public_repo.ps1
  - docs/operating_system/publication/public-repo-publication-policy.md
  - docs/operating_system/publication/public-repo-publishing.md
related_features: []
related_stages: []
---

## Goal

Implement manifest-authoritative kit classification with optional metadata discoverability (`distribution_tier: starter_kit`) and staged validator enforcement, while preserving existing publication fail-closed boundaries.

## Key Deliverables

### Deliverable 1: Classification contract integrated

Canonical kit membership remains manifest-driven, and policy docs clearly define `distribution_tier: starter_kit` as classification-only metadata.

### Deliverable 2: Validator enforcement delivered in staged mode

Repository validators detect manifest-vs-metadata drift with explicit warn/fail modes and actionable path-level diagnostics.

### Deliverable 3: Publication behavior preserved

Public export gates continue to enforce forbidden paths, metadata markers, and filename markers independently of kit classification metadata.

## Task/Wave Breakdown

### Task 1: Policy and schema contract alignment

**Purpose:**
- lock canonical terminology and boundaries before validator implementation

**Files:**
- Inspect: `docs/superpowers/specs/2026-05-12-12-16-kit-classification-contract-spec.md`
- Modify: `docs/operating_system/publication/public-repo-publication-policy.md`
- Modify: `docs/operating_system/publication/public-repo-publishing.md`
- Verify: `repo_config/publication-config.json`

**Preconditions:**
- approved spec exists

**Steps:**
- [x] Add contract language for `distribution_tier: starter_kit` as classification-only metadata.
- [x] Add explicit separation note from `repo: private` and filename/forbidden-path publish gates.
- [x] Confirm documentation references manifest authority for kit membership.

**Verification:**
- [x] manual inspection confirms no contradictory policy statements across publication docs

**Exit Criteria:**
- contract language is unambiguous and consistent across policy + runbook docs

### Task 2: Implement staged classification validator

**Purpose:**
- add enforceable drift detection between manifest membership and metadata classification

**Files:**
- Inspect: `repo_config/starter-kit-manifest.json`
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `scripts/validator_policy.py`
- Modify: `tests/test_validate_repo_contracts.py`

**Preconditions:**
- Task 1 complete

**Steps:**
- [x] Implement helper to derive expected kit membership from `copyPaths` expansion.
- [x] Implement metadata-capable file detection and `distribution_tier: starter_kit` consistency checks.
- [x] Add staged enforcement mode (`warn` then `fail`) through validator policy/config switch.
- [x] Add tests for in-kit missing tag, out-of-kit wrong tag, and non-metadata-capable file handling.

**Verification:**
- [x] `py -3 -m pytest tests/test_validate_repo_contracts.py`

**Exit Criteria:**
- validator reports deterministic, path-level findings and tests pass

### Task 3: Backfill and sync metadata-capable surfaces

**Purpose:**
- reduce initial drift noise and prepare fail-mode transition using derived marker sync

**Files:**
- Inspect: `repo_config/starter-kit-manifest.json`
- Modify: sync implementation in `scripts/` for manifest-derived `distribution_tier` marker updates
- Modify: selected metadata-capable files in `scripts/` and `docs/operating_system/` included in `copyPaths` (bounded backfill window)
- Verify: `scripts/validate_repo_contracts.py`

**Preconditions:**
- Task 2 complete

**Steps:**
- [x] Select bounded starter set of metadata-capable files from manifest-covered surfaces.
- [x] Add/verify `distribution_tier: starter_kit` via sync path where metadata schema already exists.
- [x] Resolve validator warnings for selected bounded set.

**Verification:**
- [x] `py -3 scripts/validate_repo_contracts.py --fast --sync-starter-kit-tier`

**Exit Criteria:**
- bounded backfill complete with clean validator output for selected scope

### Task 4: Flip enforcement mode and verify publication independence

**Purpose:**
- finalize enforcement and prove no publish-boundary regression

**Files:**
- Modify: `scripts/validator_policy.py`
- Verify: `scripts/publish_public_repo.ps1`
- Verify: `repo_config/publication-config.json`

**Preconditions:**
- Task 3 complete

**Steps:**
- [x] Ensure sync step runs before repo-contract validation in normal execution path.
- [x] Switch classification drift policy from warn to fail.
- [x] Re-run bounded publication proof checks for `repo: private`, `.private.`, `.local.` blockers.
- [x] Confirm classification tag is not treated as forbidden publish marker.

**Verification:**
- [x] `py -3 scripts/validate_repo_contracts.py --fast --sync-starter-kit-tier`
- [x] `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\publish_public_repo.ps1`

**Exit Criteria:**
- fail-mode active, sync-before-validate path active, validation green, publication boundary behavior unchanged

## Verification

- `py -3 scripts/validate_repo_config.py`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 scripts/validate_planning_lifecycle.py --strict`
- `py -3 scripts/validate_checkpoint_packs.py`

## Completion Criteria

1. all Key Deliverables are satisfied.
2. validator and publication docs agree on classification vs secrecy boundary.
3. staged rollout reaches fail-mode with passing checks.
4. publication gates still fail-closed for private markers and forbidden filename markers.
