---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: deepagents-runtime-boundary-residual-closure
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/deepagents_result_contract.py
  - scripts/herdr_attempt_contract.py
  - scripts/herdr_parallel_dispatch.py
  - tests/test_deepagents_result_contract.py
  - tests/test_dcode_project.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/planning/planning-dispatch.md
---

# Close DeepAgents Runtime Boundary Residuals

## Review Basis

Reviewed verdict against branch `codex/deepagents-runtime-boundary` at
`20f7b02` (`Keep print config at runtime boundary`). Worktree is clean. Prior
runtime, adapter, starter-kit, compile, and full-suite checks are recorded as
passing (`746 passed, 1 skipped`). Source inspection confirms only these
residual implementation issues:

- `scripts/dcode_project.py:_publish_result_receipt()` emits both
  `shell_capabilities` and `capabilities`, but
  `scripts/deepagents_result_contract.py:parse_result_receipt()` returns only
  lifecycle fields. `scripts/herdr_main_launcher.py:_main_body()` therefore
  cannot consume worker capability evidence through its parser.
- `scripts/herdr_attempt_contract.py:attempt_decision()` exists, but
  `scripts/herdr_parallel_dispatch.py:run_lane()` still reconstructs resource
  settlement and capacity meaning locally. Task-result acceptance remains a
  separate CoS fact and must not be folded into lifecycle state.
- `scripts/herdr_parallel_dispatch.py:run_parallel()` consumes futures with
  `as_completed()` but returns before its CLI prints results; fast settled lanes
  are invisible until the full wave finishes.
- `scripts/herdr_parallel_dispatch.py:run_lane()` has no bounded transient
  dispatch deadline before worker launch. A confirmed pre-launch failure must
  retire unowned capacity; it must not be reported as an occupied unresolved
  attempt.

The verdict's assignment lock, single attempt deadline, coordinated allowance
requirement, and integral effective-budget fixes are already present in the
branch. Do not reimplement them.

## Goal

Close receipt evidence loss, give lifecycle semantics one shared owner, enforce
the existing attempt deadline at dispatch, and expose settled lane results as
they arrive. Preserve separate ownership: `dcode-project` owns worker facts and
cleanup, Herdr owns transport and diagnostics, the attempt contract owns
lifecycle semantics, and CoS owns task acceptance and continuation.

## Implementation Outcomes

### Capability evidence integrity survives the boundary

`capabilities` is canonical parsed worker-proof evidence with requested,
passed-to-worker, validated-available, digest, and validation-error fields.
`shell_capabilities` remains compatibility input only. Both objects must agree
when present, and invalid or absent capability evidence cannot prove worker
capability availability even when lifecycle settlement is proven.

### Lifecycle semantics have one shared owner

Dispatcher consumes evidence-appropriate shared lifecycle decisions without
fabricating claim state. Where full claim facts are unavailable, it uses the
narrower shared settlement contract. Task-result status, acceptance, and
continuation remain independent evidence and are not treated as settlement
proof.

### Settled lanes become observable immediately

`run_parallel()` exposes one optional observational event callback. It emits
admission events before worker wait and each terminal lane result exactly once;
the CLI uses it with flush semantics. Admission outcomes remain disjoint as
admitted, deferred-capacity, blocked, and rejected.

### Provider proof stays separate from local proof

Verification records local contract proof and, when credentials already exist,
one bounded external DeepAgents provider probe. Missing credentials report
unavailable provider evidence, not local test failure. No authentication,
provider fallback, scheduler, heartbeat, runtime ledger, or new result protocol
is added.

## Explicit Non-Goals

- No new assignment lock, deadline model, budget representation, or retry
  policy; preserve current whole-attempt deadline, reserve, and integer-budget
  design. Bounded transient dispatcher deadline integration is in scope.
- No replacement of the existing lifecycle receipt plus `task-result.json`
  protocol with native or competing durable storage.
- No `attempt inspect` or `attempt reconcile` CLI in this slice. Existing
  bounded internal reconciliation is sufficient until an operator workflow
  demonstrates a concrete need for public commands.
- No adaptive concurrency. Keep `MAX_CONCURRENCY = 2` until streaming and
  assignment behavior have fresh proof.
