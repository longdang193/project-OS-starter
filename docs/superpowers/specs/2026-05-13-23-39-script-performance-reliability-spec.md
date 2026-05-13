---
layer: operating_system
artifact_type: spec
status: proposed
template_id: detailed-specification
name: script-performance-reliability
parent_workstream: none
targets:
  - scripts/validate_repo_contracts.py
  - scripts/validate_adoption_shape.py
  - scripts/validate_planning_lifecycle.py
  - scripts/sync_agent_adapters.py
  - scripts/benchmark_runtime_validators.py
  - tests/test_validate_repo_contracts.py
  - tests/test_validate_adoption_shape.py
  - tests/test_validate_planning_lifecycle.py
related_features: []
related_stages: []
---

# Script Performance Reliability Specification

## Goal

Define bounded, behavior-preserving optimization and hardening design for repository validator scripts in `project-OS-starter` worktree, reducing runtime and redundant computation while improving robustness, diagnosability, and maintainability.

## Key Deliverables

### Hotspot-prioritized optimization scope

Document measured target scripts and internal hot paths where optimization will happen first, led by benchmark evidence rather than broad rewrite.

### Shared reliability and efficiency design

Define reusable patterns for traversal, parsing, subprocess invocation, and deterministic error reporting to remove duplicate logic and reduce drift risk.

### Verification-backed handoff contract

Provide explicit success criteria and proof requirements that ensure performance gain claims and behavior parity claims are both testable and auditable.

## Why These Target Files Are Chosen

- `scripts/validate_repo_contracts.py`
  - benchmark-identified hotspot and highest expected runtime reduction leverage
  - central orchestration path where redundant traversal/parsing costs accumulate
- `scripts/benchmark_runtime_validators.py`
  - canonical measurement harness for before/after proof
  - required to make performance claims auditable
- `scripts/validate_adoption_shape.py`
  - downstream policy surface invoked by repo-contract flows; included to guard indirect behavior drift
- `scripts/validate_planning_lifecycle.py`
  - downstream lifecycle gate coupled to repo-contract validation; included for parity checks
- `scripts/sync_agent_adapters.py`
  - included as secondary candidate for shared utility reuse when profiling indicates repeated subprocess/traversal patterns
- `tests/test_validate_repo_contracts.py`
  - primary regression suite for hotspot validator semantics and edge handling
- `tests/test_validate_adoption_shape.py`
  - protects adoption-mode policy parity affected indirectly by orchestration changes
- `tests/test_validate_planning_lifecycle.py`
  - protects planning-lifecycle parity in repo-contract execution chain

### Why Other Files Are Not Primary In This Pass

- work is intentionally hotspot-first to reduce blast radius and keep behavior parity verification strong
- non-hotspot validators remain out of primary modification scope unless post-change profiling promotes them
- this preserves incrementalism: optimize measured bottlenecks first, then expand scope only with new evidence

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- establish measured bottlenecks and concrete failure classes before any refactor

**Steps:**
- [ ] collect baseline timings for validator command set
- [ ] isolate dominant runtime contributors and repeated-cost operations
- [ ] map robustness gaps (missing path handling, malformed content, subprocess failure surfaces)
- [ ] identify shared low-level helper opportunities without changing CLI contracts

**Verification:**
- [ ] hotspot list tied to benchmark evidence
- [ ] reliability gap list tied to concrete scenarios

**Exit Criteria:**
- optimization targets are bounded and evidence-backed

### Wave 2: Decision closure

**Purpose:**
- close design choices and define safe refactor boundaries

**Steps:**
- [ ] define prioritized optimization set for hotspot validators
- [ ] define helper extraction boundaries for repeated low-level operations
- [ ] define per-script behavior-preservation constraints
- [ ] define deterministic error/exit handling expectations

**Verification:**
- [ ] each change class has explicit in-scope and out-of-scope boundary
- [ ] no decision depends on hidden assumptions

**Exit Criteria:**
- design can be implemented without semantic ambiguity

### Wave 3: Validation and approval readiness

**Purpose:**
- finalize proof model for speed, parity, and reliability

**Steps:**
- [ ] define before/after benchmark comparison requirements
- [ ] define regression and edge-case test additions
- [ ] define acceptance thresholds and fallback decisions

**Verification:**
- [ ] validation plan can prove both improvement and compatibility

