---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: deepagents-attempt-contract-consolidation
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_attempt_contract.py
  - scripts/dcode_project.py
  - scripts/herdr_main_launcher.py
  - scripts/herdr_parallel_dispatch.py
  - scripts/owned_process.py
  - scripts/deploy_agent_runtime.py
  - repo_config/starter-kit-manifest.json
  - tests/test_herdr_attempt_contract.py
  - tests/test_dcode_project.py
  - tests/test_herdr_main_launcher.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_owned_process.py
  - tests/test_deploy_agent_runtime.py
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
---

# Consolidate Herdr Attempt Admission, Settlement, And Budget Authority

## Review Basis

The attached verdict is justified on one P1 and seven implementation P2
findings, plus two plan-readiness corrections. Its proposed
amendments are also justified: lifecycle and admission must stay distinct,
receipt deletion needs durable settlement evidence, coordinated identity must
be mandatory, budget propagation needs end-to-end proof, and the plan must use
the reviewed baseline and existing test files. Evidence is current source,
tests, and the merged ownership changes; no runtime completion claim is
inferred from pane state.

### [P1] Competing claim does not stop execution

`scripts/dcode_project.py:_claim_attempt` can return `action: BLOCKED`, but the
main execution path only short-circuits `RECONCILE` and idempotent reuse. A
competing invocation can therefore continue into role-view or worker launch.
The smallest safe correction is an explicit admission result consumed before
all execution side effects.

### [P2] Recovery input is not transported

`prior_attempt_known` exists in `scripts/dcode_project.py` but is not propagated
through `scripts/herdr_main_launcher.py` and
`scripts/herdr_parallel_dispatch.py`. A known prior attempt can be lost before
admission, so replacement work may be treated as unclaimed.

### [P2] Prior settlement evidence is not durable

The launcher deletes confirmed receipts and the receipt parser rejects files
older than one hour. A one-time receipt inspection cannot support later
recovery. The existing attempt guard must retain validated correlated terminal
evidence before receipt deletion; this is not a second registry.

### [P2] Capacity and task-result uncertainty are coupled

`herdr_parallel_dispatch.py:classify` treats settled resources with
`reconciliation_required` as occupied. Missing report or acceptance evidence
therefore retains capacity even when worker and descendants are retired.
Resource retirement and semantic task acceptance need separate outcomes.

### [P2] Dispatcher bypasses shared policy

`herdr_parallel_dispatch.py` imports launcher-private `_normalize_runtime_grant`
and repeats `WHOLE_ATTEMPT_WALL_CLOCK_SECONDS`. This creates two policy owners
and makes future contract changes incomplete.

### [P2] Dispatcher budget ceiling contradicts contract

`_effective_budget_is_contained()` caps wall-clock budget at
`NATIVE_WORKER_WALL_CLOCK_SECONDS` (`420`), while
`herdr_attempt_contract.py:resolve_attempt_budget()` permits an explicit grant
such as `600` when remaining authority contains it. Production must consume
the shared resolver without adding a stricter unrelated ceiling.

### [P2] Deployment ownership uses unstable source path

`deploy_agent_runtime.py` records and compares `source_root`. Deleting or
relocating a source worktree can make a valid deployment look foreign. Marker
ownership must use stable Git common-repository identity, while retaining bundle
and source-path checks.

### [P2] Captured-output success lacks retirement proof

`owned_process.py` explicitly proves the POSIX `capture_output=False` path, but
the normal successful `capture_output=True` path returns without equivalent
descendant-group retirement evidence. Add focused proof before using this path
as settlement authority; keep fail-closed behavior.

### [P2] Operational documentation overstates convergence

Personal-local, runtime-adapter, and related CoS guidance still permits Herdr
observation or wrapper state to sound like workflow authority, and completed
plan wording implies full contract convergence. Correct ownership and
reconciliation language without editing generated files directly.

### [P2] Plan proof and baseline are underspecified

