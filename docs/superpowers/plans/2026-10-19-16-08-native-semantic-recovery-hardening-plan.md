---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-recovery-hardening
parent_spec: none
targets:
  - scripts/project_os_runtime/codex_app_server.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/secretary_live_runtime.py
  - tests/test_codex_app_server.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-19-16-08-native-semantic-recovery-hardening-plan.md
---

# Native Semantic Recovery Hardening

## Review Basis

The supplied verdict is architecturally sound: the native Secretary app-server
path is the semantic owner, v3 remains the current contract, CoS-to-Herdr
execution remains separate, and LightRSI remains context/history/replay/audit
infrastructure. The remaining work is a bounded recovery and lifecycle cleanup,
not another observer, registry, daemon, schema, or coordination layer.

The review accepts these findings as in scope:

- Project OS runtime evidence can currently alter the workspace digest used by
  the request that produced that evidence.
- Failure classification, rather than output ownership, controls whether the
  invocation record can be overwritten.
- Retirement evidence is not projected consistently after execution failures.
- The one-slot writer queue still has a sentinel race during close.
- The client records a provider value that does not affect process launch.
- Git/workspace identity is resolved twice during one normal invocation.
- Direct v3 projection still traverses historical semantic normalization.
- Pre-#107 v3 evidence needs an explicit read-only, non-reuse compatibility
  boundary.

The review explicitly defers synthetic `session`, `pane`, and `agent_name`
cleanup unless the shared projection extraction removes them without changing
the direct v3 contract. It also preserves conservative retry behavior, Herdr's
governed role, LightRSI internals, and all existing identity, binding,
submission, final-answer, atomic-publication, read-back, and retirement
safeguards.

## Goal

Finish the native Secretary recovery hardening without changing the semantic
architecture: runtime bookkeeping must not invalidate task-input identity,
foreign output namespaces must remain read-only, every started native child
must produce independent retirement evidence, provider and repository identity
must describe the actual launch context, and direct v3 output must remain
independent from historical semantic arbitration.

## Implementation Outcomes

### Task-input identity excludes owned runtime bookkeeping

Workspace fingerprints exclude only the exact invocation output, native
binding/submission/result, output atomic-write temporary prefix,
binding/submission/result publication temporary prefixes, and their persistent
`.release.lock` paths. If Task 2 adds an invocation-output lock, that exact lock
path is included as well. A tracked task-input path cannot alias any stable
runtime-owned path. Workspace identity scanning bounds status/path-list bytes,
tracked-diff bytes, untracked count, per-file bytes, aggregate bytes, and
command wall-clock; when any limit is exceeded or identity is otherwise
uncertain, the invocation continues with `reuse_allowed=false` rather than
inventing a fingerprint.

### Output ownership controls all persistence

Normal Secretary execution classifies the output namespace before any write as
empty and claimable, owned by the exact current operation, or foreign/unknown.
An empty namespace may persist an outcome only after this attempt establishes
ownership atomically; an already owned current operation may reconcile
explicitly. Foreign, malformed, partial, conflicting, or legacy evidence
remains read-only regardless of failure kind, and rejected binding/submission
attempts cannot overwrite a prior invocation record.

### Lifecycle and provider evidence remain truthful

Native retirement is captured and identity-bound after both successful and
failed execution. The writer exits deterministically when closing begins. The
effective top-level Codex provider is read from `CODEX_HOME` and verified
against the fixed Secretary provider; the app-server client no longer carries a
misleading provider field. One immutable repository/workspace snapshot feeds
fingerprinting, launch, diagnostics, and recovery.

### Current v3 projection stays isolated and compatible

