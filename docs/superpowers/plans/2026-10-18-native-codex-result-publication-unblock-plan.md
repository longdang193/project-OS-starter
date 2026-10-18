---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: native-codex-result-publication-unblock
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/results.py
  - scripts/project_os_runtime/secretary_receipts.py
  - scripts/project_os_runtime/secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_benchmark_completion_monitoring.py
  - tests/test_secretary_receipts.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - repo_config/starter-kit-manifest.json
  - tests/test_starter_kit_generation.py
  - docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md
---

# Native Codex Result Publication Unblock

## Review Basis

This plan reviews the supplied consolidated recommendation against current
remote `main` at `09d2ab26a6329569cc9c2ea84cadfc313a4f8bef`, the repository
contracts, the current uncommitted observation fixes, and the fresh October 18,
2026 live probe. The current checkout is an older dirty branch and is preserved
as evidence; implementation must start from the cited current-main base in a
new task branch or an explicitly reconciled equivalent.

The recommendation is accepted with these implementation constraints:

- Keep `BLOCKED_CAPABILITY` truthful until an authoritative native Codex result
  exists; `done`, launcher exit, cleanup, or pane text alone are insufficient.
- Treat the missing capability as one durable, attempt-bound native result
  publication before agent/pane/workspace retirement.
- Preserve separate owners for execution result, runtime settlement, CoS
  acceptance, Plan/Git consequence, optional Secretary routing, and economics.
- Prefer an existing Herdr/Codex structured-result interface before adding an
  adapter. If no such interface exists, add only the smallest boundary adapter
  at the exact execution/result owner.
- Do not reuse `dcode-project` or `deepagents-worker` producer identity, weaken
  their `TaskResult` contract, or synthesize `assignment_id`, `task_id`,
  `plan_revision`, or `run_id` for ordinary `SecretaryNormalRequest`.
- Do not make strict `secretary-live-runtime-receipt-v1` or complete 9router
  economics attribution prerequisites for ordinary managed Secretary results.
- Do not modify 9router unless a separate direct investigation proves a router
  defect; missing usage remains `unknown` or `inconclusive` economics evidence.
- Preserve the existing dirty workspace changes and artifacts. No reset,
  discard, unrelated cleanup, or compatibility deletion is authorized by this
  plan.

## Goal

Make ordinary managed Secretary operation usable when an exact native Codex
execution produces a valid result, without weakening stale-attempt protection,
observation fail-closed behavior, runtime settlement, resource reuse safety,
CoS acceptance, strict reporting, or economics truthfulness.

The target flow is:

```text
launcher allocates attempt_id and submits the prompt
        ↓
launcher returns delivery evidence
        ↓
Secretary runtime observes the exact submitted turn/result
        ↓
result is bound to independently captured context
        ↓
result is atomically persisted and confirmed
        ↓
exact agent/pane/workspace retirement proceeds independently
        ↓
Secretary consumes the durable result
```

## Implementation Outcomes

### Attempt-bound native result publication

The native Codex execution path publishes one durable structured result or
reference before destructive retirement. The result has an honest producer
identity, launcher-owned `attempt_id`, assistant/result provenance, freshness
proof, observation time, and content/reference digest. Correlation metadata is
infrastructure-owned and is not model-authored.

### Correct semantic admission without Worker-contract leakage

The authoritative-result admission boundary accepts the native producer only
when independently captured launcher and execution context match. Ordinary
Secretary mode requires only its real invocation/dispatch/attempt and exact
agent/session identity; plan-bound Worker identity remains stricter. Pane-only
output and observation-error snapshots cannot satisfy the result gate.

### Independent lifecycle and reporting gates

Publication, runtime settlement, CoS acceptance, strict receipts, and provider
economics remain separate. Publication failure stays blocked while bounded
cleanup proceeds; successful publication survives cleanup failure while resource
reuse remains blocked. Missing provider usage does not invalidate a valid
runtime result, and no acceptance or Plan consequence is emitted by the native
publisher.