- No packaging migration or historical-guidance rewrite.
- No automatic continuation or retry by Herdr or dispatcher.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: current workspace
- Commit policy: no commits during execution
- Preauthorized local actions: edit listed repository files, add focused regression tests, run declared local checks, run bounded read-only provider probe when already configured
- User-approval actions: push, merge, authentication, credential or provider configuration changes, destructive cleanup, unrelated edits
- Parallel ownership: none; contract and dispatcher changes share semantic boundaries
- Sequential fallback: complete Tasks 1–3 in order, then run Task 4 final verification
- Activation rule: change plan status from `proposed` to `active` before the
  first task becomes `active`; change to `completed` only after fresh completion
  verification returns `verified`.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/deepagents-runtime-boundary`
- Base commit: `20f7b02`
- Expected workspace: clean before execution
- Next action: hand off to authorized branch-finishing disposition
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | receipt parser round-trip tests | `6 passed`; launcher proof tests pass in focused suite |
| Task 2 | `completed` | current | `codex` | Task 1 | shared lifecycle decision tests | dispatcher uses `terminal_settlement_proven`; deadline and ownership tests pass |
| Task 3 | `completed` | current | `codex` | Task 2 | callback ordering and admission-tag tests | `62 passed`; barrier and subprocess pipe proofs pass |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | full suite, validators, live probes | `758 passed, 1 skipped`; validators, compile, diff, local probes passed; external provider unavailable because credentials absent |

## Task Breakdown

### Task 1: Preserve capability evidence integrity through receipt parsing

**Purpose:**
- Keep worker capability proof available to launcher and dispatcher after
  receipt parsing without allowing projected intent to masquerade as proof.

**Task Function:**
- Repair shared receipt validation, parser projection, and launcher evidence
  handling without changing receipt identity or lifecycle settlement semantics.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: resolve from bounded parser and regression-test scope.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead-controller verification of schema, malformed input, and
  round-trip behavior.

**Specification Coverage:**
- Capability evidence is independent from projected intent and remains bound to
  the same attempt.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_publish_result_receipt`
- Modify: `scripts/deepagents_result_contract.py:_validate_payload`,
  `scripts/deepagents_result_contract.py:parse_result_receipt`,
  `scripts/herdr_main_launcher.py:_main_body`
- Verify: `tests/test_deepagents_result_contract.py`,
  `tests/test_dcode_project.py`, `tests/test_herdr_attempt_contract.py`,
  `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Existing receipt producer and capability shapes remain canonical.

**Authority:**
- Preauthorized local actions: add optional capability validation/projection and focused tests in listed files.
- Stop for: receipt schema version change, incompatible legacy payload behavior, or required credential/configuration change.

**Steps:**
- [x] Step 1: Add failing tests for receipts containing canonical `capabilities`,
  compatibility `shell_capabilities`, both agreeing objects, disagreement, and
  digest mismatch.
- [x] Step 2: Validate canonical capability fields and digest through the shared
  attempt-contract tests; preserve lifecycle proof for legacy receipts without
  capability fields.
- [x] Step 3: Make `parse_result_receipt()` return canonical worker-proof
  capability evidence and explicit unavailable state for malformed, absent, or
  disagreeing capability facts.
- [x] Step 4: Update launcher assignment evidence so missing receipt capability
  proof cannot silently retain projected capability intent as verified evidence.

**Verification:**
- [x] `py -m pytest -q tests/test_deepagents_result_contract.py tests/test_dcode_project.py tests/test_herdr_main_launcher.py`
- Expected: capability round-trip and semantic agreement pass; malformed, stale,
  mismatched, absent, and digest-invalid capability evidence remains unavailable
  while lifecycle-only settlement remains valid.

**Exit Criteria:**
- Parser output contains validated worker capability evidence whenever producer
  emitted it, with no change to receipt correlation or lifecycle states.

### Task 2: Make lifecycle semantics contract-owned and deadline-bounded

**Purpose:**
- Remove duplicated lifecycle/resource interpretation and close dispatcher
  deadline handling while preserving task-result and acceptance independence.

**Task Function:**
- Refactor dispatcher classification to consume evidence-appropriate shared
  lifecycle/settlement decisions. Do not fabricate claim state when dispatcher
  lacks authoritative claim binding. Establish a transient dispatch deadline
  immediately before worker launch; confirmed pre-launch failure retires
  unowned capacity.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded shared-contract refactor with caller audit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead-controller verification of active, settled, recovery,
  malformed, deadline, and acceptance-pending cases.

**Specification Coverage:**
- Admission, resource settlement, and task outcome remain separate facts; no
  missing task report authorizes replacement or acceptance.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:attempt_decision`,
  `scripts/herdr_parallel_dispatch.py:run_lane`,
  `scripts/herdr_parallel_dispatch.py:run_parallel`,
  `scripts/herdr_main_launcher.py:_build_assignment_result`
