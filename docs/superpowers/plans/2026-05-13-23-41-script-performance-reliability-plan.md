---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: script-performance-reliability-hardening
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-05-13-23-39-script-performance-reliability-spec.md
targets:
  - scripts/validate_repo_contracts.py
  - scripts/benchmark_runtime_validators.py
  - scripts/validator_policy.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
  - tests/test_validate_planning_lifecycle.py
related_features: []
related_stages: []
---

# Script Performance Reliability Hardening Plan

## Goal

Execute bounded, behavior-preserving performance and robustness improvements for validator scripts in the `script-performance-hardening` worktree, led by measured hotspots and guarded by strict verification parity.

## Key Deliverables

### Hotspot validator runtime improvement

Reduce execution latency of hotspot validator flows (especially `scripts/validate_repo_contracts.py`) through targeted work-reduction refactors and elimination of redundant scanning/parsing.

### Reliability hardening with preserved semantics

Strengthen edge-case handling and failure diagnostics for touched validator paths without changing CLI contracts, exit semantics, or policy strictness.

### Evidence-backed completion pack

Produce before/after benchmark artifacts plus passing validator/test evidence proving both performance gain intent and behavior parity.

## Why These Target Files Are Chosen

- `scripts/validate_repo_contracts.py`
  - primary hotspot implementation target from baseline benchmark evidence
  - main source of expected runtime gains through traversal/parsing work reduction
- `scripts/benchmark_runtime_validators.py`
  - required benchmark harness for baseline and post-change evidence capture
- `scripts/validator_policy.py`
  - shared policy constants surface inspected to ensure no accidental policy drift during refactor
- `tests/test_validate_repo_contracts.py`
  - direct regression guard for hotspot behavior and refactor-sensitive semantics
- `tests/test_validate_adoption_shape.py`
  - indirect parity guard for adoption-shape policy behavior affected by repo-contract orchestration
- `tests/test_validate_planning_lifecycle.py`
  - indirect parity guard for lifecycle gate behavior touched by validator flow changes

### Why Other Files Are Deferred

- plan is intentionally bounded to highest-impact hotspot and nearest coupled parity suites
- additional validators/scripts are only promoted into scope if re-profiling shows material bottlenecks or uncovered reliability gaps
- this keeps implementation incremental, testable, and low-risk

## Task/Wave Breakdown

### Task 1: Re-baseline and lock optimization test edges

**Purpose:**
- re-establish measurable baseline and create failing-first tests for refactor-sensitive paths

**Files:**
- Inspect: `scripts/benchmark_runtime_validators.py`
- Inspect: `scripts/validate_repo_contracts.py`
- Modify: `tests/test_validate_repo_contracts.py`
- Verify: `tests/test_validate_repo_contracts.py`

**Preconditions:**
- approved spec exists at `docs/superpowers/specs/2026-05-13-23-39-script-performance-reliability-spec.md`
- working branch is `feature/script-performance-hardening`

**Steps:**
- [x] Step 1: Run benchmark baseline and save `.tmp-tests/benchmark_before.json`
- [x] Step 2: Identify one or more traversal/parsing behaviors needing regression guard
- [x] Step 3: Add focused tests that fail before implementation for selected behavior-preserving optimization edges

**Verification:**
- [x] `python scripts/benchmark_runtime_validators.py --runs 2 --json-out .tmp-tests/benchmark_before.json`
- [x] `python -m pytest tests/test_validate_repo_contracts.py -q`

**Exit Criteria:**
- baseline benchmark artifact captured
- failing-first tests isolate bounded optimization surface

### Task 2: Implement hotspot work-reduction refactor

**Purpose:**
- cut redundant computation in hotspot validator while preserving policy behavior

**Files:**
- Inspect: `scripts/validate_repo_contracts.py`
- Inspect: `scripts/validator_policy.py`
- Modify: `scripts/validate_repo_contracts.py`
- Verify: `tests/test_validate_repo_contracts.py`

**Preconditions:**
- Task 1 complete with failing tests proving refactor target

**Steps:**
- [x] Step 1: Refactor traversal to skip irrelevant directories early and avoid broad eager scans
- [x] Step 2: Consolidate repeated file read/parse operations where safe with per-run local reuse only
- [x] Step 3: Preserve existing output categories and failure semantics while satisfying new regression tests

**Verification:**
- [x] `python -m pytest tests/test_validate_repo_contracts.py -q`

**Exit Criteria:**
- failing tests now pass
- no CLI/exit semantic drift introduced

### Task 3: Reliability hardening and parity checks

**Purpose:**
- strengthen error-handling and edge-case behavior in touched paths

**Files:**
- Inspect: `scripts/validate_repo_contracts.py`
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `tests/test_validate_adoption_shape.py`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Verify: `tests/`

**Preconditions:**
- Task 2 complete

**Steps:**
- [x] Step 1: Add/adjust edge-case tests for malformed or missing inputs relevant to touched logic
- [x] Step 2: Harden touched implementation branches to produce deterministic actionable failures
- [x] Step 3: Confirm policy strictness unchanged through related validator test coverage

**Verification:**
- [x] `python -m pytest tests/test_validate_repo_contracts.py tests/test_validate_adoption_shape.py tests/test_validate_planning_lifecycle.py -q`

**Exit Criteria:**
- touched reliability paths covered by passing tests
- no weakened enforcement behavior

### Task 4: Benchmark delta and final validation gate

**Purpose:**
- prove improvement direction and full behavioral compatibility

**Files:**
- Inspect: `.tmp-tests/benchmark_before.json`
- Modify: `.tmp-tests/benchmark_after.json`
- Verify: `scripts/benchmark_runtime_validators.py`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `tests/`

**Preconditions:**
- Tasks 1-3 complete

**Steps:**
- [x] Step 1: Run post-change benchmark and capture `.tmp-tests/benchmark_after.json`
- [x] Step 2: Compare hotspot command medians/p95 and record observed delta
- [x] Step 3: Run validator gates and full pytest suite before completion claim

**Verification:**
- [x] `python scripts/benchmark_runtime_validators.py --runs 2 --json-out .tmp-tests/benchmark_after.json`
- [x] `python scripts/validate_repo_contracts.py --fast`
- [x] `python -m pytest -q`

**Exit Criteria:**
- before/after benchmark evidence exists
- validator/test suite passes
- completion claim supported by command output evidence

## Verification

- `python scripts/benchmark_runtime_validators.py --runs 2 --json-out .tmp-tests/benchmark_before.json`
- `python -m pytest tests/test_validate_repo_contracts.py -q`
- `python -m pytest tests/test_validate_repo_contracts.py tests/test_validate_adoption_shape.py tests/test_validate_planning_lifecycle.py -q`
- `python scripts/benchmark_runtime_validators.py --runs 2 --json-out .tmp-tests/benchmark_after.json`
- `python scripts/validate_repo_contracts.py --fast`
- `python -m pytest -q`

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
