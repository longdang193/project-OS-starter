---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: deepagents-attempt-ownership-and-result-settlement
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_attempt_contract.py
  - scripts/owned_process.py
  - scripts/deepagents_result_contract.py
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - tests/test_herdr_attempt_contract.py
  - tests/test_deepagents_result_contract.py
  - tests/test_dcode_project.py
  - tests/test_owned_process.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
---

# DeepAgents Attempt Ownership And Result Settlement

## Review Disposition

The attached verdict is implementation-worthy after narrowing scope.

### Justified issues

1. **P1 — Crash ambiguity after lock release.** `dcode-project` currently holds
   `_role_views_lock` around role-view setup, worker execution, cleanup, and
   lifecycle receipt publication, but the lock file does not preserve which
   attempt owned the worktree after an abrupt wrapper exit. A later launch can
   acquire the OS lock while prior ownership remains unresolved.
2. **P1 — Lifecycle receipt cannot prove semantic task completion.**
   `dcode-project.result.v1` proves worker, descendant, cleanup, and recovery
   facts. Herdr currently derives `task_result` from pane marker/report
   observation, so clean worker exit plus clean receipt can still be mistaken
   for completed task evidence.
3. **P2 — Observation remains coupled to lifecycle decisions.**
   `_deepagents_completion_evidence()` and pane process reads can affect
   completion classification, retry/reconciliation, and effective ownership,
   despite observation being transient and non-authoritative.
4. **P2 — Replacement eligibility is distributed.** Callers interpret receipt,
   cleanup, descendant, and observation fields independently. This permits
   inconsistent `retry`, `release`, and `reconcile` decisions.
5. **P2 — Process-settlement authority is not yet proven on every platform.**
   The POSIX `capture_output=False` path in `owned_process.py` waits for the
   parent and returns success without an explicit descendant-group check. It
   cannot become settlement authority without direct surviving-descendant proof.

### Preserve

- Existing same-worktree exclusion; do not add a second execution lock.
- Separate Herdr pane-delivery serialization from worktree execution ownership.
- Keep native executor lifecycle and delivery mechanisms native; adapters only
  translate evidence at the Project OS boundary.
- `dcode-project.result.v1` terminal receipt shape initially; no `claimed` state
  added to lifecycle receipt.
- CoS authority for continuation, acceptance, cumulative allowance, and Git
  checkpoint decisions.
- Explicit uncertainty. Missing receipt, unknown cleanup, live descendants, or
  stale claim never becomes safe retry evidence.

### Rejected or deferred

- No daemon, runtime registry, database, multi-slot journal, scheduler, or
  second supervisor.
- No automatic retry or continuation in Herdr or dispatcher.
- No removal of the existing 10-second retry cap in this change. Reconsider only
  after lifecycle proof and paired runtime evidence.
- Renaming `_role_views_lock` is clarity work bundled with ownership integration,
  not an independent correctness requirement.
- Codex and Tura adapter implementation is deferred; this plan hardens the
  DeepAgents path first.

## Goal

Make DeepAgents worktree ownership, terminal settlement, semantic task results,
and Herdr observation independent and truthful across normal exit, duplicate
dispatch, wrapper crash, late receipt, and retry reconciliation.

## Implementation Outcomes

### Crash-surviving single-slot ownership evidence

One assignment-scoped guard record survives wrapper failure and binds one
assignment identity, current worktree, `attempt_id`, executor, task digest, grant
digest, and lifecycle receipt path. CoS owns serialized
assignment admission; the atomic guard preserves unresolved ownership evidence
across crashes and prevents a later serialized admission from silently treating
it as settled.

### Canonical lifecycle and settlement decision

One pure contract normalizes executor evidence into `UNCLAIMED`, `ACTIVE`,
`SETTLED`, or `RECOVERY_REQUIRED`. A derived action returns `BLOCKED`,
`RECONCILE`, or `ELIGIBLE`. All retry and replacement callers consume these
contract results; no caller rebuilds receipt interpretation.

### Independent task-result evidence

