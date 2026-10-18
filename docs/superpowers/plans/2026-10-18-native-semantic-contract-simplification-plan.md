---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: native-semantic-contract-simplification
parent_spec: none
targets:
  - scripts/herdr_main_launcher.py
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/project_os_runtime/lightrsi_reader.py
  - tests/test_herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - tests/test_lightrsi_reader.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-18-native-semantic-contract-simplification-plan.md
  - external LightRSI context-history/rollout-parser.ts (compatibility oracle only)
  - external LightRSI context-history completed-turn reader, CLI, and tests
---

# Native Semantic Contract Simplification

## Review Basis

This plan reviews the supplied consolidated recommendation against the current
Project OS source at `origin/main` commit `59f7b8e8cbc12845d58b4738b46bcf0488dff73a`
and the implementation established by PR #102.

The recommendation is directionally correct, but execution must distinguish
confirmed local defects from capability-dependent upstream work:

- The attempt identity mismatch is a local integration defect. The launcher
  allocates the authoritative execution attempt, while normal Secretary currently
  generates `invocation_id` inside `run_normal()` and uses it as the native
  binding attempt ID. The fix is to carry the launcher-owned `attempt_id` back
  across the launch boundary and use `invocation_id` only for correlation.
- The rollout metadata mismatch is a compatibility defect in the cross-repository
  boundary: Project OS currently reads `payload.session_id`, while the supplied
  LightRSI parser/fixture contract uses payload.id; that existing parser/fixture is
  the compatibility oracle. Fix Project OS, and modify LightRSI only if its own
  tests expose an independent defect. Rollout-file discovery is not retained as
  ordinary attribution.
- The positive native-start proof is capability-dependent. Herdr's interactive
  start remains readiness-only, but the installed Codex app-server now provides
  an approved native path: `initialize` -> `thread/start` returns an ephemeral,
  idle child thread/session with zero prior turns before prompt submission. The
  implementation uses that path and keeps the Herdr rollout path only as a
  compatibility fallback until direct-path rollout is complete.
- The external LightRSI repository and exact installed Herdr interface are not
  present in this checkout. Their availability is a task prerequisite, not a
  reason to invent a local substitute. Project OS may consume only a documented
  opaque cursor/turn contract owned by LightRSI/Codex.

The target invariant is:

> A result is authoritative only when it is the final successful assistant
> output of the exact native turn submitted for the exact launcher attempt.

Transport identifiers, rollout paths, pane text, benchmark data, strict receipts,
cleanup, acceptance, and 9router telemetry remain independent evidence planes.
They must not be required merely because they observe the same answer.

## Goal

Simplify ordinary managed Secretary native-result attribution around one
launcher-owned attempt, one durable attempt-to-native binding, and one LightRSI
completed-turn reader, while preserving stale-result rejection, exact-turn
proof, failure/interruption rejection, atomic publication, idempotent replay,
reconciliation-before-retry, and independent cleanup/acceptance/telemetry.

## Implementation Outcomes

### One authoritative execution identity

The launcher owns and emits one `attempt_id`. Secretary uses that ID for native
binding, native result publication, cleanup, reconciliation, and retry decisions.
`invocation_id` remains correlation-only. `project_os_attempt_id` is removed
from semantic validation after compatibility coverage proves it is no longer
needed.

### Direct native binding before submission

When the installed Herdr/Codex boundary supports it, the launcher obtains a
native session/thread handle and a trusted pre-submit boundary, persists the binding
atomically before prompt delivery, submits exactly once, and records the
returned native turn/request ID when available. Rollout-directory discovery and
the temporary handoff/ACK protocol are removed from the ordinary path.

### LightRSI-owned completed-turn semantics

LightRSI owns cursor and turn-ID formats plus the bounded completed-turn wait.
Project OS treats those values as opaque and accepts only a validated completed
turn with matching native session, exact turn/request identity when available,
assistant ownership, semantic completeness, bounded content, and deterministic
content digest.

### Minimal durable publication contract

The durable native binding and `secretary-native-result.v1` retain semantic
identity, freshness, producer/authority, content, and digest proof. Herdr
transport metadata remains optional diagnostics. Existing v1 artifacts remain
readable; new publication never requires transport metadata, legacy
`native_completed_turn`, generic source arbitration, fake capability queries, or
manually managed per-run source fingerprints.

