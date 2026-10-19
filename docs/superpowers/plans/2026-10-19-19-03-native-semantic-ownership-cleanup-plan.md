---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: native-semantic-ownership-cleanup
parent_spec: none
targets:
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/secretary_results.py
  - scripts/herdr_main_launcher.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-19-19-03-native-semantic-ownership-cleanup-plan.md
---

# Native Semantic Ownership Cleanup

## Review Basis

The supplied consolidated recommendation is directionally correct and fits the current architecture at Project OS commit 15e8b96f0ce37ec0ce0c16b88749594a2b41b07f. The native app-server path already owns ordinary Secretary semantic completion; the three v3 artifacts remain separate crash-boundary evidence; Herdr remains governed CoS transport and observation; and LightRSI remains independent history, replay, audit, and telemetry infrastructure.

Source review confirms these remaining facts:

- _reconcile_native_artifacts() rejects occupied namespaces only in the non-resume branch. With resume=True and a supplied logical operation, an unrelated output can reach a fresh native execution and later be overwritten.
- _read_only_workspace_identity() still uses path.stat() followed by path.read_bytes() for untracked files. Symlinks, special files, growth after the size check, and unbounded reads are not conservatively handled.
- SecretaryNormalRequest, the direct run CLI, and build_normal_launcher_command() still carry Herdr session/pane inputs even though run_normal() uses the native app-server directly.
- Current direct v3 writers still store descriptive session, pane, and agent_name values beside authoritative native identity, although transport metadata is optional to the v3 validator.
- run_probe() still captures bounded Herdr pane text before launch. Replacing it as primary attribution is capability-dependent on Herdr exposing native identity before prompt delivery.
- This repository contains no LightRSI implementation to modify. The plan does not invent a LightRSI API or require an external repository write.

The review accepts the recommendation with these constraints:

- Keep secretary-native-binding.v3, secretary-native-submission.v3, and secretary-native-result.v3 as separate artifacts.
- Keep exact logical-operation, request, session, thread, turn, publication, read-back, retirement, and acceptance safeguards.
- Keep uncertain delivery non-retryable until reconciliation proves a completed current result.
- Keep Herdr in governed CoS execution and preserve pane/process ownership checks.
- Keep v1/v2 readers read-only. Do not add v4, a registry, observer, daemon, coordination queue, or upstream dependency.
- Require trustworthy current request identity before any complete-current reconciliation; a valid-looking sidecar set alone is not ownership proof.
- Treat existing malformed, mismatched, conflicting, or otherwise unattributable occupants as FOREIGN_OR_UNCERTAIN and preserve their bytes.

## Goal

Make native semantic ownership independent of the resume flag, bound all workspace identity reads conservatively, and remove residual direct-normal Herdr and synthetic transport plumbing without weakening exact native binding, submission, result publication, read-back, retirement, or CoS acceptance.

## Implementation Outcomes

### Resume-independent namespace ownership

Every native output namespace is classified before resume-specific behavior as EMPTY, VERIFIED_COMPLETE_CURRENT, VERIFIED_INCOMPLETE_CURRENT, or FOREIGN_OR_UNCERTAIN. Only EMPTY can claim a new attempt. A complete current v3 artifact set reconciles without a second native turn only when reuse_allowed is true and the exact current request fingerprint and logical-operation/attempt relationships are proven. A valid binding alone, or a mutually consistent binding/submission pair without a result, is VERIFIED_INCOMPLETE_CURRENT; submission without its matching binding, result without matching binding/submission, and conflicts are FOREIGN_OR_UNCERTAIN. Foreign or uncertain evidence remains byte-for-byte read-only.

### Conservative workspace identity

Untracked workspace inputs are read through one bounded regular-file helper that rejects symlinks and unsupported file types, verifies the opened file, reads at most limit + 1 bytes, and converts uncertainty into workspace_identity uncertainty with reuse_allowed=false.

### Smaller direct-normal surface

Direct SecretaryNormalRequest and the run CLI no longer expose Herdr session/pane selectors or the unused normal Herdr command builder. Current v3 native writers stop emitting synthetic transport identity while optional transport metadata remains readable for historical evidence and outer reporting.

### Capability-gated probe attribution

When the existing Herdr launch boundary exposes native session/thread/cursor identity before prompt delivery, that immutable identity is carried through existing start evidence and observation. Pane text and completion counters remain diagnostic or compatibility fallback evidence. If the installed boundary does not expose such identity, the implementation records the capability limitation and preserves the bounded fallback without creating a second discovery API; this optional attribution improvement is deferred without blocking the core cleanup.