Semantic report evidence remains separate from lifecycle evidence. Native
DeepAgents structured output is preferred through a thin adapter; a persisted
custom artifact is added only if crash recovery requires it. Herdr observation
may collect a bounded candidate report with explicit provenance, but cannot
release ownership, authorize retry, extend budget, or turn runtime completion
into CoS acceptance.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-writing-plans`, `skill-plan-document-reviewer`, and `skill-using-git-worktrees`
- Isolation: `dedicated native Git worktree`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, specification, and runtime-documentation files; run declared local checks and bounded harmless live probes
- User-approval actions: push, merge, publication, external runtime writes, destructive cleanup, and removal of the 10-second retry cap
- Parallel ownership: `none`; contract, wrapper, launcher, dispatcher, tests, and docs share one lifecycle contract
- Sequential fallback: complete Task 1 before Task 2; complete Tasks 2–5 before documentation reconciliation and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/deepagents-attempt-ownership`
- Base commit: `98b7b2f`
- Primary/main checkout: unchanged
- Expected workspace: dedicated worktree from `98b7b2f`; primary/main checkout
  unchanged; preserve unrelated untracked `.playwright-mcp/`, `db/`, and existing
  OCR plan files in primary checkout
- Next action: completed; commit and push after final verification
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | `codex` | none | process-tree retirement tests | `7 passed` |
| Task 2 | `completed` | dedicated worktree | `codex` | Task 1 | focused contract tests | `35 passed` |
| Task 3 | `completed` | dedicated worktree | `codex` | Tasks 1–2 | claim/settlement and crash-boundary tests | focused suite `380 passed` |
| Task 4 | `completed` | dedicated worktree | `codex` | Task 2–3 | native-result/adapter tests; schema tests if justified | no durable task-result protocol justified; pane evidence marked non-authoritative; launcher regressions pass |
| Task 5 | `completed` | dedicated worktree | `codex` | Tasks 3–4 | deterministic lifecycle regressions and bounded runtime smokes | identity propagation, capacity retention, and provenance regressions pass; live runtime smoke recorded below |
| Task 6 | `completed` | dedicated worktree | `codex` | Task 5 | docs/spec alignment and final validators | canonical docs reconciled; final validators pass |

## Invariants

- One worktree has at most one active DeepAgents attempt.
- Worktree lock is an exclusion primitive only. Lock release does not imply safe
  replacement; claim settlement does.
- Canonical lifecycle states are `UNCLAIMED`, `ACTIVE`, `SETTLED`, and
  `RECOVERY_REQUIRED`; the pure contract derives only `BLOCKED`, `RECONCILE`, or
  `ELIGIBLE`. `LAUNCH`, `CONTINUE`, and no-op decisions remain CoS decisions
  after eligibility.
- Plan task ledger plus Git remain durable coordination SSOT. Assignment guard is
  local executor safety evidence: it may block unresolved work, but is not
  coordination state or authority to resume work.
- Claim record is single-slot, assignment-scoped, attempt-correlated, atomically
  replaced, and stored in stable user-local runtime storage outside tracked
  project files. It contains no credentials or raw task text.
- Assignment identity is explicit and is derived from repository identity,
  canonical plan identity, and stable task/lane ID; it is not derived from
  worktree, `attempt_id`, task text, pane, or `dispatch_id`.
- CoS serializes assignment admission and the dispatcher rejects duplicate
  logical lanes. The worktree lock remains an execution exclusion primitive;
  atomic guard writes do not provide cross-worktree compare-and-swap.
- `UNCLAIMED` requires durable `prior_attempt_known=False` plus no current
  assignment record. Durable `prior_attempt_known=True` plus a missing runtime
  record is `RECOVERY_REQUIRED`, never `UNCLAIMED`.
- Same `attempt_id` is idempotent only when assignment, repository, executor,
  task, and grant bindings all match; mismatched reuse is recovery-required.
- `cleanup_confirmed=True` is settlement evidence only when `owned_process.py`
  proves the owned process tree is retired.
