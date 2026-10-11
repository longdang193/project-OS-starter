---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: secretary-review-corrections
targets:
  - scripts/secretary_live_runtime.py
  - tests/test_secretary_live_runtime.py
---

# Secretary Review Corrections

## Goal

Address the independent review findings on PR #84 without reopening the
completed convergence, semantic-capture, or provenance plans.

## Implementation Outcomes

### Truthful semantic reporting

Partial, stopped, timed-out, or otherwise unconfirmed observation content never
becomes an authoritative completed result.

### Stable final-answer extraction

When multiple rendered answer segments exist, the latest answer is selected
instead of earlier progress commentary.

### Complete terminal-state handling

`done` is treated consistently with `idle` for transport evidence, cleanup,
runtime snapshots, and normal probe classification.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `existing approved task-specific worktree`
- Commit policy: `one amended local checkpoint; push PR branch; no merge before review PASS or review-turn limit`
- Parallel ownership: `none`
- Sequential fallback: `reproduce review findings → patch → focused proof → final validators → push → next review turn`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-coordination-source-truth-convergence`
- Base commit: `84c4e2bb634fcda9a3e62d6879e8e2a367e61c1d`
- Expected workspace: preserve only review-fix source/tests and this plan
- Next action: commit, push, and request the next review turn
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | focused regressions and final validators | `326 passed`; planning/contracts/diff checks pass |

## Task Breakdown

### Task 1: Correct reviewed runtime boundaries

**Purpose:**
- Remove the two important correctness gaps and the done-state mismatch identified by review-1.

**Task Function:**
- Harden semantic result admission and terminal-state symmetry.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded review correction with existing runtime ownership.

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`, `_extract_codex_semantic_content`, `_normalize_invocation_outcome`, `_classify_capabilities`
- Modify: `scripts/secretary_live_runtime.py`, `tests/test_secretary_live_runtime.py`
- Verify: focused Secretary and launcher tests

**Authority:**
- Preauthorized local actions: reproduce review findings, edit declared source/tests/plan, run local proof, commit and push this PR branch.
- Stop for: unresolved attribution ambiguity, external destructive action, or semantic conflict requiring user choice.

**Steps:**
- [x] Reject unconfirmed semantic content and add timeout/stopped regressions.
- [x] Select the latest answer segment and add multi-answer regression.
- [x] Align `done` with `idle` and add transport regression.
- [x] Run final proof, update evidence, commit, push, and request review.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py` (`280 passed`)
- [x] Final validators passed; pushed PR head awaits next review turn.

**Exit Criteria:**
- Review findings are covered by regressions, the branch is pushed, and the next independent review returns PASS or the authorized review-turn limit is reached.

## Verification

- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_benchmark.py tests/test_secretary_evidence_adapter.py tests/test_reconciliation.py tests/test_project_os_reconciliation.py` (`326 passed`)
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `git diff --check`

## Evidence

- Review-1 Important finding: unconfirmed semantic content is now excluded from observation evidence and cannot infer a completed result.
- Review-1 Important finding: extractor selects the latest answer segment after prior `Worked for` commentary.
- Review-1 Minor finding: `done` is accepted consistently for transport evidence, runtime snapshots, and probe classification.
- Focused and related test suites pass with `326` tests; no unrelated files changed.

## Completion Criteria

1. All review-1 Important findings are fixed and regression-tested.
2. The Minor done-state finding is fixed and regression-tested.
3. Focused tests, planning validation, repository contracts, and diff checks pass.
4. The amended PR head is pushed before the next review turn.
5. Merge remains blocked until review PASS or the maximum of three review turns.
