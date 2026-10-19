---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: native-semantic-contract-freeze-follow-up
parent_spec: none
targets:
  - scripts/secretary_live_runtime.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-19-19-28-native-semantic-contract-freeze-follow-up-plan.md
---

# Native Semantic Contract Freeze Follow-up

## Goal

Deliver one final narrow correctness and reliability follow-up after PR #109,
then freeze the current v3 semantic contracts. The change must prevent valid
native sidecars from authorizing reconciliation over unrelated invocation
output, make native-sidecar discovery bounded and fail-closed, and tighten the
existing Herdr freshness fallback without adding a new integration layer.

The governing invariant is:

> Capture authoritative child identity at the owning boundary as soon as it is
> available, carry that identity forward, and never rediscover it downstream
> unless no authoritative identity exists.

## Review Basis

The supplied recommendation is implementation-ready after four scope clarifications:

- Existing invocation output must be independently attributable before a
  verified v3 sidecar triplet can reconcile. Sidecar validity alone never grants
  write authority over output bytes.
- Herdr pane snapshots remain bounded diagnostic fallback when no trustworthy
  native identity or valid completion counter exists. They are removed from the
  attribution/authority path when a valid start boundary is present; no new
  Herdr or LightRSI API is introduced.
- Output attribution must name the current output projection's authoritative
  attempt evidence, especially the `preflight` attempt binding and lifecycle
  retirement evidence, without adding another output schema.
- Native evidence discovery must expose an explicit absent/present/uncertain
  state contract, and bounded-read guarantees must be limited to detectable
  replacement, metadata, or size changes on the opened descriptor.

Current repository evidence at `61e1983` confirms the named owners exist:

- `_reconcile_native_artifacts()` validates the v3 triplet but currently uses
  `_existing_output_matches_current_identity()` only for prior retirement
  reuse, not as a reconciliation prerequisite.
- `_discover_native_logical_operation()` uses `is_file()` and unrestricted
  `read_text()` before bounded namespace handling.
- `_observe_submitted_codex()` treats the presence of
  `pre_submit_completion_seq` as a boundary even when its value is `None`, and
  `_submission_freshness_proven()` currently accepts a first post-submit
  sequence after a null baseline.
- Existing direct-native execution, the three v3 artifacts, v1/v2 readers,
  Herdr transport ownership, LightRSI independence, and CoS acceptance remain
  outside this follow-up's redesign scope.

## Implementation Outcomes

### Output ownership is authoritative during reconciliation

Complete-current reconciliation requires either an absent invocation output or
an existing output whose top-level `logical_operation_id` and
`request_fingerprint` match the current request. The current output
projection's authoritative writer evidence must also be used where present or
required: the `preflight.attempt_id` binding and the lifecycle retirement
evidence under `preflight.retirement` must agree with the current sidecar
attempt and native identity. This reuses the existing projection and does not
add another output schema. Missing, conflicting, malformed, or unrelated
output identity returns `NATIVE_RESULT_CONFLICT`, preserves all output and
sidecar bytes, and never starts Codex or writes a reconstructed result.

### Native evidence discovery is bounded and fail-closed

Logical-operation discovery reads only supported regular files through the
existing bounded local-file safety primitive, does not follow symlinks, reads
no more than `NATIVE_RESULT_MAX_BYTES + 1`, verifies object identity across the
read, and treats special, oversized, replaced, unreadable, or malformed
evidence as conflict. Its state contract is explicit: `lstat` raising
`FileNotFoundError` means `ABSENT`; otherwise the bounded regular-file reader
is invoked; successful bytes mean `PRESENT`; and an existing path whose read
fails means `UNCERTAIN`. A path disappearing between `lstat` and open remains
`UNCERTAIN`, not `ABSENT`. The guarantee covers detectable replacement,
metadata, or size changes on the opened descriptor and does not promise
detection of same-inode concurrent byte mutation. Missing evidence remains
distinguishable from uncertain evidence so absent sidecars do not become false
conflicts.

### Herdr freshness has an honest fallback boundary

Only a non-boolean, non-negative integer pre-submit completion sequence counts
as a sequence baseline, and only a strictly newer post-submit integer proves
freshness; a missing or invalid value disables sequence-based freshness rather
than proving it. A valid native session/thread/cursor, if the existing start
boundary exposes one, remains authoritative and dominates pane evidence.
Because `run_probe()` captures the pre-submit pane snapshot before the launcher
returns the completion sequence, this follow-up does not attempt to conditionally
remove that read. Bounded pane evidence remains diagnostic fallback only and
cannot become semantic authority.

