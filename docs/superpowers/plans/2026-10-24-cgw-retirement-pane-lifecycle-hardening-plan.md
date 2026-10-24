---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cgw-retirement-pane-lifecycle-hardening
targets:
  - scripts/herdr_main_launcher.py
  - scripts/agent_profile_registry.py
  - tests/test_herdr_main_launcher.py
  - tests/test_agent_profile_registry.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
---

# CGW Retirement And Pane Lifecycle Hardening

## Goal

Complete the validated hardening needed after the dual-model review of
`main@e830cc3531ec68f866aa3c78261f9b8f536a177e`: preserve CGW retirement as a
fail-closed policy boundary while making automatic pane selection reliable,
non-mutating in dry runs, safe under concurrent dispatch, and bounded under
slow Herdr responses.

The central behavioral correction is to distinguish recoverable candidate-local
inspection failures from global discovery failures. A pane with an incompatible
context must be rejected and allow allocation to continue; malformed or
partially unavailable evidence that is isolated to that candidate must not
prevent the authorized replacement-pane fallback. A valid session-wide agent
listing may expose pane-specific evidence that is rejectable, but failure of
the session-wide listing command, timeout, or envelope remains a global
identity failure. Global workspace identity, transport integrity, and
ownership failures remain fail-closed.

## Implementation Outcomes

### Reliable automatic pane fallback

`--session auto --pane auto` continues past safely isolated candidate-local
agent/process inspection failures, records rejection evidence, and allocates a
replacement pane when no eligible candidate remains. Global snapshot and
workspace-identity failures still produce structured fail-closed resolution
errors. Named-session discovery preserves the same allocation reserve as
snapshot discovery.

### Safe launch lifecycle

Dry runs do not split panes or release stale agents. Codex logical operations
claim their submission gate before prompt delivery. Reused panes retain a short
exclusive dispatch lease through final validation and prompt submission, while
full model execution remains unlocked. Concurrent auto-allocation performs a
short recheck-and-split transition under a session/workspace lock.

### Stable context and error contracts

Collision recovery preserves the final context marker, verified-start retries
retain profile and context constraints, and malformed retirement policy data
becomes structured `LaunchBlocked` evidence rather than a raw traceback. CGW
identifiers remain in retirement policy and regression evidence intentionally;
no executable CGW path or new lifecycle service is introduced.

### Measurement-led efficiency

The implementation removes only proven redundant inspection and indexes snapshot
metadata only if focused measurements show material cost. Existing performance
evidence remains the source for reserve and subprocess decisions; no speculative
retry framework, persistent pane registry, or scheduler is added.

## Evidence And Validated Scope

- Repository: `longdang193/project-OS-starter`.
- Reviewed revision: `e830cc3531ec68f866aa3c78261f9b8f536a177e` on `main`.
- Primary source: `scripts/herdr_main_launcher.py`.
- Models: `GPT-5.6-Sol / High` and `GPT-6 / High`, both completed read-only reviews.
- CGW result: executable and selectable CGW paths are retired; policy/test/history
  identifiers remain intentionally for rejection and regression proof.
- Validated defects: candidate-local failure classification, dry-run mutation,
  Codex gate admission, reused-pane ownership, duplicate allocation, context
  marker loss, retry constraint loss, named-session reserve loss, and retirement
  policy error normalization.
- Conditional optimizations: duplicate pane inspection and snapshot indexing;
  implement only after baseline measurement confirms material cost.
- Post-review corrections: allocation readiness now remains lock-held, refresh
  snapshots reuse the initial global validation contract, allocation lock
  contention waits within the existing reserve, dry-run suppresses stale-agent
  release, and lock-held dispatch selects the verified start/reuse action.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, tests, and runtime documentation; run focused tests, repository validators, and bounded mocked lifecycle/performance probes; preserve existing untracked artifacts
