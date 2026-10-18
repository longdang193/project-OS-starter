---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: lightrsi-native-result-reader-and-publication-boundary
targets:
  - scripts/secretary_live_runtime.py
  - scripts/herdr_main_launcher.py
  - scripts/project_os_runtime/lightrsi_reader.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/secretary_evidence_adapter.py
  - tests/test_secretary_live_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_lightrsi_reader.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - external: C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader
---

# LightRSI Native Result Reader And Publication Boundary

## Review Findings

- Adopt the proposal's authority split: LightRSI owns semantic truth, Project
  OS owns attempt binding and durable publication, Herdr owns execution and
  lifecycle evidence, CoS owns acceptance, and 9router owns observability.
- Reconcile the implementation baseline before coding. Project OS `origin/main`
  at `89556f8ebcf93d3e1083c137f1fdf0ac7adccdf7` already contains
  `scripts/project_os_runtime/secretary_results.py`, `publish_native_result`,
  tests, and the `native_completed_turn` transport path. Modify that canonical
  publisher; do not add a competing `native_results.py` module.
- Keep lifecycle receipt parsing separate from the semantic native-result
  contract. The existing `secretary_results.py` remains the publication owner;
  the LightRSI adapter supplies semantic input without changing
  `dcode-project.result.v1` receipt meaning.
- Make the missing durable binding explicit. The normal `run` path currently
  has an `invocation_id` but no persisted native session/turn cursor before
  submission. Persist a per-invocation binding before prompt delivery and
  reconcile it before any retry or resubmission; do not create a global result
  registry.
- Make the LightRSI reader contract explicit before implementation. The
  proposal names four states but also requires aborted, incomplete, unresolved
  continuation, and conflict handling. Use `completed`, `pending`,
  `unavailable`, and `conflict`, with stable rejection reasons under the
  non-completed states; only `completed` may publish semantic content.
- Treat the existing independent runtime projections as invariants, not as a
  reason to redesign the whole output envelope. A confirmed semantic result
  must survive cleanup uncertainty; strict receipt and provider telemetry may
  remain probe-only evidence.
- Pin the LightRSI checkout/runtime commit and local CLI build during admission.
  Do not depend on `Get-Command lightrsi` or a persistent global install. No
  implementation or live claim is valid if Project OS invokes a different
  source tree, build artifact, or source diff from the reader tested in the
  LightRSI worktree.

## Goal

Replace Herdr pane/agent observation as the authoritative normal Secretary
semantic-result path with a narrow, attempt-bound LightRSI completed-turn
reader and a durable Project OS native-result publication boundary, while
preserving fail-closed attribution, stale-result rejection, cleanup safety,
CoS acceptance authority, and truthful probe/telemetry reporting.

## Implementation Outcomes

### Attempt-bound LightRSI semantic authority

LightRSI exposes a stable JSON completed-turn reader and `codex completed-turn`
CLI operation backed by its existing Codex journal, effective-history, and
rollout interpretation. Project OS captures a pre-submit native cursor or
explicit native request/turn acknowledgement, binds it to the invocation, and
accepts only a fresh terminal assistant turn from that binding.

### Durable native-result publication

Project OS validates and atomically publishes a bounded
`secretary-native-result.v1` record whose semantic identity is independent of
Herdr transport metadata. Replaying the same attempt/native turn/content is
idempotent and preserves the first publication; a different native identity or
content digest remains a conflict.

### Independent evidence planes and truthful recovery

Normal execution reports semantic result, execution, resource settlement,
acceptance, and observability independently. Herdr pane text remains
diagnostic only. Missing strict receipts or 9router rows do not erase an
available semantic result. Recovery reconciles the persisted binding/result
before submitting again and never uses latest-result, prompt-text, timestamp,
pane, or Herdr completion sequence alone as attribution.

### Cross-repository verification and rollout readiness