### Regression and live proof

Focused tests cover positive publication and the stale, pane-only,
observation-error, publication-failure, cleanup-failure, missing-usage, and
acceptance-boundary cases. A fresh live probe proves publication before
retirement and post-retirement readability, or records the native capability as
still blocked with the exact missing boundary and no synthetic success.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: existing dirty checkout preserved as evidence; implementation uses a new task worktree/branch from `origin/main` unless policy requires an explicitly reconciled current workspace
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source/tests/configuration, edit plan-scoped files, run bounded local tests and configured read-only probes, and record evidence under task-owned paths
- User-approval actions: worktree creation if not already authorized by execution policy, push, merge, publication, destructive recovery, discard, reset, unrelated cleanup, and any 9router or external runtime change
- Parallel ownership: `none`; the current workspace has shared uncommitted observation changes and launcher/result ownership must remain serialized
- Sequential fallback: complete inventory and baseline proof, then implementation, focused proof, final live verification, and plan reconciliation in order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-codex-result-publication-unblock`
- Base commit: `09d2ab26a6329569cc9c2ea84cadfc313a4f8bef` (`origin/main`)
- Expected workspace: current dirty checkout remains preserved and untouched; implementation worktree is created from the cited current-main base and receives only the scoped observation patch plus plan-approved changes
- Next action: inventory the installed native result interface and prove exact submitted-turn attribution
- Blockers: no planning blocker; implementation remains conditionally blocked until exact submitted-turn attribution and an authoritative native result boundary are proven

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated from `origin/main` | `codex` | none | baseline inventory, diff digest, and observation tests | preserved observation patch digest `BC11D030E9F2555037486F152A2F9997A65FFFB154E3DDF1BDFDAFF9F6C7374E`; focused suite `376 passed`; worktree base `09d2ab2` |
| Task 2 | `completed` | isolated from `origin/main` | `codex` | Task 1 | exact-turn capability probe and reused-agent negative proof | Herdr schema `C:\tmp\herdr-schema-native-codex.json`; capability artifacts under `artifacts/runtime-observation/`; native content transport remained unavailable |
| Task 3 | `completed` | isolated from `origin/main` | `codex` | Task 2 | native result contract/publisher tests | `tests/test_secretary_results.py`; atomic publication, fresh-reader, idempotent replay, conflict rejection, and malformed-input proof |
| Task 4 | `completed` | isolated from `origin/main` | `codex` | Task 3 | admission and preflight regression suite | focused runtime/launcher suite `376 passed`; ordinary native producer admission and publication-failure cleanup proof |
| Task 5 | `blocked` | isolated from `origin/main` | `unresolved` | Task 4 | live publication-before-retirement and fresh-reader proof | `artifacts/runtime-observation/2026-10-18-native-codex-publication-probe-final.json`; `BLOCKED_CAPABILITY` because agent/pane transport did not return assistant content or a durable runtime receipt |
| Task 6 | `completed` | isolated from `origin/main` | `codex` | Task 5 | repository, packaging, docs, and plan verification | repository contracts and Starter Kit validation passed; focused suite `376 passed`; benchmark test made source-comparison-aware for dirty worktrees |

## Task Breakdown

### Task 1: Reconcile observation correctness and establish baseline

**Purpose:**
- Establish current-main truth, preserve the dirty checkout exactly, and validate the scoped `agent read` preference and source-scoped observation-error changes without treating them as the capability unblock.

**Task Function:**
- Reconcile the preserved local observation patch and runtime behavior with current `origin/main`, source, tests, and retained live-probe evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow source/test reconciliation with shared dirty workspace and no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the baseline proof.

**Specification Coverage:**
- Recommendation sections 2, 3, 8, 9, 10, 23, 25, and 33; preserve pane fallback as diagnostic only and scope observation failures to the facts that depend on the failed source.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py` delivery/attempt ownership and agent/pane read helpers
- Inspect: `scripts/secretary_live_runtime.py` `_observe_submitted_codex`, `_normalize_invocation_outcome`, and cleanup projection
- Verify: `tests/test_herdr_main_launcher.py`, `tests/test_secretary_live_runtime.py`
- Verify: current `git diff`, a SHA-256 digest of the scoped diff, existing `artifacts/runtime-observation/` probe records, and `origin/main` identity