### Compatibility and documentation alignment

Historical v1/v2 decoders remain read-only and cannot enter current v3 reconciliation. Runtime documentation describes native identity ownership, Herdr's narrowed authority, the four namespace states, and the absence of a LightRSI semantic dependency in normal completion.

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Required skills: skill-backend-verification, skill-verification-before-completion
- Isolation: current workspace
- Commit policy: no commits during execution
- Preauthorized local actions: edit declared Project OS source, tests, and runtime documentation; run declared local tests and repository validators; inspect configured local runtime evidence without authentication or external writes
- User-approval actions: commit, push, pull request, merge, external LightRSI changes, destructive cleanup, or any new provider/API integration
- Parallel ownership: none; tasks share secretary_live_runtime.py and must remain sequential
- Sequential fallback: execute Tasks 1 through 6 in order; stop when a task changes the accepted contract or exposes an unavailable capability not covered by its stated deferral

## Coordination State

- Coordination owner: single lead controller
- Coordination schema: 2
- Branch: main
- Base commit: 15e8b96f0ce37ec0ce0c16b88749594a2b41b07f
- Expected workspace: clean
- Next action: eligible for separate authorized Git disposition
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | completed | current | codex | none | focused namespace and recovery tests | 14 focused tests passed; automatic reconciliation, occupied namespaces, unknown identity, incomplete evidence, and claim preservation verified |
| Task 2 | completed | current | codex | Task 1 | bounded workspace identity tests | 5 passed, 1 platform-guarded special-file test skipped; regular, symlink alias, size-limit, and Git-budget paths verified |
| Task 3 | completed | current | codex | Task 1 | direct-normal API and v3 writer tests | 75 focused normal/result tests passed; direct selectors/builder removed and v3 writers omit synthetic transport metadata |
| Task 4 | completed | current | codex | Task 3 | probe attribution tests or named capability deferral | Accepted non-blocking deferral: existing Herdr evidence has no native pre-prompt session/thread/cursor identity; bounded pane/agent fallback remains diagnostic-only; focused probe tests passed |
| Task 5 | completed | current | codex | Tasks 1-4 | compatibility and documentation checks | 434 passed, 1 skipped in focused runtime/results/launcher matrix; historical compatibility remains read-only and no helper refactor was needed |
| Task 6 | completed | current | codex | Task 5 | validators, full suite, and bounded live proof | focused matrix 434 passed/1 skipped; repository validators passed; full suite 1476 passed/3 skipped; bounded native run and no-resume reconciliation both settled |

Allowed states are pending, active, blocked, and completed. Task state changes, evidence, blockers, and next actions are owned by the lead controller. A task is not complete merely because its code edit or test command has run; declared proof must be accepted and recorded.

## Task Breakdown

### Task 1: Make namespace ownership authoritative before resume

**Purpose:**
- Prevent resume=True or a failure classification from allowing a fresh attempt to claim or overwrite an occupied output namespace.

**Task Function:**
- Implement one pre-write ownership classifier and connect it to native reconciliation and fresh-attempt claim behavior.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: careful state-machine and crash-boundary reasoning; resolve the lowest discovered profile that can prove ownership and recovery behavior.

**Validator Profile:**
- Controller-selected: none
- Selection basis: no separate validator lane is assigned; the lead controller validates byte preservation, no-resubmit behavior, and current-result reconciliation.

**Specification Coverage:**
- Recommendation items 1, 3, and 4; the four namespace states; separate v3 binding/submission/result crash boundaries; no automatic retry after uncertain delivery.

**Required Skills:**
- skill-backend-verification

**Files And Symbols:**
- Inspect: scripts/secretary_live_runtime.py:_bind_native_resume_request
- Inspect: scripts/secretary_live_runtime.py:_reconcile_native_artifacts
- Inspect: scripts/secretary_live_runtime.py:_run_normal_via_native_app_server
- Modify: scripts/secretary_live_runtime.py:_bind_native_resume_request
- Modify: scripts/secretary_live_runtime.py:_reconcile_native_artifacts
- Modify: tests/test_secretary_live_runtime.py reconciliation and run_normal tests
- Verify: scripts/project_os_runtime/secretary_results.py v3 validators and publishers