The plan recorded `98b7b2f`, preceding reviewed implementation
`de107057f6a7060e3e06955ee7e3bea9164d81f2`, and its verification named two
nonexistent test files. Adapter platform coverage and legacy marker migration
compatibility were also implicit. Reconcile baseline before editing, use
existing tests or explicitly create new ones, check all adapter platforms when
canonical skills change, and preserve uncertain ownership without adoption.

## Goal

Make one DeepAgents attempt truthful and bounded from admission through worker
cleanup, launcher settlement, dispatcher capacity, deployment ownership, and
CoS handoff. Preserve current two-lane limit, plan-plus-Git coordination SSOT,
runtime completion versus acceptance separation, and the existing 10-second
retry cap.

## Implementation Outcomes

### Admission is side-effect safe

The shared contract exposes `ADMITTED`, `IDEMPOTENT`, `BLOCKED`, and
`RECONCILE`. Only `ADMITTED` reaches role views and worker launch. Legitimately
active claims preserve `ACTIVE`/`BLOCKED`; same-binding reuse returns
`IDEMPOTENT` with existing status; only missing, inconsistent, or uncertain
evidence returns `RECONCILE`. Claim decision and guard update stay inside the
existing ownership lock.

### Production callers use one contract

Launcher, wrapper, and dispatcher consume public normalization, budget,
settlement, lifecycle, and eligibility functions from
`herdr_attempt_contract.py`. Private launcher imports and duplicated policy
constants disappear. Explicit grants remain valid when contained by durable
authority; native worker limits remain enforced at their owning boundary.

### Recovery and settlement remain bounded

`prior_attempt_known` reaches admission from durable CoS/plan coordination
evidence. Existing claims preserve lifecycle state and are reconciled only when
evidence is missing, inconsistent, or uncertain. A validated terminal
settlement record remains in the existing attempt guard before receipt
deletion. Resource retirement releases dispatcher capacity independently of
missing task report, verification, or CoS acceptance. Pane observation never
proves retirement.

### Ownership and documentation stay durable

Deployment markers survive source-worktree deletion through stable Git identity,
and docs describe Plan + Git, CoS, attempt contract, `dcode-project`, Herdr,
and DeepAgents boundaries without adding an orchestration layer.

## Non-Goals

- No scheduler, retry engine, recovery daemon, heartbeat, or multi-attempt ledger.
- No automatic continuation, dispatcher-owned acceptance, or pane-based reconciliation.
- No Codex/Tura lifecycle parity in this change.
- No concurrency increase beyond `MAX_CONCURRENCY = 2`.
- No removal of the existing 10-second retry cap; only stale rationale changes.
- No new dependency, provider fallback, tracked `.deepagents/` state, or project MCP mutation.
- No automatic adoption of legacy deployment markers whose ownership is uncertain.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing untracked paths
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source/tests/docs, run focused tests, live local probes, validators, and `git diff --check`
- User-approval actions: push, merge, branch/worktree disposition, destructive cleanup, authentication, external runtime writes
- Parallel ownership: `none`; contract, launcher, wrapper, dispatcher, and proof share behavior
- Sequential fallback: admission contract → transport/policy callers → settlement/ownership proof → docs → full verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `de107057f6a7060e3e06955ee7e3bea9164d81f2`
- Expected workspace: reconcile local `main` to reviewed baseline before editing; preserve untracked `.playwright-mcp/`, `db/`, and prior plans
- Next action: historical plan closed; follow-up convergence work is tracked in `2026-09-17-deepagents-runtime-boundary-convergence-plan.md`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused admission regressions | `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_dcode_project.py` — 165 passed |
| Task 2 | `completed` | current | `codex` | Task 1 | contract/budget/transport tests | `377 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | recovery and capacity tests | `378 passed` |
| Task 4 | `completed` | current | `codex` | Task 3 | process/deployment ownership tests | `30 passed` |
| Task 5 | `completed` | current | `codex` | Task 4 | docs and repository validators | `71 passed`; validators passed |
| Task 6 | `completed` | current | `codex` | Task 5 | live probes and full verification | `408` focused; `720 passed, 1 skipped` full |

## Task Breakdown

### Task 1: Make admission authoritative

**Purpose:** Prevent duplicate owners from reaching any worker side effect.

**Task Function:** Implement and consume explicit admission outcomes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared safety boundary; low ambiguity after source confirmation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests run by lead controller

**Specification Coverage:** Safe lane admission; exclusive assignment ownership; no execution after `BLOCKED` or `RECONCILE`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_claim_attempt` and main admission/launch path
- Modify: `scripts/herdr_attempt_contract.py` public admission result and `scripts/dcode_project.py` caller
- Verify: `tests/test_herdr_attempt_contract.py`, `tests/test_dcode_project.py`

