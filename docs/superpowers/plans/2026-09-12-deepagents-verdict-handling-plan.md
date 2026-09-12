---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: deepagents-verdict-handling
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - docs/superpowers/plans/2026-09-12-deepagents-verdict-handling-plan.md
---

# DeepAgents Verdict Handling

## Goal

Prevent Starter from reporting a DeepAgents task as successfully completed when
worker output contains the prescribed terminal verdict `FAIL` or `BLOCKED`, even
when a completion marker also appears. Preserve separation between delivery,
execution, observation, cleanup, and acceptance. Do not assign the original
fixture-write failure to DeepAgents without direct runtime evidence.

## Implementation Outcomes

### Truthful terminal classification

`herdr_main_launcher.py` recognizes supported `FAIL` and `BLOCKED` terminal
verdict lines from available pane output as existing `failed` task state. Both
produce launcher exit `2`, set `reconciliation_required` to `True`, and, with a
valid lifecycle receipt, produce `task_result` equal to
`{"state": "reported_failed", "accepted": False}`. Completion markers cannot
override negative evidence.

### Regression proof

`tests/test_herdr_main_launcher.py` covers bare and colon-form verdicts, quoted
or embedded examples, stale output before the latest startup banner,
completion-marker precedence, and incomplete observation. One parametrized
`main()` regression asserts exit code and emitted assignment fields together.

## Parsing Contract

- Report boundary: consider non-empty pane lines after the most recent exact `Running task non-interactively...` banner in available recent output. Lines before that banner are stale for the current attempt.
- Supported negative verdicts: line-start bare `FAIL` or `BLOCKED`, optionally followed by `: <message>`. Existing `[FAIL] Task failed`, traceback, and `ERROR:` formats remain supported.
- Quoted, embedded, indented, or fixture-content examples do not count as verdict lines.
- When startup banner is absent, parser may classify recognized content in available output but makes no complete attempt-correlation claim. Missing or unreliable terminal evidence remains non-success.
- Both negative verdicts map to existing `failed` state. No new `blocked` parser state is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed launcher, tests, and plan; run focused tests, repository validators, and bounded classifier probes; preserve unrelated dirty and untracked workspace state
- User-approval actions: commits, pushes, merges, external writes, destructive cleanup, and edits outside listed targets
- Parallel ownership: none; launcher and regression tests share one behavior contract
- Sequential fallback: baseline, regression cases, minimal parser patch, focused proof, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `ca218d676c7708a5cfc3aa7a94aa8cae99f4f6e7`
- Expected workspace: preserve untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite unrelated changes
- Next action: none; implementation and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline launcher tests and classifier behavior | `108 passed`; reproduced parser gap confirmed |
| Task 2 | `completed` | current | `codex` | Task 1 | `FAIL`/`BLOCKED` cases fail before fix | `43 passed` after parser/test patch |
| Task 3 | `completed` | current | `codex` | Task 2 | focused launcher suite passes with truthful exit state | `118 passed`; parser and launcher regression pass |
| Task 4 | `completed` | current | `codex` | Task 3 | final verification and preserved workspace proof | `118 passed`; validators passed; live Herdr → dcode-project probe returned exit `2`, `failed`, `reported_failed`, acceptance `False`, worker exit `0`, cleanup removed |

## Task Breakdown

### Task 1: Establish classifier baseline

**Purpose:**
- Confirm current failure-pattern and terminal-state behavior before editing.

**Task Function:**
- Map worker pane evidence through `_deepagents_task_state` and `_classify_deepagents_outcome`.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-local inspection and baseline execution.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: baseline only.

**Specification Coverage:**
- Recognized negative task reports must not be hidden by completion markers.

**Required Skills:**
- `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_DEEPAGENTS_FAILURE_PATTERN`
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_task_state`
- Inspect: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`
- Verify: `tests/test_herdr_main_launcher.py:test_deepagents_task_state_detects_failure_report`

**Dependencies:**
- Current source and tests at base commit.

**Authority:**
- Preauthorized local actions: inspect listed source/tests and run declared baseline tests.
- Stop for: changed base, unexpected launcher contract, or unrelated workspace mutation.

