---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: superseded
layer: change
name: native-semantic-residual-correctness
targets:
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-20-17-21-native-semantic-residual-correctness-plan.md
---

# Native Semantic Residual Correctness

Historical plan superseded by the native semantic implementation now present on
`main` and its subsequent runtime follow-up work. Retained for historical review
and recommendation context; no separate successor plan is required.

## Goal

Close the two correctness defects that remain after the native semantic contract
freeze: an occupied output namespace must never fall through to a fresh native
launch, and every current-v3 artifact comparison must use the complete
applicable native identity tuple. Preserve the direct Codex app-server path,
three current-v3 sidecars, four-state recovery behavior, read-only historical
compatibility, independent LightRSI context/history behavior, and CoS
acceptance authority.

The governing invariant is:

> Capture authoritative native identity at the boundary that creates the child,
> persist it once, correlate only against that identity, and reconcile only for
> exceptional recovery.

## Review Basis

The supplied consolidated recommendation is directionally correct, but source
review produces three material corrections:

- **P1 occupied namespace gap:** `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
  returns `None` after an occupied namespace has no result, binding, or
  submission sidecar. `_run_normal_via_native_app_server` interprets `None` as
  permission to create a new client, so an output-only foreign file can be
  overwritten when the request supplies a logical operation ID.
- **P1 incomplete identity comparison:** the reconciliation path compares the
  binding without `logical_operation_id` or `native_thread_id`, compares the
  submission without `logical_operation_id`, and
  `scripts/project_os_runtime/secretary_results.py:_publication_identity` omits
  `logical_operation_id`. The v3 validators already require these fields; the
  comparison code must match the contract.
- **P2 capability and scope boundary:** the normal path already calls
  `CodexAppServerClient.start_thread()` before `start_turn()`, persists the
  returned session/thread/pre-submit boundary in the binding, and uses the exact
  turn in the submission and result. Current source and prior completed plan
  evidence show no trustworthy Herdr pre-prompt native identity capability.
  This plan therefore verifies and documents the existing native-first path; it
  does not invent a second Herdr discovery call, observer, registry, or service.

The prior completed freeze plan
`docs/superpowers/plans/2026-10-20-00-15-native-semantic-contract-freeze-and-measurement-plan.md`
already covers bounded evidence reads, current-v3 ownership attribution,
measurement characterization, and direct native recovery proof. This plan does
not repeat those changes; it closes the residual fall-through and identity
holes found in the current `main` source.

## Scope Boundaries

This plan does not introduce a v4 schema, session registry, latest-session
discovery, reconciliation daemon, retry service, pooled or persistent
app-server, Project OS-specific LightRSI API, new semantic observer, or
background cleanup process. It does not remove or deprecate `--resume`, retire
v1/v2 readers, change Herdr API shape, or optimize polling, workspace hashing,
app-server startup, publication, or retirement. Those changes require caller
inventory or fresh measurement and a separate approved plan.

## Implementation Outcomes

### Occupied namespaces fail closed

Only a completely empty native namespace may return `None` and authorize a new
attempt. A complete, attributable current-v3 namespace reconciles without a
new turn. Binding/submission evidence without a result remains uncertain and
non-retryable. Any other occupied, foreign, malformed, or uncertain namespace
raises the existing conflict or uncertain-delivery failure, preserves every
existing byte, and never constructs a new native client.

### Current-v3 identity is exact and centralized

Binding comparisons use `logical_operation_id`, `request_fingerprint`,
`attempt_id`, `native_session_id`, and `native_thread_id`. Submission and result
comparisons add `native_turn_id`. Publication idempotency includes
`logical_operation_id` in addition to the existing result identity and content
digest. No schema fields change and v1/v2/legacy readers remain read-only.

### Native-first behavior remains explicit

The direct app-server path persists the authoritative thread identity before
prompt submission and uses the exact returned turn for submission, completion,
publication, read-back, and retirement. Existing Herdr pane/freshness logic
remains compatibility diagnostics only where the direct native capability is
not used. Maintained runtime documentation states this boundary without
claiming unavailable Herdr identity propagation.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `task-specific isolated worktree`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the listed canonical source, test, documentation, and plan files; run the named repository tests and validators; create the task-specific worktree from the recorded base when execution begins
- User-approval actions: push, merge, publication, destructive recovery, deleting compatibility behavior, changing external repositories, or changing the plan scope
- Parallel ownership: none; `_reconcile_native_artifacts`, `native_artifact_identity`, and their focused tests are shared semantic owners and remain serialized
- Sequential fallback: execute Tasks 1 through 4 in order in one clean worktree

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `479259218dc1f20248795e932509a7a783d71882`
- Expected workspace: `clean before plan creation; this plan file is the only intended change`
- Next action: `review and approve Task 1, then activate the plan before implementation`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | task-specific isolated worktree | `unresolved` | none | focused namespace regression | pending |
| Task 2 | `pending` | task-specific isolated worktree | `unresolved` | Task 1 | identity and publication regression matrix | pending |
| Task 3 | `pending` | task-specific isolated worktree | `unresolved` | Task 2 | direct native identity test and runtime contract inspection | pending |
| Task 4 | `pending` | task-specific isolated worktree | `unresolved` | Tasks 1-3 | repository validators, focused suite, full suite, diff check | pending |

## Task Breakdown

### Task 1: Fail closed for every occupied namespace without complete recovery evidence

**Purpose:**
- Prevent output-only, foreign, malformed, or otherwise occupied storage from authorizing a fresh native attempt.

**Task Function:**
- Harden the current-v3 namespace admission state machine at its shared reconciliation owner.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `resolve through planning dispatch from the bounded correctness and risk contract before activation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `the lead controller runs the focused regression and accepts the evidence`