- User-approval actions: commits, pushes, merges, live authentication, external configuration writes, destructive cleanup, and edits outside listed targets
- Parallel ownership: none; target resolution, dispatch ownership, retry semantics, and shared tests use overlapping launcher contracts
- Sequential fallback: establish failing regression tests, implement target-resolution boundaries, implement dispatch lifecycle fixes, implement retry/error-contract fixes, measure optimization candidates, then run final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-pane-lifecycle-plan-review`
- Base commit: `e830cc3531ec68f866aa3c78261f9b8f536a177e`
- Expected workspace: preserve existing untracked `.playwright-mcp/`, `.runtime/`, and `node_modules/`; do not stage or rewrite them
- Next action: none; execution is complete and Git disposition remains approval-gated
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused failing tests and baseline | 297 focused tests pass; new regressions initially failed before implementation |
| Task 2 | `completed` | current | `codex` | Task 1 | candidate fallback, reserve, and allocation concurrency tests | candidate rejection, named reserve, lock recheck, and global failure tests pass |
| Task 3 | `completed` | current | `codex` | Task 1 | dry-run, gate, and dispatch-ownership tests | dry-run proposal and lock-held callback tests pass; Codex gate claim is identity-gated |
| Task 4 | `completed` | current | `codex` | Task 1 | retry, marker, and structured-policy-error tests | marker, retry constraint plumbing, and RuntimeError normalization are covered |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | measured inspection/allocation baseline and targeted optimization proof | no speculative optimization merged; existing performance evidence retained and lock/recheck bounded |
| Task 6 | `completed` | current | `codex` | Tasks 2–5 | docs, focused suite, validators, and final diff proof | 300 tests pass; planning, contract, config, runtime-drift, adapter-sync, compile, and diff checks pass; post-review race and dry-run fixes covered |

## Task Breakdown

### Task 1: Establish contracts and regression tests

**Purpose:**
- Convert the dual-review findings into executable acceptance cases before source
  changes.
- Preserve the distinction between candidate rejection and global resolution
  failure.

**Task Function:**
- Add focused tests in `tests/test_herdr_main_launcher.py` and
  `tests/test_agent_profile_registry.py` using the existing mocked Herdr and
  launcher seams.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded test-first work with source-authoritative contracts.

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_resolve_target_selector`, `_herdr_pane`, `_agent_for_pane`, `_run_with_pane_ownership`, `_main_body`, `_unique_agent_name`.
- Inspect: `scripts/agent_profile_registry.py:_load_retirement_policy`, `load_agent_profiles`.
- Modify: `tests/test_herdr_main_launcher.py`, `tests/test_agent_profile_registry.py`.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: add tests and run the focused launcher/profile-registry tests.
- Stop for: contradictory source contracts, unrelated tracked changes, live runtime mutation, or any need to edit outside the listed test files.

**Steps:**
- [x] Add a candidate-local pane-agent evidence failure case after a valid
  session-wide agent response, with another matching pane having an
  incompatible context; assert the selector reaches allocation and returns a
  validated new pane.
- [x] Retain the existing candidate-local process-info invalid-envelope and
  timeout coverage; do not add a general process-info rewrite unless a new
  focused regression identifies a distinct gap.
- [x] Add global snapshot identity corruption and session-wide agent-list
  command/timeout/envelope failure cases; assert each remains fail-closed as
  structured target-resolution evidence.
- [x] Add slow named-session pane-list coverage proving the allocation reserve
  is preserved.
- [x] Add dry-run auto-resolution coverage proving no split and no stale-agent
  release occur.
- [x] Add Codex logical-operation gate coverage, reused-pane dispatch ownership
  coverage, and concurrent allocation coverage.
- [x] Add collision-marker, verified-retry constraint, and malformed-retirement
  policy coverage.
- [x] Add launcher-level retired-provider/model alias coverage proving rejection
  occurs before executable lookup, identity discovery, pane locking, or
  dispatch; retain the narrower registry alias tests as-is.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_agent_profile_registry.py -q` passes with the implemented contracts; the pre-implementation mismatch is recorded in the task evidence.

**Exit Criteria:**
- Every validated defect has a focused regression case with an explicit expected
  side effect or failure classification.

### Task 2: Repair candidate classification, deadlines, and allocation ownership

**Purpose:**
- Make incompatible or locally malformed candidates rejectable without
  blocking safe replacement-pane allocation.
- Prevent slow discovery and concurrent launches from defeating allocation.

**Task Function:**
- Implement the smallest typed boundary changes in the launcher; do not catch
  all exceptions indiscriminately.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded launcher changes with explicit fail-closed ownership.

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_candidate_json_command`, `_agent_for_pane`, `_herdr_pane`, `_inspect_auto_candidate`, `_resolve_target_selector`.
- Add or reuse: a short session/workspace allocation lock helper adjacent to the
  existing pane lock helpers.
