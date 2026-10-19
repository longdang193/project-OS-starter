---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-contract-freeze-and-measurement
parent_spec: none
targets:
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - tests/test_herdr_main_launcher.py
  - tests/test_benchmark_completion_monitoring.py
  - scripts/benchmark_completion_monitoring.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-20-00-15-native-semantic-contract-freeze-and-measurement-plan.md
---

# Native Semantic Contract Freeze And Measurement

## Goal

Close the remaining current-v3 recovery ambiguity, make every current-v3
recovery read use one bounded regular-file policy, and establish a reproducible
measurement baseline before any latency optimization is considered. Preserve the
existing direct Secretary authority model, the four-state recovery model, the
three v3 artifacts, read-only v1/v2 compatibility, and the independence of
Herdr and LightRSI from normal semantic completion.

The governing invariant remains:

> Capture an authoritative fact at the boundary that owns it, carry it forward
> once, and never rediscover it downstream when the owning boundary already
> supplied it.

## Review Basis

The supplied recommendation is architecturally sound but needs the following
execution corrections before implementation:

- Existing-output attribution currently checks operation and fingerprint
  identity but permits a present output with no authoritative current-attempt
  binding. The plan therefore requires at least one current-writer binding
  from `preflight.attempt_id` or `preflight.retirement.attempt_id`, rejects
  missing or conflicting bindings without writing, and treats top-level
  `attempt_id` as a consistency check only.
- `parse_native_binding()`, `parse_native_submission()`, and
  `parse_native_result()` still perform `is_file()` plus `read_text()` reads.
  The live reconciliation path also rereads result and output paths. The plan
  makes live current-v3 reads bounded and avoids redundant rereads inside
  reconciliation once a parsed payload is available, while preserving the
  existing path-based compatibility readers.
- The bounded reader currently verifies path/device/inode identity but does not
  compare final descriptor metadata. The plan adds a second `fstat()` check for
  descriptor identity/type and size, uses only deliberately selected stable
  metadata if needed, and documents that same-inode byte mutation is not fully
  detectable.
- The recommendation calls performance work measurement-driven but does not
  define a workload, repetition count, metrics, or acceptance gate. The plan
  uses the existing Herdr completion-monitoring characterization harness with
  20 repetitions and records direct-native evidence as a correctness proof,
  not as a general Project OS latency benchmark. No optimization ships from
  baseline data alone.

## Scope Boundaries

This plan does not introduce a v4 schema, registry, daemon, retry service,
persistent or pooled app-server, latest-session discovery, Project-OS-specific
LightRSI API, new semantic observer, or background reconciler. It does not
remove `--resume`; that compatibility migration remains a separate future
change after caller inventory and approval. It does not change LightRSI lock or
tracing behavior, Herdr API shape, or CoS acceptance authority.

## Implementation Outcomes

### Existing output attribution is closed

A present invocation output may reconcile only when its logical operation and
request fingerprint match the current request, at least one current-writer
attempt binding exists in `preflight.attempt_id` or
`preflight.retirement.attempt_id`, and every present binding matches the exact
v3 sidecar attempt. A top-level `attempt_id`, when present, must agree with
the current-writer binding but cannot satisfy the minimum ownership proof.
Missing, malformed, foreign, or conflicting identity returns
`NATIVE_RESULT_CONFLICT`, preserves output and sidecar bytes, and never starts
Codex or writes a reconstructed result.

### Current-v3 evidence reads are bounded and non-redundant

The live current-v3 recovery path reads binding, submission, result, existing
output, and retirement evidence derived from that output through the existing
no-follow bounded regular-file reader. All current-v3 reads are bounded, and a
pathname is not redundantly reread inside live reconciliation once its parsed
payload is available. Existing v1/v2/legacy path-based readers remain
read-only compatibility surfaces and are not used to authorize current-v3
ownership when their evidence is historical.

### Measurement is characterization, not speculative optimization

