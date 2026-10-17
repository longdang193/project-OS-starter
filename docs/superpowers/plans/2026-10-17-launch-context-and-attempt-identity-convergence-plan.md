---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: launch-context-and-attempt-identity-convergence
targets:
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - scripts/secretary_evidence_adapter.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/secretary_live_pilot.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_evidence_adapter.py
  - tests/test_secretary_receipts.py
  - tests/test_acceptance_handoff.py
  - tests/test_secretary_live_pilot.py
  - tests/test_starter_kit_generation.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-17-launch-context-and-attempt-identity-convergence-plan.md
---

## Review Basis

The consolidated recommendation is accepted with a narrower implementation boundary.

It identifies a real defect: `SecretaryLaunchRequest` requires an `attempt_id` before
execution, while `scripts/herdr_main_launcher.py:_main_body` allocates a fresh UUID for
the actual launch. The strict Secretary path then validates launcher evidence against the
preselected request identity. One execution occurrence therefore has two competing owners.

The recommendation does not authorize collapsing semantic boundaries. Worker execution
result, Runtime settlement and cleanup, CoS `PASS | FAIL | BLOCKED`, Plan consequence,
Git/GitHub consequence, and optional Secretary routing remain separate facts and owners.

The current repository already provides launcher evidence, `dispatch_id`,
`registry_launcher.result_file`, `registry_launcher.task_result_file`, and validated
task-result parsing. `scripts/secretary_evidence_adapter.py` is also an active consumer and
must be included in the identity inventory. This plan adds no receipt service, database,
registry, supervisor, event bus, retry coordinator, or second result transport. The strict
Secretary receipt remains a compatibility/export format until its consumers migrate; it is
not an ordinary Worker prerequisite.

## Goal

Make the launcher the only allocator of a real execution `attempt_id`, capture stable
Plan/task/assignment facts once from admission, consume the existing attempt-specific
result channel, and keep settlement and CoS acceptance independently authoritative.

```text
PreparedLane / admitted Plan
        -> captured stable launch context
        -> launcher allocates one fresh attempt_id
        -> existing result channel
        -> result and settlement validation
        -> independent CoS acceptance
        -> validated Plan consequence
```

Preflight, target-resolution failure, and dry-run use existing `dispatch_id` and the
current ephemeral invocation context; they produce no execution `attempt_id`. A real
execution `attempt_id` is allocated exactly once immediately before the launcher commits
to execution. It is never derived from task, Plan, assignment, branch, worktree, or digest
values, and no new cross-process identity is introduced unless Task 1 proves an existing
consumer cannot correlate without it.

## Implementation Outcomes

The implementation preserves separate ownership while removing the competing
execution-identity allocator. The following outcomes are the authoritative
contract for the launcher, Secretary adapter, Runtime settlement, CoS
acceptance, and Plan consequence boundaries.

## One owner for execution identity

`PreparedLane` remains the admission-owned source of stable task, Plan, repository,
worktree, grant, digest, and assignment facts. Existing launcher assignment evidence adds
the fresh attempt ID and result destinations. A new binding abstraction is not introduced
unless Task 1 proves that the existing `PreparedLane` plus assignment evidence cannot
support recovery or validation. Pre-launch failures do not fabricate a completed attempt.

## One normal result channel

The launcher emits the generated attempt binding with its authoritative evidence. Secretary
runtime consumes the existing result and task-result files and validates them against that
binding. The Worker does not generate correlation metadata.

## Independent fail-closed authority

Stale attempts, mismatched task/grant digests, changed Plan revisions, wrong worktrees,
unsettled resources, missing structured results, and invalid acceptance decisions remain
blocked. A valid result never implies CoS acceptance.

## Derived strict reporting and recovery

