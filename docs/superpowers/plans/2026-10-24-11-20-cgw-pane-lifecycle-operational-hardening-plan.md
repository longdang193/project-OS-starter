---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: cgw-pane-lifecycle-operational-hardening
targets:
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/submission_gate.py
  - scripts/secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
  - tests/test_agent_profile_registry.py
  - tests/test_starter_kit_generation.py
  - docs/configuration.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/superpowers/plans/2026-10-24-11-20-cgw-pane-lifecycle-operational-hardening-plan.md
---

# CGW Retirement And Pane Lifecycle Operational Hardening

## Goal

Finish the validated operational hardening work around the native Secretary–CoS–Worker
dispatch path while preserving the completed CGW retirement boundary. The launcher must
keep failing closed for global identity, snapshot, and transport failures; it must not
fail closed merely because every existing `--session auto --pane auto` candidate has an
incompatible context. Delivery state must distinguish admission, prompt delivery,
worker execution, and observation so retries are not blocked by failures that happened
before delivery.

## Review Basis

- Reviewed revision: `origin/main` at `ccc8a25e12c0464974bfc0b0b445a9153a19cd93`.
- Reviewers: GPT-5.6-Sol High and GPT-6 High, both completed through the repository's
  authenticated browser-review workflow.
- Primary implementation surface: `scripts/herdr_main_launcher.py`.
- CGW conclusion: no active CGW launcher, provider, package, startup, overlay, or port
  path remains in maintained executable/configuration surfaces. CGW identifiers in the
  retirement policy, rejection logic, regression tests, and historical plans are
  intentional retirement evidence and must remain.
- Existing auto-pane conclusion: candidate-local incompatible context is already modeled
  as a rejection that can reach replacement allocation; the implementation must preserve
  and regression-test that behavior rather than add another allocator or coordinator.

## Implementation Outcomes

### Correct logical admission and delivery settlement

The submission gate durably claims logical operation ownership early enough to prevent
duplicate assignments from consuming pane/startup resources, while keeping delivery
preparation separate until pane ownership and final context verification succeed. The
record carries a recoverable admission phase plus an attempt lease (or an equivalent
durable reconciliation marker): after restart, an expired admission with no dispatch
receipt is released as `not_delivered`, while an ambiguous or observed dispatch remains
`delivery_uncertain`. Pre-dispatch failures settle as `not_delivered`; accepted prompt
delivery settles as `submitted`; worker execution failure is reported separately from
delivery and does not rewrite confirmed delivery as `not_delivered`.

### Race-free pane lifecycle

Fresh Codex startup, startup identity confirmation, and the first prompt submission run
under one pane-ownership critical section. Stale-idle release and any state-changing
candidate mutation occur only while the relevant pane ownership or allocation lock is
held. Long-running completion observation remains outside the ownership lock.

### Bounded and lower-overhead operation

DeepAgents completion evidence uses bounded backoff instead of a fixed 100 ms receipt
poll for the entire runtime. Auto-discovery builds reusable workspace/session indexes,
avoids repeated full-snapshot scans and duplicate pane inspections, and keeps a distinct
bounded lock-wait budget from candidate inspection and replacement allocation. The
existing discovery deadline and allocation reserve remain bounded; no scheduler,
background supervisor, registry, or second lifecycle store is introduced.

### Durable CGW retirement and contract proof