A reproducible 20-repetition completion-monitoring baseline records diagnostic
subprocess totals, timeout counts, receipt checks, diagnostic probe counts, time
to receipt, receipt-to-return delay, and lifecycle/cleanup/reconciliation
mismatches. A direct-native same-output recovery proof records total invocation
identity, sidecar identity, read-back, retirement, and duplicate-turn absence
when Codex capability is available. Missing capability is recorded as blocked,
not converted into synthetic success.

### Runtime documentation and freeze rules align

The runtime surface documentation states the required attempt-binding rule,
the bounded-read guarantee and its limits, the preserved four-state model, the
read-only historical compatibility boundary, and the measurement gate for any
future optimization.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `optional worktree`; use a clean worktree from `origin/main` because the current checkout contains unrelated relay changes
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the named runtime, parser, tests, benchmark, documentation, and plan files; create a clean local worktree; run declared local tests, validators, benchmark characterization, diff checks, and bounded direct-native proof
- User-approval actions: push, merge, publication, external model/API calls beyond the bounded direct-native proof, destructive cleanup, and disposition of unrelated relay files
- Parallel ownership: `none`
- Sequential fallback: complete attribution before parser/read changes, complete read changes before documentation and baseline, then run final verification from the clean worktree

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-semantic-contract-freeze-and-measurement`
- Base commit: `649ac4364226fdad609914227e5e96035e4c1f06`
- Expected workspace: `clean dedicated worktree; preserve current checkout relay changes without staging or editing them`
- Next action: run final integrated verification from the clean worktree in Task 5
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | codex | none | attribution regressions and byte-preservation proof | `230 passed, 2 skipped` focused suite; current-writer binding regressions pass |
| Task 2 | `completed` | dedicated worktree | codex | Task 1 | bounded read, payload-reuse, and compatibility regressions | `230 passed, 2 skipped` focused suite; descriptor-size and v3-only validator regressions pass |
| Task 3 | `completed` | dedicated worktree | codex | Task 2 | runtime documentation and planning validators | `16 passed`; repository, planning, template, generated-surface, and contract validators passed |
| Task 4 | `completed` | dedicated worktree | codex | Task 3 | 20-repetition characterization baseline and direct-native proof or explicit capability block | `fake_boundary_observation`, 20 repetitions, zero lifecycle/cleanup/reconciliation mismatches; direct-native completed and reconciled with retired lifecycle and unchanged sidecars |
| Task 5 | `completed` | dedicated worktree | codex | Tasks 1-4 | focused suite, full suite, validators, and diff checks | `453 passed, 2 skipped` focused suite; `1492 passed, 4 skipped` full suite; repository, planning, template, and diff checks passed; direct-native proof completed |

One lead controller owns this ledger and all task-state transitions.

## Task Breakdown

### Task 1: Require authoritative attempt attribution

**Purpose:**
- Prevent valid v3 sidecars from authorizing reconciliation over an existing output that cannot be tied to the current writer attempt.

**Task Function:**
- Tighten the existing output ownership predicate without adding a schema or recovery state.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-impact state-machine correctness with a narrow shared owner and deterministic regressions.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns sequential backend proof.

**Specification Coverage:**
- `logical_operation_id` and `request_fingerprint` must match; at least one current-writer attempt binding from `preflight.attempt_id` or `preflight.retirement.attempt_id` must exist; every present binding must equal the current sidecar `attempt_id`; a top-level `attempt_id` is consistency-only; foreign or uncertain output remains read-only.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_existing_output_matches_current_identity`
- Inspect: `scripts/secretary_live_runtime.py:_retirement_identity_matches`
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Modify: `scripts/secretary_live_runtime.py:_existing_output_matches_current_identity`
- Modify: `tests/test_secretary_live_runtime.py` attribution and reconciliation cases
- Verify: `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Preserve `secretary-native-binding.v3`, `secretary-native-submission.v3`, and `secretary-native-result.v3` unchanged.

**Authority:**
- Preauthorized local actions: edit the named predicate and focused tests; run the focused runtime test selection.
- Stop for: schema migration, new ownership artifact, automatic resubmission, output-format redesign, or external writes.

**Steps:**
- [x] Step 1: Define `preflight.attempt_id` and `preflight.retirement.attempt_id` as the authoritative current-writer binding set; require at least one of those fields and require every one present to match the sidecar attempt. If top-level `attempt_id` is present, require it to agree but do not let it satisfy the minimum ownership proof.
- [x] Step 2: Keep exact logical-operation and request-fingerprint matching and reject malformed or non-mapping preflight/retirement evidence as foreign or uncertain.
- [x] Step 3: Add a regression with valid v3 sidecars and matching operation/fingerprint but no attempt binding; assert `NATIVE_RESULT_CONFLICT`, no native client start, no output write, and byte-for-byte preservation.
- [x] Step 4: Retain regressions for matching `preflight.attempt_id`, matching retirement-only attempt binding, a matching top-level `attempt_id` as a consistency check, conflicting bindings, and unrelated output identity.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "reconcile or resume or output or identity"`
- Expected: only absent output or independently attributable current output reconciles; every rejected output remains byte-for-byte unchanged.

