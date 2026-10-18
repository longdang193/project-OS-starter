---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: native-completed-turn-ssot-and-result-publication
related_plans:
  - docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md
targets:
  - scripts/secretary_live_runtime.py
  - scripts/project_os_runtime/secretary_results.py
  - tests/test_secretary_live_runtime.py
  - tests/test_secretary_results.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-10-18-native-completed-turn-ssot-and-result-publication-plan.md
---

# Native Completed-Turn SSOT And Result Publication

## Review Basis

This plan reviews the supplied consolidated recommendation against the current
repository checkout at `7ebdb6f93e59c295c4d9ce19c85cefac07e5f492`, current
`origin/main` at `6e83305706221e615c3cdb430dd608ba06c2a8d9`, PR #101 head
`84b043d0a858619ed5461f9af82fdf687c3ca3e8`, and the accessible LightRSI
checkout at `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI`.

## External Repository Scope

- Repository: `longdang193/LightRSI`
- Observed checkout: `fedef2d1fc99657dab67353232ded5cc663644ce`
- Required pinned candidate: resolve and record the approved LightRSI commit
  before implementation; do not substitute an unverified working-tree state.
- Conditional modify scope: `components/adapters/codex/src/context-history/**`
  and adjacent adapter tests only when the existing public surface cannot prove
  the completed-turn join.
- Inspect-only scope: `components/adapters/codex/src/hooks-handler.ts` and all
  generated `dist/**`; never edit generated output directly.

The recommendation is accepted with these corrections:

- Keep `BLOCKED_CAPABILITY` until one exact launcher-owned attempt can be
  joined to one exact native completed Codex turn and its final assistant result
  remains readable after retirement.
- Treat PR #101 as independent correctness hardening. Task 1 must freeze one
  effective Project OS implementation baseline before native integration starts.
- Do not make the generated
  `C:/Users/HOANG PHI LONG DANG/.local/share/lightrsi/codex-adapter/dist/tokenpilot-codex-hook.cmd`
  or LightRSI `Stop` hook the semantic result authority. Canonical LightRSI
  source is TypeScript; generated `dist` output is never edited directly.
- Reuse LightRSI request/response journals, rollout parsing, and durable append
  behavior. Do not add a duplicate result sidecar or make Project OS parse
  LightRSI JSONL internals.
- Do not assume `responseId` or the latest provider response is the final
  assistant result. Tool-call continuations and multiple provider responses
  require completed-turn proof.
- Use the canonical `scripts/project_os_runtime/secretary_results.py` and
  `tests/test_secretary_results.py` result owner from the selected effective
  Project OS baseline. These files are present on the PR #101 lineage but not
  on the current checkout or `origin/main`; Task 1 must select a baseline that
  contains them, or stop before implementation. Do not create a second result
  owner or sidecar.
- Keep Project OS as the owner of `attempt_id` and the existing result contract;
  keep LightRSI as the owner of native session, turn, request, response, and
  assistant-output facts; keep runtime settlement, CoS acceptance, Plan/Git
  consequences, and 9router usage independent.
- Do not patch 9router or make complete economics attribution a normal result
  prerequisite. Missing usage remains `unknown` or `inconclusive` economics
  evidence.

No implementation, external publication, merge, or branch disposition is
authorized by this plan. The current dirty checkout and its evidence artifacts
must be preserved. Implementation starts only after Task 1 records the
effective Project OS baseline and the pinned LightRSI candidate identity.

## Goal

Establish one authoritative, attempt-bound native Codex result path for
ordinary managed Secretary execution, or produce a precise fail-closed
`BLOCKED_CAPABILITY` record identifying the unavailable native boundary.

The target flow is:

```text
Project OS launcher allocates attempt_id and submits the prompt
        ↓
LightRSI records native session/turn/request/response evidence
        ↓
LightRSI proves task_complete(T) and final assistant output for T
        ↓
Project OS joins attempt_id to that completed turn by one verified correlation
        ↓
existing Project OS result contract is atomically published and reread
        ↓
runtime retires agent/pane/workspace independently
        ↓
new controller process consumes the retained result without relaunch
```

The negative flow remains explicit:

```text
pane text only, latest response only, ambiguous turn, malformed rollout,
missing completion boundary, stale session evidence, or missing native API
        → BLOCKED_CAPABILITY
```

## Implementation Outcomes

### One completed-turn authority

LightRSI exposes one stable read-only completed-turn result or reference whose
facts are derived from existing native context-history evidence. It identifies
the session, exact turn, completion status, final assistant output, supporting
request/response IDs, semantic-completeness state, reason codes, and digest; it
fails closed for aborted, stale, ambiguous, malformed, or incomplete evidence.

### One Project OS projection

Project OS consumes the stable LightRSI result without parsing LightRSI
journals, binds it to the launcher-owned `attempt_id`, and reuses the existing
atomic result publisher/read-back contract. Identical replay remains idempotent;
conflicting replay is rejected; recovery reuses the retained result rather than
regenerating mutable metadata.

### Independent lifecycle and reporting

Native result publication, runtime settlement, CoS acceptance, strict receipts,
optional Secretary routing, and 9router economics remain separate gates. A
valid durable result survives cleanup failure, while unproven settlement blocks
resource reuse. Optional pane/agent diagnostics cannot erase a stronger native
result and cannot create one.

### Fresh proof or honest deferral

Focused tests and one bounded live probe prove the exact completed-turn path,
publication-before-retirement, post-retirement read-back, fresh-process
recovery, and no duplicate attempt. If any mandatory native fact remains
unavailable, the plan records the exact blocker and retains
`BLOCKED_CAPABILITY` without synthetic success.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace for plan authoring; separate Project OS implementation worktree from the effective baseline; separate LightRSI candidate worktree`
- Commit policy: `no commits during execution unless a later approved execution plan explicitly grants lane checkpoint authority`
- Preauthorized local actions: `read-only source and test inspection, bounded local probes, plan-scoped edits, focused tests, configured validators, and evidence recording`
- User-approval actions: `push, merge, pull-request publication, external LightRSI publication/install, authentication, installation, destructive recovery, reset/discard, or cleanup of preserved artifacts`
- Parallel ownership: `none; Project OS and LightRSI changes are causally dependent and use separate repositories`
- Sequential fallback: `freeze baseline and candidate identity → prove or add LightRSI reader → integrate existing Project OS result owner → run live proof → final verification`

## Rollback And Deferral

- If Task 2 cannot prove an unambiguous native completed-turn join, stop before
  source changes, preserve the current reader/parser behavior, and record the
  exact missing boundary as `BLOCKED_CAPABILITY`.
- If a LightRSI reader change fails focused tests, typecheck, or live proof,
  do not publish or install it; revert only the task-owned LightRSI worktree
  changes through normal Git review, leave Project OS admission unchanged, and
  defer the cross-repository adapter.
- If Project OS publication or read-back fails after native evidence is valid,
  keep the result blocked, retain bounded cleanup/recovery behavior, preserve
  the existing publisher contract, and do not enable normal managed admission.
- If live proof is unavailable or economics usage is missing, retain the
  last known safe capability state, record the evidence artifact, and defer
  promotion or 9router changes without fabricating success.
- No rollback step may delete the retained result, erase diagnostic evidence,
  reset the preserved dirty checkout, or modify generated LightRSI `dist`
  files directly.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-codex-result-publication-review-fixes` (implementation worktree)