### Honest capability and failure classification

`BLOCKED_CAPABILITY` is reserved for unavailable installed interfaces or
unsupported schema/API versions. Local identity mismatches, malformed metadata,
reader incompatibility, unavailable results, conflicts, execution failures,
timeouts, settlement quarantine, and inconclusive observability receive distinct
failure classifications and remain fail-closed.

### Fresh integration proof

A real non-mocked positive path proves launcher allocation, native child identity,
pre-submit binding, exactly-once prompt submission, exact completed-turn read,
durable publication/read-back, and independent settlement. A deterministic
failure matrix covers stale, wrong, failed, interrupted, unresolved, duplicate,
conflicting, restart, cleanup, and missing-economics cases.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `fresh checkout from origin/main`; preserve this planning branch and unrelated user artifacts
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared Project OS/LightRSI source, tests, docs, and plan ledger; run declared local checks; run bounded capability probes without changing external configuration
- User-approval actions: push, merge, publication, destructive cleanup, credential/authentication changes, installing/upgrading Herdr/Codex/LightRSI, and external repository writes outside the declared LightRSI lane
- Parallel ownership: `none`; launcher, Secretary, reader, and schemas share one semantic contract
- Sequential fallback: complete identity repair and contract tests first; if native-start capability is absent, record `BLOCKED_CAPABILITY` and stop before deleting handoff/ACK code

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-semantic-contract-simplification`
- Base commit: `59f7b8e8cbc12845d58b4738b46bcf0488dff73a`
- Expected workspace: `clean checkout from origin/main`; this plan file is the only planning artifact introduced before execution
- Next action: `run publication/recovery and final verification matrices; retain the legacy handoff only as an explicit compatibility fallback until direct-path rollout has fresh positive semantic proof`
- Blockers: `accepted upstream deferral: no fresh positive semantic-result proof is claimed until the installed LightRSI reader and Codex app-server path are exercised together; this is evidence availability, not a confirmed Project OS logic defect`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | identity, compatibility, and fallback regressions | 417 focused tests passed; launcher attempt binding and payload.id compatibility fixed |
| Task 2 | `completed` | current + external LightRSI lane | `codex` | Task 1 | native-start preflight and implemented reader contract | LightRSI reader contract verified; fresh live app-server probe returned ephemeral idle thread/session with zero prior turns |
| Task 3 | `completed` | current + external LightRSI lane | `codex` | Task 2 | direct binding before prompt, no rollout attribution | app-server direct binding path implemented and covered by ordering/failure tests; fabricated JSON-RPC request ID removed; compatibility handoff retained only as explicit fallback under the accepted positive-proof deferral |
| Task 4 | `completed` | current | `codex` | Task 3 | durable publication and recovery matrix | publisher/read-back split implemented; legacy read compatibility, replay/conflict, deterministic digest, and focused runtime regressions pass (`426` focused tests) |
| Task 5 | `active` | current + external LightRSI lane | `codex` | Task 4 | live proof, docs, validators, full verification | docs/validators/full suite complete; positive semantic live proof remains the accepted upstream deferral |

## Task Breakdown

### Task 1: Repair identity, compatibility, and attribution rules

**Purpose:**
- Fix the two confirmed local defects and freeze the safe attribution rules before
  changing the transport architecture.

**Task Function:**
- Debug the current launcher/Secretary boundary and establish regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source-first debugging with shared contract risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused regression tests are sufficient for this local repair.

**Specification Coverage:**
- Launcher-owned `attempt_id` is authoritative; `invocation_id` is correlation
  only; the existing LightRSI `payload.id` parser/fixture is the compatibility
  oracle; no-turn-ID fallback is explicit and fail-closed.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py::_main_body`,
  `scripts/herdr_main_launcher.py::resolve_launch`,
  `scripts/herdr_main_launcher.py::_discover_codex_native_handoff`,
  `scripts/secretary_live_runtime.py::run_normal`,
  `scripts/secretary_live_runtime.py::_native_binding_for_submission`,
  `scripts/secretary_live_runtime.py::_result_source_authoritative`
- Modify: launcher-to-normal-runtime result boundary, Project OS rollout metadata
  compatibility, and semantic admission; do not modify LightRSI parser/fixture
  unless its own tests reveal an independent defect