**Exit Criteria:**
- Existing output cannot be reconciled solely because valid sidecars match operation and fingerprint.

### Task 2: Make current-v3 recovery reads bounded and non-redundant

**Purpose:**
- Eliminate unbounded or inconsistent current-v3 evidence reads while preserving historical compatibility.

**Task Function:**
- Route current-v3 reconciliation through bounded bytes and parsed payloads without creating a filesystem abstraction or changing v1/v2 semantics. Do not introduce a new evidence-snapshot carrier solely to enforce a global read-count slogan.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: medium-risk I/O and parser-boundary change with explicit race and compatibility tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns parser and runtime integration proof.

**Specification Coverage:**
- Existing regular files are read without symlink following, no more than `NATIVE_RESULT_MAX_BYTES + 1` bytes are consumed, replacement and observable descriptor changes fail closed, and live reconciliation does not reread a pathname once its parsed current-v3 payload is available.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_read_bounded_regular_file`
- Inspect: `scripts/secretary_live_runtime.py:_discover_native_logical_operation`
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Inspect: `scripts/project_os_runtime/secretary_results.py:parse_native_binding`
- Inspect: `scripts/project_os_runtime/secretary_results.py:parse_native_submission`
- Inspect: `scripts/project_os_runtime/secretary_results.py:parse_native_result`
- Modify: `scripts/secretary_live_runtime.py:_read_bounded_regular_file`, `_discover_native_logical_operation`, and `_reconcile_native_artifacts`
- Modify: `scripts/project_os_runtime/secretary_results.py` with payload-validation entry points that preserve existing path-based readers
- Modify: `tests/test_secretary_live_runtime.py` bounded-reader, payload-reuse, and reconciliation cases
- Modify: `tests/test_secretary_results.py` payload-validation and historical-reader compatibility cases
- Verify: `tests/test_secretary_live_runtime.py`, `tests/test_secretary_results.py`

**Dependencies:**
- Task 1 defines the output-attribution decision after parsing.
- Historical v1/v2/legacy readers remain read-only and continue accepting their existing supported inputs.

**Authority:**
- Preauthorized local actions: edit the bounded reader, current-v3 parser boundary, and named tests; run focused parser and runtime tests.
- Stop for: new schema versions, removal of historical readers, unbounded fallback reads, or a second filesystem abstraction.

**Steps:**
- [x] Step 1: Add narrow v3-only payload-validation entry points for binding, submission, and result objects so the live runtime can pass bounded decoded mappings without forcing a second pathname read; retain existing path-based APIs as v1/v2/legacy compatibility readers and do not let them authorize current-v3 ownership.
- [x] Step 2: Read current-v3 result, binding, submission, and existing output through `_read_bounded_regular_file`, decode each available payload once, and reuse those parsed mappings for reconciliation and retirement projection. Do not require a global once-per-invocation guarantee when discovery has already read a path before reconciliation.
- [x] Step 3: Extend `_read_bounded_regular_file` to perform a second `fstat()` and compare descriptor identity/type and size, plus only a deliberately selected stable timestamp field if a platform-safe same-size mutation check is required; use a final pathname `lstat()` to confirm the same regular object. Return uncertainty on mismatch while preserving the stated limit that same-inode byte mutation may escape detection.
- [x] Step 4: Add symlink, special-file, oversized, disappearance, replacement, descriptor-metadata-change, malformed, and reconciliation-reuse regressions; mock descriptor metadata deterministically rather than depending on filesystem timing, and assert historical v1/v2 readers remain read-only and unchanged.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py`
- Expected: all current-v3 evidence reads are bounded and non-redundant inside reconciliation; uncertain reads fail closed; historical readers retain their prior behavior.