- Lifecycle receipt proves resource facts only.
- Semantic task-result evidence proves report evidence only; `accepted` remains
  CoS-owned.
- Pane observation is diagnostic and may be incomplete, stale, or unavailable.
- `BLOCKED` prevents admission, `RECONCILE` requires explicit settlement work,
  and only `ELIGIBLE` permits new admission.
- Worker grant and whole-attempt budget remain unchanged during this plan.
- Existing cleanup safety refuses user-owned role content and preserves unknown
  cleanup rather than deleting it.

## Task Breakdown

### Task 1: Prove owned-process retirement

**Purpose:**
- Make `cleanup_confirmed=True` truthful for normal exit, timeout, and
  output-limit cleanup before receipts can authorize settlement.

**Task Function:**
- Native process-lifecycle repair and regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small shared primitive with high safety impact and direct
  platform-specific evidence.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of process-group and Windows Job Object
  retirement claims.

**Specification Coverage:**
- Process-tree ownership, descendant retirement, recovery-required fallback, and
  no DeepAgents-specific cleanup implementation.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/owned_process.py:run_owned_process`
- Modify: `scripts/owned_process.py`
- Verify: `tests/test_owned_process.py`

**Dependencies:**
- Existing `owned_process.py` platform paths and current cleanup result contract.

**Authority:**
- Preauthorized local actions: modify owned-process lifecycle code and focused tests; run bounded local parent/descendant simulations
- Stop for: unproven process-group ownership, platform-specific cleanup claims without evidence, or new executor-specific process primitives

**Steps:**
- [x] Step 1: Add normal-exit process-group verification on POSIX when the
  Project OS owns the process tree.
- [x] Step 2: If descendants remain, terminate and re-check the owned group or
  return `BLOCKED` with `cleanup_confirmed=False`.
- [x] Step 3: Preserve existing timeout/output-limit behavior and Windows Job
  Object handling; do not weaken cleanup guarantees.
- [x] Step 4: Add tests for parent exit with surviving child, clean normal exit,
  timeout cleanup, output-limit cleanup, and Windows cleanup failure simulation.

**Verification:**
- [x] `python -m pytest -q tests/test_owned_process.py`
- Expected: normal parent exit with surviving descendant cannot return successful
  cleanup confirmation; all existing platform-path tests remain green.

**Exit Criteria:**
- `owned_process.py` proves process-tree retirement or returns explicit
  recovery-blocked evidence on every path used by DeepAgents.

### Task 2: Add claim and replacement-eligibility contract

**Purpose:**
- Define stable guard schema, normalized identity fields, four canonical
  lifecycle states, terminal-settlement predicate, and derived controller action.

**Task Function:**
- Contract design and pure state-transition logic.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded contract work with low implementation ambiguity after
  source-first debugging.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of state matrix and unsafe fallthroughs.

**Specification Coverage:**
- Single-slot claim, stale-claim reconciliation, no silent retry, terminal
  resource settlement, cross-worktree assignment identity, and preserved CoS
  acceptance authority.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:normalize_attempt`
- Inspect: `scripts/deepagents_result_contract.py:parse_result_receipt`
- Modify: `scripts/herdr_attempt_contract.py`
- Verify: `tests/test_herdr_attempt_contract.py`

**Dependencies:**
- Task 1 process-retirement proof, current receipt states, and existing attempt
  identity fields.

**Authority:**
- Preauthorized local actions: modify contract symbols and focused tests; run the focused contract test module
- Stop for: new lifecycle receipt states, changed grant/budget semantics, or any need for a second ownership registry

**Steps:**
- [x] Step 1: Define stable assignment identity separately from worktree and
  attempt identity; derive `assignment_id` from repository identity, canonical
  plan identity, and stable task/lane ID. Keep grant/task digests as binding
  evidence. Scope this input to coordinated/Herdr-managed execution; standalone
  `dcode-project` does not invent a plan identity.