The LightRSI and Project OS test suites prove the contract and rejection cases,
and one fresh live probe proves exact binding, LightRSI final-turn proof,
native publication, and read-back. Cleanup, CoS acceptance, and 9router
observability are recorded as separate outcomes.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-systematic-debugging`, `skill-verification-before-completion`
- Isolation: `current workspace` for this plan and an approved isolated worktree for the LightRSI checkout before external edits
- Commit policy: `no commits during execution`; checkpoint commits require explicit authorization after fresh verification
- Preauthorized local actions: inspect declared repositories, edit declared files, add focused tests and docs, run declared local checks, and run one disposable task-owned live probe after all contract tests pass
- User-approval actions: external installation, persistent global hook/runtime changes, push, merge, production rollout, destructive cleanup, or deleting retained evidence
- Parallel ownership: `none`; the LightRSI contract, Project OS adapter, and live proof are dependency-ordered
- Sequential fallback: contract admission -> LightRSI reader -> Project OS native contract -> runtime integration -> documentation/evidence reconciliation -> final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `89556f8ebcf93d3e1083c137f1fdf0ac7adccdf7` accepted target baseline; current checkout is reconciled to this commit
- Expected workspace: preserve the untracked plan and the isolated LightRSI worktree from `7e4147674c018f0654b3840704e0d0ee8c9e9330` without modifying the original detached checkout
- Next action: retain the upstream handoff blocker and rerun the disposable positive probe only after Herdr/Codex exposes a child-native session rollout before prompt delivery
- Blockers: upstream Herdr/Codex launch does not currently create or expose a new native Codex rollout before `agent prompt`; Project OS now fails closed rather than substituting the Herdr transport session

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current + LightRSI worktree | `codex` | none | baseline inventory and frozen cross-repo contract | Project OS `89556f8ebcf93d3e1083c137f1fdf0ac7adccdf7`; LightRSI `7e4147674c018f0654b3840704e0d0ee8c9e9330`; tree `398d5a63ec703f88dbd382a984516c61f0680fab`; diff `e3b0c44298fc1c149af4c8996fb92427ae41e4649b934ca495991b7852b855`; CLI SHA-256 `7fbcae29e6eddc7adf2051764d16e5d8d894e27b0788dee35e759679d87d0290`; direct build passed |
| Task 2 | `completed` | LightRSI worktree | `codex` | Task 1 | LightRSI unit, CLI, and type checks | adapter suite `602 passed`; CLI suite `39 passed`; typecheck passed; direct build `components/products/cli/dist/cli.js` passed; source fingerprint `3749139e35d73817b9df9d01f0c11abc09f072a2be8df11ba017845092a64903`; artifact SHA-256 `b38847eb4608e7a9381401e0372d306fe6933e736fb0140a7dc72f5240acdd26`; fresh and missing-session probes passed |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | native-result contract and idempotency tests | `20 passed` focused reader/publication tests; `182 passed` with Secretary runtime compatibility; compileall and diff check passed |
| Task 4 | `completed` | current | `codex` | Tasks 2-3 | runtime binding, reader wait, and state-plane tests | focused launcher/runtime suite `393 passed`; native handoff now uses an atomic pre-submit artifact plus acknowledgement gate; transport session/env aliases are not used as native identity; no normal resubmission loop exists, so retry-reconciliation remains a covered publication/reader idempotency scope rather than a live retry path |
| Task 5 | `completed` | current | `codex` | Task 4 | probe/evidence/docs regression checks | evidence/docs suite `41 passed`; missing 9router usage is `inconclusive`; strict receipt remains probe-only; runtime surfaces and tool-resolution docs updated; legacy pane/native-turn paths remain diagnostic-only |
| Task 6 | `blocked` | current plus LightRSI worktree | `codex` | Tasks 2-5 | fresh end-to-end live proof and final validators | Project OS full suite `1435 passed, 2 skipped`; focused launcher/runtime suite `393 passed`; LightRSI typecheck passed; LightRSI CLI suite `39 passed`; lifecycle validator passed; `compileall` and `git diff --check` passed; pinned CLI probe returned bounded `session_unavailable`; fresh live invocation `776c51b535c24e8f8562618c509a757c` reached Herdr preflight and settled workspace `w63`, but Herdr startup produced zero new Codex rollout files (six pre-existing), so the new handoff gate blocked before prompt and no positive semantic claim is made |

## Task Breakdown

### Task 1: Reconcile and freeze the effective cross-repository baseline

**Purpose:**
- Reconcile the stale local checkout with the accepted Project OS baseline and
  convert the reviewed recommendation into testable schemas, state mappings,
  identity rules, and a pinned runtime boundary before either repository is
  changed.

**Task Function:**
- Establish source-of-truth boundaries, inspect the existing PR #101 publisher,
  and expose any remaining baseline mismatch before implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-first contract admission; no implementation authority
  is needed.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent review of cross-repository identity and
  rejection semantics before implementation.

**Specification Coverage:**
- Review Findings; Goal; attempt-bound authority; independent evidence planes;
  no latest-result attribution.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:SecretaryNormalRequest`,
  `run_normal`, `_observe_submitted_codex`, `_normalize_invocation_outcome`
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Inspect: `scripts/project_os_runtime/secretary_results.py:_validate`,
  `publish_native_result`, `parse_native_result`, `native_result_path`
- Inspect: `scripts/project_os_runtime/results.py:parse_result_receipt`,
  `evidence_path_lock`