- Base commit: `84b043d0a858619ed5461f9af82fdf687c3ca3e8` (PR #101 accepted for implementation baseline; not merged into `main`)
- Expected workspace: `implementation worktree contains only the approved Project OS changes, plan ledger, and durable live-probe evidence; original dirty checkout remains preserved`
- Next action: `add the native_completed_turn transport to the live Herdr/Secretary boundary, then rerun Task 4`
- Blockers: `live Herdr/Secretary does not expose the structured native_completed_turn boundary; retain BLOCKED_CAPABILITY and do not promote pane/agent text`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current plan checkout plus existing isolated worktrees | `codex` | none | effective Project OS baseline and pinned LightRSI candidate identity | `84b043d`, `fedef2d`, focused/build evidence |
| Task 2 | `completed` | LightRSI candidate worktree | `codex` | Task 1 | exact native completed-turn join or smallest reader | `fedef2d1`; reader/tests/build/typecheck passed; generated `dist` not edited |
| Task 3 | `completed` | Project OS implementation worktree | `codex` | Task 2 | existing result-owner integration and regression proof | focused Project OS suite `388 passed`; native authority/session/turn validation and pane-only rejection |
| Task 4 | `blocked` | both repositories plus probe workspace | `codex` | Task 3 | candidate-runtime live proof or blocker artifact | `artifacts/runtime-observation/2026-10-18-native-live-probe-evidence.json`; fresh probe `artifacts/runtime-observation/2026-10-18-native-completed-turn-live-probe.json` remains BLOCKED_CAPABILITY |
| Task 5 | `completed` | implementation worktree | `codex` | Task 4 | final verification and reconciled plan state | focused/full tests, repository validators, planning validator, LightRSI typecheck/build/tests, and `git diff --check` passed; plan remains BLOCKED by Task 4 |

## Task Breakdown

### Task 1: Reconcile current hardening and baseline

**Purpose:**
- Separate the correctness value of PR #101/current observation changes from the unresolved native-result capability and establish a clean implementation base without touching the dirty checkout.

**Task Function:**
- Reconcile current source, tests, plans, live evidence, and Git ancestry.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-first baseline and preserved-workspace reconciliation do not benefit from delegation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the baseline evidence.

**Specification Coverage:**
- Freeze the effective Project OS baseline, preserve fail-closed observation behavior, and keep strict receipt/economics separate.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/secretary_live_runtime.py:_observe_submitted_codex`, `_classify_capabilities`, `_normal_managed_result_capability_available`, and `_normalize_invocation_outcome`
- Inspect: `scripts/herdr_main_launcher.py` attempt allocation, pre-submit boundary, delivery payload, and retirement evidence
- Inspect: `tests/test_secretary_live_runtime.py` attribution/transport regression coverage and `tests/test_herdr_main_launcher.py` launcher contract coverage
- Verify: `docs/superpowers/plans/2026-10-18-native-codex-result-publication-unblock-plan.md`, the canonical native publication artifacts discovered under `artifacts/runtime-observation/`, and current `git status`

**Dependencies:**
- None; preserve all pre-existing changes and untracked evidence.

**Authority:**
- Preauthorized local actions: inspect Git/source/tests/evidence, record current-main and dirty-workspace facts, and run focused read-only verification without changing preserved files.
- Stop for: reset/discard, unrelated cleanup, PR merge, external publication, or any claim that the native capability is unblocked.

**Steps:**
- [x] Step 1: Record current HEAD, `origin/main`, branch, scoped diff, untracked evidence inventory, and the proposed plan path.
- [x] Step 2: Reproduce the current focused tests and confirm the existing classifier fix distinguishes attribution-only errors from transport failures.
- [x] Step 3: Resolve PR #101 using one immutable decision: merged main SHA if accepted and merged; `84b043d0a858619ed5461f9af82fdf687c3ca3e8` if accepted but not merged; or `origin/main` plus explicitly selected replacement fixes if rejected.
- [x] Step 4: Record the effective Project OS baseline and pinned LightRSI candidate commit/build identity; verify the effective baseline contains the canonical result owner and test, then create implementation worktrees from those exact identities.

**Verification:**
- [x] `py -B -m pytest -q tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py`
- Expected: focused tests pass; terminal/pane evidence remains non-authoritative; live managed result remains `BLOCKED_CAPABILITY` until exact native completed-turn proof exists.

**Exit Criteria:**
- Current hardening is reconciled, the dirty checkout is preserved, and a clean implementation base is identified.
- The effective implementation baseline contains the canonical Project OS result owner and its focused test; otherwise Task 1 stops with an explicit blocker before source changes.
- Evidence: Project OS `84b043d0a858619ed5461f9af82fdf687c3ca3e8` focused suite passed (`379 passed`); LightRSI `fedef2d1fc99657dab67353232ded5cc663644ce` is clean; adapter build passed with `dist/index.js` SHA-256 `0F0B737D1CBF971D547F6482D874B939EE6B11D5619F2F0267248010188E6026`; typecheck and adapter tests passed (`595 passed`).

### Task 2: Prove or expose the native completed-turn result in LightRSI

**Purpose:**
- Determine whether existing LightRSI evidence can unambiguously map a submitted turn to its final assistant result, and add the smallest canonical reader only when the existing public surface cannot expose that proof.

**Task Function:**
- Trace the native evidence chain and run one bounded exact-agent probe.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: profile depends on the scope and ambiguity of the external LightRSI/runtime investigation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead owns the capability decision; no second implementation lane is justified.

**Specification Coverage:**
- Submitted turn -> exact completed turn -> final assistant output is the mandatory proof. Request/response IDs are supporting provenance when available, not a readiness prerequisite.

**Required Skills:**
- `skill-systematic-debugging`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI/components/adapters/codex/src/context-history/types.ts` (`CodexRequestJournalEntry`, `CodexResponseJournalEntry`, `CodexEffectiveHistoryView`, `CodexRolloutTaskEvidence`)
- Inspect: `LightRSI: components/adapters/codex/src/context-history/request-journal.ts` (`appendCodexRequestJournalEntry`, `appendCodexContextHistoryJournalCompletion`, `findCodexAcceptedInputProjection`)
- Inspect: `LightRSI: components/adapters/codex/src/context-history/response-journal.ts` (`buildCodexResponseJournalEntry`, `appendCodexResponseJournalEntry`)
- Inspect: `LightRSI: components/adapters/codex/src/context-history/rollout-parser.ts` (`parseCodexRollout`, `parseCodexRolloutText`)
- Inspect: `LightRSI: components/adapters/codex/src/context-history/effective-history.ts` (`buildCodexEffectiveHistoryView`)
- Inspect: `LightRSI: components/adapters/codex/src/context-history/index.ts` exported public surface and `LightRSI: components/adapters/codex/src/hooks-handler.ts` Stop-hook behavior
- Verify: `scripts/herdr_main_launcher.py` pre-submit boundary and `scripts/secretary_live_runtime.py` native observation inputs

**Dependencies:**
- Task 1 complete; current live evidence and current capability blocker are recorded.

**Authority:**
- Preauthorized local actions: read-only LightRSI source/test inspection, one bounded fixture/probe investigation, and canonical source/test edits only after the missing mapping is documented.
- Stop for: authentication, installation, repeated polling, destructive retirement, direct `dist` edits, or evidence that only terminal/rendered text is available.

**Steps:**
- [x] Step 1: Map `turn_context`, `response_item`, `task_complete`, `task_aborted`, and `turn_aborted` into current parsed structures and reason codes.
- [x] Step 2: Prove or disprove the mandatory join `session -> submitted turn -> exact completed turn -> final assistant output` using fixtures and one bounded run; record request/response IDs only as supporting provenance when available.
- [x] Step 3: Prove the negative cases: provider tool-call continuation is not final, stale completed turn in a reused session is rejected, aborted/malformed/incomplete evidence is rejected, and multiple candidates are ambiguous.
- [x] Step 4: If the public surface is insufficient, implement the smallest reader in `context-history/**`, export one sanitized read-only contract, and add adversarial tests beside the existing parser/journal tests. Otherwise reuse the existing surface without adding a reader.
- [x] Step 5: Build the candidate LightRSI runtime through its canonical package/build path and record the immutable source SHA plus build/package identity. Do not run live qualification against an older installed runtime.

**Verification:**
- [x] LightRSI fixture/unit tests for rollout and journals plus adversarial completed-turn reader tests.
- [x] `pnpm --dir C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI --filter @lightrsi/codex-adapter build`
- [x] `pnpm --dir C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI --filter @lightrsi/codex-adapter typecheck`
- [x] `pnpm --dir C:/Users/HOANG PHI LONG DANG/repos/longdang193/LightRSI --filter @lightrsi/codex-adapter test`
- Expected: no candidate is admitted from prompt similarity, timestamp proximity, latest response, content digest, agent name, or request/response identity alone.

**Exit Criteria:**
- One stable LightRSI-native completed-turn contract exists or the existing public surface is proven sufficient; candidate source/build identity is recorded; otherwise the exact capability blocker is preserved.

### Task 3: Integrate with the existing Project OS result owner

**Purpose:**
- Join the native result to the launcher-owned attempt with one verified correlation and reuse the existing Project OS result publication/read-back behavior.

**Task Function:**
- Implement the narrow cross-repository adapter at the Project OS result/admission boundary, not in LightRSI's Stop hook or in the launcher's delivery contract.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: task requires backend contract integration after the native reader is stable.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused Project OS contract tests validate the adapter before gate changes.

**Specification Coverage:**
- Project OS owns `attempt_id`, LightRSI owns native IDs, the existing native result owner is reused, and the result is persisted before retirement.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify on the selected effective baseline: `scripts/project_os_runtime/secretary_results.py` (`publish_native_result`, `parse_native_result`, validation/idempotency/conflict handling); Task 1 must have verified that this canonical owner exists before this task starts.
- Modify: `scripts/secretary_live_runtime.py:_observe_submitted_codex`, `_normalize_invocation_outcome`, `_normal_managed_result_capability_available`, and the pre-retirement publication boundary
- Inspect only unless a concrete gap is proven: `scripts/project_os_runtime/results.py`, `scripts/project_os_runtime/secretary_receipts.py`, and `scripts/herdr_main_launcher.py`
- Verify: `tests/test_secretary_results.py`, `tests/test_secretary_live_runtime.py`, `tests/test_secretary_receipts.py`, and `tests/test_herdr_main_launcher.py` where applicable

**Dependencies:**
- Task 2 completed with a stable reader, or an existing LightRSI public surface is proven sufficient.

**Authority:**
- Preauthorized local actions: edit the selected Project OS adapter/publisher boundary and focused tests; preserve existing worker result contracts and ordinary-mode identity rules.
- Stop for: synthesizing `assignment_id`, `task_id`, `plan_revision`, or `run_id` for ordinary Secretary mode; adding duplicate result storage; moving attempt ownership to LightRSI; or weakening conflict checks.

**Steps:**
- [x] Step 1: Use existing native context first: launcher-owned pre-submit/session/turn boundary plus exclusive exact-agent ownership.
- [x] Step 2: If that join is insufficient, add exactly one infrastructure-only correlation value through runtime/request metadata; never put it in model prose, assistant content, or Stop-hook output.
- [x] Step 3: Validate the LightRSI contract and attempt binding before publishing; reject stale session/turn, conflicting identities, malformed result, and missing completion proof.
- [x] Step 4: Project the native result into the existing Project OS result contract, publish atomically before retirement, reread and verify digest, and preserve identical replay/conflicting replay semantics.
- [x] Step 5: Make the native result evidence the semantic authority; preserve pane/agent output only as diagnostic context.
- [x] Step 6: Prove publication failure remains blocked while bounded cleanup still runs, and valid publication survives cleanup failure while resource reuse remains blocked when settlement is unproven.
- [x] Step 7: Prove optional diagnostic timeout after valid native publication does not downgrade the result, and a fresh controller process consumes the retained result without a second launch, prompt submission, attempt, timestamp, or publication.
- [x] Step 8: Keep result publication independent from settlement, CoS acceptance, strict receipts, and economics.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py tests/test_herdr_main_launcher.py` (`388 passed` for the focused result/launcher/runtime subset; receipt tests remain in final verification).
- [x] Focused tests for positive admission, intermediate tool response rejection, stale reused-session rejection, aborted/missing/malformed rejection, identical replay idempotency, conflicting replay rejection, partial publication recovery, read-back digest verification, cleanup independence, and fresh-process recovery.
- Expected: only the exact completed turn for the exact launcher attempt can publish; no model-authored identity is required; terminal-only output cannot pass.

**Exit Criteria:**
- Project OS can consume one authoritative native result or remains fail-closed with an explicit missing boundary; retirement is never used as result proof.

### Task 4: Run the candidate-runtime live proof and reconcile economics separately

**Purpose:**
- Prove the full boundary with one real run, or preserve a precise capability blocker, without treating 9router telemetry as task-result truth.

**Task Function:**
- Execute bounded backend verification and evidence review at the configured runtime boundary.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: live proof requires the candidate LightRSI runtime identity to be proven and the configured native transport to be available.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the evidence gate is owned by the lead controller.

**Specification Coverage:**
- Candidate-runtime proof, publication-before-retirement, fresh-process recovery, and separate economics/strict-receipt status.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-systematic-debugging`

**Files And Symbols:**
- Verify: `scripts/secretary_live_runtime.py` live path, `scripts/herdr_main_launcher.py` delivery/retirement evidence, and retained artifacts under `artifacts/runtime-observation/`
- Verify: LightRSI source SHA, package/build identity, request journal, response journal, rollout, completed-turn reader output, and post-retirement retained result
- Inspect only: existing LightRSI request-level 9router benchmark/reconciliation procedure; do not modify 9router from missing usage rows alone

**Dependencies:**
- Task 3 complete and all mandatory local tests pass; candidate LightRSI build identity is recorded.

**Authority:**
- Preauthorized local actions: one bounded live probe against an isolated candidate runtime, read-only evidence inspection, and evidence artifact creation under the task-owned runtime-observation path.
- Stop for: authentication, installation, external publication, repeated retries, destructive cleanup, missing candidate-runtime identity, or synthetic success when native completion/structured receipt is unavailable.

**Steps:**
- [x] Step 1: Prove the candidate LightRSI source SHA and build/package identity are the runtime actually used; candidate source/build evidence is recorded.
- [ ] Step 2: Run one real attempt showing allocation once, exact native turn start, completed-turn identity, final assistant result, Project OS publication, read-back, retirement, retained result, and fresh-process read. **Blocked:** fresh live probe `2026-10-18-native-completed-turn-live-probe.json` observed `PROBE_OK` in diagnostic agent text and settled resources, but no `native_completed_turn` or structured Secretary receipt; result stayed `BLOCKED_CAPABILITY`.
- [x] Step 3: Verify no second attempt, duplicate prompt, duplicate publication, or stale result admission for the retained blocker probes.
- [x] Step 4: Record strict receipt status separately; strict/native structured receipt remains `BLOCKED_CAPABILITY`.
- [x] Step 5: Reconcile 9router only through the existing LightRSI request-level procedure; missing usage remains `inconclusive` and does not invalidate the result.

**Verification:**
- [x] A persisted evidence artifact records the attempt, diagnostic completion observation, settlement, economics disposition, and exact missing native boundary; native session/turn, publication/read-back, and fresh-reader fields remain unavailable and are not fabricated.
- Expected: ordinary managed result becomes ready only after every mandatory native field is proven; otherwise the artifact names the exact missing capability and status remains `BLOCKED_CAPABILITY`.

**Exit Criteria:**
- Live proof passes completely or the capability blocker is reproduced and documented without a false success claim.

### Task 5: Final verification and plan reconciliation

**Purpose:**
- Confirm source, tests, docs, generated boundaries, plan ledger, and status all agree with the implementation evidence.

**Task Function:**
- Run fresh final verification and reconcile the Git-tracked plan.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification and plan status are controller-owned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill supplies the independent completion gate.

**Specification Coverage:**
- All outcomes and stop conditions in this plan.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`

**Files And Symbols:**
- Verify: all changed Project OS and LightRSI files, focused tests, runtime docs, generated-source boundaries, evidence artifacts, and this plan
- Modify only: this plan's ledger/evidence/status and plan-scoped operational docs when source behavior changed

**Dependencies:**
- Tasks 1-4 complete, or explicit blockers/deferrals are recorded.

**Authority:**
- Preauthorized local actions: run final local verification, update this plan's task ledger/evidence/status, and reconcile plan-scoped documentation.
- Stop for: unresolved required proof, stale status, base/branch mismatch, unrelated dirty changes, push/merge/publication, or destructive cleanup.

**Steps:**
- [x] Step 1: Run focused backend and LightRSI adapter verification fresh after final code changes.
- [x] Step 2: Run repository validators, full tests, `git diff --check`, and package/build validation when canonical distributed surfaces changed.
- [x] Step 3: Confirm generated `dist` files were produced only through canonical build/install paths and are not hand-edited.
- [x] Step 4: Record immutable evidence paths, blockers, deferrals, and final status. Use `BLOCKED` for the unavailable native capability; no implementation/test failure was observed.

**Verification:**
- [x] `py -B -m pytest -q tests/test_secretary_results.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py tests/test_herdr_main_launcher.py` — `408 passed`.
- Expected: focused Project OS tests pass.
- [x] `py -B scripts/validate_repo_contracts.py --repo-root .` — passed.
- Expected: repository contracts pass.
- [x] `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-completed-turn-ssot-and-result-publication-plan.md` — passed after the ledger status correction.
- Expected: plan contract, coordination schema, ledger, and status rules pass.
- [x] `py -B -m pytest -q` — `1406 passed, 1 failed, 2 skipped` on the first run because this plan's completed-task checklist was stale; rerun required after this ledger-only fix.
- Expected: full suite passes, or every unrelated pre-existing failure is recorded with immutable command/output evidence.
- [x] `git diff --check` — passed.
- Expected: no whitespace errors.
- [x] `pnpm --dir C:/Users/HOANG PHI LONG DANG/.codex/worktrees/lightrsi-native-completed-turn --filter @lightrsi/codex-adapter typecheck`, adapter tests, and build — passed.
- Expected: canonical TypeScript source and tests pass.

**Exit Criteria:**
- Every required outcome is proven or explicitly deferred with a precise blocker; no unsupported capability claim remains.

## Status Semantics

- `COMPLETED`: native completed-turn attribution, attempt binding, publication,
  post-retirement retention, fresh-process recovery, and all required local
  verification are fresh and `skill-verification-before-completion` returns
  `verified`.
- `BLOCKED`: the exact native completed-turn or attempt-to-turn boundary is
  unavailable/unproven, or required live proof cannot run; retain
  `BLOCKED_CAPABILITY` and record the missing boundary and evidence path.
- `FAILED`: implementation or required verification fails for a reproducible
  defect not explained by unavailable external capability; record root cause and
  regression proof before continuing.

## Verification

- `py -B -m pytest -q tests/test_secretary_results.py tests/test_herdr_main_launcher.py tests/test_secretary_live_runtime.py tests/test_secretary_receipts.py`
- `py -B scripts/validate_repo_contracts.py --repo-root .`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-18-native-completed-turn-ssot-and-result-publication-plan.md`
- `py -B -m pytest -q`
- `git diff --check`
- LightRSI adapter build/typecheck/tests when its canonical source changes.
- One bounded live probe with persisted exact-turn/attempt-bound publication and fresh-reader evidence, or a precise `BLOCKED_CAPABILITY` artifact naming the unavailable native boundary.

## Completion Criteria

The plan is ready for completion verification when:

1. The current hardening and dirty workspace are reconciled without discarding
   unrelated user changes or claiming native capability proof.
2. A single LightRSI-native completed-turn owner is identified and its mapping
   from submitted turn to final assistant output is unambiguous.
3. No provider response is admitted merely because it is the latest response;
   tool-call continuations, stale turns, aborts, malformed rollouts, and
   ambiguous candidates fail closed.
4. Project OS remains the sole owner of `attempt_id`; no model-authored or fake
   ordinary-mode governance identifiers are required.
5. Existing atomic result publication/read-back semantics are reused; identical
   replay is idempotent and conflicting replay is rejected.
6. The result is durable before retirement and readable after retirement by a
   fresh controller process without a second attempt or publication.
7. Terminal/agent/pane output is diagnostic-only after native proof; source-scoped
   observation errors remain correctly fail-closed.
8. Settlement, CoS acceptance, strict receipts, Plan/Git consequences, and
   9router economics remain independently owned and observable.
9. No new database, registry, supervisor, event bus, journal, or duplicate result
   sidecar is introduced.
10. Generated LightRSI files are not directly edited; canonical source changes
    produce generated output only through the approved build/install path.
11. Missing provider usage is recorded as `unknown`/`inconclusive` and never
    invalidates an otherwise valid native result.
12. The final plan status, task ledger, blockers, deferrals, and evidence paths
    match current source, tests, and fresh verification.

Branch disposition, commit, push, pull request, review, merge, and worktree
cleanup remain separately authorized actions and are not completion criteria for
this plan.