Direct validated v3 results remain independent of historical semantic
arbitration. They use shared lifecycle/resource projection when the optional
small extraction is safe; otherwise the existing harmless redundancy remains.
Existing v1/v2 readers remain read-only compatibility surfaces. Pre-#107 v3
artifacts are documented and tested as historical evidence that is not
automatically reusable by the current fingerprint contract; no v4 schema or
dual writer is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect the current source and tests, edit the declared code/tests/documentation/plan paths, run declared local tests and repository validators, and run one bounded native probe after implementation
- User-approval actions: branch creation, commit, push, pull request, merge, publication, destructive cleanup, credential/config changes, and any write outside the declared target paths
- Parallel ownership: `none`; `scripts/secretary_live_runtime.py` is a shared owner and all tasks are serialized
- Sequential fallback: execute Tasks 1–6 in order, then run Task 7 final verification; do not split the shared runtime file across workers

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-semantic-recovery-hardening` after approval; current proposal base is `main`
- Base commit: `04a809a28bc2eed1d0c798966cb7ac41c7589fa9`
- Expected workspace: `clean`
- Next action: none; implementation and verification are complete
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | bounded identity and runtime-artifact tests | `32 passed`; output/lock/temp exclusion, bounded Git collection, and tracked collision proof |
| Task 2 | `completed` | current | `codex` | Task 1 | ownership and non-overwrite regressions | `19 passed`; explicit namespace states, foreign-output preservation, and claim-loss proof |
| Task 3 | `completed` | current | `codex` | Task 1 | success/failure retirement proof | `21 passed`; explicit client lifetime and failure-path retirement evidence |
| Task 4 | `completed` | current | `codex` | none | writer-close race and bounded join tests | `10 passed`; closing gate, full-queue writer retirement, and post-close send rejection |
| Task 5 | `completed` | current | `codex` | Tasks 1–2 | provider and single-snapshot proof | `13 passed`; active provider validation, client-provider removal, and one Git-anchor resolution |
| Task 6 | `completed` | current | `codex` | Tasks 1–5 | v3 projection and compatibility proof | `9 passed`; direct-v3 isolation, historical compatibility, resume binding, and pre-#107 non-reuse documented/tested |
| Task 7 | `completed` | current | `codex` | Tasks 1–6 | final validators, full suite, and bounded live proof | `343 passed`, repository/planning validators passed, and live initial/resume proof completed with one bound attempt and no second native turn/start |

## Task Breakdown

### Task 1: Separate task-input identity from runtime artifacts

**Purpose:**
- Prevent Project OS output and sidecar publication from changing the
  fingerprint of the task that produced those artifacts, while bounding the
  cost of workspace identity collection.

**Task Function:**
- Harden the normal-request identity boundary and preserve fail-safe reuse
  eligibility.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct regression proof for fingerprint and reuse behavior

**Specification Coverage:**
- Verdict findings 1 and 2: runtime artifacts must not self-invalidate task
  identity; oversized or uncertain identity must disable reuse without blocking
  ordinary execution.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_read_only_workspace_identity`, `_resolve_normal_request`, `run_normal`, `_atomic_write_json`
- Modify: `scripts/secretary_live_runtime.py:_read_only_workspace_identity`, `_resolve_normal_request`, `run_normal`, `_atomic_write_json`
- Verify: `tests/test_secretary_live_runtime.py` workspace identity and resume tests

**Dependencies:**
- Current `main` at `04a809a28bc2eed1d0c798966cb7ac41c7589fa9`

**Authority:**
- Preauthorized local actions: edit the named runtime and test paths; add precise identity limits and exact owned-artifact handling; run the task-local pytest command
- Stop for: a need to introduce a new durable registry/state service, a tracked output-path migration, or a change to the v3 schema contract

**Steps:**
- [x] Step 1: Add one helper that resolves the output, native binding,
  submission, result, invocation-output lock, release-lock files, and all
  atomic/publication temporary prefixes as Project OS-owned artifacts. Treat
  only those exact paths and generated prefixes as owned; do not ignore broad
  extensions, arbitrary directories, or unrelated untracked files.
- [x] Step 2: Reject a requested output, binding, submission, result, or
  release-lock path that resolves to a tracked task-input file before native
  launch. Update workspace identity collection to omit only the owned runtime
  paths from the status-derived untracked set and retain tracked Git diff
  content as task input.
- [x] Step 3: Add explicit limits of 4096 untracked entries, 8 MiB per file,
  and 64 MiB aggregate untracked content, plus finite status/path-list and
  tracked-diff byte budgets and a command wall-clock deadline. Collect status
  and diff output with bounded buffering or streaming so overflow is detected
  before unbounded output is retained. On any limit, timeout, stat/read
  failure, or ambiguous path ownership, return `workspace_identity` in
  `unknown_fields`, omit the digest, and set `reuse_allowed=false` without
  preventing a fresh invocation.