- Inspect external worktree: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/adapters/codex/src/context-history/types.ts`,
  `rollout-parser.ts`, `effective-history.ts`, `index.ts`,
  `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/products/cli/src/hosts/codex.ts`,
  `dispatch.ts`
- Verify: Project OS `origin/main` baseline, LightRSI remote `main`, the
  isolated worktree, and the absolute local CLI build path used for all later
  calls

**Dependencies:**
- Project OS refs and the detached LightRSI checkout are readable; the current
  untracked plan is preserved while execution admission reconciles the target
  baseline.

**Authority:**
- Preauthorized local actions: inspect refs and source, reconcile the execution target to the accepted baseline without discarding the plan, create the approved isolated LightRSI worktree, and update this plan with frozen contract decisions.
- Stop for: missing external checkout, dirty/unowned changes outside the plan, inability to establish the accepted Project OS or LightRSI baseline, or any request to modify a persistent/global runtime during admission.

**Steps:**
- [x] Reconcile the Project OS implementation target to
  `89556f8ebcf93d3e1083c137f1fdf0ac7adccdf7` or a recorded newer accepted
  successor, then inspect the existing `secretary_results.py` publisher and
  `native_completed_turn` path before changing any target list.
- [x] Create the isolated LightRSI implementation worktree from remote
  `main` at `7e4147674c018f0654b3840704e0d0ee8c9e9330` or newer; record the
  base commit, source diff/tree fingerprint, built `dist/cli.js` artifact
  digest, and the absolute `node .../components/products/cli/dist/cli.js`
  command path. Do not use `Get-Command lightrsi` as the runtime binding.
- [x] Freeze reader JSON schema `lightrsi.codex.completed-turn/v1` with
  `completed`, `pending`, `unavailable`, and `conflict` states. Define reasons
  for aborted turns, incomplete history, unresolved tool calls, missing turn
  boundaries, stale cursors, wrong sessions, and multiple candidates. Only
  `pending` is retryable; `unavailable` and `conflict` are terminal for that
  query.
- [x] Freeze one canonical turn identity: `native_turn_id` is the deterministic
  LightRSI absolute-turn ID derived from `(sessionId, turnSeq)`; retain
  `turn_seq` separately as the session-scoped monotonic cursor and never accept
  an ID-or-sequence alternative for durable identity. A completed result must
  include `sessionId`, `turnSeq`, `turnId`, request/response IDs when known,
  content digest, bounded assistant text, and semantic completeness. Normal
  publication uses `content_source=lightrsi_completed_turn`; legacy
  `native_completed_turn` remains diagnostic/compatibility evidence only.
- [x] Freeze cursor schema `lightrsi.codex.cursor/v1` with session scope and
  monotonic `turnSeq`; `after_cursor` accepts only a cursor from the bound
  session and a candidate must be strictly newer. Restart/compaction continuity
  is resolved by LightRSI, not inferred by Project OS; invalid or cross-session
  cursors are terminal `unavailable`/`conflict` outcomes with stable reasons.
- [x] Freeze multi-source precedence inside LightRSI: journal/effective-history
  owns assistant content and request/response completion; rollout evidence owns
  session/turn boundaries and abort evidence; disagreement is `conflict`, never
  a choice of the richer source.
- [x] Freeze the immutable per-invocation sidecar formed by appending
  `.native-binding.json` to the invocation output path as
  `secretary-native-binding.v1` with
  `attempt_id`, optional `assignment_id`, `lightrsi_source_fingerprint`,
  `native_session_id`, `pre_submit_cursor`, optional expected request/turn IDs,
  transport selectors, and `created_at`. Write it atomically before delivery;
  only explicit reconciliation metadata may be added later. It is not a global
  registry.
- [x] Freeze the successful join as: reader session equals binding session;
  reader turn sequence is greater than the pre-submit cursor; an expected
  request ID or expected turn ID matches, or the bound session has exactly one
  outstanding attempt; and reader state is `completed`. Define the fallback
  exclusivity as one outstanding attempt per native session/binding lane, not
  one outstanding Secretary run globally.
- [x] Define CLI exit behavior and adapter timeout/poll bounds; JSON state,
  not process exit text, remains the semantic authority.

**Verification:**
- [x] `git status --short --branch`, `git rev-parse HEAD`, and
  `git show origin/main:scripts/project_os_runtime/secretary_results.py`
- Expected: the execution target is reconciled to the accepted baseline, the
  existing publisher is present, and only the plan's preserved untracked file
  is outside Git.
- [x] `git -C "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI" ls-remote origin refs/heads/main`
- Expected: remote LightRSI `main` resolves to `7e4147674c018f0654b3840704e0d0ee8c9e9330` or a recorded newer successor.
- [x] Run the recorded absolute local LightRSI build command and hash the
  resulting `components/products/cli/dist/cli.js` artifact.
- Expected: the source fingerprint, artifact digest, and exact command path are
  recorded together and reused by Tasks 2, 4, and 6.

**Exit Criteria:**
- The reader schema, native-result identity, binding persistence owner, CLI
  contract, and exact tested runtime are recorded; no implementation starts
  with unresolved attribution semantics.

### Task 2: Implement the LightRSI completed-turn reader and CLI on the reconciled baseline

**Purpose:**
- Make LightRSI the single semantic interpreter for Codex completion,
  attribution, final-turn status, aborted evidence, and unresolved continuation.

**Task Function:**
- Extend the Codex context-history adapter with a narrow read-only result
  resolution surface.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded cross-repository TypeScript reader and CLI work with
  settled schema, moderate integration risk, and focused verification.

**Validator Profile (optional):**
- Controller-selected: `review-2`
- Selection basis: independent validation of parser completeness and CLI
  rejection behavior.

**Specification Coverage:**
- LightRSI owns semantic truth; Project OS must not parse LightRSI JSONL;
  completed turns must be fresh, terminal, assistant-owned, session/turn
  bound, and semantically complete.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/adapters/codex/src/context-history/types.ts`