- Verify: `tests/test_herdr_main_launcher.py`,
  `tests/test_secretary_live_runtime.py`, and a Project OS regression using the
  existing LightRSI `payload.id` fixture shape

**Dependencies:**
- Current `origin/main` source and the supplied review's defect claims.

**Authority:**
- Preauthorized local actions: add failing tests, make declared identity/compatibility repairs, and run focused checks.
- Stop for: changed ownership model, missing launcher result field, external parser defect not reproduced by its tests, or weakened stale-attempt rejection.

**Steps:**
- [x] Step 1: Add a real launcher/Secretary boundary regression proving the
  launcher-generated `attempt_id` is the ID persisted in binding/result and that
  `invocation_id` remains correlation-only.
- [x] Step 2: Add a Project OS regression using the existing LightRSI `payload.id`
  fixture shape; correct `_discover_codex_native_handoff()` while that diagnostic
  path still exists. Do not change the known-good LightRSI parser/fixture.
- [x] Step 3: Freeze the admissible boundary:
  `native_session_id + opaque pre_submit_cursor` for an existing/resumed session,
  or `native_session_id + launcher-proven fresh exclusively owned session + zero
  prior submissions` for a new child. A returned turn/request match is strongest;
  otherwise accept only one qualifying terminal turn after the trusted boundary
  with one outstanding submission. Never use latest-turn, prompt-text, timestamp,
  pane, or completion-counter inference.
- [x] Step 4: Thread launcher attempt through the normal launch boundary and remove
  `project_os_attempt_id` from semantic admission while retaining required legacy
  reads.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_results.py`
- Expected: identity, `payload.id`, fresh-session, resumed-session, no-turn-ID, and stale/mismatch tests pass while weaker inference remains rejected.

**Exit Criteria:**
- One attempt ID is authoritative and the exact admissible native boundary is encoded in tests and runtime validation.

### Task 2: Establish native-start capability and implement the LightRSI reader

**Purpose:**
- Verify the native-start primitives and implement the LightRSI-owned bounded
  completed-turn operation in the same task; absence of a pre-existing CLI command
  is not itself a capability blocker.

**Task Function:**
- Resolve interface ownership and deliver the semantic reader without asking
  Project OS to parse native formats.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-repository capability and backend contract work.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct preflight evidence and reader contract tests.

**Specification Coverage:**
- LightRSI owns cursor/turn formats and implements one bounded wait. Native start
  requires a session plus a trusted boundary, not always a cursor. Semantic and
  adapter failure states remain separate.

**Required Skills:**
- `skill-backend-verification`, `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py::_discover_codex_native_handoff`,
  `scripts/herdr_main_launcher.py::_codex_rollout_paths`,
  `scripts/project_os_runtime/lightrsi_reader.py::LightRSIResultReader::capability_check`,
  external `context-history/rollout-parser.ts::parseSessionMeta`
- Modify: external LightRSI completed-turn reader/CLI/tests and
  `scripts/project_os_runtime/lightrsi_reader.py` adapter only where the owned
  contract requires it
- Verify: installed Herdr/Codex start boundary, LightRSI source/tests, CLI help/version, and bounded preflight probe

**Dependencies:**
- Task 1 complete; external LightRSI checkout and installed runtime are available.

**Authority:**
- Preauthorized local actions: inspect/read-only probe installed primitives, implement the declared LightRSI reader, add contract tests, and update the Project OS adapter.
- Stop for: missing native session/thread primitive before prompt, authentication/install changes, or identity inference from rollout diffs/pane text. An absent completed-turn command is not a stop condition because this task owns its implementation.

**Steps:**
- [x] Step 1: Probe the installed Herdr/Codex start boundary for a child native
  session/thread handle before prompt delivery and classify whether the child is
  fresh/owned with zero prior submissions or requires an opaque pre-submit cursor.
  Evidence: Herdr interactive start remains readiness-only, while the installed
  `codex 0.162.1 app-server --stdio` accepts `initialize` and `thread/start` and
  returns an ephemeral idle thread/session with `turns=[]` before any prompt.
- [x] Step 2: Freeze the reader contract: semantic states are `completed`,
  `unavailable`, `conflict`, and `pending/timeout`; adapter/runtime failures are
  `reader_unavailable`, `reader_malformed`, `reader_incompatible`, and
  `reader_process_failed`.
- [x] Step 3: Implement/publish one bounded LightRSI completed-turn operation
  accepting session plus cursor or fresh-session boundary and optional returned
  turn/request ID. It must validate only the bound turn's attribution, terminal
  status, assistant ownership, unresolved continuation, and final output; unrelated
  earlier-history defects do not block a bound turn that is independently proven.
- [x] Step 4: Make cursor/turn IDs opaque to Project OS, expose declarative API/schema
  capability reporting, and map reader failures without pretending semantic absence.
- [x] Step 5: Reclassify the old Herdr-only blocker after the app-server probe;
  retain fail-closed `BLOCKED_CAPABILITY` behavior for environments without the
  app-server executable or required LightRSI reader, and continue to Task 3 only
  through the direct binding path.

**Verification:**
- [x] External LightRSI tests, Project OS reader tests, and bounded native-start preflight
- Evidence: `py -B -m pytest -q tests/test_lightrsi_reader.py` passes as part of the
  focused suite; installed CLI capability check returns `ready`; a bounded live
  app-server probe returned native thread/session identity, idle status, and zero
  prior turns before prompt submission.
- Expected: the reader is implementable from available primitives, supports fresh and resumed sessions, has one bounded wait, and returns distinct semantic/adapter states.

**Exit Criteria:**
- Native-start capability is classified; the LightRSI reader is implemented/tested and the direct app-server primitive is available. Task 3 may proceed without rollout inference.

### Task 3: Replace rollout discovery and handoff/ACK with direct binding

**Purpose:**
- Make the launch owner perform `start -> bind -> submit` once Task 2 proves the
  native-start capability.

**Task Function:**
- Remove synchronization machinery that adds no independent semantic evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-file lifecycle change with fail-closed ordering risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: launcher/runtime tests and direct ordering assertions.

**Specification Coverage:**
- No ordinary rollout-directory attribution, temporary handoff/ACK ping-pong, or
  second polling loop. The durable binding is atomic before prompt delivery.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py::_discover_codex_native_handoff`,
  `scripts/herdr_main_launcher.py::_await_native_handoff_ack`,
  `scripts/herdr_main_launcher.py::_main_body`,
  `scripts/secretary_live_runtime.py::build_normal_launcher_command`,
  `scripts/secretary_live_runtime.py::_wait_for_native_handoff`,
  `scripts/secretary_live_runtime.py::_write_native_handoff_ack`,
  `scripts/secretary_live_runtime.py::run_normal`