- [x] Step 4: Establish the final resolved execution-context shape, thread the
  output-aware identity inputs through request resolution, and keep the
  existing fingerprint field order and sentinel values unchanged for known
  identities. Task 5 must consume this API rather than reshape it.
- [x] Step 5: Add regressions for every runtime artifact and lock/temp prefix
  appearing after publication, tracked collisions on every stable runtime path,
  large-file and large-tree degradation, oversized status/diff output,
  command timeout, unreadable untracked input degradation, and unchanged-task
  resume eligibility.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "workspace or fingerprint or identity or runtime_artifact"`
- Expected: all new and existing identity tests pass; owned runtime artifacts do
  not change a known workspace digest, and bounded/uncertain scans disable reuse
  without raising a synthetic execution failure.

**Exit Criteria:**
- A normal invocation has one precise task-input identity calculation that does
  not include its own runtime evidence and has bounded work under dirty-tree
  stress.

### Task 2: Make output ownership the persistence gate

**Purpose:**
- Ensure rejected or conflicting native work never overwrites output belonging
  to another operation or an unknown prior attempt.

**Task Function:**
- Replace failure-kind-based write suppression with an explicit output namespace
  ownership decision.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: binding/submission conflict and byte-preservation tests

**Specification Coverage:**
- Verdict finding 2 and the required regressions for occupied output paths,
  binding-only rejection, and submission-only rejection.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`, `_run_normal_via_native_app_server`, `main`
- Modify: `scripts/secretary_live_runtime.py:_reconcile_native_artifacts`, `_run_normal_via_native_app_server`, `main`
- Verify: `tests/test_secretary_live_runtime.py:test_rejected_native_invocation_does_not_overwrite_existing_output`

**Dependencies:**
- Task 1 establishes exact runtime artifact ownership and output-path validation.

**Authority:**
- Preauthorized local actions: edit the named runtime and regression tests; route every normal-mode output write through the ownership gate; run task-local tests
- Stop for: any requirement to delete, rewrite, or reinterpret foreign evidence

**Steps:**
- [x] Step 1: Define the namespace states from the output plus its exact native
  sidecars using this decision table:
  `empty_available` means no output and no sidecars and is only claimable;
  `owned_existing_operation` requires a complete current v3 binding,
  submission, and result with exact logical operation, request fingerprint,
  attempt, session/thread, and turn identities and permits explicit resume
  reconciliation; `foreign_or_uncertain` covers binding-only,
  binding-plus-submission without result, result without binding/submission,
  missing sidecars, malformed, legacy, conflicting, and foreign-operation
  evidence and is read-only with no automatic retry or overwrite.
- [x] Step 2: Make fresh and resume reconciliation return the ownership
  decision before any output mutation. An empty namespace becomes owned only
  after this attempt atomically publishes its current binding; if publication
  conflicts, the attempt loses ownership and must not write invocation output
  or alter the winner's sidecars. Pre-binding failures either return without
  persistence or use an atomic create-if-still-unclaimed operation. Do not add
  a durable registry or claim sidecar.
- [x] Step 3: Route normal success, failure, conflict, and CLI exception
  persistence through one ownership-aware publisher. Preserve existing conflict
  errors and read-only historical behavior, and return rejected outcomes to the
  caller without writing them over a foreign, partial, or losing namespace.
- [x] Step 4: Add tests proving binding-only, binding-plus-submission,
  submission-only, malformed, legacy, occupied, and concurrent same-output
  conflicts leave the prior output and all sidecars byte-for-byte unchanged,
  while an empty namespace can receive a current result after its atomic claim.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "output or conflict or ownership or resume"`
- Expected: every rejected invocation preserves foreign evidence and no failure
  classification can bypass the ownership gate.

**Exit Criteria:**
- No normal Secretary failure path can overwrite a namespace it does not own.

### Task 3: Unify finalization and preserve retirement after failure

**Purpose:**
- Keep semantic execution outcome independent from actual native process/thread
  retirement on both success and failure paths.

**Task Function:**
- Consolidate native finalization and bind retirement evidence to the strongest
  exact identity available.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct failure-path retirement proof

**Specification Coverage:**
- Verdict finding 3, including the rule that an execution failure with verified
  retirement must not become a recovery-required resource state.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_run_normal_via_native_app_server`, `_bind_native_retirement_identity`, `_apply_native_retirement_evidence`, `_normalize_invocation_outcome`