### Contracts and documentation remain frozen

The three v3 artifacts remain separate and unchanged in schema. Historical
v1/v2 readers remain read-only. No v4, registry, daemon, retry service,
additional observer, LightRSI semantic API, latest-session lookup, or new
upstream dependency is introduced. Runtime documentation describes the final
authority boundaries and the four-state recovery model.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared source, tests, and runtime documentation; run declared tests, validators, diff checks, and bounded local runtime probes without authentication or external writes
- User-approval actions: push, merge, pull request, external LightRSI changes, new provider/API integration, destructive cleanup, discard, or scope expansion
- Parallel ownership: none; tasks share recovery and observation semantics and must remain sequential
- Sequential fallback: execute Tasks 1 through 4 in order; stop if an upstream capability, schema change, or authority decision is required

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `61e1983147cd34846fdb759a644c15f6bca4cc89`
- Expected workspace: `current with preserved untracked plan documents`
- Next action: update runtime documentation and run final verification for Task 4
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | completed | current | codex | none | output attribution and no-write reconciliation tests | `37 passed, 1 skipped` |
| Task 2 | completed | current | codex | Task 1 | bounded native discovery and uncertainty tests | `61 passed, 1 skipped` |
| Task 3 | completed | current | codex | Task 2 | freshness-boundary and diagnostic-fallback tests | `105 passed, 1 skipped` |
| Task 4 | active | current | codex | Task 3 | validators, full suite, and bounded native recovery proof | direct-native proof passed; repository-wide validator remains blocked by preserved unrelated plan |

Allowed states are pending, active, blocked, and completed. One lead controller
owns this ledger and all task-state transitions.

## Task Breakdown

### Task 1: Make existing output identity a reconciliation prerequisite

**Purpose:**
- Prevent a valid current v3 binding/submission/result set from replacing an unrelated invocation output.

**Task Function:**
- Harden the existing reconciliation state machine at the narrowest shared owner and preserve the four-state model.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-impact state-machine correctness with a small, well-bounded code surface.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns sequential backend proof.

**Specification Coverage:**
- Sidecar validity never grants output ownership; only `EMPTY` or independently attributable current output may reconcile; incomplete and foreign evidence remain non-retryable and read-only.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_existing_output_matches_current_identity`
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Inspect: `scripts/secretary_live_runtime.py:_apply_native_retirement_evidence`
- Modify: `scripts/secretary_live_runtime.py:_existing_output_matches_current_identity`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Verify: `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Current v3 validators and sidecar relationships remain unchanged.

**Authority:**
- Preauthorized local actions: edit the named runtime symbols and their focused regressions; run focused tests.
- Stop for: schema migration, new ownership record, retry behavior, unrelated output format changes, or external writes.

**Steps:**
- [x] Step 1: Define the existing-output attribution contract against the current projection: absent output is allowed; present output must match top-level `logical_operation_id` and `request_fingerprint`; the current writer's authoritative attempt evidence is read from `preflight.attempt_id` and, where present or required, `preflight.retirement`; no second output schema is introduced.
- [x] Step 2: Make `_reconcile_native_artifacts()` reject missing, conflicting, malformed, or unrelated output identity before reconstructing a result; preserve every existing byte and avoid Codex client construction/start.
- [x] Step 3: Add ordinary and `resume=True` regressions for valid sidecars plus unrelated output, missing output identity, conflicting fingerprint/operation, conflicting attempt, and matching output identity; assert no write and no native start on rejection.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "reconcile or resume or output or identity"`
- Expected: unrelated or insufficiently attributed output returns `NATIVE_RESULT_CONFLICT`, remains byte-for-byte unchanged, and never starts a native client; matching output still reconciles without a new turn.

**Exit Criteria:**
- Reconciliation cannot replace present output unless its identity is independently attributable to the exact current operation and request.

### Task 2: Bound native logical-operation discovery

**Purpose:**
- Prevent symlink following, unbounded reads, and path-replacement races while discovering an existing logical operation.

**Task Function:**
- Reuse the existing bounded regular-file reader and distinguish absent evidence from uncertain evidence before JSON parsing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: medium-risk local I/O hardening with deterministic failure-path tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns sequential backend proof.

**Specification Coverage:**
- Native-sidecar discovery is bounded, no-follow, identity-checked, and fail-closed; uncertainty never starts Codex.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_read_bounded_regular_file`
- Inspect: `scripts/secretary_live_runtime.py:_discover_native_logical_operation`
- Inspect: `scripts/project_os_runtime/secretary_results.py:NATIVE_RESULT_MAX_BYTES`
- Modify: `scripts/secretary_live_runtime.py:_discover_native_logical_operation`
- Verify: `tests/test_secretary_live_runtime.py`
- Verify: `tests/test_secretary_results.py`