- Modify: `tests/test_herdr_main_launcher.py` cases from Task 1.

**Dependencies:**
- Task 1 regression tests exist.

**Authority:**
- Preauthorized local actions: edit the listed launcher symbols and their focused tests; run mocked lifecycle tests.
- Stop for: a proposed catch-all that would swallow global identity failure, a new persistent registry/scheduler, or any external Herdr mutation outside bounded tests.

**Steps:**
- [x] Convert only pane-attributable agent evidence and candidate-local
  transport/envelope failures, after a valid session-wide response, into
  `TargetCandidateRejected` with rejection evidence. Preserve the existing
  `_candidate_json_command` process-info behavior unless a new focused test
  proves a distinct gap.
- [x] Keep session-wide agent-list command, timeout, and envelope failures,
  malformed current-workspace snapshot identity, unavailable global snapshot
  envelopes, and global transport failures as `TargetResolutionBlocked` with
  `global_identity` or the established global failure kind.
- [x] Apply the candidate deadline minus `_TARGET_ALLOCATION_RESERVE_SECONDS`
  to named-session pane listing as well as global snapshot discovery.
- [x] Protect the allocation transition and action selection with a keyed
  session/workspace lock: re-read or revalidate the current candidate set under
  the lock, then atomically choose a still-compatible reuse action, one split,
  or a re-resolution result before releasing the lock. Do not release after a
  recheck while dispatch still holds a stale precomputed action.
- [x] Preserve partial-allocation evidence and validate the returned pane before
  selecting it; do not retry an uncertain split blindly.

**Verification:**
- [x] Candidate-local failure still reaches allocation and returns a validated
  pane.
- [x] Global identity corruption remains fail-closed.
- [x] Named-session slow-list test leaves the allocation reserve intact.
- [x] Concurrent allocation tests prove that the same session/workspace
  transition does not duplicate a split, that a changed pane state cannot cause
  a stale action to dispatch, and that genuinely incompatible contexts may
  allocate distinct panes with safe ownership.
- [x] The Task 2-owned candidate-classification, deadline, allocation, and race
  tests pass alongside the later lifecycle regressions.

**Exit Criteria:**
- The original `--session auto --pane auto` bottleneck is corrected without
  weakening global fail-closed safety or adding a second lifecycle authority.

### Task 3: Repair dry-run, submission gating, and reused-pane ownership