- Add external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/adapters/codex/src/context-history/completed-turn.ts`
- Modify external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/adapters/codex/src/context-history/index.ts`
- Modify external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/products/cli/src/hosts/codex.ts:createCodexCliBridge`
- Modify external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/products/cli/src/usage.ts`
- Verify external: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/adapters/codex/tests/context-history-completed-turn.test.ts`, existing context-history rollout/effective-history tests, and CLI bridge tests

**Dependencies:**
- Task 1 contract and source/runtime pin complete; the isolated worktree is
  based on LightRSI `7e4147674c018f0654b3840704e0d0ee8c9e9330` or newer.

**Authority:**
- Preauthorized local actions: edit only the isolated LightRSI reader, exports, Codex CLI handler, usage text, and named tests; run LightRSI typecheck and focused tests.
- Stop for: a need to parse raw LightRSI files in Project OS, a new daemon/queue/persistence service, a schema change outside the frozen contract, or any install/global hook mutation.

**Steps:**
- [x] Add a typed resolution result with `state`, `sessionId`, monotonic
  `turnSeq`, deterministic `turnId`, request/response identity when known,
  bounded assistant text, content digest, semantic completeness, authority,
  and stable rejection reason fields.
- [x] Resolve the native session through the existing journal/effective-history
  readers and rollout evidence according to Task 1's precedence rule; do not
  duplicate parser rules in the CLI handler and do not select the richer source
  when sources disagree.
- [x] Require a unique candidate strictly after the typed `after_cursor`, or a
  matching explicit request ID or canonical turn ID. Reject stale,
  wrong-session, duplicate, and conflicting candidates; only `pending` remains
  retryable.
- [x] Reject failed/aborted turns, incomplete effective history, unresolved
  tool-call continuations, missing assistant ownership, and unavailable turn
  boundaries as stable `unavailable.reason` values. Return `conflict` for
  source disagreement or irreducible candidate ambiguity.
- [x] Expose `lightrsi codex completed-turn --session SESSION_ID --after CURSOR
  [--request REQUEST_ID] [--turn TURN_ID] --json` through the existing
  Codex host CLI path. The cursor is the frozen
  `lightrsi.codex.cursor/v1` value; keep output bounded and machine-readable.
- [x] Add fixture-driven tests for fresh completion, stale cursor, wrong
  session, aborted/incomplete turn, unresolved continuation, duplicate
  candidate, conflict, and bounded secret-safe content.

**Verification:**
- [x] Run `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" lightrsi:typecheck`.
- Expected: TypeScript typecheck passes for the reader and CLI changes.
- [x] Run `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" --filter @lightrsi/codex test -- context-history`.
- Expected: existing context-history behavior plus the new resolution cases pass.
- [x] Run the CLI against fixtures for each frozen state.
- Expected: completed returns only the authoritative bounded result; all other
  states return their frozen JSON state and never semantic content.

**Exit Criteria:**
- A pinned LightRSI build can answer the completed-turn query without Project
  OS interpreting journals, and all rejection cases are covered by tests.

### Task 3: Extend the existing Project OS native-result contract and add the LightRSI adapter

**Purpose:**
- Provide reusable, atomic, bounded Project OS primitives for reading the
  LightRSI CLI, validating native semantic results, publishing them, and
  reconciling replayed observations.

**Task Function:**
- Migrate the existing semantic publication boundary to consume the frozen
  LightRSI result without changing lifecycle receipt ownership.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded backend contract work after the external reader
  schema is executable.

**Validator Profile (optional):**
- Controller-selected: `review-3`
- Selection basis: independent check of idempotency, conflict, redaction, and
  atomic publication semantics.

