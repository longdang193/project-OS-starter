---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - repo_config/publication-config.json
  - scripts/validate_repo_config.py
  - scripts/publish_public_repo.ps1
  - scripts/validate_starter_kit.py
  - docs/operating_system/publication/public-repo-publication-policy.md
  - docs/operating_system/publication/public-repo-publishing.md
related_features: []
related_stages: []
---

# Detailed Specification: Config-Authoritative Public Export Exclusion Policy

## Goal

Define single source-of-truth publication policy contract that blocks private/internal surfaces from starter-kit and public-repo exports, including deterministic rejection of files containing metadata `repo: private`.

## Key Deliverables

### Central publication policy schema

Introduce config-authoritative policy file under `repo_config/` that declares:

- never-publish path denylist
- never-publish glob/pattern deny rules (as policy evolves)
- forbidden content token rules
- forbidden metadata visibility rules (including `repo: private`)
- stable diagnostics for CI triage

### Unified enforcement path across validators

Require starter-kit and public-publish validation flows to consume same policy contract so exclusions are not duplicated across scripts/docs.

### Deterministic fail-closed behavior and proof suite

Specify parser and validation behavior such that malformed/missing policy fails export checks, with explicit tests for denied paths, metadata matches, and conflict cases.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- inventory current publication boundary surfaces and leakage risks before policy redesign

**Steps:**
- [ ] inspect current exclusion logic in starter/public validators and publish flow
- [ ] classify duplicated deny rules vs source-owned rules
- [ ] identify metadata-bearing file formats relevant to `repo: private` matching

**Verification:**
- [ ] current-state rule ownership and drift points explicitly documented

**Exit Criteria:**
- no proposed rule behavior depends on hidden script-local constants

### Wave 2: Decision closure

**Purpose:**
- lock policy schema, precedence, and enforcement semantics

**Steps:**
- [ ] finalize policy file path and schema keys
- [ ] define precedence: allowlist export then deny-policy validation
- [ ] define metadata scanner behavior and false-positive boundaries
- [ ] define compatibility strategy for existing publish/starter workflows

**Verification:**
- [ ] each major design question has documented decision or explicit deferral

**Exit Criteria:**
- implementation can proceed without reopening core contract decisions

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare spec for implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define unit/integration test matrix and expected failures
- [ ] define migration checklist and documentation updates
- [ ] define acceptance criteria for release readiness

**Verification:**
- [ ] validation plan proves boundary enforcement and contract preservation

**Exit Criteria:**
- spec ready for implementation planning/execution

## Design Decisions

### Decision: one canonical policy source

- context: path deny rules fragmented across docs/scripts create drift risk
- choice: use `repo_config/publication-config.json` as canonical policy source
- alternatives considered:
  - keep denylist embedded in each validator script
  - script-local fallback defaults
- impact:
  - rule changes become config-driven
  - validators must enforce schema before scanning

### Decision: retain allowlist-first export + deny-policy enforcement

- context: copy surface may broaden over time; defense-in-depth required
- choice: keep allowlist copy stage and enforce deny checks on output tree
- alternatives considered:
  - deny-only model
  - pre-copy deny only
- impact:
  - catches both path and content leakage
  - deny takes precedence over allowlist inclusion

### Decision: metadata visibility rule includes `repo: private`

- context: semantic privacy marker needed beyond path naming
- choice: fail publication when configured marker appears in export content
- alternatives considered:
  - path-only exclusion
  - warning-only metadata checks
- impact:
  - stronger policy boundary
  - requires deterministic marker scanner in publish/validator flow

### Decision: fail closed on policy/schema errors

- context: permissive fallback weakens governance
- choice: missing/malformed policy or required keys causes validation failure
- alternatives considered:
  - warning with pass-through
  - hidden defaults
- impact:
  - explicit, auditable policy state required

## Invariants

- publication exclusion policy has one canonical config source.
- export validation fails when denied path is present.
- export validation fails when forbidden metadata marker matches (`repo: private`).
- missing/malformed policy fails validation (fail-closed).
- allowlist approval cannot override deny-policy rejection.
- same policy semantics apply to starter-kit and public publication boundaries.

## Validation Plan

- proof target: denied directories are blocked (`.agents/`, `docs/operating_system/`, etc.)
  - method: validator and publish dry-run checks using export trees
  - evidence: deterministic failure messages

- proof target: `repo: private` metadata blocks publication
  - method: content scan tests in markdown/yaml/json/text fixtures
  - evidence: marker violation failure output with file path

- proof target: malformed/missing policy rejected
  - method: config schema validation tests
  - evidence: hard failure with schema/key diagnostics

- proof target: allowlist + deny conflict resolves to deny
  - method: integration case with denied path in copied set
  - evidence: validation failure despite copy step success

- proof target: workflows remain deterministic
  - method: run repo config validation, starter-kit validation, publish dry-run
  - evidence: stable pass/fail results under same inputs

## Completion Criteria

1. policy schema and defaults are documented and merged in `repo_config/`.
2. publish and starter validation consume shared policy semantics.
3. metadata privacy rule (`repo: private`) enforced in boundary checks.
4. fail-closed behavior covered by validation/tests.
5. publication docs reference canonical policy source.

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
