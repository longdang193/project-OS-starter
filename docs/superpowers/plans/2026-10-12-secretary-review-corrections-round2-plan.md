---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: secretary-review-corrections-round2
targets:
  - scripts/secretary_live_runtime.py
  - scripts/benchmark_secretary_architecture.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_benchmark.py
---

# Secretary Review Corrections Round 2

## Goal

Address the second independent review findings on PR #84 while preserving the
completed convergence, semantic-capture, and provenance plans.

## Implementation Outcomes

### Fresh observation admission

Recovered output without a current state or sequence transition cannot be
reported as current semantic completion.

### Consistent evidence and measurement

Cleanup/resource summaries use one effective cleanup state, and benchmark
measurement passes the production normalizer its declared payload envelope.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `existing approved task-specific worktree`
- Commit policy: `one local checkpoint; push PR branch; merge only after review PASS or review-turn limit`
- Parallel ownership: `none`
- Sequential fallback: `reproduce → patch → tests → validators → push → final review turn`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-coordination-source-truth-convergence`
- Base commit: `95d17c3164ba897be68e0846ac5840a64b254a4e`
- Expected workspace: preserve only review-round-two source/tests and this plan
- Next action: push the third-review head and await the final review turn
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | focused tests, benchmark correctness, validators | `328 passed`; measurement scenarios correct; validators pass |

## Task Breakdown

### Task 1: Harden stale-output and evidence boundaries

**Purpose:**
- Fix the remaining Important findings and their regression coverage.

**Task Function:**
- Enforce fresh observation identity and consistent evidence reduction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded corrections to existing runtime and benchmark owners.

**Files And Symbols:**
- Inspect: `_observe_submitted_codex`, `_normalize_invocation_outcome`, `_owned_resources`, `run_measure_benchmark`
- Modify: declared targets in frontmatter
- Verify: focused runtime and benchmark tests

**Authority:**
- Preauthorized local actions: reproduce review findings, edit declared files, run proof, commit, and push the PR branch.
- Stop for: unresolved semantic conflict, destructive action, or third-party write.

**Steps:**
- [x] Reject recovered stale output without current state evidence.
- [x] Reconcile cleanup/resource state and benchmark envelope shape.
- [x] Run final proof, push, and request the third review turn.

**Verification:**
- [x] Focused runtime/benchmark tests pass (`294 passed`).
- [x] Final validators passed; corrected PR head is ready for review turn 3.

**Exit Criteria:**
- The third review receives the corrected head; merge remains gated by PASS or the maximum review-turn rule.

## Verification

- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_benchmark.py tests/test_secretary_evidence_adapter.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py` (`328 passed`)
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `git diff --check`

## Evidence

- Recovered output requires a current state or sequence transition before idle completion is accepted.
- Cleanup precedence and owned-resource summaries now use the same effective cleanup state.
- Measurement mode passes the full production normalizer envelope and reports all scenarios as correct.
- The completed convergence plan’s inherited whitespace remains preserved rather than reopened or rewritten.

## Completion Criteria

1. Review-round-two Important findings have focused regressions.
2. Relevant tests, benchmark correctness, planning, contracts, and diff checks pass.
3. The corrected head is pushed before review turn 3.
4. Merge remains blocked until review PASS or three total review turns.