**Exit Criteria:**
- spec is implementation-plan ready

## Design Decisions

### Decision: Optimize measured hotspots first

- context: benchmark baseline shows runtime concentration in subset of validators
- choice: prioritize `scripts/validate_repo_contracts.py` first, then secondary validators based on measured impact
- alternatives considered:
  - optimize all validators uniformly
  - focus by file size or complexity only
- impact:
  - maximizes performance return per change
  - reduces broad-regression risk

### Decision: Prefer work reduction before parallel execution

- context: many script costs come from repeated scans/parsing, not CPU-heavy independent tasks
- choice: reduce unnecessary traversal/parsing first (prefilters, single-pass collection, lazy parsing), delay parallelism unless still needed
- alternatives considered:
  - add concurrency immediately
  - keep eager traversal and optimize micro-operations only
- impact:
  - simpler correctness model
  - lower overhead and easier debugging

### Decision: Introduce per-run memoization for immutable artifacts

- context: repeated loads of adoption mode, manifests, and parsed metadata increase overhead
- choice: use process-local caching for immutable per-run artifacts keyed by normalized path/context
- alternatives considered:
  - no caching
  - persistent cross-run cache
- impact:
  - removes redundant compute safely
  - avoids cache invalidation complexity

### Decision: Standardize subprocess and failure reporting behavior

- context: mixed subprocess and in-process execution paths can hide failure context
- choice: keep existing behavior semantics but enforce clearer, deterministic failure propagation and messaging
- alternatives considered:
  - keep current ad-hoc reporting
  - force all steps to subprocess only
- impact:
  - better diagnosability
  - preserved compatibility with current orchestration

### Decision: Reliability hardening is first-class, not post-optimization

- context: speed gains without robust edge handling reduce trust and CI reliability
- choice: include edge-case and malformed-input handling improvements in same bounded pass
- alternatives considered:
  - performance-only pass first
  - reliability-only pass first
- impact:
  - balanced quality outcome
  - fewer regressions escaping to CI

## Invariants

- validator CLI interfaces and argument semantics remain backward compatible
- exit-code meaning remains unchanged
- pass/fail policy strictness does not weaken
- generated-versus-source ownership boundaries remain intact
- optimization must not suppress actionable stderr/stdout evidence
- caching remains per-run only and correctness-preserving
- no hidden global mutable state shared across separate command invocations

## Acceptance Criteria

- measured hotspot command runtime shows improvement versus baseline median/p95 or is documented as reliability-only with explicit reason
- touched validator behavior remains functionally equivalent on existing suite and direct command checks
- new/updated tests cover at least one edge case per changed reliability path
- no new validator policy bypass or weakened enforcement introduced

## Non-Goals

- no architecture migration of repo documentation model
- no adoption-mode semantic change
- no persistent cache layer across runs
- no rewrite of all validator scripts in one pass
- no user-facing contract redesign for commands

## Risks and Mitigations

- risk: hidden behavior drift from traversal refactors
  - mitigation: test-first regression cases for ordering/filtering-sensitive paths
- risk: false performance conclusions from noisy timing
  - mitigation: compare repeated-run medians/p95 with same command set and environment
- risk: over-abstraction from helper extraction
  - mitigation: extract only repeated low-level concerns with narrow interfaces
- risk: masking failures during in-process execution
  - mitigation: explicit return-code and message parity checks across execution paths

## Validation Plan

- proof target: hotspot prioritization is evidence-based
  - method: run benchmark script before implementation
  - evidence: `.tmp-tests/benchmark_before.json` plus console timing report

- proof target: optimized scripts preserve behavior
  - method: run focused validator tests and full pytest suite
  - evidence: passing outputs from `tests/test_validate_repo_contracts.py`, related validator tests, and full `pytest -q`

- proof target: targeted runtime improves
  - method: rerun benchmark script after changes and compare median/p95 per command
  - evidence: `.tmp-tests/benchmark_after.json` and explicit before/after comparison notes

- proof target: reliability hardening is enforced
  - method: add failing-first regression tests for edge paths then confirm pass after implementation
  - evidence: test diff + pytest output showing red/green cycle completion

- proof target: governance boundaries preserved
  - method: run repo contract validator gates
  - evidence: successful `python scripts/validate_repo_contracts.py --fast` and/or full gate as required by changed scope

## Completion Criteria

A specification item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