- [x] Step 2: Define `UNCLAIMED | ACTIVE | SETTLED | RECOVERY_REQUIRED` from
  native evidence plus durable `prior_attempt_known`, then derive
  `BLOCKED | RECONCILE | ELIGIBLE` actions.
- [x] Step 3: Define terminal settlement from receipt plus cleanup and
  descendant facts; never inspect semantic task success.
- [x] Step 4: Implement table-driven tests for missing record, active claim,
  settled claim, unresolved claim, malformed claim, unknown cleanup, and same
  assignment across different worktrees. Prove same-`attempt_id` idempotency only
  for a full binding match; mismatched reuse becomes `RECOVERY_REQUIRED`.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_attempt_contract.py`
- Expected: all existing tests pass; new matrix proves no guard plus
  `prior_attempt_known=False` is `UNCLAIMED`, while no guard plus
  `prior_attempt_known=True` is `RECOVERY_REQUIRED`; missing evidence never
  derives `ELIGIBLE`.

**Exit Criteria:**
- Contract has one authoritative eligibility function and focused tests cover
  every state transition used by callers.

### Task 3: Persist assignment claim through wrapper lifecycle

**Purpose:**
- Keep existing role-view lock as one native worktree exclusion primitive and
  persist claim before worker spawn, then settle it after terminal receipt
  publication.

**Task Function:**
- Crash-safe wrapper lifecycle integration.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: tightly coupled source change with high failure-path risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: inspect atomicity, cleanup ordering, and crash boundaries.

**Specification Coverage:**
- Worktree admission, claim-before-spawn, terminal settlement, late receipt
  correlation, user-owned role-view protection, and no unsafe replacement.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_role_views_lock`,
  `_write_role_views`, `_remove_role_views`, `_publish_result_receipt`, `main`
- Modify: `scripts/dcode_project.py`
- Verify: `tests/test_dcode_project.py`

**Dependencies:**
- Tasks 1–2 accepted.

**Authority:**
- Preauthorized local actions: modify wrapper ownership and receipt sequencing plus focused wrapper tests; run bounded local crash simulations
- Stop for: unproven descendant retirement, deletion of user-owned content, non-atomic guard writes, or stale claim treated as safe retry

**Steps:**
- [x] Step 1: Rename lock helpers to `worktree_execution_lock` semantics while
  retaining one OS lock and keeping Herdr pane locking separate.
- [x] Step 2: Add one stable user-local assignment-scoped guard record under the
  existing `~/.local/share/dcode-project/` runtime root, outside tracked files
  and disposable cleanup roots. Record current worktree and use atomic
  temp-file-plus-`os.replace()` writes. Do not make record identity depend on
  worktree alone.
- [x] Step 3: Acquire lock, inspect prior claim, return `BLOCKED` or
  `RECONCILE` before any launch side effect when evidence is insufficient, and
  publish a new `ACTIVE` claim before `_run_deepagents_worker`.
- [x] Step 4: Preserve full claim identity when updating to `SETTLED`; settle
  only after receipt and verified cleanup/descendant evidence. Preserve claim on
  settlement failure so next attempt reconciles instead of launching.
- [x] Step 5: Make repeated same-`attempt_id` requests return existing evidence
  without launching only when task, grant, executor, assignment, and repository
  bindings all match. Mismatched reuse must remain recovery-required or blocked.
  Add injected crash after claim and before spawn, wrapper crash with surviving
  descendants, late receipt, concurrent owner, and different-worktree
  same-assignment tests.
- [x] Step 6: Consume Task 1 process-retirement evidence; retain
  `RECOVERY_REQUIRED` when that evidence is unknown or reports surviving
  descendants. Do not duplicate process-tree proof in wrapper tests.

**Verification:**
- [x] `python -m pytest -q tests/test_dcode_project.py`
- Expected: owner collision remains rejected; claim-before-spawn crash leaves
  `ACTIVE`/`RECOVERY_REQUIRED` evidence; cleanup uncertainty preserves claim and
  blocks replacement; terminal receipt and settled guard correlate same
  `attempt_id`; surviving POSIX descendants cannot be reported settled.