**Exit Criteria:**
- No current-v3 reconciliation branch uses `Path.read_text()`, `Path.read_bytes()`, or an unbounded parser read for binding, submission, result, output, or retirement evidence; path-based compatibility readers remain available only for historical callers.

### Task 3: Align documentation and compatibility boundaries

**Purpose:**
- Make the maintained runtime contract state the implemented authority, bounded-read, recovery, and measurement rules without promising unsupported behavior.

**Task Function:**
- Update the canonical runtime surface documentation and verify the existing compatibility vocabulary remains non-authoritative.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low-risk canonical documentation update coupled to already-proven source behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: documentation and template validators provide sufficient proof.

**Specification Coverage:**
- Direct Secretary remains the normal semantic path; Herdr pane evidence remains diagnostic fallback; LightRSI remains independent; v1/v2 are read-only; `--resume` remains accepted but semantically inert.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md` native semantic, Herdr, and benchmark sections
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `tests/test_native_personal_local_workflow.py`, planning and template validators

**Dependencies:**
- Tasks 1 and 2 establish the source behavior and exact bounded-read limits.

**Authority:**
- Preauthorized local actions: update the named canonical runtime documentation and run documentation/planning validators.
- Stop for: generated-surface edits, new authority owners, or claims not backed by source or tests.

**Steps:**
- [x] Step 1: Document that `preflight.attempt_id` or `preflight.retirement.attempt_id` is required for current-writer ownership, that top-level `attempt_id` is consistency-only, and the distinction between absent, present, and uncertain current-v3 evidence.
- [x] Step 2: Document the final descriptor-check guarantee and explicitly exclude a guarantee against same-inode concurrent byte mutation.
- [x] Step 3: Document the preserved four-state model, read-only historical compatibility, inert `--resume` vocabulary, and no-optimization-without-baseline rule.

**Verification:**
- [x] `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-20-00-15-native-semantic-contract-freeze-and-measurement-plan.md`
- Expected: canonical documentation and planning artifacts validate without generated-surface drift.

**Exit Criteria:**
- Documentation describes only behavior proven by the source and tests, with no v4 or observer architecture implied.

### Task 4: Establish a bounded performance characterization baseline

**Purpose:**
- Measure current diagnostic and lifecycle overhead before any optimization decision, without changing production behavior.

**Task Function:**
- Produce attributable characterization evidence and a decision gate, not an optimization patch.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: measurement work requires protocol discipline but no production design change.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing benchmark validation and direct evidence checks are sufficient.

**Specification Coverage:**
- The characterization claim is limited to the Herdr completion-monitoring seam under its deterministic fake-time workload. It requires a matched workload, fixed environment, attributable evidence, sufficient repetitions, and zero lifecycle/cleanup/reconciliation mismatches; it does not measure Git preflight, workspace hashing, app-server startup, native publication/read-back, or retirement latency.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `scripts/benchmark_completion_monitoring.py:main`
- Inspect: `scripts/herdr_main_launcher.py:_new_performance_evidence`, `_record_performance_phase`, `_finalize_performance`
- Inspect: `scripts/secretary_live_runtime.py:run_normal`, `run_probe`
- Modify: none unless the benchmark validator exposes a concrete missing field required by the declared protocol
- Verify: `tests/test_benchmark_completion_monitoring.py`, direct-native output evidence, and the generated temporary baseline

**Dependencies:**
- Tasks 1-3 are complete in the clean worktree.
- The benchmark must not compare different workloads, revisions, providers, models, or capability modes.

**Authority:**
- Preauthorized local actions: run the existing deterministic benchmark, inspect emitted phase evidence, and record bounded temporary baseline output outside the repository.
- Stop for: production optimization, cross-invocation caching, external service changes, missing attribution, or synthetic live evidence.

**Steps:**
- [x] Step 1: Run the existing deterministic completion-monitoring characterization with 20 repetitions per case and record its JSON output outside the repository:
  `py -B scripts/benchmark_completion_monitoring.py --baseline-revision 649ac4364226fdad609914227e5e96035e4c1f06 --repetitions 20 --output $env:TEMP\project-os-completion-monitoring-baseline.json`.
- [x] Step 2: Validate that the baseline reports `evidence_kind=fake_boundary_observation`, all lifecycle/cleanup/reconciliation mismatches are zero, and the retention gate remains `not_evaluated` when no source delta exists; do not treat deterministic fake timing as production latency.
- [x] Step 3: When the local Codex app-server capability is available, run the same normal request twice against one output without `--resume` and record the exact operation, fingerprint, attempt, native turn, read-back, retirement, and no-duplicate-turn evidence. When capability is unavailable, record `BLOCKED_CAPABILITY`, leave this task and the plan active/blocked, and do not claim completion.
- [x] Step 4: Use the baseline only to decide whether a separately approved optimization plan is justified; do not change Git preflight, Herdr polling, LightRSI, namespace scanning, or `--resume` in this task.

**Verification:**
- [x] `py -B -m pytest -q tests/test_benchmark_completion_monitoring.py`
- [x] Inspect the temporary baseline JSON for protocol digest, repetition count, evidence kind, metrics, and zero correctness mismatches.
- Expected: characterization is attributable and reproducible, and no optimization claim is emitted without a real before/after source delta.

**Exit Criteria:**
- The 20-repetition Herdr characterization baseline exists and is valid. The direct-native proof also succeeds before completion; if capability is unavailable, the plan remains active/blocked rather than treating the capability block as completion evidence. No production optimization is accepted from unmeasured intuition.

### Task 5: Prove the freeze from a clean worktree

**Purpose:**
- Confirm the implementation, compatibility boundaries, validators, and direct recovery proof agree before the plan can be marked complete.

**Task Function:**
- Run final integrated verification and reconcile the ledger with repository evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires whole-plan source, test, validator, and runtime reconciliation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final validators and tests are the required independent checks.

**Specification Coverage:**
- Every implementation outcome is proven, no required task remains active, and the v3 architecture remains unchanged.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all files changed by Tasks 1-4 and the final Git inventory
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`, `scripts/validate_template_required_sections.py`, focused test files, full test suite, and `git diff --check`