**Dependencies:**
- Current v3 artifact validators and atomic publishers remain the source of truth for exact identity and publication.

**Authority:**
- Preauthorized local actions: edit scripts/secretary_live_runtime.py and tests/test_secretary_live_runtime.py; run focused native runtime tests.
- Stop for: merging the three v3 artifacts, retrying uncertain submission, overwriting foreign bytes, or changing the v3 wire schema.

**Steps:**
- [x] Step 1: Add one classifier that uses lstat/lexists-style occupancy detection before branching on resume. Treat directories, broken symlinks, FIFOs, sockets, other special files, and unknown occupants as occupied or uncertain; a complete sidecar triplet is reusable only when output is absent or independently attributable to the same logical operation, request, and attempt.
- [x] Step 2: Treat a consistent current v3 binding/submission/result set as VERIFIED_COMPLETE_CURRENT only when reuse_allowed is true and the exact current request fingerprint plus logical-operation, request, session, thread, and turn relationships are proven; sidecar operation discovery alone is not trust. Reconcile without starting a client or native turn.
- [x] Step 3: Treat a valid current binding alone, or a mutually consistent binding/submission pair without a validated result, as VERIFIED_INCOMPLETE_CURRENT, return recovery-required, and never call CodexAppServerClient.start_turn() again.
- [x] Step 4: Treat submission without its matching binding, result without matching binding/submission, legacy, malformed, mismatched, partial, conflicting, or unknown evidence as FOREIGN_OR_UNCERTAIN; preserve every existing output and sidecar byte and return the existing conflict class.
- [x] Step 5: Allow only an actually empty namespace to proceed to the binding claim. Scope the no-clobber guarantee to cooperating Project OS writers unless the destination claim is strengthened against a non-cooperating occupant; set output ownership only after the claim succeeds, and ensure a losing cooperating claim cannot write invocation output.
- [x] Step 6: Retain resume as a compatibility hint while removing its ability to authorize a claim or overwrite. Preserve the no-resubmit rule for uncertain delivery.
- [x] Step 7: Add regressions proving that a complete v3 sidecar set with unknown workspace identity has reuse_allowed=false, does not reconcile, does not start a new turn, and does not write output; also prove resume never grants ownership.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_live_runtime.py -k "reconcile or resume or native_run or binding_claim"
- Expected: foreign output with resume=True stays byte-for-byte unchanged; malformed and partial combinations fail closed; complete current evidence reconciles only with exact current identity and reuse_allowed=true; unknown identity never reconciles or writes; uncertain submission remains recovery-required and non-retryable.

**Exit Criteria:**
- Namespace classification is independent of resume, all four states are covered by focused tests, and no path can overwrite a foreign or uncertain namespace.

### Task 2: Bound untracked workspace identity reads

**Purpose:**
- Make workspace fingerprint input conservative under symlinks, special files, file growth, and read failures without blocking fresh execution.

**Task Function:**
- Replace the untracked-file stat() plus read_bytes() sequence with one bounded regular-file reader and preserve aggregate budgets.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: localized but platform-sensitive bounded filesystem behavior; resolve a profile able to reason about safe opening and failure classification.

**Validator Profile:**
- Controller-selected: none
- Selection basis: no separate validator lane is assigned; the lead controller exercises symlink, special-file, limit, and read-race behavior.

**Specification Coverage:**
- Recommendation item 2; workspace_identity uncertainty must disable reuse while permitting a fresh invocation.

**Required Skills:**
- skill-backend-verification

**Files And Symbols:**
- Inspect: scripts/secretary_live_runtime.py:_read_only_workspace_identity
- Inspect: scripts/secretary_live_runtime.py:_path_is_runtime_artifact
- Modify: scripts/secretary_live_runtime.py:_read_only_workspace_identity
- Modify: scripts/secretary_live_runtime.py bounded workspace identity helper near existing workspace constants
- Modify: tests/test_secretary_live_runtime.py workspace identity tests

**Dependencies:**
- Task 1 must leave runtime-artifact exclusion and namespace ownership semantics intact; the helper must not read owned output or native sidecars.

**Authority:**
- Preauthorized local actions: edit the workspace identity helper and focused tests; run bounded workspace identity tests.
- Stop for: platform-specific complexity that changes fresh-run behavior, follows a symlink, reads an unbounded file, or introduces a new filesystem dependency.