**Specification Coverage:**
- Durable native-result publication; stable canonical turn identity/content
  digest; first publication metadata preservation; no Herdr/native-session
  namespace equality; no lifecycle-receipt overloading.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Add: `scripts/project_os_runtime/lightrsi_reader.py:LightRSIResultReader`
- Modify: `scripts/project_os_runtime/secretary_results.py:_validate`,
  `publish_native_result`, `parse_native_result`, `native_result_path`
- Add only if required by the stable equality implementation:
  `native_result_identity`
- Verify: `tests/test_lightrsi_reader.py`, `tests/test_secretary_results.py`
- Reuse: `scripts/project_os_runtime/results.py:evidence_path_lock` and its
  atomic-file conventions without changing `dcode-project.result.v1`

**Dependencies:**
- Task 1 frozen schemas; Task 2 executable LightRSI CLI.

**Authority:**
- Preauthorized local actions: add the LightRSI adapter, modify the existing publisher and focused tests, reuse existing atomic locking, and run direct boundary tests.
- Stop for: changing lifecycle receipt meaning, adding a global registry, accepting content without canonical LightRSI identity, weakening size/secret checks, or publishing over an existing conflicting result.

**Steps:**
- [x] Implement `LightRSIResultReader` with the absolute CLI path from Task 1,
  bounded subprocess timeout, JSON-only parsing, state validation, and one
  diagnostic error record per failed/expired wait. Capability-check this path
  before any normal prompt delivery.
- [x] Extend `secretary-native-result.v1` validation with maximum byte limits,
  safe text/redaction rules, required canonical `native_session_id`,
  `native_turn_id`, `turn_seq`, semantic completeness, and content digest
  verification. Keep `native_completed_turn` as a compatibility/diagnostic
  input during migration; it is not the new semantic source of truth.
- [x] Implement atomic publication and read-back. For an existing result,
  compare `attempt_id`, canonical native session/turn identity, `turn_seq`, and
  content digest; return idempotent for the same result while preserving
  original bytes and observation metadata; raise a fail-closed conflict for
  different native identity or content.
- [x] Keep Herdr transport fields optional diagnostics and never use them in
  semantic equality or native-session validation.
- [x] Add tests for valid LightRSI publication, malformed/oversized/secret-
  bearing payloads, wrong attempt, same-result replay with a changed
  observation time, native-identity conflict, content conflict, atomic
  replacement, compatibility diagnostics, and read-back.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_lightrsi_reader.py tests/test_secretary_results.py`
- Expected: all contract, idempotency, conflict, and failure-path tests pass.
- [x] Inspect a published fixture with two different `observed_at` values.
- Expected: same semantic identity is idempotent and the first persisted
  observation metadata remains unchanged.

**Exit Criteria:**
- Project OS has a tested, durable semantic publication boundary and a reader
  adapter that cannot confuse transport diagnostics with native identity.

### Task 4: Bind normal invocations and consume LightRSI results

**Purpose:**
- Make the normal Secretary path use the attempt-bound LightRSI reader while
  retaining Herdr as execution/lifecycle observation only.

**Task Function:**
- Integrate native submission binding, bounded semantic waiting, result
  normalization, and recovery reconciliation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: material runtime behavior change with cross-module impact;
  resolve only after Tasks 2 and 3 are accepted.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent review of attribution and retry safety.

**Specification Coverage:**
- Pre-dispatch capability admission; submission-time native binding;
  exclusive-session fallback; no latest-result attribution; Herdr
  diagnostic-only observation; semantic result independent from cleanup and
  telemetry; reconcile before retry.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `scripts/secretary_live_runtime.py:SecretaryNormalRequest`,
  `build_normal_launcher_command`, `run_normal`,
  `_observe_submitted_codex`, `_normalize_invocation_outcome`,
  `_normal_managed_result_capability_available`
- Inspect and modify only if required: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`
- Reuse: `scripts/project_os_runtime/secretary_results.py` and the invocation
  output path plus `.native-binding.json` sidecar contract frozen in Task 1
- Verify: `tests/test_secretary_live_runtime.py`,
  `tests/test_herdr_main_launcher.py`, `tests/test_secretary_results.py`

**Dependencies:**
- Tasks 2 and 3 complete; reader executable is pinned and capability-checkable.

**Authority:**
- Preauthorized local actions: edit the named normal-runtime integration and focused tests, run mocked/direct boundary tests, and preserve existing diagnostic Herdr evidence.
- Stop for: failed LightRSI capability admission, missing explicit native
  acknowledgement without a proven exclusive-session/pre-submit-cursor
  fallback, more than one outstanding attempt in the bound native session,
  cross-session result, stale result, or retry before persisted
  binding/result reconciliation.