**Exit Criteria:**
- Every DeepAgents execution path enters one worktree claim, publishes terminal
  lifecycle evidence, and settles or preserves that assignment-scoped claim
  before lock release. The record retains current-worktree evidence for
  reconciliation.

### Task 4: Separate semantic task-result evidence

**Purpose:**
- Preserve explicit worker-result evidence without making pane observation or
  lifecycle receipt stand in for task acceptance.

**Task Function:**
- Native-result inspection and thin adapter; no persistence added because crash
  recovery did not require a second protocol.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small isolated contract with direct regression proof.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: verify native producer selection, schema separation, and
  bounded correlation validation.

**Specification Coverage:**
- Independent semantic report evidence, attempt correlation, bounded output,
  missing-report uncertainty, explicit producer/source, and CoS-only acceptance.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`,
  `_classify_deepagents_outcome`, `_build_assignment_result`
- Inspect: `scripts/dcode_project.py:_run_deepagents_worker`
- Modify: `scripts/herdr_main_launcher.py`
- Verify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Tasks 2–3 attempt identity and lifecycle receipt path binding.

**Authority:**
- Preauthorized local actions: inspect native DeepAgents result output, add only
  the thinnest required adapter, and run focused launcher/contract checks
- Stop for: lifecycle receipt schema churn, unbounded raw pane persistence, or any `accepted: true` path outside CoS

**Steps:**
- [x] Step 1: Inspect native DeepAgents structured final-result output and identify
  its producer, transport into `dcode-project`, and stable correlation fields.
- [x] Step 2: If native output is stable, map it through a thin adapter into
  `assignment.task_result`; do not introduce a second persisted protocol.
- [x] Step 3: If native output is not stable, retain bounded pane-derived report
  evidence with explicit `source=herdr_pane` provenance and non-authoritative
  status. Lifecycle settlement must not depend on it.
- [x] Step 4: Assess whether `dcode-project.task-result.v1` is needed; crash
  recovery did not require a durable intermediate artifact, so no second
  protocol was added.
- [x] Step 5: Update assignment composition so clean lifecycle receipt without
  semantic evidence yields `task_result: unverified`, not completion. Add
  regressions for marker-only output, native/adapter output, clean receipt with
  no report, mismatched attempt, oversized artifact when applicable, and CoS
  acceptance remaining unset.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: lifecycle and semantic states remain separate; no pane marker alone
  produces accepted or completed task evidence.

**Exit Criteria:**
- Launcher carries semantic report evidence independently through native output or
  an explicitly justified bounded fallback, with `unverified` fallback and
  unchanged lifecycle receipt contract.

### Task 5: Demote observation and enforce settlement gate in Herdr

**Purpose:**
- Make Herdr pane probes diagnostic only and prevent observation timeout from
  releasing ownership, authorizing retry, changing budget, or changing receipt
  state. Permit verified process-retirement evidence only through a named
  `RECOVERY_REQUIRED` procedure.

**Task Function:**
- Launcher/dispatcher lifecycle integration, deterministic regression proof, and
  bounded runtime smoke verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-module integration with runtime-boundary proof.

**Validator Profile:**
- Controller-selected: `high`
- Selection basis: independent failure-path and live-probe validation.

**Specification Coverage:**
- Explicit assignment identity propagation, receipt-first settlement, diagnostic
  observation, dispatcher capacity retention, no automatic retry, and provider
  backoff within remaining grant.
- Native process retirement is accepted only where `owned_process.py` evidence
  proves it; otherwise state remains `RECOVERY_REQUIRED`.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`,
  `_classify_deepagents_outcome`
- Inspect: `scripts/herdr_parallel_dispatch.py:_run_lane`,
  `_lane_capacity_state`
- Inspect: `scripts/owned_process.py:run_owned_process`
- Modify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`
- Verify: `tests/test_herdr_main_launcher.py`,
  `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Tasks 1–4 accepted.