**Steps:**
- [x] Step 1: Add read_bounded_regular_file(path, limit) with a conservative result contract that distinguishes bytes from uncertainty.
- [x] Step 2: Reject symlinks and unsupported/non-regular files without following or blocking on them, including when the path changes during inspection. Use descriptor-based no-follow/nonblocking mechanisms where supported, then fstat the opened descriptor as regular and read no more than limit + 1 bytes; if equivalent safety cannot be guaranteed on the platform, return workspace uncertainty.
- [x] Step 3: Convert over-limit, stat/open/read inconsistency, and identity-establishment failures into workspace_identity uncertainty and reuse_allowed=false; preserve existing aggregate entry and byte limits.
- [x] Step 4: Replace only the untracked-file read path. Keep Git subprocess budgets, tracked diff handling, runtime-artifact exclusion, and digest format unchanged; ensure _path_is_runtime_artifact() excludes only actual runtime paths and does not silently exclude arbitrary symlink aliases to those paths.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_live_runtime.py -k "workspace_identity or untracked"
- Expected: regular files within budget hash normally; symlinks, broken symlinks, special files, path replacement races, over-limit files, growth/read failures, and unsupported paths return unknown == ("workspace_identity",) without blocking, following, or raising into fresh execution.

**Exit Criteria:**
- No untracked workspace path reaches read_bytes() from the fingerprinting path, the bounded helper never follows a symlink or blocks on a special file, and every unsafe read disables reuse rather than inventing identity.

### Task 3: Remove residual direct-normal Herdr and synthetic transport plumbing

**Purpose:**
- Make direct normal Secretary input and current native v3 writes describe only native semantic identity, while preserving governed probe inputs and optional historical transport metadata.

**Task Function:**
- Delete dead direct-normal routing parameters and stop emitting descriptive transport labels from native binding/result writers.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: deletion-oriented API cleanup spans command surface, serializers, tests, and documentation while preserving established v3 validation.

**Validator Profile:**
- Controller-selected: none
- Selection basis: independently verify direct native execution and governed probe execution remain distinct.

**Specification Coverage:**
- Recommendation items 6 and 7; preserve Herdr session/pane on SecretaryLaunchRequest and governed probe paths; keep optional transport fields readable for old evidence.

**Required Skills:**
- skill-backend-verification

**Files And Symbols:**
- Inspect: scripts/secretary_live_runtime.py:SecretaryNormalRequest
- Inspect: scripts/secretary_live_runtime.py:build_normal_launcher_command
- Inspect: scripts/secretary_live_runtime.py:main
- Inspect: scripts/secretary_live_runtime.py:_run_normal_via_native_app_server
- Inspect: scripts/project_os_runtime/secretary_results.py:_validate_binding and _validate_contract
- Modify: scripts/secretary_live_runtime.py:SecretaryNormalRequest, main, and direct native payload construction
- Modify: scripts/project_os_runtime/secretary_results.py only if shared projection extraction is required; do not change v3 schema acceptance
- Modify: tests/test_secretary_live_runtime.py
- Modify: tests/test_secretary_results.py
- Modify: docs/operating_system/runtime/runtime-surfaces.md

**Dependencies:**
- Task 1 establishes current ownership and reconciliation behavior.

**Authority:**
- Preauthorized local actions: edit direct-normal request/CLI/writer surfaces, focused tests, and runtime documentation; run direct-normal and result-contract tests.
- Stop for: removing governed SecretaryLaunchRequest routing, changing v3 required identity fields, or deleting compatibility readers.

**Steps:**
- [x] Step 1: Remove session and pane from SecretaryNormalRequest and stop exposing --session and --pane on direct run. Keep both fields on SecretaryLaunchRequest and probe/smoke.
- [x] Step 2: Delete build_normal_launcher_command() and its direct-normal test because normal execution already uses the native app-server.
- [x] Step 3: Remove synthetic session, pane, and agent_name values from current v3 binding/result payloads. Keep friendly labels only in outer invocation/reporting projections when needed.
- [x] Step 4: Preserve optional transport parsing and historical v1/v2 compatibility. Add tests proving current v3 payloads without transport publish, read back, and reconcile successfully, while old transport-bearing fixtures remain read-only compatible.
- [x] Step 5: Update runtime surfaces documentation to distinguish direct native execution from governed Herdr probe execution and state that native IDs, not synthetic transport labels, own semantic attribution.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py -k "normal or transport or native_result or native_binding"
- Expected: direct run no longer accepts or forwards Herdr selectors; probe routing still accepts them; current v3 writers omit synthetic transport metadata; optional transport and historical readers remain valid.

