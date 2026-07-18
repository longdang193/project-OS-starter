---
layer: operating_system
artifact_type: spec
status: completed
template_id: detailed-specification
name: kit-classification-contract-spec
parent_workstream: none
targets:
  - repo_config/starter-kit-manifest.json
  - scripts/validate_repo_contracts.py
  - scripts/validate_env_gitignore_contract.py
  - scripts/publish_public_repo.ps1
  - docs/operating_system/publication/public-repo-publication-policy.md
related_features: []
related_stages: []
---

## Goal

Define deterministic, low-drift contract for identifying starter-kit-owned files versus project-owned files, without breaking current publication-boundary enforcement.

## Key Deliverables

### Deliverable 1: Canonical kit ownership contract

Single source of truth for kit membership remains manifest-path based (`repo_config/starter-kit-manifest.json`), with optional metadata classification only on metadata-capable files.

### Deliverable 2: Validator-enforced consistency

Add explicit validator behavior to detect mismatches between manifest membership and metadata classification, with staged rollout (`warn` then `fail`).

### Deliverable 3: Boundary separation preserved

Keep publication security gates (`forbiddenPaths`, metadata markers, filename markers) independent from kit-classification tags so public export rules remain fail-closed and predictable.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- capture existing ownership and publication controls before adding new classification contract

**Steps:**
- [x] inspect manifest authority and existing starter-kit validators
- [x] inspect current metadata marker semantics and publish gating semantics
- [x] enumerate metadata-capable file classes and unsupported file classes

**Verification:**
- [x] analysis explicitly maps current ownership truth and all interacting validators

**Exit Criteria:**
- no design decision depends on unstated assumptions about current export or validation behavior

### Wave 2: Decision closure

**Purpose:**
- finalize metadata contract and enforcement mode without scope creep

**Steps:**
- [x] define canonical classification key and allowed values
- [x] define enforcement matrix (in-kit vs out-of-kit; metadata-capable vs non-capable)
- [x] define rollout sequence (`warn` then `fail`) and migration boundaries

**Verification:**
- [x] each non-obvious alternative has explicit reject rationale

**Exit Criteria:**
- design is bounded, conflict-free with publication policy, and implementation-plan ready

### Wave 3: Validation and approval readiness

**Purpose:**
- make proof and closeout expectations executable

**Steps:**
- [x] define command-level validation evidence
- [x] define acceptance criteria and non-goals
- [x] define risks and mitigations for false positives and migration drift

**Verification:**
- [x] validation plan proves contract correctness and backward compatibility

**Exit Criteria:**
- spec can hand off to implementation planning without unresolved design ambiguity

## Design Decisions

### Decision: Manifest remains canonical source of kit membership

- context: repo already uses `starter-kit-manifest.json` as export authority
- choice: keep manifest as sole authoritative kit-membership source
- alternatives considered:
  - metadata-only ownership (`kit: yes` on all files)
  - dual-authority (manifest + mandatory metadata everywhere)
- impact:
  - avoids mass file-format edits and parser breakage
  - keeps deterministic path-based export behavior

### Decision: Use manifest-derived metadata marker on metadata-capable files

- context: user wants easy identification of kit files without long-term manual drift
- choice: treat `distribution_tier: starter_kit` as manifest-derived marker maintained by sync step, then validated
- alternatives considered:
  - manual optional tagging on every edit
  - metadata-only authority (`distribution_tier` as source of truth)
- impact:
  - preserves single authority in `starter-kit-manifest.json`
  - removes repeated manual patch burden
  - keeps deterministic validation and repair path

### Decision: Enforce consistency with staged validator policy

- context: immediate hard-fail can create migration noise
- choice: enforce in two phases:
  - phase A: warn-only drift report while sync/backfill converges
  - phase B: fail on mismatches after sync step is wired and baseline is clean
- alternatives considered:
  - immediate hard fail
  - no validator enforcement (documentation-only)
- impact:
  - safer adoption path with measurable closure criteria
  - fail mode protects against post-sync regression

### Decision: Keep kit-classification separate from private/public boundary markers

- context: existing publish gate blocks `repo: private` markers and forbidden filename markers
- choice: do not make `distribution_tier` a publication deny marker
- alternatives considered:
  - treat kit marker as export blocker
  - auto-strip kit marker during publish
- impact:
  - avoids accidental export failures and hidden mutation logic
  - preserves explicit boundary model in publication config/script

## Invariants

- `repo_config/starter-kit-manifest.json` is canonical kit-membership authority.
- Publication boundary enforcement remains fail-closed via existing policy keys and publish assertions.
- `distribution_tier: starter_kit` is classification-only and not secrecy marker.
- Metadata enforcement applies only to metadata-capable file surfaces.
- Non-metadata-capable files are governed by manifest path classification only.

## Acceptance Criteria

- validator can detect and report all in-scope mismatches between manifest membership and `distribution_tier` classification.
- no current valid publication export becomes invalid solely due to introduction of classification key.
- rollout can run in warn mode without blocking existing contributor flow.
- final fail mode blocks new drift with actionable error messages including file paths and expected state.

## Non-Goals

- no migration to metadata-only export authority.
- no blanket insertion of metadata into every file in repository.
- no changes to runtime/product behavior.
- no replacement of existing forbidden metadata/filename marker gates.

## Risks and Mitigations

- risk: contributor confusion between `distribution_tier` and `repo: private`
  - mitigation: policy doc language explicitly separates classification vs secrecy markers.
- risk: false positives from files without supported metadata schema
  - mitigation: validator restricts enforcement to metadata-capable file classes.
- risk: long-lived warn mode with unresolved drift
  - mitigation: define bounded migration window and explicit flip-to-fail checkpoint.

## Validation Plan

- proof target: manifest-authoritative classification preserved
  - method: inspection + validator test fixtures
  - evidence: validator output shows manifest-derived expected state for mismatched files
- proof target: publication boundary behavior unchanged for existing rules
  - method: run publish script checks with controlled fixtures
  - evidence: failures still trigger on `repo: private`, `.private.`, `.local.` as before
- proof target: staged enforcement works
  - method: run validator in warn mode then fail mode against same fixture set
  - evidence: warn mode reports non-blocking findings; fail mode exits non-zero on same findings
- proof target: repo contract suite remains green after compliant backfill
  - method: execute bounded validation commands
  - evidence: successful outputs from repo contract validation commands

## Completion Criteria

1. all Key Deliverables are satisfied.
2. validator behavior and policy docs agree on contract semantics.
3. implementation planning handoff has no unresolved design ambiguities.
4. acceptance criteria have explicit measurable proof methods.