**Purpose:**
- Make dry-run truthful and serialize only the short dispatch boundary needed for
  Codex safety and deduplication.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded lifecycle changes with direct mocked dispatch proof.

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_main_body`, `resolve_launch`, `_run_with_pane_ownership`, Codex prompt-submission branch around `claim_model_submission` and `_submit_codex_prompt`.
- Modify: `tests/test_herdr_main_launcher.py`.
- Update: `docs/operating_system/runtime/runtime-surfaces.md` if it documents
  dry-run or dispatch ownership semantics.

**Dependencies:**
- Task 1 tests; Task 2 target-resolution contract.

**Authority:**
- Preauthorized local actions: edit listed launcher/docs/test surfaces and run focused mocked dispatch tests.
- Stop for: holding a pane lock across full model execution, changing delivery settlement semantics, or modifying unrelated lifecycle authorities.

**Steps:**
- [x] Separate dry-run target proposal from mutating split/stale-agent release;
  dry-run must not create, release, or otherwise mutate Herdr state. When
  allocation would be required, return explicit `allocation.status =
  "would_allocate"` evidence with no fabricated pane ID and no executable
  command, and short-circuit real-pane preparation.
- [x] Claim the submission gate for Codex when a logical operation identity is
  present, before `_submit_codex_prompt`, and preserve existing uncertain/
  acknowledged settlement states.
- [x] Keep a short exclusive dispatch lease from final reuse validation through
  prompt submission; release it after the delivery boundary, not after model
  completion. The lease-held validation must choose the executable action, and
  dispatch must execute that returned action rather than a stale command built
  before the lease.
- [x] Preserve final pane/process/context validation immediately before dispatch
  and re-resolve when the state changed. Same-context concurrent launches may
  converge on one safely reused pane; incompatible contexts may allocate
  separately.

**Verification:**
- [x] Dry-run auto path has no split/release side effect.
- [x] Two Codex launches with one logical operation produce one gate claim and
  one admitted prompt submission.
- [x] Concurrent compatible reuse cannot submit to the same pane concurrently.
- [x] A race that changes a pane from empty to reusable between resolution and
  dispatch never issues a duplicate agent start from stale resolution evidence.
- [x] Delivery timeout remains `delivery_uncertain` and is not replayed without
  reconciliation.
- [x] The Task 3-owned dry-run, gate, ownership, and race tests pass alongside
  the collision, retry, and policy regressions.

**Exit Criteria:**
- Dry-run is non-mutating and Codex dispatch is deduplicated and ownership-safe
  without serializing full model execution.

### Task 4: Preserve context identity and normalize policy errors

**Purpose:**
- Prevent collision and retry paths from silently degrading pane reuse or error
  contracts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow identity and error-contract preservation.

**Files And Symbols:**
- Modify: `scripts/herdr_main_launcher.py:_unique_agent_name`, verified-start retry branch around `_resolve_target_selector`, `_herdr_pane`, and `_profile`.
- Inspect: `scripts/agent_profile_registry.py` and its tests for the existing
  `RuntimeError` contract; do not modify the registry or move retirement policy
  ownership for this defect.
- Modify: `tests/test_herdr_main_launcher.py`, `tests/test_agent_profile_registry.py`.

**Dependencies:**
- Task 1 tests; Task 2 context and candidate contracts.

**Authority:**
- Preauthorized local actions: edit listed identity/error-boundary symbols and focused tests.
- Stop for: changing retirement policy contents, deleting rejection evidence, or weakening fail-closed admission.

**Steps:**
- [x] Preserve the `-ctx-<hash>` marker as the final suffix when adding a
  uniqueness component after an agent-name collision.
- [x] Pass the existing dispatch profile and context identity into verified-start
  retry resolution and follow-up pane validation.
- [x] Translate `RuntimeError` raised by retirement-policy loading into the
  launcher’s structured `LaunchBlocked` contract at `_profile`; leave
  `_load_retirement_policy` and its registry tests unchanged.
- [x] Keep CGW aliases rejected before executable lookup, Git identity, Herdr
  discovery, pane locking, or dispatch.

**Verification:**
- [x] Collision recovery followed by same-context launch reuses the recovered
  agent when safe.
- [x] Verified-start retry preserves profile/context constraints.
- [x] Malformed retirement policy emits structured launcher failure evidence,
  not a traceback.
- [x] Retired provider/model aliases remain rejected before side effects.
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_agent_profile_registry.py -q` passes.

**Exit Criteria:**
- Context identity remains stable across collision/retry paths and policy failures
  preserve the established structured fail-closed contract.

### Task 5: Measure and apply only justified efficiency improvements

**Purpose:**
- Reduce unnecessary Herdr work without weakening freshness, ownership, or
  final validation.

**Task Function:**
- Establish a before/after baseline using existing performance evidence and
  bounded mocked workloads before changing data flow.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: measurement-gated optimization with bounded scope.

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`, `_resolve_target_selector`, `_herdr_pane`, existing performance evidence helpers.
- Modify only if justified: launcher inspection-state handoff and snapshot
  indexing code; update focused performance tests.

**Dependencies:**
- Tasks 2–4 complete.

**Authority:**
- Preauthorized local actions: run bounded performance probes and make measured, local optimizations in the listed launcher/test symbols.
- Stop for: no material baseline, stale-state safety regression, or any proposal for a scheduler, persistent registry, broad retry framework, or speculative timeout change.

**Steps:**
- [x] Measure candidate counts, Herdr subprocess counts, discovery latency,
  split/readiness latency, and p95/p99 behavior for empty, incompatible, and
  reusable pane sets.
- [x] Remove the redundant middle pane inspection only if the discovered pane
  state can be carried into launch preparation and final lock-held validation
  remains intact.
- [x] If snapshot grouping is material, pre-index validated panes once by
  resolved CWD/workspace ID; otherwise record the optimization as intentionally
  deferred.
- [x] Keep the fixed reserve unchanged unless measured p95/p99 evidence supports
  a bounded adjustment; record the decision in the plan evidence.
- [x] Add explicit metrics for allocation attempts, allocation failures, and
  partial-allocation reconciliation if the existing evidence lacks them.

**Verification:**
- [x] Before/after results show no increase in stale-pane dispatch, duplicate
  allocation, or uncertain delivery.
- [x] Any shipped optimization reduces measured subprocess count or latency on a
  representative workload; otherwise no optimization code is merged.
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q` passes.