**Dependencies:**
- Task 1 must preserve the same no-write and no-start conflict behavior.

**Authority:**
- Preauthorized local actions: edit the named discovery path and focused tests; run local validators and tests.
- Stop for: a new shared I/O framework, schema change, external dependency, or any fallback that follows uncertain evidence.

**Steps:**
- [x] Step 1: Replace `is_file()` plus unrestricted `read_text()` with the bounded state contract: `lstat` `FileNotFoundError` is `ABSENT`; otherwise invoke the bounded regular-file reader; successful bytes are `PRESENT`; existing-path reader failure is `UNCERTAIN`; a disappearance between `lstat` and open is still `UNCERTAIN`; enforce the native evidence byte limit.
- [x] Step 2: Preserve current v3-only operation discovery and conflicting-operation rejection; keep legacy evidence readable only through existing historical compatibility paths.
- [x] Step 3: Add regressions for symlink, oversized, special-file, malformed, changed-during-read, disappearance between `lstat` and open, and absent sidecars; assert uncertain evidence returns conflict and no Codex start. Prove detectable replacement, metadata, and size changes on the opened descriptor without promising detection of same-inode concurrent byte mutation.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "native or discovery or sidecar or bounded or symlink or malformed"`
- Expected: absent evidence remains skippable, valid bounded regular evidence discovers one operation, and all uncertain evidence fails closed without a native launch.

**Exit Criteria:**
- Discovery never follows or unboundedly reads an uncertain sidecar and cannot authorize a new execution from uncertain evidence.

### Task 3: Tighten Herdr freshness and preserve diagnostic fallback

**Purpose:**
- Ensure completion freshness is proven only from a real start boundary while keeping native identity capability-gated.

**Task Function:**
- Correct the existing completion-sequence predicate while preserving the pre-submit pane read as bounded diagnostic evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded observation semantics with compatibility fallback and broad existing test coverage.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns sequential backend proof.

**Specification Coverage:**
- Valid integer pre-submit sequence plus strictly newer post-submit sequence proves freshness; invalid/missing baseline does not; pane snapshots remain diagnostic only; native identity wins when exposed.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Inspect: `scripts/secretary_live_runtime.py:_submission_freshness_proven`
- Inspect: `scripts/secretary_live_runtime.py:_capture_submission_anchor`
- Inspect: `scripts/secretary_live_runtime.py:run_probe`
- Modify: `scripts/secretary_live_runtime.py:_observe_submitted_codex`
- Modify: `scripts/secretary_live_runtime.py:_submission_freshness_proven`
- Inspect: `scripts/secretary_live_runtime.py:run_probe`
- Verify: `tests/test_secretary_live_runtime.py`
- Verify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Tasks 1 and 2 must be complete; no upstream native identity capability is assumed.

**Authority:**
- Preauthorized local actions: edit the named observation path and focused regressions; inspect existing Herdr output; run local tests.
- Stop for: new Herdr/LightRSI APIs, latest-session lookup, semantic authority from pane text, or blocking normal execution on optional identity enrichment.

**Steps:**
- [x] Step 1: Accept `pre_submit_completion_seq` as a baseline only when `type(value) is int` and `value >= 0`; do not treat `None`, booleans, or malformed values as captured boundaries.
- [x] Step 2: Require a strictly newer integer post-submit sequence for sequence-based freshness; update the null-baseline regression to remain false and preserve existing structured/native identity checks.
- [x] Step 3: Do not attempt to conditionally eliminate the pre-submit pane read: `run_probe()` captures it before the launcher returns the completion sequence. Fix only freshness semantics so a valid completion counter or native identity dominates pane evidence; retain the bounded pane snapshot as diagnostic/fallback evidence, and keep semantic acceptance unavailable without stronger evidence.
- [x] Step 4: Record only the optional lack of trusted Herdr pre-prompt native session/thread/cursor identity as a non-blocking capability deferral when the current interface does not expose it; do not add discovery, a Herdr/LightRSI interface redesign, or new integration.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py -k "freshness or completion or anchor or observation or native"`
- Expected: null/invalid baselines never prove freshness; valid counters require strict advancement; valid native identity remains authoritative; pane evidence is never promoted to semantic authority.