**Exit Criteria:**
- Direct normal Secretary has no Herdr-shaped request/CLI/builder surface, and no current v3 writer presents descriptive transport values as native identity.

### Task 4: Use pre-prompt native identity for Herdr probes when available

**Purpose:**
- Prefer child-owned native start identity over pane-content discovery without weakening Herdr ownership, diagnostics, or capability-safe fallback behavior.

**Task Function:**
- Project an already-exposed native session/thread/cursor into existing launch evidence and observation, with no new discovery service or external contract.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: capability-dependent cross-boundary work; resolve only after confirming the installed Herdr evidence shape.

**Validator Profile:**
- Controller-selected: none
- Selection basis: no separate validator lane is assigned; the lead controller verifies identity provenance and fallback classification.

**Specification Coverage:**
- Recommendation items 5, 8, and 9; Herdr remains governed transport and diagnostic observation; LightRSI is never asked to choose a likely child.

**Required Skills:**
- skill-backend-verification

**Files And Symbols:**
- Inspect: scripts/secretary_live_runtime.py:run_probe
- Inspect: scripts/secretary_live_runtime.py:_capture_submission_anchor
- Inspect: scripts/secretary_live_runtime.py:_observe_submitted_codex
- Inspect: scripts/herdr_main_launcher.py:resolve_launch and launch evidence projection
- Modify: scripts/secretary_live_runtime.py:run_probe and observation projection only if native start evidence exists
- Modify: scripts/herdr_main_launcher.py only to carry already-provided native identity through existing sanitized launch evidence
- Modify: tests/test_secretary_live_runtime.py
- Modify: tests/test_herdr_main_launcher.py
- Modify: docs/operating_system/runtime/runtime-surfaces.md

**Dependencies:**
- Task 3 must preserve the distinction between direct native semantics and governed probe transport.
- The installed Herdr/Codex boundary is checked for trustworthy native identity before prompt delivery. If absent, the bounded fallback is an accepted Task-4 deferral; the external LightRSI repository is not a dependency.

**Authority:**
- Preauthorized local actions: inspect configured local Herdr evidence and edit only existing launch-evidence/observation projections and their tests.
- Stop for: any need for latest-session discovery, any new LightRSI API, or any change that makes pane text authoritative for native semantic completion. Missing pre-prompt native identity is recorded as the accepted Task-4 deferral and leaves the bounded fallback in place.

**Steps:**
- [x] Step 1: Confirm whether existing Herdr start evidence exposes native session, thread, cursor, or equivalent before prompt delivery; record the field and provenance in task evidence. No such trustworthy pre-prompt identity is exposed; only pane/agent/completion evidence and post-submit historical turn data are available.
- [x] Step 2: If available, add immutable native start identity to existing sanitized launch evidence and carry it through _observe_submitted_codex and existing attempt evidence, bound to the same attempt and workspace. No implementation is added because the capability is unavailable.
- [x] Step 3: Use pane snapshots, agent get/read, and completion counters only as diagnostics or compatibility fallback. Do not use them to select a likely native child when native identity is known.
- [x] Step 4: If unavailable, leave _capture_submission_anchor() as bounded fallback evidence, record the accepted capability deferral, and do not create a second discovery API.
- [x] Step 5: Preserve Herdr target/process ownership validation and CoS PASS | FAIL | BLOCKED acceptance as a separate authority.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_herdr_main_launcher.py -k "probe or anchor or native or observation or target"
- Expected: supplied native start identity is the attribution source; when unavailable the fallback remains bounded and explicitly diagnostic, with no synthetic identity or likely-session lookup.

**Exit Criteria:**
- Native pre-prompt identity is used when the existing boundary provides it, or the exact unavailable capability and preserved fallback are recorded as an accepted non-blocking Task-4 deferral without broadening scope. Direct native Secretary execution/recovery proof remains mandatory for final verification.

### Task 5: Isolate compatibility and reconcile maintained documentation

**Purpose:**
- Make the current-v3 versus historical-evidence boundary explicit in tests and maintained runtime documentation, changing compatibility helpers only if actual leakage is found.

**Task Function:**
- Perform the smallest compatibility-boundary cleanup that removes ambiguity without changing historical wire formats or current v3 semantics; prefer documentation and regression coverage over helper refactoring.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: low-risk compatibility/documentation cleanup after behavior changes are proven.