**Authority:**
- Preauthorized local actions: update launcher/dispatcher settlement decisions, focused tests, and bounded harmless runtime probes using existing configured capabilities
- Stop for: automatic retry/release behavior, capacity release before settlement, live process without owner evidence, or required external authentication/write

**Steps:**
- [x] Step 1: Project `assignment_id` from repository identity, canonical plan
  identity, and stable task/lane ID through dispatcher → `herdr_main_launcher`
  → `dcode-project`. Keep this projection scoped to coordinated/Herdr-managed
  execution; standalone `dcode-project` does not invent a plan identity.
- [x] Step 2: Read attempt-correlated lifecycle receipt and claim settlement
  before optional pane probes.
- [x] Step 3: Keep routine pane reads, markers, waits, and process observations
  under `observation` and task-result evidence only; never let them rewrite
  execution, cleanup, claim, receipt, budget, retry, or acceptance fields.
- [x] Step 4: Define named `RECOVERY_REQUIRED` handling that may gather verified
  native process-retirement evidence and feed the settlement contract. Do not let
  `_deepagents_completion_evidence()` switch opportunistically between routine
  diagnostic and recovery-authoritative interpretations.
- [x] Step 5: Route replacement decisions through the canonical state/action
  mapping; retain capacity as occupied for `ACTIVE` and
  `RECOVERY_REQUIRED`/`RECONCILE`.
- [x] Step 6: Preserve the 10-second retry cap during migration. Prove 60-second
  `Retry-After`, claim-before-spawn crash, surviving descendant, late receipt,
  duplicate attempt, and cross-worktree prior-claim cases with deterministic
  local tests.
- [x] Step 7: Run one bounded installed-runtime smoke and one ownership/cleanup
  smoke when needed; do not make routine provider calls carry deterministic
  lifecycle proof.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- Expected: assignment identity reaches wrapper; observation timeout emits
  diagnostics only; unresolved claim keeps capacity occupied; missing process
  retirement remains recovery-required; settled receipt and task result remain
  separately visible. Deterministic tests carry lifecycle edge cases; bounded
  runtime smokes verify installed-runtime boundaries only.

**Exit Criteria:**
- Herdr cannot create a replacement from pane silence or marker output alone and
  cannot report semantic completion from lifecycle settlement alone.

### Task 6: Reconcile specification and runtime guidance

**Purpose:**
- Make canonical specification and runtime documentation describe the new claim,
  settlement, observation, and result boundaries without generated-surface drift.

**Task Function:**
- Contract documentation reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded canonical-document update after behavior is proven.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: check docs against source and plan invariants.

**Specification Coverage:**
- Existing parallel DeepAgents dispatch spec, runtime surfaces, and runtime-tool
  resolution guidance.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`,
  `docs/operating_system/runtime/runtime-surfaces.md`,
  `docs/operating_system/tooling/runtime-tool-resolution.md`,
  `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Verify: generated-header and adapter boundaries remain unchanged.

**Dependencies:**
- Task 5 complete with fresh proof.

**Authority:**
- Preauthorized local actions: edit canonical specification and runtime documentation; run planning, contract, adapter, and diff validators
- Stop for: documentation claims not supported by source/tests/live evidence or any generated file requiring direct edits

**Steps:**
- [x] Step 1: Document two locks with distinct ownership: pane delivery and
  worktree attempt execution.
- [x] Step 2: Document single-slot, assignment-scoped `dcode-project.attempt.v1`
  with current-worktree evidence, explicit `assignment_id` inputs, stale-claim
  reconciliation, four canonical lifecycle states, and
  `BLOCKED | RECONCILE | ELIGIBLE` semantics. Keep plan+Git as coordination SSOT
  and guard as executor-local safety evidence.
- [x] Step 3: Document lifecycle receipt versus semantic task-result evidence
  versus CoS acceptance; remove wording that equates observation or clean exit
  with task completion.
- [x] Step 4: Record 10-second retry cap as temporary migration policy and leave
  its removal outside this plan.