- Modify: `scripts/herdr_parallel_dispatch.py:run_lane`,
  `scripts/herdr_parallel_dispatch.py:run_parallel`; modify
  `scripts/herdr_attempt_contract.py:attempt_decision` only when an additive
  evidence-appropriate field is required
- Verify: `tests/test_herdr_attempt_contract.py`,
  `tests/test_herdr_parallel_dispatch.py`,
  `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 complete; lifecycle receipt and task-result schemas remain separate.

**Authority:**
- Preauthorized local actions: refactor listed production callers and add focused lifecycle/capacity regressions.
- Stop for: proposal to merge task acceptance into lifecycle, new scheduler/retry state, or shared behavior with no stable contract owner.

**Steps:**
- [x] Step 1: Enumerate every production caller of
  `attempt_decision()`, `terminal_settlement_proven()`, and local lifecycle
  mappings; identify authoritative claim, binding, receipt, cleanup, and
  descendant evidence available at each caller.
- [x] Step 2: Use `attempt_decision()` only where full claim facts exist; use the
  shared settlement contract for receipt-only capacity decisions. Never
  synthesize `{"state": "active"}` as claim evidence.
- [x] Step 3: Establish a transient attempt/transport deadline in the
  dispatcher immediately before `Popen`; preserve the existing settlement
  reserve and launcher deadline. A confirmed failure before `Popen` returns
  retired/unowned capacity; post-launch uncertainty remains occupied.
- [x] Step 4: Leave task-result `status`, `accepted`, checkpoint, and
  continuation facts separate; preserve `acceptance_pending` behavior.
- [x] Step 5: Remove imports and branches made dead by the refactor.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: evidence-appropriate decisions map consistently to active, settled,
  recovery, binding mismatch, pre-launch failure, and post-launch uncertainty;
  task-result uncertainty never turns into settlement or acceptance.

**Exit Criteria:**
- Dispatcher no longer reconstructs lifecycle meaning outside shared contracts;
  pre-launch failures retire unowned capacity; all existing result categories
  remain compatible.

### Task 3: Stream terminal lane evidence exactly once

**Purpose:**
- Make fast lane completion visible before slow sibling completion without
  changing bounded wave ownership.

**Task Function:**
- Add one optional observational event callback and flushed CLI emission. Emit
  disjoint admission categories before worker wait and each terminal result once.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: small public-function compatibility change with ordering
  proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead-controller verification of callback timing, exactly-once
  delivery, sibling preservation, pipe visibility, and exit codes.

**Specification Coverage:**
- Observation timeout is diagnostic only; settled result availability does not
  require waiting for unrelated sibling lanes.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`,
  `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:run_parallel`, `main`
- Modify: `scripts/herdr_parallel_dispatch.py:run_parallel`, `main`
- Verify: `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 2 complete; `MAX_CONCURRENCY = 2` remains unchanged.

**Authority:**
- Preauthorized local actions: add backward-compatible callback/tag emission and timing tests in listed files.
- Stop for: background scheduler, cancellation redesign, changed capacity ceiling, or output protocol break.

**Steps:**
- [x] Step 1: Define one canonical category per lane: `admitted`, `deferred`,
  `blocked`, or `rejected`. Derive any legacy combined failure view only after
  canonical buckets are complete.
- [x] Step 2: Add an in-process barrier test with one fast lane and one slow
  sibling; assert terminal event fires once before sibling completion.
- [x] Step 3: Invoke the event callback after storing each completed result,
  synchronously on coordinator thread. Record callback failures separately as
  `callback_errors`; never replace valid worker settlement.
- [x] Step 4: Emit admission events before worker wait, print JSONL with
  `flush=True`, and prevent aggregate return handling from printing terminal
  results again.
- [x] Step 5: Add subprocess/pipe regression proving externally visible flushed
  fast-lane output, plus file, iterable, and pre-admitted mapping category
  coverage.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_parallel_dispatch.py`