**Dependencies:** Current claim, receipt, binding, and role-view behavior remain unchanged except for pre-launch gating.

**Authority:**
- Preauthorized local actions: edit Task 1 files and run focused tests
- Stop for: changed claim schema, unresolved same-binding identity, or any required external runtime write

**Steps:**
- [x] Step 1: Add the smallest public admission result representation and map claim evidence to `ADMITTED`, `IDEMPOTENT`, `BLOCKED`, or `RECONCILE`.
- [x] Step 2: Keep claim decision and guard update inside the existing ownership lock; preserve legitimately active claims as `ACTIVE`/`BLOCKED`, return same-binding reuse as `IDEMPOTENT` with existing status, and reserve `RECONCILE` for missing, inconsistent, or uncertain evidence.
- [x] Step 3: Short-circuit `dcode_project.py` before role-view creation, worker launch, or other execution side effects unless result is `ADMITTED`.
- [x] Step 4: Add tests for same binding, competing active binding, legitimately active claim, uncertain prior claim, and successful admission.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_dcode_project.py` — `166 passed`
- Expected: competing and uncertain claims produce no worker/role-view side effect; same binding does not relaunch.

**Exit Criteria:** Every claim path has one explicit admission outcome and only `ADMITTED` can launch.

### Task 2: Route launcher and dispatcher through shared policy

**Purpose:** Remove policy forks and restore budget authority symmetry.

**Task Function:** Replace private imports and local calculations with contract APIs.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-module API migration; exact symbols known

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused caller and budget tests

**Specification Coverage:** Canonical identity, normalization, budget, lifecycle, settlement, and eligibility interpretation.

**Required Skills:** `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_attempt_contract.py:normalize_runtime_grant`, `resolve_attempt_budget`, `terminal_settlement_proven`, `derive_lifecycle_state`, `eligibility_action`
- Modify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`; remove private `_normalize_runtime_grant` coupling and duplicated `WHOLE_ATTEMPT_WALL_CLOCK_SECONDS`
- Verify: `tests/test_herdr_attempt_contract.py`, `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`

**Dependencies:** Task 1 public admission shape is stable.

**Authority:**
- Preauthorized local actions: edit Task 2 files and run focused tests
- Stop for: need for a second policy owner, changed public receipt contract, or budget behavior not expressible through current resolver