- Modify: launcher arguments/ordering, normal runtime orchestration, temporary
  artifact cleanup, and Project OS cursor construction; old temporary handshake
  files need no compatibility parser
- Verify: launcher/runtime tests for exactly-once submission and crash-before/after-binding cases

**Dependencies:**
- Task 2 proves native-start capability and the reader contract is implemented.

**Authority:**
- Preauthorized local actions: remove declared ordinary-path handoff/ACK code, update focused tests/docs, and run local probes.
- Stop for: binding durability not proven before prompt, a second prompt after restart, or stale-result acceptance.

**Steps:**
- [x] Step 1: Add ordering tests that fail if prompt submission precedes binding
  publication/read-back, and cover the fresh ephemeral-session boundary.
- [x] Step 2: Pass launcher attempt and native binding directly through the controlled
  app-server boundary; record returned turn/request identity when provided.
- [x] Step 3: Delete rollout discovery from the direct ordinary attribution path and
  remove its handoff/ACK dependency. The legacy rollout/handoff parser remains only
  behind the explicit compatibility fallback; full deletion is deferred under the
  accepted upstream positive-proof deferral.
  Do not use the fallback machinery for direct app-server semantic equality.
- [x] Step 4: Preserve optional Herdr diagnostics without allowing them to determine
  semantic equality.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py` — `400 passed`
- Expected: one attempt, one binding, one prompt submission on the app-server path; the compatibility handoff remains isolated until final rollout removal.

**Exit Criteria:**
- Direct binding is durable before submission and no temporary synchronization layer remains in the ordinary path.

### Task 4: Simplify durable publication and recovery

**Purpose:**
- Keep only semantic proof in durable artifacts, make digesting deterministic, and
  freeze reconciliation-before-resubmit behavior without changing other executor semantics.

**Task Function:**
- Simplify native Codex publication and recovery at the canonical Project OS boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: schema, replay, and recovery compatibility require careful contract work.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: parser/publisher and recovery regression matrix.

**Specification Coverage:**
- Transport fields are optional; reader API/schema version is semantic while exact
  executable/artifact/source digest is optional provenance. LightRSI is the sole
  semantic source for native Codex; other executors retain their existing rules.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/project_os_runtime/secretary_results.py::publish_native_binding`,
  `scripts/project_os_runtime/secretary_results.py::parse_native_binding`,
  `scripts/project_os_runtime/secretary_results.py::publish_native_result`,
  `scripts/project_os_runtime/secretary_results.py::parse_native_result`,
  `scripts/project_os_runtime/secretary_results.py::redact_semantic_content`,
  `scripts/secretary_live_runtime.py::_result_source_authoritative`,
  recovery/reconciliation paths in `scripts/secretary_live_runtime.py`