- Expected: fast result appears once before slow sibling settles; all lanes
  remain represented; deferred capacity, blocked conflict, and rejected input
  remain distinct in structured and streamed output.

**Exit Criteria:**
- Consumers can process each terminal lane result once as soon as it settles,
  with no automatic replacement or capacity inference from observation timing.

### Task 4: Fresh integration verification and live probes

**Purpose:**
- Prove changed behavior locally and collect separate provider-runtime evidence
  without confusing unavailable external service with local failure.

**Task Function:**
- Run focused and full backend verification, adapter checks only if canonical
  guidance changed, and bounded runtime probes with four latency metrics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Git, acceptance, and provider evidence remain controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: lead-controller fresh verification of final repository state.

**Specification Coverage:**
- Local contract proof, direct boundary proof, and optional external provider
  proof remain distinct and reproducible.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: changed files and current runtime validators
- Modify: none unless verification finds an in-scope defect
- Verify: repository tests, validators, and bounded runtime outputs

**Dependencies:**
- Tasks 1–3 complete and worktree contains only planned changes.

**Authority:**
- Preauthorized local actions: run declared tests, validators, compile/diff checks, local probes, and read-only provider probe when configured.
- Stop for: authentication, credential/configuration changes, external writes, unrelated failures, or unresolved ownership/cleanup evidence.

**Steps:**
- [x] Step 1: Run focused suites, then full suite and repository validators.
- [x] Step 2: Run `py -B scripts/dcode_project.py --print-config --no-mcp --json`
  as local runtime smoke proof; run bounded wrapper/duplicate-owner probes with
  unique temporary identities.
- [x] Step 3: Separately run one external DeepAgents provider probe through the
  existing launcher only when provider credentials are already configured.
- [x] Step 4: Record dispatch-to-claim latency, completion-to-capacity-release
  latency, controller tool calls per attempt, and manual reconciliation count.
  Mark unavailable metrics explicitly when provider execution does not occur.
- [x] Step 5: Run adapter synchronization and `--check` only if canonical
  guidance files changed; do not touch generated adapters for code-only changes.

**Verification:**
- [x] `py -m pytest -q`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `py -m compileall scripts tests`
- [x] `git diff --check`
- Expected: fresh automated proof passes; local probe proves lifecycle,
  capability, and duplicate-owner behavior; provider result includes runtime
  revision and metrics or an explicit unavailable reason.

**Exit Criteria:**
- Verification returns `verified` for in-scope local behavior, with external
  provider evidence separately recorded and no hidden credential/configuration
  change.

## Verification

Final artifact verification runs serially:

- `py -m pytest -q`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --repo-root .`
- `py -m compileall scripts tests`
- `git diff --check`
- `py -B scripts/dcode_project.py --print-config --no-mcp --json`
- bounded Windows claim-race, lifecycle-settlement, capability round-trip, and
  fast-lane streaming probes with unique temporary roots
- separate bounded external DeepAgents provider probe when already configured

Verified result: local contract and runtime proof passed. Live metrics: claim
race operation `1014.792 ms`, completion-to-capacity-release `1.114 ms`,
controller tool calls per local attempt `0`, manual reconciliation count `0`.
External DeepAgents provider probe deferred as unavailable: no provider
credentials configured; no authentication or configuration changes made.

## Completion Criteria

The plan is ready for completion verification when:

1. capability evidence survives producer → receipt → parser → launcher/
   dispatcher round-trip with attempt correlation
2. malformed or missing capability evidence remains unresolved and never falls
   back to projected intent as proof
3. dispatcher lifecycle/resource decisions consume the shared attempt contract
4. task-result acceptance and continuation remain independent CoS facts
5. terminal lane results stream before unrelated sibling completion
6. deferred, blocked, and rejected admission outcomes remain distinguishable
7. no P0 fix, scheduler, adaptive-concurrency change, or packaging migration is
   reintroduced
8. focused and final verification are fresh and reproducible
9. external provider evidence, when unavailable, is reported separately from
   local correctness
10. plan status changes from `proposed` to `active` before the first task is
    activated, then changes to `completed` only after
    `skill-verification-before-completion` returns `verified`
