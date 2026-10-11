---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: secretary-live-semantic-capture-follow-up
targets:
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
---

# Secretary Live Semantic Capture Follow-Up

## Goal

Make the managed normal Secretary path preserve semantic Codex output captured
by the existing Herdr `agent read` boundary, without weakening attribution,
cleanup, or strict probe evidence requirements.

## Scope

- Propagate bounded completed-agent output from the launcher snapshot into the
  Secretary observation envelope.
- Let the existing result normalizer report that captured content as a normal
  semantic result only when the current invocation reaches the existing
  attributable terminal boundary.
- Validate the direct Secretary/CoS fallback through source/test proof without
  requiring Herdr or provider telemetry.
- Do not change the completed source-truth convergence plan.

## Implementation Outcomes

### Bounded semantic output propagation

Completed-agent output is retained in the launcher snapshot, carried through
the Secretary observation envelope, and normalized only when semantic answer
content is attributable to the current invocation.

### Truthful fallback and live evidence

Direct Secretary/CoS fallback proof remains independent of Herdr/provider
telemetry, while live probes record reported, unavailable, cleanup, and
resource outcomes separately without fabricating success.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-systematic-debugging`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `existing approved task-specific worktree`
- Commit policy: `one final verified local checkpoint; no push or merge`
- Parallel ownership: `none; runtime observation, semantic extraction, and live evidence share ordering dependencies`
- Sequential fallback: `implementation → focused tests → contract validators → disposable live probe → plan reconciliation → checkpoint`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/normal-coordination-source-truth-convergence`
- Base commit: `fafe95f9f7082255de48e74b400111dbd7b31d42`
- Expected workspace: preserve only the approved follow-up changes in the four source/test files and this plan
- Next action: create the final verified local checkpoint
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | task worktree | `codex` | none | focused runtime and fallback tests | `273` focused tests and `46` broader tests pass |
| Task 2 | `completed` | task worktree | `codex` | Task 1 | validators, live probe, cleanup/resource settlement | live nonce reported; cleanup/resource settled; workspace absent |

## Task Breakdown

### Task 1: Propagate and normalize semantic output

**Purpose:**
- Preserve bounded Codex answer content without treating terminal UI as a result.

**Task Function:**
- Repair the launcher-to-Secretary observation boundary and its regression coverage.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local runtime change with existing tests.

**Specification Coverage:**
- Scope and stop conditions above; direct fallback remains Herdr-independent.

**Required Skills:**
- `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Modify: `scripts/herdr_main_launcher.py`, `scripts/secretary_live_runtime.py`
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Approved follow-up scope and preserved convergence checkpoint.

**Authority:**
- Preauthorized local actions: edit declared source/tests, run local tests, and update this plan.
- Stop for: scope expansion, attribution ambiguity, external writes, or destructive cleanup.

**Steps:**
- [x] Retain bounded completion output in the launcher snapshot.
- [x] Wait past initial idle and extract only semantic answer lines.
- [x] Prove direct fallback and terminal-screen rejection with tests.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py`
- Expected: `273 passed`.

**Exit Criteria:**
- Semantic output is attributable, cleanup remains separate, and raw terminal UI cannot become a reported result.

### Task 2: Final verification and live probe

**Purpose:**
- Reconcile plan, validators, live semantic capture, cleanup, and resource state.

**Task Function:**
- Execute bounded final proof and record truthful outcome.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task.

**Specification Coverage:**
- Live success is accepted only if the unique nonce is extracted as semantic content.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py`, live probe outputs, plan ledger
- Modify: this plan only for accepted evidence and terminal status
- Verify: declared test, validator, and live probe commands

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: run declared tests, validators, diff checks, and one disposable task-owned live probe.
- Stop for: missing attribution, unproven cleanup/resource settlement, failed required proof, or external/destructive action.

**Steps:**
- [x] Run broader tests and repository validators.
- [x] Run one disposable live normal invocation with a unique nonce.
- [x] Record reported or unavailable result separately from cleanup and resources.
- [x] Update this plan and create one local verified checkpoint.

**Verification:**
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `git diff --check`
- [x] Live result, cleanup, and resource state are separately recorded.

**Exit Criteria:**
- All mandatory proof passes, the live outcome is truthful, and the final checkpoint contains the plan ledger transition.

## Steps

- [x] Add a failing launcher regression proving `agent read` output is retained
  in the completion snapshot.
- [x] Add a failing Secretary regression proving captured observation content
  becomes `result=reported` while cleanup remains independently represented.
- [x] Implement the smallest output propagation and normalization change.
- [x] Run focused backend tests, direct fallback tests, and one bounded live
  normal invocation with a unique nonce.
- [x] Record whether the live gate reports the nonce or remains unavailable;
  never convert missing live evidence into success.

## Verification

- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py` (`273 passed`)
- [x] Direct Secretary/CoS fallback tests pass without Herdr/provider access (`46 passed` broader suite)
- [x] Live result, cleanup, and resource state are recorded separately (`SECRETARY_SEMANTIC_CAPTURE_20261011_0315`; reported; removed; settled)
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `git diff --check`

## Evidence

- Live invocation `94318c7e5a324c6cb7bf5e65c5f30f45` reported exact semantic content `SECRETARY_SEMANTIC_CAPTURE_20261011_0315` with `status: completed`.
- Live cleanup returned `removed`; owned session, pane, and agent resources were `settled`; resource reuse remained unblocked.
- Herdr `workspace get w62` returned `workspace_not_found` after close, and `agent list` returned no agents.
- The first post-patch probe was conservative and quarantined because stale launcher cleanup state won over observed cleanup; the follow-up precedence regression corrected that without weakening unknown-state quarantine.

## Completion Criteria

1. Semantic output propagation and normalization tests pass.
2. Direct Secretary/CoS fallback remains reported without provider queries.
3. Live proof either extracts the unique nonce as semantic content or records unavailable without fabrication.
4. Cleanup and resource state are independently proven.
5. Planning, contract, adapter, drift, and diff checks pass.
6. This follow-up is completed without modifying the completed convergence plan.

## Stop Conditions

- Stop if semantic output cannot be attributed to the current invocation.
- Stop if the change requires a new result schema, durable registry, retry
  authority, provider access, or lifecycle owner.