**Steps:**
- [x] Step 1: Expose only required public contract functions/constants; keep pure contract free of process inspection and Herdr calls.
- [x] Step 2: Route launcher and dispatcher grant normalization, lifecycle, settlement, eligibility, and budget decisions through the shared module.
- [x] Step 3: Name and wire remaining authority, elapsed attempt time, effective worker budget, and cleanup reserve through launcher → dispatcher → wrapper; treat `420` as native default ceiling only, not an explicit-grant ceiling.
- [x] Step 4: Prove explicit `600`-second grant reaches the worker as `600` when authority contains it, insufficient remaining budget fails closed, and native default remains `420` at wrapper boundary.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py` — `377 passed`
- Expected: no dispatcher import of launcher-private normalization; no duplicate whole-attempt constant; contract and production callers agree on `600` versus `420` cases.

**Exit Criteria:** Shared contract owns policy interpretation; callers only collect evidence and consume decisions.

### Task 3: Propagate bounded recovery and decouple capacity

**Purpose:** Reconcile known prior work without treating missing task evidence as live capacity.

**Task Function:** Carry recovery intent through launcher/dispatcher and split resource settlement from task acceptance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lifecycle integration with existing receipt and cleanup evidence

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic mocked evidence tests

**Specification Coverage:** Safe retry/reconciliation; bounded two-lane capacity; runtime completion distinct from CoS acceptance.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: launcher assignment parsing/descriptor construction; dispatcher command construction and `classify`; contract settlement predicates
- Modify: `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, `scripts/dcode_project.py`
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_herdr_parallel_dispatch.py`, `tests/test_dcode_project.py`

**Dependencies:** Tasks 1–2 contract outcomes and public policy APIs.

**Authority:**
- Preauthorized local actions: edit Task 3 files and run focused tests/live local fixture probes
- Stop for: pane state proposed as authoritative, unbounded polling, automatic continuation, or ambiguous receipt correlation

**Steps:**
- [x] Step 1: Add `prior_attempt_known` to launcher parser, assignment descriptor, dispatcher command chain, and correlated wrapper invocation.
- [x] Step 2: Require CoS to derive `prior_attempt_known` from durable plan/coordination evidence and pass the complete repository/plan/lane/assignment/grant identity contract on every coordinated launch.
- [x] Step 3: Under the existing ownership lock, preserve `ACTIVE`/`BLOCKED` and same-binding `IDEMPOTENT` outcomes; reserve `RECONCILE` for missing, inconsistent, or uncertain evidence.
- [x] Step 4: Before confirmed receipt deletion, persist validated correlated terminal settlement evidence in the existing attempt guard; recovery reads that record first and retained receipt second.
- [x] Step 5: Change dispatcher classification so retired worker resources release capacity even when task report, verification, or acceptance remains unverified; preserve per-lane evidence and `BLOCKED` aggregate semantics.
- [x] Step 6: Add regressions for receipt-publication/guard-settlement crash, receipt expiry/deletion, stale receipt replacement, active claim preservation, and retired capacity with missing report.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_dcode_project.py` — `378 passed`
- Expected: prior-attempt flag survives full command chain; active claims preserve `ACTIVE`/`BLOCKED`, same-binding reuse is `IDEMPOTENT`, only uncertain evidence yields `RECONCILE`, and retired resources classify as available while semantic result stays unverified.

**Exit Criteria:** Recovery is one bounded admission action; capacity reflects resource state, not task acceptance.

### Task 4: Prove process retirement and stable deployment ownership

**Purpose:** Close settlement evidence gaps on captured output and source-worktree lifecycle.

**Task Function:** Strengthen direct process/deployment regression proof without widening ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: platform-sensitive backend evidence; bounded test doubles already exist

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct tests and local deployment fixture