**Steps:**
- [x] Before prompt delivery, capability-check the exact LightRSI command,
  schema, and source/artifact fingerprint recorded in Task 1. Fail the normal
  invocation immediately if the configured build cannot answer the frozen
  completed-turn query; do not submit an attempt that cannot produce
  authoritative evidence. The reader checks the frozen schema and validates
  `LIGHTRSI_ARTIFACT_SHA256` when configured; source fingerprint remains recorded
  in the immutable binding sidecar.
- [x] Generate one stable normal invocation/attempt identity and atomically
  write the invocation output path plus `.native-binding.json` before prompt
  delivery. Record the
  native session, typed pre-submit cursor, optional request/turn acknowledgement,
  LightRSI source/build identity, and transport selectors in separate
  namespaces. Keep the sidecar immutable except for explicit reconciliation
  metadata.
- [x] Prefer an explicit native request/turn acknowledgement. If unavailable,
  require an exclusive native session, pre-submit cursor, and exactly one
  outstanding attempt in that session/binding lane; do not use latest result,
  prompt text, wall-clock proximity, Herdr completion sequence, or pane
  contents as proof.
- [x] Poll `LightRSIResultReader` until completed, pending, unavailable, or
  conflict. Retry only `pending`; treat `unavailable` and `conflict` as
  terminal for that query. Use Herdr `agent get`/`agent read` only for
  execution/lifecycle diagnostics and perform one bounded diagnostic
  collection on failure or timeout.
- [x] Publish a confirmed completed turn through `publish_native_result`, then
  read it back and pass only the validated semantic result to
  `_normalize_invocation_outcome`.
- [x] Keep execution, semantic result, resource settlement, and observability
  fields independent. A confirmed result survives cleanup failure and is
  accompanied by `resource.state=quarantined` or `recovery_required=true` as
  appropriate.
- [x] Before any retry/resubmission, recover in this order: read the persisted
  binding, read the existing native result, query LightRSI, then resubmit only
  when no confirmed result exists and the binding remains eligible. Reuse an
  idempotent confirmed result, stop on conflict, and reject stale/ambiguous
  bindings.
- [x] Retain `native_completed_turn` and current Herdr freshness/pane-content
  logic as diagnostic compatibility evidence during migration; remove their
  authority to create or publish the normal semantic result.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py`
- Expected: existing delivery/cleanup tests pass; new tests prove native
  binding, reader state handling, stale rejection, and independent cleanup.
- [x] Add and run focused cases for preflight rejection, fresh bound
  completion, wrong session, wrong turn, stale cursor, unresolved
  continuation, aborted turn, terminal pane text without LightRSI completion,
  duplicate observation, identity conflict, cleanup failure after confirmed
  result, and binding/result-first retry reconciliation.
- [x] Verify the normal CLI return code reports semantic availability without
  requiring a strict probe receipt.

**Exit Criteria:**
- Normal Secretary can report an exact LightRSI-confirmed semantic result, or
  truthful unavailable/conflict state, without Herdr transport impersonating
  native semantic authority.

### Task 5: Reconcile probe evidence, documentation, and compatibility

**Purpose:**
- Preserve strict probe qualification and update maintained documentation to
  describe the new authority boundaries without making probe-only failure
  block ordinary semantic results.

**Task Function:**
- Align evidence adapters, runtime documentation, and compatibility tests with
  the implemented contract.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: documentation and integration reconciliation after runtime
  behavior is proven.

**Validator Profile (optional):**
- Controller-selected: `review-2`
- Selection basis: independent check that probe strictness was preserved and
  ordinary-result truth was not re-coupled to telemetry.

**Specification Coverage:**
- Strict receipts remain probe/benchmark evidence; CoS acceptance remains
  independent; missing 9router usage is observability `inconclusive`; Herdr
  remains transport/diagnostic evidence.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect and modify: `scripts/secretary_evidence_adapter.py:_secretary_receipt`,
  `build_evidence_bundle`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`,
  `docs/operating_system/tooling/runtime-tool-resolution.md`
- Verify: `tests/test_secretary_evidence_adapter.py`,
  `tests/test_secretary_receipts.py`, `tests/test_runtime_tool_resolution_contract.py`

**Dependencies:**
- Task 4 produces the final normal-runtime state shape.

**Authority:**
- Preauthorized local actions: edit only the named evidence/docs surfaces and regression tests; run documentation/contract validators and focused tests.
- Stop for: making probe readiness the normal semantic-result gate, promoting provider telemetry into semantic truth, changing CoS acceptance authority, or publishing credentials/raw transport data.

**Steps:**
- [x] Keep `runtime_structured_receipt_missing` as a probe-readiness reason
  where strict probe evidence is required, but prevent it from rewriting a
  confirmed normal semantic result.