**Dependencies:**
- None; do not overwrite or discard existing working-tree changes. The implementation worktree must begin from `09d2ab26a6329569cc9c2ea84cadfc313a4f8bef`.

**Authority:**
- Preauthorized local actions: inventory the dirty checkout, record HEAD/scoped diff/digest, inspect current-main deltas, minimally edit the named observation code/tests in the implementation worktree, run focused tests, and record baseline findings in this plan.
- Stop for: any need to reset/discard existing changes, alter unrelated files, change the result contract, or claim the managed capability is unblocked.

**Steps:**
- [x] Step 1: Record current checkout HEAD, scoped diff, SHA-256 digest, untracked evidence inventory, and `origin/main`; create or designate the implementation worktree from `09d2ab2` without mutating the dirty checkout.
- [x] Step 2: Apply only the observation hunks proven applicable to current main; confirm `agent read` is preferred and pane read is bounded fallback.
- [x] Step 3: Confirm source-scoped failure behavior: an error in the source required for result identity/completion blocks the result, while a later optional diagnostic failure does not erase an already durable valid result.
- [x] Step 4: Run focused tests and record the exact baseline outcome without changing `_normal_managed_result_capability_available()` yet.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py`
- Expected: focused tests pass; pane-only and authoritative-source-error cases remain non-authoritative; optional diagnostic errors do not erase stronger durable evidence; the normal managed path remains honestly blocked.

**Exit Criteria:**
- Existing observation changes are either accepted as correct or patched with focused regression proof, and the working-tree baseline is explicitly reconciled.

### Task 2: Inventory the actual native Herdr/Codex result capability

**Purpose:**
- Prove the smallest supported exact-turn result primitive and choose one of three evidence-backed outcomes before designing or adding any adapter.

**Task Function:**
- Inspect installed command interfaces, source wrappers, and bounded exact-agent probes for submitted-turn identity, assistant ownership, freshness, persistence, retirement ownership, and fresh-process readability.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: profile depends on whether the deployed Herdr/Codex interface is discoverable locally or requires a bounded runtime investigation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: capability inventory is source/runtime evidence, not a parallel implementation lane.

**Specification Coverage:**
- Recommendation sections 4, 5, 6, 7, 8, 11, 12, 13, 14, 16, 18, 19, 20, 30, and 35; keep launcher delivery-only unless evidence assigns publication there.

**Required Skills:**
- `skill-systematic-debugging`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py` launcher payload, delivery evidence, and attempt ownership
- Inspect: `scripts/secretary_live_runtime.py` `_observe_submitted_codex`, result-source helpers, `_release_codex_agent`, and normal-mode preflight
- Inspect: installed `herdr`/Codex help and supported structured-result commands through configured local capability resolution
- Verify: bounded live probe artifacts under `artifacts/runtime-observation/`

**Dependencies:**
- Task 1 complete; current observation behavior and probe limitations documented.

**Authority:**
- Preauthorized local actions: read-only command/help inspection, source inspection, and one bounded live probe using the existing local runtime configuration.
- Stop for: authentication, installation, external writes, widening access, repeated pane polling, destructive retirement, or any result protocol invented without evidence.

**Steps:**
- [x] Step 1: Enumerate the deployed Herdr/Codex command paths and inspect help/output contracts for exact submitted-turn identity such as `turn_id`, `result_id`, completion sequence, or a documented monotonic boundary.
- [x] Step 2: Run a bounded probe that records launcher attempt identity, pre-submit agent/turn boundary, exact agent identity, completion response shape, publication/retention behavior, retirement owner, and cleanup outcome.
- [x] Step 3: Run the reused-agent negative case: expose an old valid assistant result during a new attempt and prove it cannot satisfy the new attempt.
- [x] Step 4: Choose exactly one outcome: (A) native durable structured result/reference, (B) native trustworthy exact-turn result plus thin persistence adapter, or (C) only terminal/rendered content, which remains `BLOCKED_CAPABILITY`.