**Dependencies:**
- Tasks 1-4 complete with task-local evidence.
- The final worktree contains no unrelated edits or untracked files except explicitly preserved plan-owned artifacts.

**Authority:**
- Preauthorized local actions: run declared final validators, focused tests, full pytest, diff checks, and inspect direct-native evidence.
- Stop for: failed required proof, dirty unrelated worktree state, missing capability, schema drift, or incomplete retirement evidence. A missing direct-native capability is a blocking condition, not a successful verification result.

**Steps:**
- [x] Step 1: Reconcile the task ledger, final changed-file list, base commit, current HEAD, and preserved unrelated work before testing.
- [x] Step 2: Run focused tests, repository validators, full pytest, and `git diff --check` from the clean worktree.
- [x] Step 3: Apply `skill-verification-before-completion`; leave the plan proposed or active when required evidence is blocked, and mark it completed only after a fresh `verified` result.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py tests/test_benchmark_completion_monitoring.py` (`453 passed, 2 skipped`)
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .` (passed, including planning, template, generated-surface, and contract checks)
- [x] `py -B -m pytest -q` (`1492 passed, 4 skipped`)
- [x] `git diff --check` (passed)
- Expected: all required checks pass from the clean worktree and the direct-native proof succeeds; an unavailable direct-native capability is explicitly recorded as `BLOCKED_CAPABILITY`, but the plan remains active/blocked rather than verified.