**Specification Coverage:**
- Empty namespace is the only fresh-execution authorization.
- Foreign or unknown occupants are preserved and never launched over.
- Binding/submission without result remains uncertain delivery with no automatic resubmission.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_native_namespace_state`
- Inspect: `scripts/secretary_live_runtime.py:_run_normal_via_native_app_server`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Verify: `tests/test_secretary_live_runtime.py:test_reconcile_native_artifacts_rejects_unattributed_existing_output`
- Verify: `tests/test_secretary_live_runtime.py:test_reconcile_native_artifacts_blocks_unknown_identity_reuse`
- Add or modify: `tests/test_secretary_live_runtime.py:test_reconcile_native_artifacts_rejects_foreign_output_with_explicit_logical_operation_id`

**Dependencies:**
- Current `main` source and the existing four-state recovery tests are authoritative.

**Authority:**
- Preauthorized local actions: read and edit the two named Python files, add the named regression, and run the focused runtime test selection
- Stop for: any proposed schema change, new recovery owner, overwrite/delete behavior, external repository edit, or mismatch between the current state machine and the acceptance contract

**Steps:**
- [ ] Step 1: Trace the `empty` -> `occupied` -> reconciliation -> client-construction path and preserve the existing distinction between complete result recovery and binding/submission-only uncertainty.
- [ ] Step 2: Change the occupied no-result fall-through so only `namespace_state == "empty"` returns `None`; an occupied namespace without recoverable v3 result evidence raises `NATIVE_RESULT_CONFLICT`, while binding/submission-only evidence keeps `NATIVE_SUBMISSION_FAILED`.
- [ ] Step 3: Add a regression with a foreign `normal.json` containing explicit bytes, no native sidecars, and an explicit `logical_operation_id`; assert `CodexAppServerClient` is not constructed, the failure is conflict-classified, and the output bytes remain identical.
- [ ] Step 4: Run the focused namespace tests and inspect the diff for preservation of existing binding-only and malformed-evidence behavior.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "reconcile_native_artifacts or namespace"`
- Expected: the existing reconciliation tests and the new output-only foreign-occupant regression pass; no native client is created for the new case.

**Exit Criteria:**
- No occupied namespace can return fresh-launch authorization unless it is completely empty, and every relevant failure preserves existing bytes.

### Task 2: Enforce the complete v3 identity tuple and publication idempotency

**Purpose:**
- Make cross-artifact recovery and result publication reject identity collisions that differ only by logical operation or native thread.