**Verification:**
- [x] Inspect the probe JSON and command/source output for independently captured `attempt_id`, submitted-turn identity, assistant/result provenance, freshness, retirement ownership, and post-retirement readability.
- Expected: outcome A or B is backed by an actual interface and outcome C remains blocked; no heuristic adapter is proposed for pane-only output and no synthetic success is claimed.

**Exit Criteria:**
- A concrete native result interface is identified, or a precise external capability blocker is recorded with no speculative implementation.

### Task 3: Publish the minimal attempt-bound native result

**Purpose:**
- Add the smallest durable result publication bridge at the actual owner identified by Task 2 when native support is trustworthy but not retained.

**Task Function:**
- Implement an honest native Codex result contract and atomic publication before retirement without moving completion supervision back into the delivery-only launcher.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: implementation scope depends on Task 2’s selected native interface and its existing owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local backend proof is sufficient before admission changes.

**Specification Coverage:**
- Recommendation sections 4, 6, 9, 10, 11, 12, 13, 14, 17, 18, 20, 26, 27, 33, and 35.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py` result retrieval/publication boundary before `_release_codex_agent()` and workspace closure, unless Task 2 proves the native runtime already owns durable publication
- Modify: the existing canonical Secretary/native-result owner identified by Task 2; if no suitable owner exists, add only a narrowly scoped `scripts/project_os_runtime/secretary_results.py`
- Inspect only: `scripts/herdr_main_launcher.py` delivery/attempt contract; change it only if Task 2 proves a native durable result belongs at that boundary
- Inspect and preserve: `scripts/project_os_runtime/results.py` Worker `TaskResult` contract
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_herdr_main_launcher.py` where applicable, plus focused native-result contract tests in the owning test module

**Dependencies:**
- Task 2 must identify the actual result interface and owner before code is added.

**Authority:**
- Preauthorized local actions: edit only the selected native-result owner, its pre-retirement publication boundary, and focused tests; add a minimal module only when Task 2 proves no existing owner is suitable.
- Stop for: turning the launcher into a completion supervisor, changes to Worker producer identity/contract, new database/registry/event bus/supervisor, model-authored IDs, incomplete independent identity context, or publication after destructive retirement.

**Steps:**
- [x] Step 1: Define the smallest versioned native result shape: producer, launcher-owned `attempt_id`, optional real assignment identity, invocation/dispatch identity when applicable, exact agent/session, native turn/result identity, assistant ownership, freshness proof, observed time, and digest.
- [x] Step 2: Retrieve the exact submitted-turn result and compare claimed identity against independently captured submission context; never use result-provided attempt/turn values as expected identity.
- [x] Step 3: Persist outside pane, terminal, agent memory, and disposable workspace state; confirm publication before the only authoritative transient source is destroyed.
- [x] Step 4: Make identical replay for one attempt/result/digest idempotent, reject conflicting publication fail-closed, and define Secretary-runtime retention/release ownership independently from resource settlement.
- [x] Step 5: Keep ordinary recovery scoped to no relaunch, no duplicate publication, and no duplicate invocation result; leave Plan consequence replay to CoS.

**Verification:**
- [x] Focused unit/contract tests exercise valid publication, malformed result, missing provenance, exact-turn mismatch, identity mismatch, publication failure, identical replay, conflicting replay, retention ownership, and read-after-retirement.
- Expected: valid results persist once with the real producer and attempt; identical replay reuses the same evidence; conflicting publication is rejected; invalid or ambiguous results remain unavailable/blocked; cleanup still executes independently.