**Exit Criteria:**
- Efficiency changes are evidence-led, bounded, and simpler than the behavior
  they replace.

### Task 6: Documentation alignment and final verification

**Purpose:**
- Reconcile source, tests, docs, CGW retirement evidence, and final acceptance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final source/test/doc reconciliation and acceptance proof.

**Files And Symbols:**
- Update, only where semantics changed: `docs/operating_system/runtime/runtime-surfaces.md` and `docs/operating_system/procedures/runtime-adapter-procedure.md`.
- Inspect: retirement policy, maintained `agents/*.toml`, launcher, tests, and
  all task-owned diffs.

**Dependencies:**
- Tasks 2–5 complete.

**Authority:**
- Preauthorized local actions: run focused and broad validation, update listed runtime docs, inspect diff/status, and record evidence.
- Stop for: failed required proof, stale generated surfaces, unrelated tracked changes, commit, push, merge, or destructive cleanup.

**Steps:**
- [x] Document that dry-run is non-mutating, candidate-local failures are
  quarantined, global identity failures remain fail-closed, and allocation is
  bounded and reconciled.
- [x] Verify no active CGW launcher/provider/package/startup/overlay/port/receipt
  path was reintroduced; retain policy and regression identifiers.
- [x] Run focused tests, repository/config validators, and `git diff --check`.
- [x] Record measured performance decisions and any intentionally deferred
  optimization.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py tests/test_agent_profile_registry.py -q` (`297 passed`).
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`.
- [x] `py -3 scripts/validate_repo_config.py --repo-root .`.
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`.
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] `git diff --check`.
- [x] `git status --short --branch` confirms only intended tracked changes and
  preserves existing untracked artifacts.

**Exit Criteria:**
- Fresh proof supports every implementation outcome, docs match behavior, CGW
  remains executable-path retired, and the plan is ready for approval or
  execution handoff.

## Non-Goals

- No restoration, compatibility shim, or executable CGW path.
- No literal deletion of CGW identifiers from retirement policy, tests, or
  historical evidence that intentionally enforce rejection.
- No new scheduler, pane registry, lifecycle service, janitor, or coordination
  authority.
- No catch-all exception handling that converts global identity failures into
  candidate rejection.
- No broad timeout increase or automatic retry after uncertain ownership,
  delivery, or allocation state.
- No live authentication, external configuration writes, or production pane
  mutation as part of local verification.
- No changes to unrelated runtime, agent-profile, or generated surfaces.

## Verification

- Test-first proof for every validated defect.
- Direct mocked Herdr boundary proof for candidate rejection, fallback
  allocation, dry-run non-mutation, lock ownership, gate admission, timeout,
  malformed policy, collision recovery, and retry context.
- Performance evidence for any inspection or indexing optimization, including
  representative candidate counts and p95/p99 latency.
- Repository contract/config/runtime drift checks and `git diff --check`.
- Fresh status proof preserving `.playwright-mcp/`, `.runtime/`, and
  `node_modules/` as existing untracked artifacts.

## Completion Criteria

1. Incompatible contexts and isolated malformed candidates reach safe replacement
   allocation; global snapshot/identity failures remain fail-closed.
2. `--session auto --pane auto` and named-session `--pane auto` both preserve a
   bounded allocation reserve.
3. Dry-run produces no Herdr mutations.
4. Codex logical operations claim the submission gate before prompt delivery.
5. Reused panes remain exclusively owned through final validation and prompt
   submission, without locking full execution.
6. Concurrent auto-allocation does not duplicate splits for one session/workspace
   transition.
7. Collision and retry paths preserve profile/context identity.
8. Retirement-policy failures emit structured launcher evidence.
9. CGW remains rejected before runtime side effects and no active executable CGW
   path is present.
10. Any performance improvement is measured, documented, and regression-tested;
    speculative orchestration is not introduced.
11. Focused tests and required validators pass with fresh output.
12. No commit, push, merge, destructive cleanup, or unrelated change occurs
    without explicit authorization.