**Task Function:**
- Establish one reusable native-artifact identity projection and apply it to recovery and publication comparisons.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `resolve through planning dispatch from the bounded correctness and risk contract before activation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `the lead controller runs the focused contract and reconciliation tests`

**Specification Coverage:**
- Binding identity is `(logical_operation_id, request_fingerprint, attempt_id, native_session_id, native_thread_id)`.
- Submission/result identity adds `native_turn_id`.
- Publication idempotency includes `logical_operation_id` and preserves immutable evidence on conflict.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_results.py:_publication_identity`
- Modify: `scripts/project_os_runtime/secretary_results.py:native_artifact_identity`, `_publication_identity`, `__all__`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`
- Verify: `scripts/project_os_runtime/secretary_results.py:parse_native_binding`, `parse_native_submission`, `parse_native_result`
- Add or modify: `tests/test_secretary_results.py:test_native_result_publication_identity_includes_logical_operation_id`
- Add or modify: `tests/test_secretary_live_runtime.py` cross-artifact mismatch coverage for logical operation and native thread identity

**Dependencies:**
- Task 1 complete; the namespace state machine must fail closed before identity comparison changes are accepted.

**Authority:**
- Preauthorized local actions: read and edit the named identity owners and focused tests, add the reusable projection without changing schemas, and run the focused result/runtime suites
- Stop for: any v4 field, migration, legacy-reader behavior change, identity rule that omits a required current-v3 field, or publication behavior that overwrites existing bytes

**Steps:**
- [ ] Step 1: Add `native_artifact_identity(payload, *, include_turn_id)` in `scripts/project_os_runtime/secretary_results.py` with the exact ordered fields defined by the current-v3 contract.
- [ ] Step 2: Make `_publication_identity()` use the complete result identity projection plus `content_sha256`, and export the helper only if the runtime import requires a public module surface.
- [ ] Step 3: Replace the manual binding and submission comparison lists in `_reconcile_native_artifacts()` with the shared projection, preserving the binding-without-turn and submission-with-turn distinction.
- [ ] Step 4: Add tests that mutate only `logical_operation_id` or `native_thread_id` in binding/submission evidence and assert reconciliation fails closed; add a publication test that mutates only `logical_operation_id` and asserts `NativeResultConflictError` with unchanged bytes.
- [ ] Step 5: Run focused result and reconciliation tests, including the existing v1/v2 compatibility cases, and confirm no schema or read-only compatibility change.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py -k "publication or reconcile_native_artifacts or native_result or native_binding or native_submission"`
- Expected: identity mutations are rejected, exact replay remains idempotent, conflicting publication preserves the first file, and historical compatibility tests remain green.

**Exit Criteria:**
- All current-v3 recovery and publication comparisons use the complete applicable identity tuple through one canonical projection.

### Task 3: Verify and document the existing native-first identity boundary

**Purpose:**
- Prove that the direct app-server path captures native identity before prompt submission and prevent future work from reintroducing textual freshness or Herdr discovery as semantic authority.

**Task Function:**
- Reconcile the maintained runtime contract with the existing direct-native implementation and its regression evidence.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `resolve through planning dispatch from the bounded correctness and risk contract before activation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `the lead controller accepts the direct boundary test and documentation inspection`

**Specification Coverage:**
- `start_thread()` identity is persisted before `start_turn()`.
- Exact session/thread/turn identity remains authoritative for result and retirement correlation.
- Herdr and LightRSI remain independent compatibility/context systems.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_run_normal_via_native_app_server`
- Modify: `tests/test_secretary_live_runtime.py:test_run_normal_native_app_server_uses_bound_turn_identity`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` current-v3 recovery and native semantic path bullets

**Dependencies:**
- Task 2 complete; identity fields must be stable before documentation and direct-boundary assertions are updated.

**Authority:**
- Preauthorized local actions: strengthen the existing direct-native test and update the maintained runtime contract without changing Herdr, LightRSI, or CLI interfaces
- Stop for: any need for a second discovery call, latest-session lookup, new observer/service, external LightRSI change, or claim that Herdr exposes native pre-prompt identity in this repository

**Steps:**
- [ ] Step 1: Extend the existing fake-client test so `start_turn()` asserts the binding file already exists with the exact session/thread identity returned by `start_thread()`.
- [ ] Step 2: Assert the persisted submission and result carry the same native session/thread and the exact returned turn, while the normal path does not invoke Herdr pane preparation.
- [ ] Step 3: Update `docs/operating_system/runtime/runtime-surfaces.md` to state that only empty namespaces authorize fresh execution, current-v3 comparisons use the complete applicable identity, and direct app-server identity is captured before prompt submission; retain the documented Herdr diagnostic fallback limitation.
- [ ] Step 4: Inspect the documentation for duplicate or contradictory normative claims and leave historical plans unchanged.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "run_normal_native_app_server_uses_bound_turn_identity"`
- Expected: the direct boundary test proves pre-submit binding persistence, exact turn correlation, no Herdr normal-path use, and stable native identity propagation.