- [x] Step 5: Record native adapter boundary: DeepAgents is in scope; Codex and
  Tura mappings require separate follow-up plans.
- [x] Step 6: Reconcile personal-local worktree guidance so Herdr observation is
  diagnostic, verified process inspection is limited to named recovery, and
  runtime guard state cannot resume work or replace plan+Git coordination truth.

**Verification:**
- [x] `python scripts/validate_repo_contracts.py` — pass
- [x] `python scripts/validate_planning_lifecycle.py --repo-root .` — pass
- [x] `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection` — pass
- [x] `python scripts/sync_agent_adapters.py --check` — pass
- [x] `git diff --check` — pass
- Expected: canonical docs and proposed plan validate; no generated adapter
  surface changes because no adapter source was modified.

**Exit Criteria:**
- Source, tests, specification, runtime guidance, and plan agree on ownership,
  settlement, observation, semantic result, and acceptance boundaries.

## Verification

- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_deepagents_result_contract.py tests/test_dcode_project.py tests/test_owned_process.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_planning_lifecycle.py --repo-root .`
- `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `python scripts/sync_agent_adapters.py --check`
- `git diff --check`
- `git status --short --branch`

## Live Probe Evidence

- Installed runtime probe through patched `scripts/dcode_project.py` with
  `--assignment-id`, explicit repository/task/grant bindings, `--no-mcp`, one
  turn, and 12-second timeout: exit `0` in `12315ms`; emitted confirmed
  `dcode-project.result.v1` receipt with worker `exited`, exit code `0`,
  descendants `terminated`, cleanup `removed`, and `recovery_required: false`;
  assignment guard reached `state: settled` with matching `attempt_id`.
- Same binding rerun: exit `2` in `316ms`, no result file, and no worker launch;
  wrapper reported active-or-settled claim rejection.
- Installed shell `dcode-project` remains stale shared copy and rejects new
  identity flags; deployment drift is pre-existing and was not overwritten.
- `owned_process.py` live child-process probe returned `timeout` with
  `cleanup_confirmed: true`; focused fake process-group regression covers normal
  parent exit with surviving descendant and cleanup re-check.

## Completion Criteria

The plan is ready for completion verification when:

1. A same-worktree owner collision remains blocked by one execution lock.
2. A wrapper crash after claim publication leaves a discoverable unresolved
   claim and cannot launch a replacement silently.
3. Missing runtime record after known prior work becomes
   `RECOVERY_REQUIRED`, never `UNCLAIMED`; same-`attempt_id` reuse is idempotent
   only with a full task, grant, executor, assignment, and repository binding.
4. Canonical lifecycle state preserves `UNCLAIMED`, `ACTIVE`, `SETTLED`, and
   `RECOVERY_REQUIRED`; derived actions preserve `BLOCKED`, `RECONCILE`, and
   `ELIGIBLE` behavior.
5. A terminal receipt proves lifecycle/resource settlement without claiming task
   success; separate semantic evidence carries explicitly sourced report
   evidence, using native output first and a persisted artifact only when needed.
6. Pane observation timeout, marker presence, and stale pane output cannot release
   ownership, authorize retry, extend budget, or set acceptance.
7. `BLOCKED`, `RECONCILE`, and `ELIGIBLE` decisions come from one pure contract
   and preserve unknown evidence.
8. `owned_process.py` proves or refuses process retirement on each supported
   platform path used for settlement.
9. Focused tests, full tests, validators, and deterministic lifecycle regressions
   pass; bounded runtime smokes pass where applicable, with no unrelated tracked
   changes.
10. The 10-second retry cap remains unchanged unless a separately approved plan
   supplies lifecycle proof and paired runtime measurements.

The plan may move from `proposed` to `active` only after approval. It may move to
`completed` only after `skill-verification-before-completion` returns `verified`.

## Deferred Follow-Up

Provider retry-cap removal, active worker cancellation, durable multi-attempt
history, streaming task-result transport, automatic reconciliation service,
concurrency expansion, and semantic acceptance automation remain out of scope.