- Modify: `scripts/project_os_runtime/secretary_results.py`,
  `scripts/secretary_live_runtime.py`, and related tests; preserve DeepAgents and
  other producer arbitration behavior
- Verify: `tests/test_secretary_results.py`, `tests/test_secretary_live_runtime.py`

**Dependencies:**
- Task 3 direct binding path is complete.

**Authority:**
- Preauthorized local actions: make transport fields optional, preserve durable
  old-artifact reads, remove native-only legacy publication/arbitration, and add
  replay/conflict/recovery tests.
- Stop for: incompatible schema change without explicit migration, weakened stale-attempt protection, or cross-executor behavior changes.

**Steps:**
- [x] Step 1: Define the minimal semantic field set. Require only attempt/native
  identity, reader API/schema version, completion/freshness, bounded assistant
  content, and digest proof; keep exact reader/artifact digests optional.
- [x] Step 2: Keep schema IDs when backward-compatible; otherwise add an explicit
  versioned reader/writer while retaining read-only support for prior durable artifacts.
- [x] Step 3: Split publication from validation: `normalize_for_publication()`
  sanitizes once with a versioned policy, persists sanitized content, and hashes
  that content; `validate_persisted_result()` verifies stored content/digest and
  never re-runs current-environment redaction.
- [x] Step 4: Remove production publication of legacy `native_completed_turn`,
  generic source competition only for native Codex, fake capability payloads, and
  per-run source fingerprints. Retain diagnostic readers only where required.
- [x] Step 5: Encode the recovery table: absent binding plus proven undelivered
  prompt may create a new attempt; binding plus result uses the result; binding
  without result reconciles the same native state before any retry; uncertain
  delivery never implies not-submitted.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py tests/test_lightrsi_reader.py` — `426 passed`
- Expected: minimal artifacts publish/read atomically, identical replay is idempotent, conflicts fail closed, digest survives environment changes, and other executors retain their current result rules.

**Exit Criteria:**
- Native publication/recovery is semantic, deterministic, backward-readable, and never resubmits before reconciliation.

### Task 5: Prove, document, and verify

**Purpose:**
- Prove the integrated behavior and reconcile canonical documentation/generated
  surfaces without leaving stale architecture claims.

**Task Function:**
- Validate the backend boundary, failure matrix, documentation, and repository artifacts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material backend proof plus cross-surface consistency.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh automated output and evidence inspection.

**Specification Coverage:**
- Exact attempt/native attribution, publication before retirement, fresh-reader
  recovery, independent cleanup/acceptance/telemetry, and narrow capability blocking.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: integration fixtures/tests, `docs/operating_system/runtime/runtime-surfaces.md`, relevant canonical plan references, and generated-surface inputs only
- Verify: real launcher, installed Herdr/Codex, LightRSI reader, persisted binding/result, fresh reader process, repository validators, and full test suite

**Dependencies:**
- Tasks 1-4 complete; all blockers/deferrals recorded.

**Authority:**
- Preauthorized local actions: run one bounded live probe, deterministic failure matrix, documentation reconciliation, generated-surface checks, and declared validators.
- Stop for: missing native capability, credential/authentication need, unexpected external writes, failed required validation, or result not bound to the exact submitted turn.

**Steps:**
- [ ] Step 1: Run one real positive attempt proving launcher allocation, native child
  identity, fresh/resumed trusted boundary, exactly-once prompt submission, bound
  completed-turn read, publication/read-back, retirement, and fresh-reader recovery.
- [ ] Step 2: Run cases for unrelated concurrent session, stale cursor, wrong
  session/turn, failed/interrupted turn, unresolved continuation, malformed reader
  output, reader process failure, duplicate observation, conflicting result,
  restart recovery, cleanup failure after result, and absent 9router usage after
  confirmed result.
- [x] Step 3: Native-start primitives are available from Task 2, so no
  `BLOCKED_CAPABILITY` artifact is required; preserve fail-closed behavior for
  environments that lack the app-server executable or configured LightRSI reader.
- [x] Step 4: Update runtime ownership docs and remove stale ordinary-path references
  to rollout diff, handoff/ACK, duplicate attempts, legacy semantic publication,
  and fake capability gates; retain historical references only when labeled. The
  compatibility handoff is explicitly labeled as fallback, and the direct path
  has no handoff/ACK dependency.
- [x] Step 5: Run repository contract, planning lifecycle, focused, full, whitespace,
  and starter-kit checks when distributed runtime surfaces changed.

**Verification:**
- [ ] Fresh positive semantic live proof remains deferred to the accepted upstream
  LightRSI/Codex handoff; native-start preflight proof is retained from Task 2.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .`
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-semantic-contract-simplification-plan.md`
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_lightrsi_reader.py` — `422 passed`
- [x] `py -B -m pytest -q` — `1446 passed, 2 skipped`
- [x] `py -B scripts/build_starter_kit.py --repo-root . --output-root <task-owned-temp>`
- [x] `py -B scripts/validate_starter_kit.py --repo-root . --output-root <task-owned-temp>`
- [x] `git diff --check`
- Expected: positive proof is complete and inspectable, or the exact upstream
  primitive blocker is recorded without synthetic success; validators/tests pass.