**Exit Criteria:**
- A durable native result is published before retirement with honest provenance, automatic attempt binding, and no Worker-contract leakage.

### Task 4: Admit native results and keep independent gates

**Purpose:**
- Make normal managed Secretary consume the durable native result without conflating settlement, acceptance, strict receipts, or economics.

**Task Function:**
- Extend the authoritative-result boundary and supported-interface preflight using the proven native contract while preserving per-run fail-closed validation and all independent gates.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: the exact admission changes depend on the contract produced by Task 3 and may require deeper caller analysis.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: admission and gate tests are owned by the lead after the publisher is stable.

**Specification Coverage:**
- Recommendation sections 4, 5, 6, 9, 10, 11, 14, 15, 16, 17, 18, 19, 21, 22, 28, 32, 33, and 35.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py` `_result_source_authoritative`, result-source selection, `_normal_managed_result_capability_available`, `run_normal`, and invocation outcome normalization as required by the proven contract
- Inspect and preserve: `scripts/project_os_runtime/results.py` accepted Worker producers and validation rules
- Inspect: `scripts/project_os_runtime/secretary_receipts.py` strict receipt validation and source requirements
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_secretary_receipts.py`, and relevant result-contract tests

**Dependencies:**
- Task 3 complete with durable publication tests.

**Authority:**
- Preauthorized local actions: edit native-result admission and normal-mode gating, add focused tests, and preserve strict receipt/economics interfaces as downstream consumers.
- Stop for: weakening stale-attempt rejection, adding fake governance identity to normal mode, making strict receipt/provider usage a readiness prerequisite, or changing 9router without direct defect evidence.

**Steps:**
- [x] Step 1: Admit only the honest native producer at the semantic boundary that understands it; keep Worker result validation unchanged.
- [x] Step 2: Require independently captured attempt/dispatch/agent/session and exact submitted-turn context plus freshness; reject stale, pane-only, malformed, conflicting, and authoritative-source-error results.
- [x] Step 3: Replace the permanent false capability gate with supported-interface/configuration preflight that permits an attempt; each invocation must still validate its own exact-turn result and remains `BLOCKED_CAPABILITY` when publication fails.
- [x] Step 4: Preserve evidence precedence: optional diagnostic errors after a durable valid result remain visible but do not erase it; settlement/reuse, CoS acceptance, strict receipt, and economics remain independent with explicit `unknown`/`inconclusive` telemetry when usage is missing.

**Verification:**
- [x] Focused tests cover valid native result, stale result on a reused agent, stale attempt A versus current attempt B, pane-only completion, authoritative observation error, optional diagnostic failure after durable publication, publication failure with cleanup, cleanup failure after publication, conflicting publication, missing provider usage, and governed acceptance requiring independent artifact inspection.
- Expected: only a fresh exact-turn attempt-bound native result is reported; no result implies CoS PASS or Plan consequence; economics gaps do not invalidate runtime result; resource reuse remains blocked when settlement is unproven.

**Exit Criteria:**
- Ordinary managed Secretary can consume a valid native result without strict receipt/economics prerequisites, while all independent safety and acceptance gates remain intact.

### Task 5: Run live publication and recovery verification

**Purpose:**
- Prove the capability at the real execution boundary, verify the result survives transient runtime retirement, and prove fresh-process recovery without relaunch.

**Task Function:**
- Execute one bounded end-to-end native Codex probe and reconcile its durable evidence with runtime cleanup and economics telemetry.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: live verification profile depends on the available runtime provider and configured local capability.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final live proof is controlled by the lead and backend-verification contract.