- Modify: `scripts/secretary_live_runtime.py:_run_normal_via_native_app_server`, shared lifecycle helpers
- Verify: `tests/test_secretary_live_runtime.py:test_run_normal_native_result_survives_unverified_retirement` and new failure-retirement tests

**Dependencies:**
- Task 1 supplies stable request identity; Task 2 supplies the persistence gate.

**Authority:**
- Preauthorized local actions: edit native finalization and lifecycle tests; preserve semantic failure status while projecting retirement independently
- Stop for: any automatic retry, durable session registry, or semantic-success promotion based only on retirement

**Steps:**
- [x] Step 1: Instantiate the native client before entering or starting it, then
  use an explicit `try`/`with client`/`finally` (or equivalent `start()`/`close()`
  structure) so the client object remains accessible when `__enter__()` or
  `start()` raises. Track whether it started and capture structured retirement
  evidence in one `finally` path after normal completion and exceptions,
  including context-manager initialization failures where evidence exists.
- [x] Step 2: Bind logical operation, fingerprint, attempt, session, thread,
  and turn identities when known; preserve unknown fields rather than inventing
  them when failure occurs before the corresponding native identity exists.
- [x] Step 3: Apply retirement/resource projection to the final invocation
  record after semantic normalization, keeping execution failure, semantic
  outcome, and recovery-required state independent.
- [x] Step 4: Add tests for binding failure after client start, submission
  failure after thread creation, turn failure after acknowledgement, verified
  retirement after execution failure, and genuinely unknown retirement.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py -k "retirement or failure or submission or binding"`
- Expected: failed semantic execution retains exact retirement evidence when
  available, and only uncertain resources set `recovery_required=true`.

**Exit Criteria:**
- Every started native client has one finalization path that records retirement
  independently from semantic success or failure.

### Task 4: Close the native writer shutdown race

**Purpose:**
- Make the owned app-server writer terminate deterministically when closing
  begins, even when the one-slot queue prevents the sentinel from being queued.

**Task Function:**
- Harden the existing writer/reader lifecycle without adding another execution
  or coordination layer.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fake-process and thread-lifecycle tests

**Specification Coverage:**
- Verdict finding 4 and the existing short-write, deadline, sentinel, and
  bounded-join safeguards.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient.close`, `_send`, `_write_loop`
- Modify: `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient.__init__`, `close`, `_send`, `_write_loop`
- Verify: `tests/test_codex_app_server.py:test_client_close_retires_owned_writer_and_reader_threads`

**Dependencies:**
- None; this task has a disjoint implementation owner but is serialized because
  final verification covers the complete native runtime.

**Authority:**
- Preauthorized local actions: edit the owned client and its focused tests; use one closing event/flag plus the existing sentinel and bounded joins
- Stop for: adding another thread, executor, async framework, queue, or retry path

**Steps:**
- [x] Step 1: Add one client-lifetime closing event set before process and pipe
  retirement; make `_send` reject new work once closing starts.
- [x] Step 2: Keep the best-effort sentinel for an idle writer, but make the
  writer return after finishing its current item when the closing event is set.
  Preserve short-write loops, deadline checks, acknowledgment behavior, and
  bounded reader/writer joins.
