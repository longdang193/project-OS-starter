---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: secretary-observation-provenance-follow-up
targets:
  - scripts/secretary_live_runtime.py
  - tests/test_secretary_live_runtime.py
---

# Secretary Observation Provenance Follow-Up

## Goal

Make the provenance of launcher observation diagnostics explicit without
discarding useful diagnostics or changing the authoritative Secretary result.

## Implementation Outcomes

### Explicit launcher diagnostic scope

Preserve `execution.observation_error` for compatibility, mark it as
launcher-local, and expose the same diagnostic under the observability envelope
with explicit provenance.

### Non-blocking final result

When Secretary later observes semantic output successfully, launcher-local
`not_observed` remains diagnostic evidence and does not downgrade `result`.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `existing approved task-specific worktree`
- Commit policy: `one final verified local checkpoint; no push or merge`
- Parallel ownership: `none`
- Sequential fallback: `consumer inspection → regression → minimal provenance patch → final verification → checkpoint`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-coordination-source-truth-convergence`
- Base commit: `84c91d7aa04f69f7c359b6200ee10f2319806803`
- Expected workspace: clean at the semantic-capture checkpoint before this follow-up
- Next action: create the final verified local checkpoint
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | consumer inspection, focused regression, final validators | no final-status consumers found; `274` focused tests pass |

## Task Breakdown

### Task 1: Clarify launcher diagnostic provenance

**Purpose:**
- Prevent launcher-local observation uncertainty from being mistaken for the final Secretary outcome.

**Task Function:**
- Preserve compatibility while making diagnostic ownership explicit.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, bounded schema-provenance correction.

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`
- Modify: `scripts/secretary_live_runtime.py`, `tests/test_secretary_live_runtime.py`
- Verify: repository consumers and focused runtime tests

**Authority:**
- Preauthorized local actions: inspect declared consumers, edit declared source/tests/plan, and run local verification.
- Stop for: external consumers requiring incompatible schema changes, scope expansion, or destructive action.

**Steps:**
- [x] Confirm no repository consumer treats `execution.observation_error` as final status.
- [x] Add the regression for launcher uncertainty plus successful Secretary observation.
- [x] Add explicit launcher provenance and run final proof.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py` (`62 passed`)
- Expected: focused suite passes and result remains `reported`.

**Exit Criteria:**
- Diagnostic provenance is explicit, compatibility is preserved, and no final result is downgraded.

## Verification

- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py` (`274 passed`)
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `git diff --check`

## Evidence

- Repository search found no consumer that interprets `execution.observation_error` as final status.
- Compatibility field remains intact; `execution.observation_error_scope` and `execution.launcher_observation_error` identify launcher ownership.
- `observability.launcher_observation_error` is distinct from Secretary `observability.observation_error`.
- Regression proves launcher `not_observed` plus successful Secretary semantic capture remains `result=reported`.

## Completion Criteria

1. Repository consumers are inspected and no final-status consumer is found.
2. Launcher observation diagnostics retain their value and explicit scope.
3. Secretary success remains `result=reported` when launcher observation was unavailable.
4. Focused tests and validators pass.
5. The completed convergence and semantic-capture plans remain unchanged.