`secretary-live-runtime-receipt-v1` keeps its current required fields and is built only after
source-local launch, task-result, settlement, and acceptance evidence has been validated. If
the strict schema must change, a new schema version is required; v1 is not silently loosened.
Existing acceptance/launch evidence supports idempotent recovery without a new registry: no
Worker relaunch and no duplicate Plan transition. A delayed result from attempt A cannot
satisfy attempt B.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: `optional worktree`
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: create a clean task-owned worktree from `origin/main`, edit listed source, test, and documentation files, run declared local checks, and record capability-blocked live evidence without fabricating success
- User-approval actions: push, PR publication, review assignment, merge, provider/configuration changes, destructive cleanup, and deletion of existing evidence
- Parallel ownership: none; all tasks share the identity contract
- Sequential fallback: Tasks 1 through 5 in order; stop at the first contract or fail-closed regression

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/launch-context-attempt-identity`
- Base commit: `02c3625a357c63a06c427bcbd5a1fee9c4b2fb50`
- Expected workspace: clean task-owned worktree from `origin/main`; leave the current checkout and its four untracked runtime-observation JSON files untouched
- Next action: branch disposition after verified completion; push, PR, self-review, and merge remain separately authorized actions
- Blockers: none
- Approved deferrals: strict provider probe remains non-blocking `BLOCKED_CAPABILITY` because transport completion/cleanup and an attributable structured Secretary receipt are unavailable; no synthetic success is claimed

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | failing ownership/stale-result tests | focused regression tests passed; launcher/Secretary identity inventory recorded |
| Task 2 | `completed` | current | `codex` | Task 1 | one launcher-owned attempt binding | focused launcher and contract tests passed; pre-attempt outcomes contain no execution attempt |
| Task 3 | `completed` | current | `codex` | Task 2 | Secretary uses existing result channel | focused Secretary, evidence-adapter, receipt, and pilot tests passed |
| Task 4 | `completed` | current | `codex` | Task 3 | recovery/settlement/acceptance proof | 427 lifecycle tests passed; acceptance canary PASS/replay and negative stale/mismatch/resource cases passed |
| Task 5 | `completed` | current | `codex` | Task 4 | fresh focused/full/live verification | validators, Starter Kit build/validation, focused suite, full suite, and strict probe classification passed |

## Task Breakdown

### Task 1: Freeze the binding contract and add failing proof

**Purpose:** Rebase the work on merged `main`, inventory every identity consumer, and encode the intended fail-closed cases.

**Task Function:** Trace identity creation, result publication, settlement, acceptance, replay, and evidence aggregation; add focused regression tests.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-first contract tracing and shared-boundary ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead controller owns the initial contract inventory.

**Specification Coverage:** launcher-owned attempt identity; admission-owned stable identity; optional grouping; separate result and acceptance authority.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/lane.py:PreparedLane`, `scripts/project_os_runtime/attempt.py:normalize_attempt`, `scripts/herdr_main_launcher.py:_main_body`, `scripts/secretary_live_runtime.py:SecretaryLaunchRequest`, `scripts/project_os_runtime/results.py:parse_task_result`, `scripts/project_os_runtime/acceptance_handoff.py:handoff_acceptance`, `scripts/secretary_evidence_adapter.py`
- Modify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`, `tests/test_dcode_project.py`, `tests/test_acceptance_handoff.py`, `tests/test_secretary_evidence_adapter.py`
- Verify: `scripts/herdr_main_launcher.py`, `scripts/secretary_live_runtime.py`, `scripts/project_os_runtime/results.py`, `scripts/project_os_runtime/acceptance.py`, `scripts/secretary_evidence_adapter.py`

**Dependencies:** Current source and the completed one-fact plan are authoritative.

**Authority:**
- Preauthorized local actions: inspect the listed sources and add failing focused tests without changing runtime behavior
- Stop for: any request to collapse Worker, Runtime, CoS, Plan, or Git authority into one completion flag

**Steps:**
- [x] Record the existing `dispatch_id`/ephemeral invocation path, launcher attempt allocation points, result consumers, and strict receipt consumers.
- [x] Add tests proving dry-run and preflight/target-resolution failure produce no execution `attempt_id` and retain `dispatch_id` correlation.
- [x] Add a test proving a preselected caller `attempt_id` cannot define a later launch, plus delayed attempt-A-after-attempt-B rejection proof.
- [x] Assert valid result plus settlement does not produce `AcceptanceDecision(PASS)` without independent acceptance and that the evidence adapter preserves attribution.

**Verification:** `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_dcode_project.py tests/test_acceptance_handoff.py tests/test_secretary_evidence_adapter.py`

**Exit Criteria:** Failing tests isolate the competing owner and required fail-closed behavior.

### Task 2: Make the launcher the sole attempt allocator

**Purpose:** Remove caller-supplied execution identity while preserving Worker result and lifecycle binding.

**Task Function:** Change the shared attempt contract, launcher CLI, and evidence projection.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: launcher owns delivery, attempt creation, and result destinations.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract tests cover the bounded change.

**Specification Coverage:** one fresh launcher attempt per execution; no static derivation; existing result files; truthful pre-launch failures.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_normalize_secretary_runtime_binding`, `scripts/herdr_main_launcher.py:_main_body`, `scripts/herdr_main_launcher.py:_build_assignment_result`, `scripts/project_os_runtime/results.py:parse_result_receipt`, `scripts/project_os_runtime/results.py:parse_task_result`, `scripts/project_os_runtime/lane.py:PreparedLane`
- Modify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`
- Verify: `scripts/herdr_main_launcher.py:build_parser`, `scripts/project_os_runtime/results.py:publish_task_result`, `scripts/secretary_evidence_adapter.py`

**Dependencies:** Task 1 failing tests.

**Authority:**
- Preauthorized local actions: modify the launcher so it emits the only real `attempt_id` and uses existing dispatch/assignment evidence without adding another identity layer
- Stop for: weakened task, grant, worktree, Plan revision, cleanup, retirement, or freshness validation

**Steps:**
- [x] Remove `--secretary-attempt-id` and any caller-owned execution ID input; do not add `--secretary-invocation-id` because existing dispatch and ephemeral invocation context remain sufficient before execution.
- [x] Keep `dispatch_id` for preflight, dry-run, target-resolution, and other pre-attempt outcomes; ensure those result objects contain no execution `attempt_id`.
- [x] Allocate `attempt_id` exactly once immediately before the launcher commits to actual execution, then pass it to receipt and task-result publication.
- [x] Emit the generated attempt ID and existing result destinations in launcher assignment evidence; preserve current attempt guards and retirement behavior.

**Verification:** `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_secretary_evidence_adapter.py`

**Exit Criteria:** No production Secretary launch supplies execution `attempt_id`; launcher evidence is authoritative.

### Task 3: Consume the existing result channel from Secretary runtime

**Purpose:** Remove strict receipt generation from ordinary execution readiness and validate against captured launch context.

**Task Function:** Adapt request construction, command construction, sanitization, and strict export.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-boundary adapter change with fail-closed behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing Secretary runtime and receipt suites cover the adapter.

**Specification Coverage:** launcher-owned identity; lookup is not proof; strict probe readiness remains separate; grouping IDs stay out of Worker schemas.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:SecretaryLaunchRequest`, `scripts/secretary_live_runtime.py:build_launcher_command`, `scripts/secretary_live_runtime.py:_bound_task`, `scripts/secretary_live_runtime.py:sanitize_launcher_result`, `scripts/secretary_live_runtime.py:_binding_matches`, `scripts/project_os_runtime/secretary_receipts.py:build_live_receipt`, `scripts/secretary_evidence_adapter.py`
- Modify: `scripts/secretary_live_runtime.py`, `scripts/secretary_evidence_adapter.py`, `scripts/project_os_runtime/secretary_receipts.py`, `scripts/secretary_live_pilot.py`, `tests/test_secretary_live_runtime.py`, `tests/test_secretary_evidence_adapter.py`, `tests/test_secretary_receipts.py`, `tests/test_secretary_live_pilot.py`
- Verify: `scripts/project_os_runtime/results.py:parse_result_receipt`, `scripts/project_os_runtime/results.py:parse_task_result`