Profile admission continues rejecting retired CGW/web-combo provider aliases and model
prefixes before executable lookup or runtime dispatch. Policy projections remain in sync,
starter-kit boundaries remain correct, and documentation describes the intentional
retirement guards plus the candidate-local versus global-failure distinction.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the listed launcher, tests, documentation, and plan files; run the declared local tests, validators, and diff checks
- User-approval actions: push, merge, publication, destructive cleanup, or edits outside the listed targets
- Parallel ownership: none; the gate, pane lock, allocator, and tests share one lifecycle contract
- Sequential fallback: gate contract first, ownership and allocation second, polling/indexing optimization third, retirement/docs reconciliation fourth, final verification last

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-pane-lifecycle-plan-review`
- Base commit: `67e34f933ca5c2312305ccd855b79cecc7aa03ba`
- Expected workspace: preserve all pre-existing modified files and untracked `.playwright-mcp/`, `.runtime/`, `node_modules/`, and review-output artifacts; implementation changes are limited to the listed targets
- Next action: hand off the verified branch to the authorized Git finishing workflow
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused gate tests | 23 passed |
| Task 2 | `completed` | current | `codex` | Task 1 | ownership and auto-pane regression tests | 26 passed |
| Task 3 | `completed` | current | `codex` | Tasks 1–2 | deterministic call-count/backoff tests and focused suite | 274 passed |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | CGW policy parity, docs, and repository validators | 306 passed; validation passed |
| Task 5 | `completed` | current | `codex` | Tasks 1–4 | fresh final verification | all required checks passed |

## Task Breakdown

### Task 1: Normalize admission and delivery state semantics

**Purpose:**
- Prevent pre-delivery failures from creating persistent retry blocks and separate transport delivery from worker execution outcomes.

**Task Function:**
- Implement the smallest state-machine correction that preserves the existing submission-gate file and settlement mechanism.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: execute inline in the lead Codex controller; the approved scope is design-clear and does not require delegated implementation.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently select the lowest profile that can validate state transitions and retry behavior.

**Specification Coverage:**
- GPT-6 P1/P2 findings on premature delivery ownership, persistent `delivery_uncertain`, admission after resource consumption, and conflated worker failure.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_main_body`, `resolve_launch`, `_submission_gate_binding`, `claim_model_submission`, `settle_model_submission`, `emit_failure`, `_claim_submission_gate`, `_settle_submission_gate`, `scripts/project_os_runtime/submission_gate.py`
- Modify: `scripts/herdr_main_launcher.py:_main_body`, `resolve_launch`, `_submission_gate_binding`, `claim_model_submission`, `prepare_model_submission`, `settle_model_submission`, `emit_failure`, `scripts/secretary_live_runtime.py:run_probe`, and the existing gate implementation in `scripts/project_os_runtime/submission_gate.py`
- Verify: `tests/test_herdr_main_launcher.py` submission-gate, blocked-launch, transport-timeout, and nonzero-worker tests

**Dependencies:**
- The existing gate record remains the single source of truth; an in-place schema/semantic migration is allowed when required to persist the admission phase, lease, or reconciliation marker. Do not add a second gate file or lifecycle registry.

**Authority:**
- Preauthorized local actions: edit the named launcher symbols and their focused tests, and run the declared focused pytest command
- Stop for: retry semantics changing outside the named admission/delivery contract, a need for a second lifecycle store, or any external publication

**Steps:**
- [x] Step 1: Make `resolve_launch` construct the canonical `_submission_gate_binding()` and preflight contract as its first action, before `_resolve_target_selector` can inspect or allocate a pane; derive it from the same normalized profile, grant, model, and selector inputs consumed by launch resolution so normalization is not duplicated. Claim logical admission before expensive target startup/allocation, then promote to delivery preparation only after pane ownership and final context verification.
- [x] Step 2: Settle admission/pre-dispatch failures as `not_delivered`, preserve `delivery_uncertain` only for post-dispatch ambiguity, and keep confirmed `submitted` delivery when a worker later exits nonzero while reporting execution failure separately.
- [x] Step 3: Persist a durable admission phase and attempt lease (or equivalent recovery marker) in `scripts/project_os_runtime/submission_gate.py`; define restart reconciliation so an expired pre-dispatch admission is retryable only after authoritative receipt absence is established, while uncertain dispatch remains blocked. Add crash/restart tests covering duplicate admission, pane/startup failure after admission, lease expiry, transport timeout after dispatch, prompt acceptance followed by worker failure, and retry eligibility after `not_delivered`.