- [x] Step 3: Preserve explicit `unknown` retirement when a thread remains
  alive after the configured grace/kill windows, and add a queue-full close test
  proving the writer cannot become falsely unknown after its in-flight write
  completes.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py -k "writer or close or deadline or short"`
- Expected: the writer exits in the full-queue race, new sends fail after close,
  and all existing transport/lifecycle tests remain green.

**Exit Criteria:**
- Writer shutdown is deterministic under an occupied one-slot queue without
  changing the app-server protocol or adding a new lifecycle owner.

### Task 5: Make provider truth and repository identity single-source

**Purpose:**
- Ensure the app-server launch evidence describes the effective provider and
  model while using one immutable repository/workspace snapshot per normal
  invocation.

**Task Function:**
- Reconcile native launch configuration and request resolution at one shared
  execution-context boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: provider/configuration and single-resolution tests

**Specification Coverage:**
- Verdict findings 5 and 6: active provider truth and one repository/workspace
  snapshot.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_configured_provider`, `_resolve_normal_request`, `run_normal`, `_run_normal_via_native_app_server`; `scripts/project_os_runtime/codex_app_server.py:CodexAppServerClient`
- Modify: the same symbols and `tests/test_secretary_live_runtime.py`, `tests/test_codex_app_server.py`
- Verify: `tests/test_secretary_live_runtime.py:test_resolved_request_uses_profile_model_and_git_revision`, provider tests, and a new single-anchor-resolution test

**Dependencies:**
- Task 1 supplies the output-aware workspace identity input and the final
  resolved execution-context API; Task 4 must not change the provider/context
  contract.

**Authority:**
- Preauthorized local actions: read and validate the active top-level `model_provider` and configured provider mapping; remove the misleading client provider parameter/property; thread one resolved repository/Git/workspace context through normal execution
- Stop for: any provider fallback, ambient-provider selection, or new provider registry

**Steps:**
- [x] Step 1: Change `_configured_provider` to read the active top-level
  `model_provider`, require it to equal `9router`, require the corresponding
  `model_providers["9router"]` entry, and verify only the coarse config/auth
  source availability already required by the existing runtime. Do not
  duplicate Codex credential or provider-authentication semantics; let the
  owned Codex process establish whether credentials are usable.
- [x] Step 2: Remove `CodexAppServerClient.provider` and its constructor
  parameter because `CODEX_HOME` is the launch configuration owner. Retain the
  resolved provider in request fingerprints, preflight evidence, and binding
  evidence from the verified active config.
- [x] Step 3: Resolve the Git anchor once in `run_normal`, pass that immutable
  repository root/revision and the output-aware workspace identity into the
  final resolver API established by Task 1, and make all downstream launch,
  fingerprint, resume, and diagnostic consumers use the returned resolved
  request without a second resolver reshaping.
- [x] Step 4: Add tests for an active provider mismatch, missing provider
  mapping, provider/model evidence agreement, and exactly one Git-anchor
  resolution per normal invocation.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_codex_app_server.py -k "provider or model or resolved_request or git_revision or anchor"`
- Expected: the active provider is the one recorded and used by the configured
  app-server launch, the model remains bound to `thread/start`, and Git/workspace
  identity is resolved once.

**Exit Criteria:**
- No native client field claims provider authority it does not use, and one
  immutable resolved execution context feeds the complete normal invocation.

### Task 6: Isolate direct v3 projection and document the compatibility cutoff

**Purpose:**
- Prove direct v3 remains independent of historical semantic arbitration and
  document the safe non-reuse boundary introduced by PR #107; remove redundant
  projection only when the refactor is small and isolated.

**Task Function:**
- Required work is the compatibility documentation/test and proof that direct
  v3 remains independent. Extract shared lifecycle/resource projection only if
  it is a small isolated refactor that does not broaden changed behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns the inline sequential implementation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct-v3 and historical-decoder boundary tests

**Specification Coverage:**
- Verdict findings 7 and 8, plus the preserved v3/legacy/Herdr/LightRSI
  architecture.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_normalize_invocation_outcome`, `_normalize_native_v3_outcome`; `scripts/project_os_runtime/secretary_results.py` v1/v2/v3 parsers