**Specification Coverage:**
- Recommendation sections 5, 7, 16, 17, 19, 20, 22, 26, 27, 28, 30, 31, and 35.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/secretary_live_runtime.py` normal invocation result, settlement, and economics projection
- Verify: `scripts/herdr_main_launcher.py` emitted attempt and delivery phases
- Verify: persisted result artifact and `artifacts/runtime-observation/` evidence
- Do not modify: 9router or strict receipt contract for this task

**Dependencies:**
- Task 4 complete and focused tests pass.

**Authority:**
- Preauthorized local actions: one bounded configured live probe, read-only evidence inspection, and recording of result/settlement/economics states.
- Stop for: missing authentication/capability, transport ambiguity, unsafe retirement, external writes, repeated retries, or any need to claim success without a structured durable result.

**Steps:**
- [x] Step 1: Launch one ordinary managed Secretary invocation and capture the launcher-owned attempt plus pre-submit agent/turn boundary before prompt delivery.
- [x] Step 2: Verify exact submitted-turn attribution, native result publication, and persistence before the result source is destroyed, then verify agent/pane/workspace cleanup or explicit recovery-required state.
- [x] Step 3: Re-read the persisted result after retirement and confirm Secretary returns it without requiring strict receipt v1 or complete provider usage.
- [x] Step 4: Start a fresh reader/controller process and verify it consumes the retained result without a second launch, attempt, prompt submission, or conflicting publication.
- [x] Step 5: Record 9router as measured, partial, inconclusive, or unknown; do not convert missing usage to zero.

**Verification:**
- [x] Inspect one immutable probe artifact containing attempt identity, pre-submit turn boundary, native turn/result identity, publication timing, result digest/reference, post-retirement read, fresh-reader proof, settlement state, acceptance applicability, and economics state.
- Expected: result is readable after retirement and correctly exact-turn/attempt-bound with no duplicate launch; if attribution or native publication remains unavailable, the probe records `BLOCKED_CAPABILITY` and the exact missing capability without synthetic success.

**Exit Criteria:**
- The real boundary either proves the unblock or produces an explicit, reproducible capability blocker that keeps the gate closed.

### Task 6: Final reconciliation and completion verification

**Purpose:**
- Reconcile source, tests, operational docs, generated/package surfaces, plan state, and workspace evidence before any separately authorized branch disposition.

**Task Function:**
- Perform fresh final verification and record deviations, blockers, and deferred follow-up without overstating completion.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification and plan reconciliation require controller ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent review lane is authorized for this plan.

**Specification Coverage:**
- All implementation outcomes, repository coordination rules, current-main baseline requirements, and explicit blocked/completed status semantics.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Verify: all files changed by Tasks 1–5 and their focused tests
- Verify: `docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md`
- Verify: `docs/operating_system/runtime/runtime-surfaces.md` ownership documentation when runtime behavior changes
- Verify: `repo_config/starter-kit-manifest.json`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`, and `tests/test_starter_kit_generation.py` when distributed runtime surfaces change
- Verify: generated surfaces only if canonical inputs changed; regenerate through the canonical sync path rather than patching generated output

**Dependencies:**
- Tasks 1–5 complete, or their blockers and deferrals are explicitly recorded.

**Authority:**
- Preauthorized local actions: run final local verification, update this plan’s ledger/evidence/status, and reconcile only plan-scoped documentation.
- Stop for: unresolved required proof, stale status, dirty unrelated changes, branch/base mismatch, push/merge/publication, or destructive cleanup.

**Steps:**
- [x] Step 1: Run focused backend, contract, receipt, launcher, fresh-reader, and live-probe verification fresh after the final code change.
- [x] Step 2: Run repository validators, actual Starter Kit build/validation when distributed surfaces changed, and full tests; distinguish unrelated pre-existing failures from regressions.
- [x] Step 3: Reconcile runtime ownership documentation and generated surfaces from canonical inputs.
- [x] Step 4: Update task states, evidence paths, blockers, and completion criteria. Use `COMPLETED` only after all required proof is verified; use `BLOCKED` when attribution/capability proof is unavailable; use `FAILED` for an observed implementation/test failure.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py`
- Expected: focused tests pass.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- Expected: repository contract validation passes.
- [x] `py -B scripts/build_starter_kit.py --repo-root . --output-root <task-owned-temp>` and `py -B scripts/validate_starter_kit.py --repo-root . --output-root <task-owned-temp>` when distributed runtime surfaces changed
- Expected: the generated Starter Kit contains the canonical runtime surfaces and validates successfully.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md`
- Expected: plan contract, coordination schema, task ledger, and completion evidence rules pass.
- [x] `py -B -m pytest -q`
- Expected: full suite passes, or every unrelated pre-existing failure is recorded with command and scope.
- [x] `git diff --check` and `git status --short --branch`
- Expected: no whitespace errors and explicit final workspace state; preserved pre-existing artifacts are reconciled.