**Verification:**
- [x] `python -m pytest -q tests/test_submission_gate.py tests/test_herdr_main_launcher.py -k "submission_gate or delivery_uncertain or delivery_failed or pane_run_failure or transport_timeout"` — 23 passed.
- Expected: pre-dispatch failures are retryable `not_delivered`; post-dispatch ambiguity is `delivery_uncertain`; confirmed delivery remains `submitted` even when execution fails.

**Exit Criteria:**
- Gate ownership prevents duplicate logical delivery without converting pre-delivery failures into persistent delivery uncertainty, and worker execution state is no longer encoded as transport failure.

### Task 2: Hold pane ownership through fresh startup and preserve safe replacement allocation

**Purpose:**
- Remove same-context startup races and ensure candidate-local incompatibility still falls through to safe new-pane allocation.

**Task Function:**
- Reconcile the pane ownership critical section with the existing auto-selector and allocation lock.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: execute inline in the lead Codex controller; the approved lane is already active and does not require delegated implementation.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently validate lock coverage and candidate-local versus global failure behavior.

**Specification Coverage:**
- GPT-6 P1/P3 findings on fresh Codex startup races and stale-idle mutation; original operational bottleneck requiring `auto/auto` replacement allocation for incompatible existing panes.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_run_with_pane_ownership`, `_resolve_target_selector`, `_inspect_auto_candidate`, `_release_stale_idle_agent`, `_confirm_codex_start`, `_submit_codex_prompt`, `_main_body`
- Modify: `scripts/herdr_main_launcher.py:_run_with_pane_ownership`, `_resolve_target_selector`, `_inspect_auto_candidate`, `_main_body`
- Verify: `tests/test_herdr_main_launcher.py` pane-lock, fresh-Codex-start, auto/auto candidate-rejection, replacement-allocation, and stale-release tests

**Dependencies:**
- Task 1 must define the point at which delivery preparation is allowed.

**Authority:**
- Preauthorized local actions: edit the named launcher symbols and focused launcher tests, and run direct lock/allocation regression tests
- Stop for: a need for a new coordinator, background supervisor, or lifecycle store; any change to exact-selector fail-closed behavior; or an external action

**Steps:**
- [x] Step 1: Move fresh Codex startup, `_confirm_codex_start`, final pane verification, and first prompt submission into one `_run_with_pane_ownership` callback; release the lock before completion observation only.
- [x] Step 2: Ensure `_release_stale_idle_agent` and all other state-changing candidate mutations occur only under pane ownership or the allocation lock; keep candidate inspection read-only outside those locks.
- [x] Step 3: Preserve and adapt the existing `--session auto --pane auto` regressions where candidate-local incompatible contexts reach replacement allocation and a validated source pane produces `allocation.status=allocated`; do not duplicate equivalent tests. Preserve fail-closed results for global snapshot, identity, and transport failures.
- [x] Step 4: Settle the gate only after the ownership/context boundary established by Task 1, so lock acquisition failure cannot be reported as delivered work.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py -k "pane_ownership or auto or allocation or stale or codex_start"` — 26 passed.
- Expected: fresh startup and first prompt are serialized per pane; candidate-local rejection allocates a replacement; global failures remain blocked/incomplete; dry-run never mutates pane state.

**Exit Criteria:**
- No same-pane startup/submit race remains in the fresh Codex path, and incompatible existing panes no longer create an operational dead end when safe allocation is possible.

### Task 3: Reduce polling, scanning, and inspection overhead without adding branching infrastructure

**Purpose:**
- Reduce avoidable subprocess and in-memory work while preserving bounded evidence and deterministic lifecycle behavior.