**Specification Coverage:** Cleanup/descendant retirement proof; deployment ownership permanence.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/owned_process.py:run_owned_process`; `scripts/deploy_agent_runtime.py` marker read/write/validation helpers
- Modify: `scripts/owned_process.py`, `scripts/deploy_agent_runtime.py`, `repo_config/starter-kit-manifest.json` only if manifest metadata must declare stable identity
- Verify: `tests/test_owned_process.py`, `tests/test_deploy_agent_runtime.py`

**Dependencies:** Task 3 settlement semantics define required retirement evidence.

**Authority:**
- Preauthorized local actions: edit Task 4 files and run isolated local process/deployment fixtures
- Stop for: inability to prove descendant retirement on supported platform, marker migration requiring destructive deletion, or cross-repository ownership ambiguity

**Steps:**
- [x] Step 1: Add captured-output normal-success regression proving descendant-group retirement before settlement returns; retain fail-closed timeout/kill behavior.
- [x] Step 2: Derive stable Git common-repository identity at deployment and compare marker identity, bundle, and source paths during reuse.
- [x] Step 3: Define legacy marker compatibility: accept old markers only when existing ownership remains provable; migrate marker format in place only after stable identity is proven; preserve uncertain or foreign markers and never auto-adopt them.
- [x] Step 4: Test source worktree deletion still permits same repository ownership and a different repository remains rejected; update manifest only if canonical deployment inputs require it.

**Verification:**
- [x] `python -m pytest -q tests/test_owned_process.py tests/test_deploy_agent_runtime.py` — `30 passed`
- Expected: supported success paths prove retirement; valid deployment survives source-path removal; foreign deployment is refused.

**Exit Criteria:** Settlement can rely on direct retirement evidence and deployment markers do not depend on ephemeral checkout paths.

### Task 5: Reconcile canonical documentation

**Purpose:** Make operational guidance match enforced ownership and evidence boundaries.

**Task Function:** Update maintained docs only after code/test behavior is fixed.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation reconciliation; no new behavior

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators and generated-surface check

**Specification Coverage:** Plan + Git recovery SSOT; CoS authority; wrapper execution ownership; Herdr diagnostic role; coordinated identity chain.

**Required Skills:** `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/tooling/runtime-tool-resolution.md`, `docs/operating_system/runtime/runtime-surfaces.md`, `.agents/skills/skill-chief-of-staff/SKILL.md`, `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md`, and `docs/superpowers/plans/2026-09-16-herdr-attempt-contracts-and-settlement-plan.md`
- Modify: named maintained docs, `.agents/skills/skill-chief-of-staff/SKILL.md`, the named dispatch spec where contract wording requires amendment, and this plan; never edit generated `AGENTS.md` directly
- Verify: `scripts/sync_agent_adapters.py --all-platforms --check`, planning and contract validators

**Dependencies:** Tasks 1–4 establish final behavior and evidence names.

**Authority:**
- Preauthorized local actions: edit maintained docs and run documentation/contract validators
- Stop for: source/test behavior contradicting proposed wording or generated adapter drift requiring canonical-source discovery

**Steps:**
- [x] Step 1: State Plan + Git as durable workflow/recovery SSOT; define attempt guard as execution-safety evidence, not workflow authority.
- [x] Step 2: State CoS authorizes, shared contract interprets, wrapper owns execution facts, Herdr transports/observes, and DeepAgents operates within grant.
- [x] Step 3: Require the complete coordinated repository/plan/lane/assignment/grant identity contract on every coordinated launch; CoS derives recovery history and passes it through the full chain; describe Herdr observation as diagnostic fallback only.
- [x] Step 4: Rewrite 10-second retry rationale as temporary migration/backoff policy; leave removal deferred.

**Verification:**
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: maintained docs and plan validate; generated adapter surfaces remain synchronized.

**Exit Criteria:** Docs, source, tests, and plan express one symmetric ownership model.

### Task 6: Run live probes and final verification

**Purpose:** Verify actual launcher/wrapper behavior after deterministic proof passes.

**Task Function:** Execute bounded read-only runtime probes and reconcile evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: acceptance controller owns live evidence and stop conditions

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh final verification by lead controller

**Specification Coverage:** Live boundary proof for duplicate admission, timeout/receipt settlement, cleanup, capacity, and Git preservation.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`, `skill-disposable-artifact-cleanup`

**Files And Symbols:**
- Inspect: all Task 1–5 changed surfaces and live command entrypoints in `scripts/herdr_main_launcher.py`, `scripts/herdr_parallel_dispatch.py`, and `scripts/dcode_project.py`
- Modify: none unless probe exposes a covered regression; any new fix returns to its owning task
- Verify: focused tests, full suite, validators, live probe evidence, and Git status

**Dependencies:** Tasks 1–5 complete with task-local proof.

**Authority:**
- Preauthorized local actions: run bounded local read-only probes, capture logs/receipts under disposable locations, remove only task-owned probe artifacts, and run final checks
- Stop for: authentication, external provider writes, live worktree mutation outside named fixtures, hanging process, or evidence inconsistent with deterministic tests