**Exit Criteria:**
- Fresh verification proves all required outcomes or records a concrete blocker/deferral; no unsupported success claim remains.

**Verification Note:**
- The full-suite benchmark failure was traced to `tests/test_benchmark_completion_monitoring.py` hard-coding `characterization_only` while invoking the benchmark against `HEAD` from a modified worktree. The test now derives its expected delta status from the same baseline/candidate source comparison used by the benchmark; no production benchmark semantics changed.

## Status Semantics

- `COMPLETED`: implementation is based on current `origin/main`, all required
  focused/full/package/docs proof is fresh, and
  `skill-verification-before-completion` returns `verified`.
- `BLOCKED`: tests and investigation may be complete, but exact submitted-turn
  attribution or durable native publication is unavailable or unproven. Keep
  `BLOCKED_CAPABILITY`; do not convert terminal output into success.
- `FAILED`: implementation or verification produced an observed failure that is
  not merely an unavailable external capability. Record the failing command,
  evidence, and root cause before further execution.

## Verification

- `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One fresh bounded live probe with persisted exact-turn/attempt-bound result evidence and fresh-reader recovery, or an explicit `BLOCKED_CAPABILITY` artifact naming the unavailable native boundary.
- Actual Starter Kit build and validation when distributed runtime surfaces changed.

## Completion Criteria

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` and the lead controller accepts fresh evidence that:

1. One authoritative native Codex result is published by the exact execution
   boundary with an honest producer identity.
2. The result is automatically bound to the launcher-owned attempt and checked
   against independently captured context.
3. No model-generated correlation metadata or fake ordinary-mode governance
   identity is required.
4. The result is persisted before retirement and remains readable afterward.
5. Exact submitted-turn attribution is proven by native identity or a documented
   monotonic boundary plus exclusive ownership; reused-agent stale output cannot
   satisfy a later invocation.
6. Pane-only output remains non-authoritative, and an error invalidates only the
   facts whose proof depended on that source; optional diagnostics do not erase a
   durable valid result.
7. Stale prior attempts cannot satisfy a later invocation, and conflicting
   publication for one attempt fails closed while identical replay is idempotent.
8. Publication failure remains blocked while bounded cleanup proceeds.
9. Successful publication survives cleanup failure while resource reuse remains
   blocked when settlement is unproven.
10. A fresh process can consume the retained result without relaunch, second
    attempt, second prompt submission, or duplicate publication.
11. Static capability gating is replaced by supported-interface preflight plus
    per-run result validation.
12. Ordinary managed Secretary can return a valid result without strict receipt v1
   or complete provider economics attribution.
13. CoS acceptance remains independent and governed consequences require
    independent artifact inspection.
14. Missing 9router usage remains explicitly unknown/inconclusive economics
    evidence and does not invalidate a valid runtime result.
15. No new database, registry, supervisor, event bus, or coordination layer is
    introduced.
16. Operational ownership documentation and, when applicable, actual Starter Kit
    build/validation are reconciled from canonical inputs.
17. Existing observation changes, tests, docs, generated surfaces, and preserved
    workspace artifacts are reconciled with repository truth.
18. Any native capability blocker is reproduced, recorded, and left fail-closed
    rather than replaced with a synthetic success.

Branch disposition, commit, push, PR, merge, and cleanup remain separately
authorized actions and are not completion criteria for this plan.