**Task Function:**
- Replace repeated work with bounded reuse and simplify only branches proven redundant by the existing tests and evidence contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: execute inline in the lead Codex controller; the optimization changes share the launcher lifecycle contract and are not separable without duplicating state-machine reasoning.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently validate call-count, backoff, timeout, and outcome-classification invariants.

**Specification Coverage:**
- GPT-5.6 findings on 100 ms receipt polling, repeated pane inspection, redundant outcome branches, and the large interleaved dispatch state machine; GPT-6 findings on repeated full-snapshot scans and the shared allocation reserve.

**Required Skills:**
- `skill-performance-optimization`, `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`, `_classify_deepagents_outcome`, `_resolve_target_selector`, `_inspect_auto_candidate`, `_allocation_lock`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`, `_classify_deepagents_outcome`, `_resolve_target_selector`, `_allocation_lock`
- Verify: `tests/test_herdr_main_launcher.py` completion-evidence, classification, selector-call-count, timeout-budget, and allocation-boundary tests

**Dependencies:**
- Tasks 1 and 2 establish the correct state and ownership boundaries before optimization changes are measured.

**Authority:**
- Preauthorized local actions: edit the named performance-sensitive launcher symbols and tests, run deterministic focused tests, and collect same-environment timing/call-count evidence
- Stop for: a requirement for a new scheduler/thread, an unbounded retry loop, a relaxed global timeout, or a correctness regression hidden by a performance optimization

**Steps:**
- [x] Step 1: Replace fixed-interval receipt polling with monotonic-deadline backoff of 100 ms, 250 ms, then a 500 ms cap, while retaining the existing diagnostic interval and terminal receipt precedence. After the final sleep, perform one final receipt read before returning `unknown` so a receipt arriving at the deadline boundary is not missed.
- [x] Step 2: Build a reusable workspace/session index for each snapshot generation, but keep the initial discovery index distinct from the allocation-refresh generation. Under `_allocation_lock`, refresh the snapshot, re-inspect candidates against the refreshed index, and perform final pane/context verification; never reuse the initial index for replacement allocation.
- [x] Step 3: Split allocation lock-wait budgeting from candidate inspection/allocation budgeting inside the existing discovery deadline and one-second reserve; do not increase the overall deadline or create another budget store.
- [x] Step 4: Preserve the `receipt_confirmed` classifier branch because the existing zero-exit failed-report and missing-managed-result tests prove it is behaviorally reachable; simplify only the actually redundant paths without changing precedence.
- [x] Step 5: Add deterministic backoff-sequence and final-boundary-read assertions, including a receipt that becomes confirmed during the final deadline interval. Record the post-change focused-suite duration with `python -m pytest -q tests/test_herdr_main_launcher.py --durations=10`; treat correctness and bounded-call assertions as the acceptance gate, not noisy wall-clock variance.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py -k "completion or classification or selector or deadline or allocation"` — 82 passed.
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py --durations=10` — 274 passed in 1.82s; backoff and boundary assertions passed.
- Expected: receipt reads are bounded by deadline/backoff, candidate scans and pane inspections do not grow with repeated full-snapshot passes, allocation remains within the existing reserve, and outcome precedence remains unchanged.

**Exit Criteria:**
- The measured code path performs less redundant work under the representative tests without widening timeouts, weakening evidence requirements, or adding lifecycle infrastructure.

### Task 4: Reconcile CGW retirement proof and operational documentation

**Purpose:**
- Verify the retirement boundary remains complete and document the corrected lifecycle contract without deleting intentional guards or historical evidence.

**Task Function:**
- Reconcile canonical policy, runtime documentation, and regression evidence after launcher behavior changes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: execute inline in the lead Codex controller because policy, documentation, and generated-surface checks must be reconciled as one contract.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently validate policy parity and maintained-surface absence.

**Specification Coverage:**
- CGW removal verification; Secretary–CoS–Worker communication contract; no duplicate policy source; no public exposure of private governance or runtime state.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:_load_retirement_policy`, `agents/`, `repo_config/retired-model-policy.json`, `scripts/retired-model-policy.json`, existing CGW retirement tests
- Modify: `docs/configuration.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`, `docs/operating_system/tooling/runtime-tool-resolution.md`, `scripts/secretary_live_runtime.py:run_probe`, and only regression tests whose assertions no longer match the settled launcher contract
- Verify: `tests/test_agent_profile_registry.py`, `tests/test_starter_kit_generation.py`, `tests/test_deploy_agent_runtime.py`, and policy parity checks