- [x] Represent missing or incomplete 9router usage as observability
  `inconclusive`, not semantic failure.
- [x] Document the native authority, explicit native-session handoff and
  binding contract, result contract,
  diagnostic Herdr role, recovery rule, and independent state planes.
- [x] Update compatibility tests so old `agent read`/pane paths remain useful
  diagnostics but cannot promote terminal text to semantic success.
- [x] Record rollback: disable the normal LightRSI adapter capability flag and
  return `semantic_result=unavailable` while preserving diagnostic and cleanup
  evidence; do not restore pane text as semantic authority.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_secretary_evidence_adapter.py tests/test_secretary_receipts.py tests/test_runtime_tool_resolution_contract.py`
- Expected: strict probe evidence remains strict, normal semantic result is not
  downgraded by missing receipt/telemetry, and sensitive fields remain blocked.
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- Expected: plan/documentation contract checks pass.

**Exit Criteria:**
- Maintained docs and evidence adapters describe the implemented authority
  boundaries, and compatibility tests prevent semantic re-coupling.

### Task 6: Run final cross-repository qualification and record evidence

**Purpose:**
- Prove the integrated path against fresh source, focused tests, and one
  disposable live invocation without overstating cleanup, acceptance, or
  telemetry.

**Task Function:**
- Execute final verification, classify outcomes, and reconcile the plan ledger.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and evidence ownership stay with the lead
  controller.

**Validator Profile (optional):**
- Controller-selected: `review-3`
- Selection basis: independent final review of live evidence and stale-result
  rejection.

**Specification Coverage:**
- Implementation Outcomes; all reviewed acceptance cases; fresh end-to-end
  binding -> LightRSI proof -> publication -> read-back.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: LightRSI reader/CLI tests and typecheck
- Verify: Project OS focused and full test suites
- Verify: `scripts/secretary_live_runtime.py run`, generated invocation output,
  native-result publication, read-back, cleanup, and provider evidence
- Modify: this plan's ledger/evidence only after proof is accepted

**Dependencies:**
- Tasks 2-5 complete and all required focused checks pass.

**Authority:**
- Preauthorized local actions: run declared tests, validators, one disposable live normal invocation, read-only post-run cleanup/resource checks, and update this plan with immutable evidence identifiers.
- Stop for: live evidence that cannot prove exact binding, unverified cleanup/resource ownership, stale or conflicting result, source/build identity mismatch, failed required check, or any external publication/rollout request.

**Steps:**
- [x] Run LightRSI typecheck and focused adapter/CLI tests from the isolated
  worktree at `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader`.
- [x] Run Project OS focused native-result, runtime, launcher, receipt, and
  evidence tests, then the full Python suite.
- [x] Run `git diff --check` and planning/runtime validators.
- [x] Invoke the modified LightRSI build directly through the absolute
  `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader/components/products/cli/dist/cli.js` path; do not resolve a global `lightrsi` binary.
- [x] Run one disposable `secretary_live_runtime.py run` with a unique nonce
  and record the binding, LightRSI state, native-result identity, publication
  status, read-back, cleanup/resource state, CoS acceptance state, and 9router
  observability state separately. The new launcher/runtime handshake captured
  no child-native rollout from Herdr before prompt delivery, so the invocation
  blocked closed-loop and the positive path remains upstream-blocked; rejection
  cases remain fixture/integration evidence.
- [x] Exercise or fixture-check the following matrix:
  fresh bound final assistant turn -> semantic confirmed;
  wrong session/turn/stale cursor -> terminal unavailable/conflict;
  unresolved tool continuation -> terminal unavailable;
  aborted turn -> terminal unavailable;
  pane text without LightRSI final turn -> semantic unavailable;
  same completed result twice -> idempotent with original metadata;
  different native identity/content -> conflict;
  confirmed result plus cleanup failure -> result confirmed/resource quarantined;
  confirmed result plus missing 9router usage -> observability inconclusive.
- [x] Update the task ledger only with command output, test counts, live nonce,
  immutable commits/paths, and explicit unavailable/blocked outcomes.

**Verification:**
- [x] `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" lightrsi:typecheck`
- [x] `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" lightrsi:test`
- [x] `py -3 -m pytest -q`
- [x] `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- [x] `git diff --check`
- Expected: all required checks pass, or the plan records exact failed,
  unavailable, or blocked evidence without marking completion.

**Exit Criteria:**
- Fresh proof establishes the native result contract end to end, all required
  rejection/idempotency cases are covered, independent operational planes are
  recorded, and no unresolved required task or scope deviation remains.

## Verification

- `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" lightrsi:typecheck`
- `pnpm --dir "C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI-lightrsi-native-result-reader" lightrsi:test`
- `py -3 -m pytest -q`
- `py -3 scripts/validate_planning_lifecycle.py --repo-root .`
- `git diff --check`
- One fresh disposable live `secretary_live_runtime.py run` with exact
  LightRSI binding and native-result read-back evidence.