**Exit Criteria:**
- The implementation and maintained runtime contract agree on native-first identity ownership without adding unsupported infrastructure.

### Task 4: Run final repository verification and reconcile the plan

**Purpose:**
- Prove the two correctness fixes without weakening unrelated runtime, compatibility, planning, or generated-surface contracts.

**Task Function:**
- Perform final evidence collection and reconcile task state against Git and fresh command output.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: `resolve through planning dispatch from the bounded verification and risk contract before activation`

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `completion verification remains owned by the lead controller`

**Specification Coverage:**
- Focused behavior, repository contracts, full tests, documentation ownership, and diff integrity are all reconciled before completion.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all files listed in `targets`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `scripts/validate_template_required_sections.py`

**Dependencies:**
- Tasks 1-3 complete with accepted task-local proof.

**Authority:**
- Preauthorized local actions: run the named validators and test commands, inspect Git status/diff, and update this plan's task ledger with accepted evidence
- Stop for: any failed required check, stale plan state, generated-surface drift, unrelated file change, unavailable required capability, or unresolved scope deviation

**Steps:**
- [ ] Step 1: Run the focused runtime/result suite and the repository contract/planning validators.
- [ ] Step 2: Run the full test suite and `git diff --check` from the execution worktree.
- [ ] Step 3: Inspect changed files, confirm only canonical sources/docs/tests/plan changed, and reconcile every task ledger row with command evidence.
- [ ] Step 4: Leave the plan `proposed` until approved for execution; after execution, use `skill-verification-before-completion` before any status transition to `completed`.

**Verification:**
- [ ] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py`
- [ ] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [ ] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-20-17-21-native-semantic-residual-correctness-plan.md`
- [ ] `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- [ ] `py -B -m pytest -q`
- [ ] `git diff --check`
- Expected: all required checks pass, no unrelated change is present, and no required capability or scope decision remains unresolved.

**Exit Criteria:**
- Fresh focused and broad evidence supports every completion criterion; no task is marked complete from a checked box alone.

## Verification

- `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-20-17-21-native-semantic-residual-correctness-plan.md`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `py -B -m pytest -q`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. A completely empty namespace is the only state that authorizes a fresh native launch.
2. An output-only or foreign occupied namespace with an explicit logical operation ID fails closed, preserves bytes, and does not construct a native client.
3. Complete current-v3 result recovery requires matching logical operation, request fingerprint, attempt, native session, native thread, and native turn identity as applicable across binding, submission, result, and publication.
4. Binding/submission evidence without a result remains uncertain delivery and never triggers automatic resubmission.
5. The direct app-server path persists thread identity before prompt submission and correlates publication/read-back/retirement to the exact turn without Herdr or LightRSI semantic authority.
6. No v4 schema, new registry/service/observer, compatibility retirement, optimization, or external repository edit is introduced.
7. Focused tests, repository validators, the full test suite, and `git diff --check` pass from the execution worktree.
8. The plan remains `proposed` until approved; it may be marked `completed` only after `skill-verification-before-completion` returns `verified` with fresh evidence.

Branch creation, commit, push, pull request, merge, publication, and worktree
cleanup remain separate authorized Git actions.