**Validator Profile:**
- Controller-selected: none
- Selection basis: no separate validator lane is assigned; the lead controller confirms historical evidence remains readable but cannot be reused for current semantic publication.

**Specification Coverage:**
- Recommendation items 4, 8, and 10; v1/v2 read-only compatibility; historical lightrsi-codex-context-history authority remains wire-compatible.

**Required Skills:**
- skill-backend-verification

**Files And Symbols:**
- Inspect: scripts/project_os_runtime/secretary_results.py:parse_native_binding, parse_native_submission, parse_native_result
- Inspect: scripts/secretary_live_runtime.py:_reconcile_native_artifacts
- Modify: scripts/project_os_runtime/secretary_results.py only if tests expose actual compatibility leakage; otherwise leave compatibility helpers unchanged
- Modify: tests/test_secretary_results.py
- Modify: tests/test_secretary_live_runtime.py
- Modify: docs/operating_system/runtime/runtime-surfaces.md

**Dependencies:**
- Tasks 1 through 4 must have stable current-v3 behavior and no unresolved capability decision that changes authority boundaries.

**Authority:**
- Preauthorized local actions: edit compatibility labels only when needed, tests, and maintained runtime documentation; run focused compatibility checks.
- Stop for: schema migration, v4 introduction, conversion or dual-write of historical artifacts, or any LightRSI wire rename.

**Steps:**
- [x] Step 1: Keep v1/v2 validators and parsers available only as named historical/read-only compatibility paths; keep current writers and reconciliation on strict v3 validators. Do not rename or extract helpers solely for appearance.
- [x] Step 2: Add regression coverage proving legacy and pre-current evidence can be inspected but cannot satisfy current v3 reconciliation or overwrite a current output namespace.
- [x] Step 3: Document lightrsi-codex-context-history as a historical authority name on the wire and state that normal v3 completion does not depend on LightRSI evidence.
- [x] Step 4: Remove stale runtime documentation claims that pane discovery or LightRSI selects normal semantic identity.
- [x] Step 5: Refactor or rename compatibility helpers only if the regression tests identify actual leakage into current v3 reconciliation or publication.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py -k "legacy or v1 or v2 or compatibility or reconcile" (covered by the fresh full focused matrix: 434 passed, 1 skipped)
- Expected: historical evidence remains readable where existing APIs require it, but current v3 recovery and publication never silently reuse it; no compatibility-only rearrangement is introduced without a demonstrated leakage.

**Exit Criteria:**
- Source, tests, and runtime documentation agree on the current-v3 authority boundary and no historical compatibility path participates in normal semantic acceptance.

### Task 6: Complete final verification and bounded live proof

**Purpose:**
- Prove the implementation outcomes across focused behavior, repository contracts, the full test suite, and one bounded native execution/recovery flow.

**Task Function:**
- Run fresh final verification, reconcile plan evidence, and report any exact capability blocker without synthetic success.

**Template Profile:**
- Controller-selected: none (lead controller)
- Selection basis: final verification requires broad repository and runtime evidence.

**Validator Profile:**
- Controller-selected: none
- Selection basis: no separate validator lane is assigned; the lead controller reviews every implementation outcome and task exit criterion.

**Specification Coverage:**
- All outcomes and completion criteria in this plan; backend direct-boundary, failure-path, side-effect, idempotency, and contract proof.

**Required Skills:**
- skill-backend-verification, skill-verification-before-completion

**Files And Symbols:**
- Inspect: all files listed in targets
- Verify: scripts/validate_repo_contracts.py
- Verify: scripts/validate_planning_lifecycle.py
- Verify: focused and full test commands below

**Dependencies:**
- Tasks 1 through 5 completed with accepted proof and no unrecorded scope deviations.

**Authority:**
- Preauthorized local actions: run declared validators, focused tests, the full suite, diff checks, and one bounded native probe using existing local configuration.
- Stop for: authentication, external writes, failed required checks, unverified process retirement, unexpected branch/base mutation, or any result not bound to the exact current request.