**Dependencies:**
- Tasks 1–3 complete and their focused tests pass.

**Authority:**
- Preauthorized local actions: update the named operational docs and retirement regression assertions, and run policy, starter-kit, deployment, and repository validators
- Stop for: discovery of an active maintained CGW executable/configuration path, a mismatch between upstream policy ownership and local projections, or a required edit outside the named surfaces

**Steps:**
- [x] Step 1: Re-run the active-surface audit across `scripts`, `tests`, `repo_config`, `docs`, and `agents/`, and assert that CGW remains only in retirement policy, rejection logic, tests, and historical documentation; treat profile-loading tests as coverage for any generated or registry-backed `agents/` surface where no direct edit is needed. Do not remove intentional references.
- [x] Step 2: Document admission versus delivery settlement, fresh-start ownership coverage, bounded completion polling, candidate-local replacement allocation, and global fail-closed behavior.
- [x] Step 3: Verify `repo_config/retired-model-policy.json` and `scripts/retired-model-policy.json` remain identical projections and that starter-kit generation keeps shared runtime policy/launcher paths out of consumer copies.

**Verification:**
- [x] `python -m pytest -q tests/test_secretary_live_runtime.py tests/test_agent_profile_registry.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py` — 306 passed, 2 skipped.
- [x] `python scripts/validate_repo_config.py --repo-root . --starter-kit-manifest repo_config/starter-kit-manifest.json` — passed.
- Expected: retired aliases fail before provider dispatch, policy projections match, starter-kit boundaries remain correct, and documentation matches source behavior.

**Exit Criteria:**
- CGW remains absent from active maintained runtime selection and dispatch, while retirement guards and historical evidence remain intact and the operating contract is documented.

### Task 5: Final integration verification

**Purpose:**
- Prove the consolidated change set is internally consistent and ready for plan review or execution handoff.

**Task Function:**
- Run fresh cross-surface verification and reconcile the plan ledger with repository evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification is owned by the lead controller and requires repository-wide reconciliation after all implementation tasks.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: select an independent validator when the execution contract assigns one.

**Specification Coverage:**
- All implementation outcomes and completion criteria in this plan.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files listed in `targets`
- Modify: this plan's task ledger and evidence only after fresh verification
- Verify: repository diff, focused tests, validators, and active-surface audit output

**Dependencies:**
- Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: run the final declared verification commands, inspect diffs/status, and update this plan's ledger/evidence with immutable local results
- Stop for: failed required checks, stale generated surfaces, unresolved task scope, unexpected user changes, or any request to push/merge