**Exit Criteria:**
- Herdr observation reports only evidence justified by a real start boundary and preserves the bounded fallback without changing normal native Secretary authority.

### Task 4: Reconcile contracts, documentation, and final proof

**Purpose:**
- Freeze the v3 semantic architecture after fresh source, test, validator, and bounded runtime evidence agree.

**Task Function:**
- Run final backend verification, update maintained runtime documentation, and record any immutable capability deferral.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final cross-surface verification and plan reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns final acceptance evidence.

**Specification Coverage:**
- No v3 schema churn; no new recovery machinery; native child, Project OS, Herdr, LightRSI, and CoS retain their existing authority boundaries.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: focused runtime, result, and Herdr tests
- Verify: one bounded direct-native run followed by same-output invocation without `--resume`

**Dependencies:**
- Tasks 1 through 3 completed with accepted proof and no scope deviation.

**Authority:**
- Preauthorized local actions: update named runtime documentation, run declared validators, focused tests, full pytest, diff checks, and one bounded local native probe.
- Stop for: failed required checks, missing direct-native capability, schema migration, external writes, or unverified retirement.

**Steps:**
- [x] Step 1: Update runtime documentation to state the output-attribution prerequisite, bounded sidecar discovery, valid-counter freshness rule, and diagnostic-only pane fallback.
- [ ] Step 2: Run focused tests, repository validators, full pytest, and `git diff --check`.
- [x] Step 3: Run one bounded native Secretary invocation followed immediately by the same output without `--resume`; prove one v3 binding/submission/result chain, exact identity, read-back, retirement, and no duplicate turn.
- [ ] Step 4: Apply `skill-verification-before-completion`; leave the plan proposed until fresh evidence returns `verified`.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py` — 444 passed, 2 skipped.
- [ ] `py -B scripts/validate_repo_contracts.py --repo-root .` — blocked by preserved unrelated `docs/superpowers/plans/2026-10-19-21-25-9router-codex-opaque-relay-plan.md` with an invalid Task 1 executor field.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-19-28-native-semantic-contract-freeze-follow-up-plan.md` — passed.
- [ ] `py -B -m pytest -q` — 1485 passed, 4 skipped, 1 failed because the repository validator test sees the same preserved unrelated plan.
- [x] `git diff --check` — passed.
- [x] One bounded direct-native Secretary invocation followed by same-output recovery without `--resume` — same operation, fingerprint, attempt, turn, result reference, retired lifecycle, and `reconciled: true`.
- Expected: all required local behavior and direct-native proof pass; the only remaining failure is the immutable repository-wide validator blocker from the preserved unrelated plan, with no synthetic success.

**Exit Criteria:**
- Source, tests, documentation, validators, and direct runtime evidence agree; every required proof passes; only the explicitly optional Herdr pre-prompt identity enrichment may remain deferred; v3 contracts are eligible for freeze and separate Git disposition.

## Verification

- `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-19-28-native-semantic-contract-freeze-follow-up-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One bounded direct-native Secretary run followed by same-output recovery without `--resume`, with exact v3 identity and retirement evidence.

## Completion Criteria

The plan is ready for completion verification when:

1. Present invocation output cannot be replaced or bypassed by valid sidecars unless its current identity is independently proven.
2. Native logical-operation discovery distinguishes absent evidence from uncertain evidence and never follows or unboundedly reads uncertain files.
3. Only valid integer completion baselines and exact native identity can prove freshness; pane text remains diagnostic fallback only.
4. The four-state recovery model, three v3 artifacts, historical read-only compatibility, and authority boundaries remain intact.
5. No v4, registry, daemon, retry policy, observer, latest-session lookup, LightRSI semantic API, or new upstream dependency is introduced.
6. Focused tests, repository validators, full tests, diff checks, and the direct-native no-`--resume` recovery proof all pass; only optional Herdr pre-prompt native session/thread/cursor enrichment may remain deferred when the current interface does not expose it.

The final acceptance invariant is:

> Existing bytes are never writable merely because valid sidecars exist;
> existing evidence is never trusted through an unbounded or ambiguous read;
> and completion freshness is never inferred without a real pre-submit
> boundary.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` with fresh evidence.
Branch creation, commit, push, pull request, merge, and cleanup remain separate
authorized Git actions.