## Completion Evidence

- Verification result: `verified` for the approved implementation scope;
  positive live semantic proof remains upstream-blocked.
- Workspace: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter`; native
  local checkout; no commits, pushes, merges, installations, or global hook
  changes.
- Project OS proof: full suite `1435 passed, 2 skipped`; focused launcher/runtime
  suite `393 passed`; `compileall` passed; `git diff --check` passed;
  `git diff --check` passed.
- LightRSI proof: pinned `lightrsi:typecheck` passed; CLI suite `39 passed`;
  direct absolute CLI probe returned bounded
  `lightrsi.codex.completed-turn/v1` `session_unavailable`; artifact SHA-256
  `b38847eb4608e7a9381401e0372d306fe6933e736fb0140a7dc72f5240acdd26` and
  source fingerprint `3749139e35d73817b9df9d01f0c11abc09f072a2be8df11ba017845092a64903`
  match the Task 2 record.
- Disposable live attempt: nonce `a51241b736b14da2867cecb68e77a781`, invocation
  `4e584926a9af4aeab99b6e2dfa8bed48`; blocked before prompt because no native
  LightRSI session/cursor was configured. Herdr preflight reached `ready`, the
  task-owned workspace `w5V` closed with verified cleanup, and semantic result
  remained truthfully `unavailable`; no positive live semantic claim is made.
- Post-completion defect investigation: Herdr launches a separate Codex child
  process, but the launcher exposes only the Herdr transport session/pane and
  does not currently create or expose a new child-native rollout before
  `agent prompt`. The former implementation therefore fell back to
  `SecretaryNormalRequest.session`, causing LightRSI to poll the parent session
  and time out (`3cb14d08e5c048399d536080fc555717`, 120 seconds;
  `0b8b329240c64d50a3d08ae61908e501`, 30 seconds). Project OS now uses an
  atomic launcher-to-runtime handoff plus acknowledgement gate and never uses
  the transport session or environment aliases as native identity. The
  confirmed residual blocker is upstream native-session creation/exposure.
- Fresh fail-closed live proof after the handoff implementation: pinned
  LightRSI CLI path and artifact digest were accepted; invocation
  `776c51b535c24e8f8562618c509a757c` reached Herdr preflight, observed six
  pre-existing rollout files and zero new child rollout files, blocked before
  prompt with `LaunchBlocked`, and settled task-owned workspace `w63` with
  verified cleanup. The output remained semantic `unavailable`/resource
  `settled`; no LightRSI polling timeout occurred.
- Residual scope: normal retry/resubmission orchestration is not present in the
  current CLI path; retry safety is covered through persisted binding/result
  reconciliation primitives, pending polling, idempotency/conflict tests, and
  explicit terminal-state handling rather than a live resubmission loop.

## Completion Criteria

The plan is ready for completion verification when:

1. LightRSI exposes and tests the frozen completed-turn reader contract.
2. Project OS publishes and reads back bounded attempt-bound native results
   with stable idempotency/conflict semantics.
3. Normal Secretary consumes LightRSI semantic truth without using Herdr pane
   text, latest result, or completion counters as attribution.
4. Execution, semantic result, resource settlement, acceptance, and
   observability remain independently represented.
5. Strict probe receipt/telemetry requirements remain probe-only and are not
   promoted into ordinary semantic failure.
6. Focused tests, full tests, cross-repository checks, validators, and one fresh
   live proof pass or are recorded as explicit unavailable/blocked evidence.
7. Plan deviations, runtime/version pins, rollback behavior, and immutable
   evidence identifiers are recorded.

The plan may be marked `completed` only after
`skill-verification-before-completion` runs fresh final verification, confirms
these criteria against repository evidence, and returns `verified`.

## Stop Conditions

- Stop if the LightRSI reader cannot prove session/turn/request attribution or
  if the direct local CLI differs from the recorded source fingerprint or
  artifact digest.
- Stop if multiple outstanding native submissions make the fallback binding
  ambiguous within one native session/binding lane; do not broaden the fallback
  heuristics or serialize unrelated sessions.
- Stop if a change would make Herdr, pane text, provider telemetry, cleanup,
  strict receipts, or CoS acceptance a substitute for semantic truth.
- Stop if the execution checkout is not reconciled to the accepted Project OS
  baseline or if the existing `secretary_results.py` publisher would be
  bypassed by a competing module.
- Stop before any persistent global installation, hook update, push, merge,
  production rollout, destructive recovery, or deletion of retained evidence.