**Exit Criteria:**
- Verification returns `verified`, all required tasks are completed, and the plan records no unresolved required blocker or scope deviation.

**Verified State:**
- Workspace: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\native-semantic-contract-freeze\project-OS-starter`
- Mechanism: dedicated native Git worktree
- Branch: `codex/native-semantic-contract-freeze`
- Base commit and verified `HEAD`: `649ac4364226fdad609914227e5e96035e4c1f06`
- In-scope changes: five modified implementation/test/documentation files plus this plan; no unrelated changes detected.
- Direct-native proof: first and second invocation completed; second invocation reconciled with `preflight.reconciled=true`; retirement was `retired`; attempt ID remained `188f252ef6b14525a50b53dffa7d75a9`; result reference and all three v3 sidecar hashes remained unchanged.
- Characterization baseline: `fake_boundary_observation`, 20 repetitions, zero lifecycle/cleanup/reconciliation mismatches; evidence retained outside the repository.
- Result: `verified`; branch finishing remains a separate authorized Git action.

## Verification

- `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py tests/test_benchmark_completion_monitoring.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-20-00-15-native-semantic-contract-freeze-and-measurement-plan.md`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `py -B -m pytest -q`
- `git diff --check`
- `py -B scripts/benchmark_completion_monitoring.py --baseline-revision 649ac4364226fdad609914227e5e96035e4c1f06 --repetitions 20 --output $env:TEMP\project-os-completion-monitoring-baseline.json`
- One bounded direct-native Secretary run followed by the same output without `--resume`, with exact v3 identity, read-back, retirement, and no duplicate turn.

## Completion Criteria

The plan is ready for completion verification when:

1. Present output cannot reconcile without matching logical operation, fingerprint, and at least one current-writer binding from `preflight.attempt_id` or `preflight.retirement.attempt_id`; top-level `attempt_id` is consistency-only.
2. Current-v3 binding, submission, result, output, and retirement reads are bounded, no-follow, non-redundant inside reconciliation once parsed payloads are available, and fail closed on observable replacement or descriptor identity/type/size changes.
3. v1/v2/legacy readers remain read-only compatibility paths and never authorize current-v3 ownership.
4. The four-state recovery model, three v3 artifacts, direct Secretary authority, Herdr diagnostic fallback, LightRSI independence, and inert `--resume` compatibility remain intact.
5. The 20-repetition Herdr completion-monitoring characterization baseline is attributable and has zero lifecycle/cleanup/reconciliation mismatches; it is not presented as a general Project OS latency benchmark.
6. Focused tests, repository validators, full tests, diff checks, and a successful direct-native no-`--resume` proof are fresh and pass from a clean worktree. If the direct-native capability is unavailable, the plan remains active/blocked and cannot be marked completed.
7. No optimization, cache, polling redesign, namespace cleanup daemon, schema migration, or new semantic authority is introduced without a separately approved measurement-based plan.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` with fresh evidence.
Branch creation, commit, push, pull request, merge, and cleanup remain separate
authorized Git actions.