**Steps:**
- [x] Step 1: Run the focused launcher and retirement test suites plus repository configuration validation.
- [x] Step 2: Run `git diff --check` and inspect `git status --short`; preserve pre-existing user artifacts and report unrelated modifications without rewriting them.
- [x] Step 3: Record exact commands and observed results in this plan; leave status `active` until `skill-verification-before-completion` authorizes final completion.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_agent_profile_registry.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py` — 356 passed.
- [x] `python scripts/validate_repo_config.py --repo-root . --starter-kit-manifest repo_config/starter-kit-manifest.json` — passed.
- [x] `git diff --check` — passed.
- Expected: all required tests and validators pass; no whitespace errors exist; no active CGW path or unexplained lifecycle regression remains.

**Exit Criteria:**
- Every required task has fresh proof, all scope deviations are recorded, and the plan is ready for the authorized Git finishing workflow.

## Verification

- `python -m pytest -q tests/test_herdr_main_launcher.py tests/test_agent_profile_registry.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py`
- `python scripts/validate_repo_config.py --repo-root . --starter-kit-manifest repo_config/starter-kit-manifest.json`
- `python -m pytest -q tests/test_herdr_main_launcher.py --durations=10`
- `git diff --check`
- Active-surface audit: `rg -n -i "cgw|chatgpt-web|providerAliases|retiredProviderIds" scripts tests repo_config docs agents --glob '!docs/superpowers/plans/**'`
- Policy parity: compare `repo_config/retired-model-policy.json` with `scripts/retired-model-policy.json` byte-for-byte.
- Preserve and report pre-existing modified/untracked files; do not use cleanup commands against them.

## Evidence

- GPT-5.6-Sol identified fixed 100 ms DeepAgents receipt polling, repeated pane inspection, redundant outcome-classification branches, and a large interleaved dispatch state machine as operational overhead risks.
- GPT-6 identified premature submission-gate ownership, fresh Codex ownership release before startup confirmation/first prompt, resource consumption before admission rejection, delivery/execution conflation, a broad one-second allocation reserve, repeated snapshot scans, and stale-idle mutation outside verified ownership as lifecycle risks.
- Source inspection confirms `_run_with_pane_ownership` currently scopes only its callback/command; fresh Codex confirmation and first prompt occur later in `scripts/herdr_main_launcher.py`.
- Source inspection and focused tests confirm admission claims persist as `phase=admission`, promotion to `phase=delivery` occurs only after pane ownership/context verification, and Secretary probes promote the gate immediately before launching Herdr.
- Source inspection confirms fresh Codex startup, startup confirmation, and first prompt submission now execute inside one pane-ownership callback; the outer path reuses those results and does not confirm or submit a second time.
- The classifier simplification was intentionally narrowed: the `receipt_confirmed` branch remains because existing zero-exit failed-report and missing-managed-result tests prove it is reachable and required for `task_result_unverified` precedence.
- Deterministic monitoring tests confirm receipt backoff begins at 100 ms, advances to 250 ms, caps at 500 ms, and performs a final receipt read when the grace deadline is reached exactly.
- Final verification: launcher/retirement suite `356 passed`; launcher duration suite `274 passed in 1.82s`; Secretary/gate/configuration suite `306 passed, 2 skipped`; repository config validation passed; `git diff --check` passed; policy projections are identical.
- Source inspection confirms `_resolve_target_selector` already records candidate-local rejection and has a replacement-allocation path; the plan preserves that behavior and adds regression proof rather than adding another allocator.
- CGW audit confirms maintained executable/configuration paths are retired; policy aliases, rejection text, regression tests, and historical plans remain intentional.

## Completion Criteria

The plan is ready for completion verification when:

1. logical admission prevents duplicate assignments before expensive resource use;
2. pre-dispatch failures settle as `not_delivered`, post-dispatch ambiguity remains `delivery_uncertain`, and confirmed delivery is not rewritten by worker execution failure;
3. fresh Codex startup, identity confirmation, and first prompt are serialized by pane ownership;
4. stale-idle mutation is lock-protected and `auto/auto` incompatible candidates still reach safe replacement allocation;
5. receipt polling, snapshot scanning, candidate inspection, and allocation timing remain bounded with lower redundant work and no new coordinator/state store;
6. CGW remains absent from active maintained runtime selection and dispatch while retirement guards and historical evidence remain intact;
7. policy projections, documentation, tests, starter-kit/deployment boundaries, and validators agree;
8. fresh final verification passes and the plan records exact evidence without altering unrelated user work.

The plan may be marked `completed` only after `skill-verification-before-completion` returns `verified`; until then it remains `proposed` or `active` according to the approved execution workflow.