**Dependencies:** Task 2 launcher binding.

**Authority:**
- Preauthorized local actions: update Secretary adapters and derived receipt/export builders to consume launcher evidence and existing result files
- Stop for: promoting pane text, exit code, provider telemetry, timestamp proximity, or cleanup alone into Worker result or CoS acceptance

**Steps:**
- [x] Make `SecretaryLaunchRequest` carry stable admission context and existing dispatch/grouping context, not caller-owned execution identity.
- [x] Remove the entire machine-owned binding block from Worker task prose: `task_id`, `plan_revision`, `attempt_id`, `run_id`, and provider travel through launcher evidence, not the semantic task text or task hash.
- [x] Read and validate launcher-emitted binding and result destinations in `sanitize_launcher_result()`.
- [x] Migrate current Secretary evidence and receipt consumers to launcher-produced identities and existing result files.
- [x] Build `secretary-live-runtime-receipt-v1` only after source-local evidence is independently validated, preserving every required v1 field; no schema change was required.
- [x] Keep ordinary routing independent and classify missing strict receipts as `BLOCKED_CAPABILITY` for strict probes only.

**Verification:** `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py tests/test_secretary_live_pilot.py`

**Exit Criteria:** Secretary has no competing attempt allocator and uses the existing attempt-specific result channel.

### Task 4: Reconcile recovery, stale attempts, settlement, and acceptance

**Purpose:** Prove identity simplification preserves replay safety and authority separation.

**Task Function:** Bind acceptance/recovery to persisted launch context and exercise positive, stale, and restart paths.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: recovery and Plan mutation are authority-sensitive.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing handoff and lifecycle tests provide direct proof.