- Modify: `scripts/secretary_live_runtime.py` shared lifecycle projection; `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: `tests/test_secretary_live_runtime.py:test_native_v3_projection_ignores_legacy_semantic_sources`, `tests/test_secretary_results.py` historical decoder tests

**Dependencies:**
- Tasks 1–5 complete so projection changes do not mask recovery or lifecycle
  regressions.

**Authority:**
- Preauthorized local actions: update canonical runtime documentation and add direct-v3 compatibility tests; extract the smallest shared projection only when it remains isolated and low-risk
- Stop for: a v4 schema, dual writer, LightRSI observer, Herdr semantic path, or retry-policy expansion

**Steps:**
- [x] Step 1: Prove with focused tests that direct v3 never invokes or depends
  on legacy semantic arbitration. If a shared execution/resource/observability
  projection can be extracted without a broad normalization rewrite or legacy
  test churn, extract it; otherwise retain the harmless internal redundancy.
- [x] Step 2: When the small extraction is made, have
  `_normalize_native_v3_outcome` call the shared lifecycle projection and
  project only the already validated v3 semantic outcome. In either case, keep
  v1/v2 decoding read-only and preserve exact current field names.
- [x] Step 3: Add a regression that pre-#107 v3 fingerprint evidence is
  retained as historical/read-only evidence rather than automatically reused;
  current automatic recovery requires equality with today's request-fingerprint
  contract and does not need a vintage detector, timestamp cutoff, commit
  marker, or alternate fingerprint calculation.
- [x] Step 4: Document active/post-#107 v3 automatic recovery eligibility and
  pre-#107 v3 non-reuse in `runtime-surfaces.md`; state that Herdr and LightRSI
  ownership remains unchanged and synthetic identity-field cleanup is deferred.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "v3 or legacy or projection or resume"`
- Expected: direct v3 projection is independent, historical decoders remain
  readable, and pre-#107 evidence cannot silently enter current automatic
  recovery.

**Exit Criteria:**
- Current v3 remains the only semantic write contract, direct v3 remains
  independent of historical arbitration, and the compatibility cutoff is
  explicit; any optional projection extraction stays small and isolated.

### Task 7: Reconcile and verify the complete change

**Purpose:**
- Prove the complete recovery hardening, preserved CoS/Herdr boundary, and
  native runtime behavior before any later branch disposition.

**Task Function:**
- Final integration verification and documentation/repository reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lead controller owns final evidence and scope reconciliation

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` owns the final gate

**Specification Coverage:**
- All implementation outcomes, preserved invariants, and the supplied verdict's
  stop conditions.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed runtime, test, documentation, and plan files
- Modify: `docs/superpowers/plans/2026-10-19-16-08-native-semantic-recovery-hardening-plan.md` task ledger and evidence only
- Verify: repository status, approved path scope, generated surfaces, and current runtime documentation

**Dependencies:**
- Tasks 1–6 complete with task-local proof and no unresolved scope deviation.

**Authority:**
- Preauthorized local actions: update this plan's ledger/evidence, run declared repository checks, run one bounded native probe, and remove only that exact disposable probe root after preserving evidence
- Stop for: failed required validation, authentication, unavailable upstream capability without immutable evidence, or any result not bound to the exact current request

**Steps:**
- [x] Step 1: Run the focused native/result/lifecycle/compatibility matrix,
  including release-lock/temp exclusion, concurrent same-output claim loss,
  failure-path retirement, and queue-full close; confirm direct Secretary does
  not invoke Herdr or LightRSI while CoS/Herdr preservation tests remain green.
- [x] Step 2: Run repository contract validation, planning lifecycle validation,
  the full pytest suite, and `git diff --check`.
- [x] Step 3: Run one unique bounded native Secretary probe with an unchanged
  task workspace, then immediately rerun `--resume` against the same output path
  and task. Record both request fingerprints, logical operation, attempt/native
  turn, binding, submission, v3 result/read-back, retirement, reconciliation,
  and recovery state; prove no second submission or native turn/start occurs.
- [x] Step 4: Inspect final Git scope, stale-symbol searches, temporary artifact
  cleanup, and all completion criteria; only then record `verified` evidence and
  allow the plan status to transition to `completed`.

**Verification:**
- [x] `py -B -m pytest -q tests/test_codex_app_server.py tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_parallel_dispatch.py tests/test_skill_chief_of_staff.py`
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-16-08-native-semantic-recovery-hardening-plan.md`
- [x] `py -B -m pytest -q`
- [x] `git diff --check`
- [x] `rg -n "LightRSIResultReader|_observe_bound_lightrsi_result|_configured_lightrsi_reader|PROJECT_OS_CODEX_NATIVE_APP_SERVER" scripts tests docs/operating_system` — no current matches
- [x] `rg -n "pre_submit_cursor" scripts tests docs/operating_system` — only historical v1/v2 compatibility code and tests
- [x] `$probe = [guid]::NewGuid().ToString('N'); $out = ".tmp-tests/native-semantic-recovery-hardening/$probe/live-result.json"; py -B scripts/secretary_live_runtime.py run --output $out --cwd . --task "Return the word READY and nothing else."; py -B scripts/secretary_live_runtime.py run --resume --output $out --cwd . --task "Return the word READY and nothing else."`
- Expected: all declared checks pass; the initial run and immediate resume have
  equal request fingerprints, one logical operation and native attempt/turn,
  `reconciled=true`, no second submission or turn/start, retained retirement
  evidence, and current v3 publication/read-back, or an immutable named
  capability blocker is recorded without synthetic success.