**Steps:**
- [x] Step 1: Run `py -3 -m pytest tests/test_herdr_main_launcher.py -q` and record baseline.
- [x] Step 2: Run bounded in-memory probes for bare and colon-form `FAIL`/`BLOCKED`, quoted examples, stale lines before a later startup banner, and completion-marker combinations.
- [x] Step 3: Confirm parser misses prescribed verdicts while existing lifecycle classification already has `failed` outcome semantics.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: current suite passes; reproduced prescribed verdict combinations expose current misclassification before fix.

**Exit Criteria:**
- Baseline behavior and exact symbols needing change are recorded.

### Task 2: Add regression cases

**Purpose:**
- Encode reproduced misclassifications before implementation.

**Task Function:**
- Add focused parser tests and one launcher-level regression.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: test-only change with explicit outcome oracle.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests provide direct proof.

**Specification Coverage:**
- Bare and colon-form `FAIL` and `BLOCKED` lines map to failed state.
- Failure evidence wins over completion marker.
- Quoted examples and stale pre-banner output do not become current verdicts.
- Worker exit `0` can coexist with reported task failure.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `tests/test_herdr_main_launcher.py:test_deepagents_task_state_detects_failure_report`
- Modify: `tests/test_herdr_main_launcher.py` near existing DeepAgents outcome and `main()` tests
- Verify: `scripts/herdr_main_launcher.py:_deepagents_task_state`

**Dependencies:**
- Task 1 baseline confirms current behavior.

**Authority:**
- Preauthorized local actions: add listed regression tests and run focused test nodes.
- Stop for: production changes before regression expectations are established or scope beyond listed launcher/tests.

**Steps:**
- [x] Step 1: Add parser cases for bare `FAIL`/`BLOCKED` and `FAIL:`/`BLOCKED:` forms, with legacy `[FAIL] Task failed` retained.
- [x] Step 2: Add negative cases for quoted/embedded/indented examples and stale lines before a later startup banner.
- [x] Step 3: Add one parametrized `main()` regression for `FAIL` and `BLOCKED` with zero worker exit, settled cleanup, matching completion marker, and valid receipt.
- [x] Step 4: Assert exit `2`, `status` `failed`, `task_result.state` `reported_failed`, `task_result.accepted` `False`, and `reconciliation_required` `True`.
- [x] Step 5: Run new tests and confirm reproduced cases fail against current implementation.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q -k "deepagents and (task_state or outcome or main)"`
- Expected: new reproduced cases fail before production patch; negative and existing cases remain valid.

**Exit Criteria:**
- Regression tests express exact parser boundary and full reporting contract.

### Task 3: Patch Starter terminal verdict handling

**Purpose:**
- Make launcher classification fail closed on prescribed worker verdicts.

**Task Function:**
- Extend existing DeepAgents failure recognition without adding lifecycle states or architecture.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one shared parser boundary; small contract-sensitive change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final independent review occurs in Task 4.

**Specification Coverage:**
- Supported bare and colon-form `FAIL`/`BLOCKED` lines map to existing `failed` state and prevent `reported_completed`.
- Completion marker cannot override recognized negative evidence from current available report boundary.
- Worker exit remains separate; zero exit plus negative task report returns exit `2`, `reported_failed`, acceptance `False`, reconciliation required.
- Missing or unreliable evidence remains unverified with nonzero launcher exit.
- Valid completion remains exit `0`, `reported_completed`, acceptance `None`.
- No complete attempt-correlation claim is added when startup banner is absent.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_DEEPAGENTS_FAILURE_PATTERN`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_task_state`
- Inspect: `scripts/herdr_main_launcher.py:_classify_deepagents_outcome`
- Verify: `tests/test_herdr_main_launcher.py` DeepAgents state, outcome, and `main()` tests

**Dependencies:**
- Task 2 regression tests fail as expected.

**Authority:**
- Preauthorized local actions: edit listed launcher symbols, update matching tests, and run declared checks.
- Stop for: changes to unrelated lifecycle components, new persistence/state machine, or DeepAgents runtime ownership.

**Steps:**
- [x] Step 1: Update failure recognition to match supported line-start bare or colon-form verdicts without broad substring false positives; retain legacy failure formats.
- [x] Step 2: Keep report-boundary behavior anchored to latest startup banner and preserve documented limitation when banner is absent.
- [x] Step 3: Run negative detection before completion-marker acceptance and map both verdicts to existing `failed` state.
- [x] Step 4: Preserve valid completion, worker exit, cleanup/recovery, receipt, and observation-error behavior.
- [x] Step 5: Run parser tests, outcome tests, and parametrized launcher regression.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q -k "deepagents"`
- Expected: all DeepAgents tests pass; negative verdict cases report `failed`, exit `2`, `reported_failed`, acceptance `False`, and reconciliation required; valid completion remains successful.