**Steps:**
- [x] Step 1: Run the focused namespace, workspace, direct-normal, result, probe, and launcher test matrix; 434 passed and 1 skipped.
- [x] Step 2: Run repository contract and planning validators, then the full pytest suite and git diff --check; validators passed, full suite returned 1476 passed and 3 skipped, and diff check passed.
- [x] Step 3: Run one bounded native Secretary invocation followed immediately by the same-output recovery path with the second invocation explicitly omitting --resume. The first run produced logical operation `2e65ede1d82c493da0003337f6ac0f9e`, request fingerprint `9eed0b531cabd9228311be9870021643ec1652ced5f3b9fe59ed306851d5f4ad`, attempt `8da46b9862b349b686c021a09c77cd4a`, native turn `01a15544-bac5-7333-ba72-5d5d1d2eb2f3`, completed `READY`, published/read back the v3 result, and retired reader/writer resources; the second run returned `reconciled=true` with the same identities and no second turn.
- [x] Step 4: Treat absence of the optional Herdr pre-prompt identity capability as the accepted Task-4 deferral and do not block completion for it. Direct native Secretary execution/recovery was verified, so no capability blocker is recorded.
- [x] Step 5: Apply skill-verification-before-completion and update this plan only after fresh evidence satisfies every completion criterion.

**Verification:**
- [x] py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py (434 passed, 1 skipped)
- [x] py -B scripts/validate_repo_contracts.py --repo-root . (passed)
- [x] py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-19-03-native-semantic-ownership-cleanup-plan.md (passed)
- [x] py -B -m pytest -q (1476 passed, 3 skipped)
- [x] git diff --check (passed)
- Expected: all required checks pass; the live probe proves exact current identity and no duplicate turn through automatic same-output reconciliation without --resume, or final verification records a named immutable direct-native capability blocker without synthetic success.

**Exit Criteria:**
- Fresh verification returns verified; all task-local proof is accepted; no required task, blocker, or scope deviation remains unrecorded; the plan is eligible for a separate authorized Git disposition.

## Verification

- py -B -m pytest -q tests/test_secretary_live_runtime.py tests/test_secretary_results.py tests/test_herdr_main_launcher.py
- py -B scripts/validate_repo_contracts.py --repo-root .
- py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-19-19-03-native-semantic-ownership-cleanup-plan.md
- py -B -m pytest -q
- git diff --check
- One bounded native Secretary run followed by immediate same-output recovery without --resume, with exact fingerprint, current v3 binding/submission/result, no duplicate turn/start, and independent retirement evidence: verified using temporary output `C:\tmp\project-os-secretary-live-d225d74063504ce2bf1682fd57719007.json`.

## Completion Criteria

The plan may be marked completed only after skill-verification-before-completion returns verified and fresh evidence proves:

1. Existing bytes never become writable merely because resume was requested or valid-looking sidecars exist: reuse requires exact current identity, fresh execution requires a truly empty namespace, and uncertain delivery is never automatically repeated.
2. Namespace classification happens before resume-specific branching, only EMPTY can claim fresh work, and foreign/uncertain output remains byte-for-byte unchanged; any no-clobber claim is explicitly scoped to cooperating Project OS writers unless the destination primitive is strengthened.
3. Complete current v3 evidence reconciles without a second native turn only with reuse_allowed=true and exact current identity; binding-only or matching binding/submission evidence remains recovery-required and non-retryable, while unmatched or conflicting combinations are foreign/uncertain.
4. The three v3 artifacts remain separate and exact logical-operation, request, session, thread, and turn identity checks remain intact.
5. Untracked workspace reads reject symlinks and unsupported files, never block on or follow path-replaced special files, enforce the per-file byte bound during the read, and convert uncertainty into workspace_identity/reuse_allowed=false.
6. Direct normal Secretary no longer carries Herdr session/pane selectors or the unused normal command builder; governed probe selectors remain intact.
7. Current v3 writers no longer emit synthetic transport identity, while optional transport and historical v1/v2 readers remain read-only compatible.
8. Herdr native pre-prompt identity is used when the existing boundary exposes it; otherwise the exact capability limitation and bounded fallback are recorded as a non-blocking Task-4 deferral. Direct native execution/recovery proof remains mandatory.
9. LightRSI remains outside normal semantic acceptance, Herdr remains governed CoS transport/diagnostics, and CoS retains PASS | FAIL | BLOCKED authority.
10. No new schema, registry, observer, daemon, retry policy, upstream API, or external LightRSI modification is introduced.
11. Focused tests, repository validators, the full suite, diff checks, and bounded live proof pass, or an exact immutable direct-native capability blocker is recorded without synthetic success.

Branch creation, commit, push, pull request, merge, and worktree cleanup remain separate authorized actions and are not completion criteria for this implementation plan.