Live proof evidence: probe `ac6a737356a34d8292d83f2ba371b5cb` returned `READY`
on both runs with fingerprint
`d6020e902aed99473dff4d00b031ef5d69c15e10d64cd2ec6ff90a2eb894f4b1`, logical
operation `b02962f552e249aebfd261ae95c50dea`, attempt
`814c7009fb464ef1a4d4e0ed5f1b039e`, native thread/session
`01a154c7-030a-7631-880e-0179f3438fc1`, and native turn
`01a154c7-0857-7651-9b70-213905965c03`. The resume returned `reconciled=true`,
retirement `retired`, `recovery_required=false`, and no second submission or
native turn/start was observed. The disposable probe root was removed after
capturing these facts.

**Exit Criteria:**
- Code, tests, documentation, validators, and this plan agree; fresh
  verification returns `verified`; no required task, blocker, or scope
  deviation remains unrecorded.

## Verification

- Focused native/result/lifecycle/compatibility/CoS preservation matrix listed
  in Task 7.
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-16-08-native-semantic-recovery-hardening-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One bounded native Secretary run followed by immediate `--resume` against the
  same output and task, proving exact request binding, unchanged fingerprint,
  v3 publication/read-back, reconciliation without a second turn/start, and
  independent retirement evidence, or immutable named capability-blocker
  evidence.

## Completion Criteria

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` and fresh evidence
proves:

1. Runtime-owned output, sidecar, and atomic-write artifacts never alter the
   task-input fingerprint; bounded or uncertain identity disables reuse without
   blocking fresh execution.
2. Tracked output paths are rejected, foreign/unknown output namespaces are
   read-only, and binding/submission/reconciliation failures cannot clobber
   prior evidence.
3. Success and failure paths preserve independently bound retirement evidence;
   only genuinely uncertain resources require recovery.
4. Writer close is deterministic under a full queue, sends are rejected after
   closing, and bounded joins retain explicit unknown state when needed.
5. The active top-level Codex provider, model, repository, Git, and workspace
   identities match the native launch evidence and are resolved from one
   immutable context.
6. Direct v3 projection bypasses historical semantic arbitration; v1/v2 remain
   read-only compatibility surfaces; pre-#107 v3 is not silently reusable.
7. No new observer, registry, daemon, schema, retry policy, Herdr semantic path,
   or LightRSI integration is introduced.
8. Focused tests, repository validators, the full suite, diff check, and bounded
   live proof pass, or an exact immutable upstream capability blocker is
   recorded without synthetic success.
9. Every Project OS-created persistent lock file and recoverable temporary
   publication artifact is excluded from task-input identity by exact
   path/prefix.
10. Tracked-diff/status collection is bounded as well as untracked-file
    collection; exceeding any identity budget disables reuse instead of
    exhausting memory.
11. An empty namespace is only claimable, not owned; ownership is established
    by an atomic current-attempt claim, and losing that claim cannot write
    output.
12. A live run followed immediately by `--resume` against the same unchanged
    workspace has the same request fingerprint and performs no second
    turn/start.

Branch creation, commit, push, pull request, merge, and worktree cleanup remain
separate authorized actions and are not completion criteria for this plan.
