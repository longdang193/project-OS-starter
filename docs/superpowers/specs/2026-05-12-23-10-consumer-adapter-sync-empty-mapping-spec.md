---
layer: operating_system
artifact_type: spec
status: proposed
template_id: detailed-specification
name: consumer-adapter-sync-empty-mapping-spec
parent_workstream: none
targets:
  - scripts/sync_agent_adapters.py
  - tests/test_sync_agent_adapters.py
  - scripts/validate_agent_runtime_drift.py
  - repo_config/adoption-mode.yaml
  - repo_config/adapter-sync-policy.yaml
related_features: []
related_stages: []
---

## Goal

Define role-aware adapter-sync behavior so consumer-derived starter-kit repos pass `sync_agent_adapters.py --check` when adapter mappings are intentionally absent, while source-owner repos remain strict.

## Key Deliverables

### Deliverable 1: Consumer-safe empty-mapping contract

A deterministic contract for `sync_agent_adapters.py --check` that returns success with explicit skip messaging when `repo_role=consumer_derived` and no adapter mappings exist under default mode-policy selection.

### Deliverable 2: Source-owner strictness preserved

No relaxation for source-owner repos or explicit platform override flows; missing mappings in those contexts remains a hard validation failure.

### Deliverable 3: Regression-proof test coverage

Automated tests cover consumer default skip, source-owner hard-fail, and override-path hard-fail behavior.

## Task/Wave Breakdown

### Wave 1: Source-first behavior framing

**Purpose:**
- Establish current selection/mapping resolution semantics and identify safe guard insertion point.

**Steps:**
- [ ] Confirm current platform selection paths: mode-policy defaults, `--platform`, `--all-platforms`.
- [ ] Confirm current failure trigger when no adapter mappings resolve.
- [ ] Confirm consumer starter-kit boundary that forbids `adapters/` publication surface.

**Verification:**
- [ ] Current-state behavior is documented with no ambiguity around selection source and failure condition.

**Exit Criteria:**
- Guard conditions and non-guard conditions are explicit and testable.

### Wave 2: Decision closure and contract wording

**Purpose:**
- Close design decisions for skip conditions, failure conditions, and operator messaging.

**Steps:**
- [ ] Define exact skip predicate for consumer-derived mode-policy/default selection with no mappings.
- [ ] Define explicit non-skip paths (`source_owner`, `--platform`, `--all-platforms`).
- [ ] Define stable skip/fail messages for validator diagnostics.

**Verification:**
- [ ] All decision edges map to deterministic outcome (`skip success` vs `hard fail`).

**Exit Criteria:**
- Design can be implemented without policy guesswork.

### Wave 3: Validation readiness and handoff

**Purpose:**
- Prepare implementation-ready proof plan and bounded scope for follow-on plan execution.

**Steps:**
- [ ] Define targeted unit tests for skip/fail matrix.
- [ ] Define command-level verification sequence.
- [ ] Define rollback boundary if regression appears in source-owner flow.

**Verification:**
- [ ] Proof targets cover all critical branches of behavior.

**Exit Criteria:**
- Spec is implementation-plan ready.

## Design Decisions

### Decision: Introduce consumer-derived no-mapping skip for default policy selection

- context: Starter-kit consumer repos intentionally exclude `adapters/`; current strict no-mapping failure causes false-negative validation failures.
- choice: In `sync_agent_adapters.py --check`, return success with explicit skip message when all are true:
  - no mapping files are discovered
  - resolved repo role is `consumer_derived`
  - platform selection source is mode-policy/default (not explicit CLI override)
- alternatives considered:
  - ship minimal adapter mappings in kit
  - remove sync check from consumer validations
- impact:
  - preserves consumer packaging boundary
  - removes false-negative check failures in consumer repos
  - keeps sync tool present for managed policy flows

### Decision: Keep source-owner and explicit override paths fail-closed

- context: Relaxation must not hide true drift or missing managed surfaces in source-owner repos.
- choice: No skip when `repo_role=source_owner`, or when CLI explicitly requests platforms (`--platform`, `--all-platforms`), even in consumer role.
- alternatives considered:
  - unconditional consumer skip for all selections
  - warn-only mode for source-owner
- impact:
  - strong invariants for authoritative repos
  - explicit operator intent via CLI remains strict

### Decision: Add tests at sync-script boundary

- context: Behavior is centralized in sync script and affects higher validators indirectly.
- choice: Add unit tests in `tests/test_sync_agent_adapters.py` for matrix branches; do not duplicate logic in downstream validators.
- alternatives considered:
  - test only through `validate_agent_runtime_drift.py`
- impact:
  - direct regression detection
  - lower flakiness and faster feedback

## Invariants

- Source-owner repositories must continue to fail when required adapter mappings are absent.
- Consumer-derived repositories must not require `adapters/` presence for default mode-policy `--check` validation.
- Explicit CLI platform selection (`--platform`, `--all-platforms`) must remain strict and fail on missing mappings.
- Skip behavior must be transparent via stable log message; no silent success.
- Publication boundary remains unchanged: `adapters/` stays forbidden in starter-kit manifest.

## Acceptance Criteria

- `sync_agent_adapters.py --check` in consumer-derived repo with no mappings and default selection exits `0` with explicit skip message.
- `sync_agent_adapters.py --check` in source-owner repo with no mappings exits non-zero with missing-mapping diagnostic.
- `sync_agent_adapters.py --check --platform codex` with no mappings exits non-zero regardless of consumer role.
- `sync_agent_adapters.py --check --all-platforms` with no mappings exits non-zero regardless of consumer role.
- Updated unit tests cover all above cases and pass.

## Non-Goals

- Shipping adapter mapping assets into starter-kit consumer manifest.
- Changing publication forbidden-path policy.
- Redesigning adapter selection policy schema.
- Refactoring deploy runtime drift script beyond required compatibility.

## Risks and Mitigations

- Risk: Skip predicate too broad, masking real source-owner failures.
  - Mitigation: Predicate includes strict role + selection-source checks; source-owner branch remains unchanged.
- Risk: Selection-source detection drifts from CLI handling.
  - Mitigation: Reuse existing selection-reason/argument signals; add explicit override tests.
- Risk: Diagnostic confusion from silent pass.
  - Mitigation: Emit stable, actionable skip message including role and reason.

## Validation Plan

- proof target: consumer default no-mapping path skips successfully
  - method: unit test + direct script run
  - evidence: passing test case in `tests/test_sync_agent_adapters.py`; command output contains skip marker and exit code `0`
- proof target: source-owner no-mapping path fails
  - method: unit test
  - evidence: failing-path assertion with non-zero outcome and missing-mapping diagnostic
- proof target: explicit override no-mapping path fails
  - method: unit test for `--platform` and `--all-platforms`
  - evidence: two failing-path assertions with non-zero outcomes
- proof target: downstream drift validator remains compatible
  - method: targeted run of validator command
  - evidence: `py scripts/validate_agent_runtime_drift.py --skip-deploy-check` outcome aligned with updated sync behavior

## Completion Criteria

1. all Key Deliverables are satisfied.
2. all acceptance criteria are met with automated test evidence.
3. sync check behavior is deterministic across role/selection combinations.
4. consumer kit boundary and source-owner strictness both remain intact.