**Exit Criteria:**
- Starter cannot classify supported failed or blocked terminal verdicts as successful completion.

### Task 4: Final verification and handoff

**Purpose:**
- Prove focused behavior, repository contracts, and workspace boundaries.

**Task Function:**
- Perform final independent review and reconcile plan evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: one independent review covers parser precedence, exit code, reconciliation, and compatibility.

**Specification Coverage:**
- Confirmed Starter reporting defect fixed without claiming unproven DeepAgents causality.
- Recognized negative verdicts and missing required completion evidence cannot produce successful task reporting.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/herdr_main_launcher.py`
- Verify: `tests/test_herdr_main_launcher.py`
- Verify: `docs/superpowers/plans/2026-09-12-deepagents-verdict-handling-plan.md`

**Dependencies:**
- Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: run declared tests, validators, diff checks, and update plan evidence.
- Stop for: failed required proof, stale classifier claims, unexpected generated drift, commits, pushes, or destructive cleanup.

**Steps:**
- [x] Step 1: Run focused launcher tests.
- [x] Step 2: Run repository contract and planning validators.
- [x] Step 3: Run `git diff --check` and verify `.playwright-mcp/` and `db/` remain untouched.
- [x] Step 4: Record actual task completion, deviations, and accepted evidence; retain `active` during execution and transition plan status according to existing planning lifecycle after authorized verification.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q` — `118 passed`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .` — passed
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` — passed
- [x] `git diff --check` — passed
- [x] `git status --short` — approved source/test/plan changes plus preserved `.playwright-mcp/` and `db/`
- [x] Live Herdr → `dcode-project` probe in task-owned workspace — worker emitted `FAIL: live verdict parser probe`, then `COMPLETED` and expected marker; launcher returned `2` with `status=failed`, `task_result.state=reported_failed`, `task_result.accepted=False`, `worker_exit_code=0`, `reconciliation_required=True`; cleanup removed role views and probe workspace closed
- Expected: focused tests and validators pass; only approved launcher/test/plan paths change; unrelated untracked paths remain present.

**Exit Criteria:**
- Fresh evidence supports Starter fix, no unsupported DeepAgents attribution is added, and task ledger matches Git and test evidence.

## Non-Goals

- No change to DeepAgents worker runtime, model, shell allow-list, or timeout defaults.
- No fixture-content inspection, fixture regeneration, fixture schema validator, atomic fixture writer, rollback system, heartbeat, lease DB, scheduler, retry policy, or new state machine.
- No automatic reconciliation of arbitrary workspace files.
- No commit, push, merge, external configuration write, or destructive cleanup.
- No claim that original sandbox rejection caused fixture failure without preserved runtime evidence.

## Verification

- Focused DeepAgents launcher regression suite.
- Repository contract and planning validators.
- `git diff --check` and preserved unrelated workspace-state proof.
- One independent review of terminal-state precedence and evidence fields.

## Completion Criteria

1. Supported bare and colon-form `FAIL` and `BLOCKED` lines map to existing `failed` state and cannot produce `reported_completed`.
2. Completion markers cannot override recognized negative evidence from the same available report boundary.
3. With valid receipt evidence, worker exit `0` plus negative task report returns `reported_failed`, acceptance `False`, launcher exit `2`, and reconciliation required.
4. Missing or unreliable terminal evidence remains unverified with acceptance `None` and nonzero launcher exit.
5. Valid successful completion remains exit `0`, `reported_completed`, and acceptance `None`.
6. Regression tests cover both reproduced cases, bare/colon forms, quoted examples, stale pre-banner output, and incomplete/interrupted evidence.
7. Focused tests, validators, and diff checks pass with fresh output.
8. Unrelated dirty or untracked workspace state remains untouched.
9. Plan status transitioned to `completed` only after authorized execution and verified completion.