**Steps:**
- [x] Step 1: Probe duplicate same-assignment and competing-assignment admission; confirm one owner, no duplicate worker launch, and explicit outcome.
- [x] Step 2: Probe successful, timed-out, missing-report, and cleanup-uncertain lanes with harmless local fixtures; confirm receipt/resource/task-result separation.
- [x] Step 3: Replay identical worker evidence with successful observation, observation timeout, and unavailable pane output; confirm observation timing alone cannot change admission, resource settlement, or retry eligibility.
- [x] Step 4: Confirm `w10:p1`-style pane observation cannot authorize retry or release ownership; use direct process and receipt evidence instead.
- [x] Step 5: Remove only probe-owned disposable artifacts and record exact commands/results in plan evidence.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_owned_process.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_deploy_agent_runtime.py` — `408 passed`
- [x] `python -m pytest -q` — `720 passed, 1 skipped`
- [x] `python scripts/validate_repo_contracts.py` — passed
- [x] `python scripts/validate_planning_lifecycle.py --repo-root .` — passed
- [x] `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection` — passed
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check` — passed
- [x] `git diff --check` — passed
- [x] `git status --short --branch` — unrelated untracked paths preserved
- Expected: focused and full tests pass, validators pass, live probes produce correlated evidence, no unrelated tracked changes, and preserved untracked paths remain intact.

**Exit Criteria:** Fresh evidence supports every implementation outcome; unresolved or external runtime failures remain explicitly recorded, not converted to success.

## Live Probe Evidence

Bounded local probe command used a temporary directory and harmless child:

```text
PowerShell here-string piped to `python -`
```

Observed JSON: `ADMITTED`, same binding `IDEMPOTENT`, competing binding `BLOCKED`,
worker `success`, `cleanup_confirmed: true`, expected stdout, and no probe files
outside temporary guard state. Temporary directory cleanup removed all probe state.

## Verification

- `python -m pytest -q tests/test_herdr_attempt_contract.py tests/test_dcode_project.py tests/test_owned_process.py tests/test_herdr_main_launcher.py tests/test_herdr_parallel_dispatch.py tests/test_deploy_agent_runtime.py`
- `python -m pytest -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_planning_lifecycle.py --repo-root .`
- `python scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- `git status --short --branch`
- Live probes must use harmless local fixtures, prove admission/retirement/resource/task-result separation, and leave no task-owned disposable artifacts.

## Completion Criteria

The plan is ready for completion verification when:

1. Competing active claims return before role-view or worker side effects.
2. Same-binding reuse is idempotent and never relaunches.
3. `prior_attempt_known` survives launcher and dispatcher transport.
4. Existing claims preserve legitimately active `ACTIVE`/`BLOCKED` and same-binding `IDEMPOTENT` outcomes; `RECONCILE` covers only missing, inconsistent, or uncertain evidence.
5. Validated terminal settlement evidence survives receipt deletion in the existing attempt guard, including receipt-publication/guard-settlement crash recovery.
6. Dispatcher capacity reflects retired resources independently of task report, verification, or CoS acceptance.
7. Production callers use shared contract APIs; private launcher imports and duplicated policy constants are removed.
8. Explicit grants such as `600` reach the worker as `600` when authority contains them; native default remains `420`; insufficient remaining budget fails closed and cleanup reserve stays protected.
9. Captured-output success has direct descendant-retirement proof and unsupported cleanup remains fail-closed.
10. Deployment ownership survives source-worktree deletion, migrates only provably owned legacy markers, and rejects uncertain or foreign markers.
11. Every coordinated launch carries complete identity and CoS-sourced recovery history.
12. Docs and all-platform generated-surface checks match source and test truth.
13. Focused tests, full tests, validators, and live probes pass with preserved unrelated workspace state.

The plan may move from `proposed` to `active` only after approval. It may move
to `completed` only after `skill-verification-before-completion` returns
`verified`.

## Deferred Follow-Up

Provider retry-cap removal, active worker cancellation, durable multi-attempt
history, streaming task-result transport, automatic reconciliation service,
concurrency expansion, and Codex/Tura parity remain separate work.