**Specification Coverage:** independent acceptance binding; separate settlement; no relaunch or duplicate Plan transition; stale evidence blocked.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/acceptance_handoff.py:handoff_acceptance`, `scripts/project_os_runtime/acceptance_handoff.py:replay_acceptance`, `scripts/project_os_runtime/acceptance.py:validate_acceptance_decision`, `scripts/project_os_runtime/attempt.py:settlement_decision`, `scripts/herdr_main_launcher.py:retire_lane`
- Modify if Task 1 or Task 3 proves a concrete gap: `scripts/project_os_runtime/acceptance_handoff.py`; always update the focused lifecycle tests as needed: `tests/test_acceptance_handoff.py`, `tests/test_herdr_main_launcher.py`, `tests/test_dcode_project.py`, `tests/test_project_os_runtime.py`
- Verify: `scripts/project_os_runtime/acceptance.py:authorize_dependent_transition`, `scripts/project_os_runtime/plan_preparation.py:apply_accepted_plan_transitions`

**Dependencies:** Task 3 validated binding.

**Authority:**
- Preauthorized local actions: update acceptance/recovery binding reads and add disposable lifecycle fixtures
- Stop for: duplicate Plan mutation, Worker relaunch after accepted evidence, acceptance derived from result validity, or reuse after unresolved cleanup

**Steps:**
- [x] Persist only the minimum binding required by existing acceptance replay and recovery records.
- [x] Validate decisions against persisted binding and current mutable Plan/Git authority.
- [x] Prove the positive path end to end through the existing controller-owned acceptance handoff: launcher/attempt binding, settled evidence, independent artifact hash, real `AcceptanceDecision(PASS)`, and one guarded Plan transition.
- [x] Verify negative stale-attempt, mismatch, artifact-freshness, unsettled-resource, and malformed/missing-evidence paths.
- [x] Verify fresh-controller replay with unchanged Worker launch and Plan mutation counts, no duplicate attempt, and no duplicate Plan transition.
- [x] Retain the existing launcher assignment/result evidence and acceptance records; no `AttemptBinding` abstraction or acceptance broadening was required.

**Verification:** `py -B -m pytest -q tests/test_acceptance_handoff.py tests/test_project_os_runtime.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py`

**Exit Criteria:** One launcher-generated real result reaches validation, settlement, independent artifact verification, CoS `AcceptanceDecision(PASS)`, and one guarded Plan consequence; stale-result, mismatch, settlement, acceptance, and replay guards remain fail-closed and idempotent.

### Task 5: Reconcile documentation and run fresh verification

**Purpose:** Align maintained runtime documentation and record truthful automated/live evidence.

**Task Function:** Update the canonical runtime surface and run focused, contract, actual Starter Kit packaging, full-suite, and separately classified strict-probe verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence interpretation and capability classification.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification compares source, tests, plan, and live evidence.

**Specification Coverage:** one owner per fact; no synthetic live success; complete final proof.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md`, `repo_config/starter-kit-manifest.json`, `artifacts/runtime-observation/2026-10-17-live-secretary-bound-probe-9router-fixed.json`, `scripts/secretary_live_pilot.py:main`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`

**Dependencies:** Tasks 1 through 4 pass.

**Authority:**
- Preauthorized local actions: update maintained runtime documentation and run declared local verification, temporary Starter Kit build/validation, and existing live-probe commands
- Stop for: unowned resources, stale base, or any request to report synthetic success. Provider/authentication absence and a missing strict structured receipt are non-blocking diagnostic outcomes for the strict probe only.

**Steps:**
- [x] Document `PreparedLane`/admission, launcher attempt identity, result lookup, Runtime settlement, and CoS acceptance ownership.
- [x] Run the focused normal-path tests, repository validator, and actual temporary Starter Kit build/validation before the provider diagnostic.
- [x] Confirm the generated Starter Kit contains the manifest-approved changed runtime surfaces and no forbidden factory-only files; `--help` checks are supplementary only.
- [x] Run the existing strict Secretary probe against configured 9router only after core verification and record `READY` only for an attributable structured receipt.
- [x] Record the probe as `BLOCKED_CAPABILITY` with `runtime_completion_observation_missing`; the probe returned no structured Secretary receipt, transport completion was unproven, and 9router telemetry was `inconclusive` with `missing_usage`. Preserve this as a capability diagnostic, not a core Worker correctness failure.
- [x] Run the full suite from the committed checkpoint and planning validation; record deviations before branch disposition.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_secretary_live_runtime.py tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py tests/test_secretary_live_pilot.py tests/test_acceptance_handoff.py tests/test_project_os_runtime.py tests/test_starter_kit_generation.py` — `697 passed`.
- Expected: focused suite passes with no new failures.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: repository contract validation passes.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-launch-context-and-attempt-identity-convergence-plan.md`
- Expected: plan satisfies the modern planning contract.
- [x] `New-Item -ItemType Directory -Force .tmp/starter-kit-plan-verification | Out-Null; py -B scripts/build_starter_kit.py --repo-root . --output-root .tmp/starter-kit-plan-verification; py -B scripts/validate_starter_kit.py --repo-root . --output-root .tmp/starter-kit-plan-verification; Remove-Item -Recurse -Force .tmp/starter-kit-plan-verification`
- Expected: the temporary built output is created from `repo_config/starter-kit-manifest.json`, validates successfully, contains every required path, and contains no forbidden path. Run both `--help` commands only as supplementary CLI-availability checks.
- [x] `py -B -m pytest -q` — `1384 passed, 2 skipped` from committed checkpoint `8342d80`.
- Expected: full suite passes, or unrelated pre-existing failures are recorded with command and scope.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:** Fresh evidence proves the simplification and preserves authority and cleanup guards; live status is truthful `READY` or `BLOCKED_CAPABILITY`.

## Evidence Ledger

- Focused launcher/Secretary regression suite: `576 passed`.
- Acceptance, lifecycle, recovery, settlement, and launcher guard suite: `427 passed`.
- Controller-owned acceptance canary: `PASS`; replay remained authorized without a duplicate Plan transition; stale-attempt, artifact, mismatch, and resource-conflict cases remained blocked.
- Starter Kit build and validation: passed from `repo_config/starter-kit-manifest.json`.
- Full suite from clean committed checkpoint `8342d80`: `1384 passed, 2 skipped`.
- 9router/local-patch-hub review: README and versioned overlays already require exact-base, conflict-safe, verify-only application; no source patch was justified by the current work.
- Strict Secretary provider probe: `BLOCKED_CAPABILITY` with `runtime_completion_observation_missing`; launcher-owned attempt identity was emitted, but transport completion/cleanup and an attributable structured Secretary receipt were unavailable. 9router telemetry remained `inconclusive` with `missing_usage`.

## Verification

- `py -B -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_dcode_project.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py tests/test_secretary_live_pilot.py tests/test_acceptance_handoff.py tests/test_project_os_runtime.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-17-launch-context-and-attempt-identity-convergence-plan.md`
- `New-Item -ItemType Directory -Force .tmp/starter-kit-plan-verification | Out-Null; py -B scripts/build_starter_kit.py --repo-root . --output-root .tmp/starter-kit-plan-verification; py -B scripts/validate_starter_kit.py --repo-root . --output-root .tmp/starter-kit-plan-verification; Remove-Item -Recurse -Force .tmp/starter-kit-plan-verification`
- `py -B scripts/build_starter_kit.py --help`
- `py -B scripts/validate_starter_kit.py --help`
- `py -B -m pytest -q`
- `git diff --check`
- Existing strict live Secretary probe evidence: `BLOCKED_CAPABILITY` with `runtime_completion_observation_missing`; launcher-owned attempt identity was emitted, but transport completion/cleanup and an attributable structured Secretary receipt were unavailable. 9router telemetry remained `inconclusive` with `missing_usage`.

## Completion Criteria

The plan is ready for completion verification when:

1. No normal Secretary caller supplies execution `attempt_id`.
2. The launcher allocates one fresh attempt ID per real execution and emits it with result destinations.
3. Stable identity is captured from admission and is not retyped into Worker result prose.
4. Result location is lookup only; exact identity, freshness, settlement, and artifact checks remain enforced.
5. The strict receipt is derived/exported from validated evidence and is not ordinary execution readiness.
6. CoS remains the only semantic acceptance authority.
7. Delayed stale attempts are rejected, unresolved resources block reuse, and recovery does not relaunch or duplicate transitions.
8. One normal launcher-generated result reaches result validation, settlement, independent artifact verification, real CoS `AcceptanceDecision(PASS)`, and one guarded Plan consequence.
9. Focused tests, validators, actual Starter Kit build/validation when distributed surfaces changed, planning validation, and full suite are fresh and recorded.
10. No machine-owned identity is embedded in Worker task prose merely for correlation, and all evidence-adapter consumers remain correct.
11. Strict receipt v1 remains unchanged and derived reporting only; strict provider telemetry may be `BLOCKED_CAPABILITY` without blocking ordinary Worker correctness.
12. Live evidence is truthful `READY` or `BLOCKED_CAPABILITY`, never synthetic success.

The plan may be marked `completed` only after `skill-verification-before-completion` returns
`verified`. Push, PR creation, review assignment, review cycles, merge, and worktree cleanup
remain separately authorized branch-disposition actions.