**Exit Criteria:**
- Integrated path is proven or honestly blocked, canonical docs match code, and
  all required verification evidence is fresh.

## Verification

Final artifact-level verification only:

- `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_lightrsi_reader.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-semantic-contract-simplification-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- One fresh bounded live probe with exact attempt/native binding/result/read-back evidence, or a durable `BLOCKED_CAPABILITY` artifact naming the unavailable interface.
- Starter-kit build and validation when distributed runtime surfaces changed.

## Completion Criteria

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified` and fresh evidence
confirms:

1. One launcher-owned attempt ID is used across binding, result, cleanup,
   reconciliation, and retry; invocation ID is correlation only.
2. The rollout metadata compatibility defect is fixed and ordinary semantic
   attribution does not depend on rollout-directory diffs.
3. Native session/thread identity and a trusted pre-submit boundary are proven
   before prompt delivery. A cursor is required for an existing/resumed session; a
   fresh exclusively owned session may use proof of zero prior submissions. Native
   turn/request identity is recorded when available, otherwise the unique qualifying
   terminal turn after that boundary is required.
4. Handoff/ACK is removed only after direct identity capability is proven;
   capability absence remains fail-closed.
5. LightRSI owns cursor/turn formats and one bounded completed-turn operation;
   Project OS does not parse opaque formats, and unrelated earlier-history defects
   do not block a bound turn whose attribution, terminal state, ownership, and final
   output are independently proven.
6. Failed, interrupted, unresolved, stale, wrong-session, and wrong-turn results
   cannot publish as successful semantic results.
7. Durable publication is atomic, read-back verified, idempotent for identical
   replay, and rejects conflicting replay.
8. Semantic digesting is deterministic across restart and environment changes;
   persisted content is not redefined by ambient configuration.
9. Transport diagnostics, strict receipts, CoS acceptance, cleanup settlement,
   and 9router economics remain independent from ordinary semantic readiness.
10. Fresh-reader recovery consumes the retained result without relaunch,
    resubmission, or duplicate publication.
11. No new database, registry, event bus, supervisor, or duplicate coordination
    layer is introduced.
12. Any unavailable upstream capability is recorded as immutable blocker evidence
    and is not replaced by synthetic success. A missing pre-existing LightRSI
    command is planned implementation work, not a capability blocker when its
    underlying primitives are available.

Branch disposition, commit, push, PR, merge, and cleanup are separate authorized
actions and are not completion criteria for this plan.


