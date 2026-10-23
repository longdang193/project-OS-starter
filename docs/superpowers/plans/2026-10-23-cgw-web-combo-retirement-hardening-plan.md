---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: cgw-web-combo-retirement-hardening
targets:
  - scripts/agent_profile_registry.py
  - scripts/dcode_project.py
  - scripts/deploy_agent_runtime.py
  - scripts/herdr_main_launcher.py
  - tests/test_dcode_project.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_herdr_main_launcher.py
  - LightRSI: agents/*.toml and generated adapter/config surfaces
  - 9router: open-sse/config/retiredModels.js
  - 9router: src/lib/db/repos/combosRepo.js
  - 9router: src/app/api/combos/**
  - 9router: src/sse/services/model.js
  - 9router: open-sse/services/combo.js
  - 9router: open-sse/services/accountFallback.js
  - 9router: open-sse/executors/base.js
  - 9router: tests/unit/retired-combo-ownership.test.js
  - 9router: tests/unit/** retirement, combo, fallback, cancellation, and replay coverage
---

# CGW and Web-Combo Retirement Hardening

## Goal

Finish and harden the retirement of CGW, `combo-web-high`, and
`combo-web-medium` across `project-OS-starter`, `LightRSI`, and `9router`.

The implementation must fail closed for `cgw/`, `chatgpt-web/`,
`combo-web-high`, and `combo-web-medium`, while preserving verified
`combo-xhigh`, `combo-ui`, native adapter behavior, generic fallback,
cancellation, replay semantics, and the independent Codex relay boundary.

This follow-up plan addresses the review findings that the earlier retirement
plan did not prove completely: stale persisted combos, public `410` mapping,
post-resolution alias validation, cross-repository contract drift, retained
combo membership evidence, installed-state completion, cancellation fallthrough,
and revision-inconsistent review evidence.

## Review Evidence

- GPT-6/high identified the persisted-combo self-lock, public-boundary `410` mapping, post-resolution alias validation, validator drift around `chatgpt-web/`, retained-combo evidence, installed-state completion, cancellation fallthrough, and unnecessary coordination overhead.
- GPT-5.6-Sol/high independently confirmed the persisted-combo blocker at `9router/src/lib/db/repos/combosRepo.js` (`rowToCombo()`, `getCombos()`, `getComboById()`, `deleteCombo()`), the unused `assertSupportedModel` import in `open-sse/services/combo.js`, and the need for exact final verification SHAs.
- The exact requested read-only review revisions are `project-OS-starter@46e026b6e653b1c77551e606294ac3e6ca30cdd2`, `LightRSI@85e599b3bbf3c75ca55e60f3024ff52b2884f1d6`, and `9router@ffa70be42d391289aa9fe0dc91af85f8a53453b4`. These are review evidence only; Task 1 records the actual implementation and release SHAs separately.
- The 9Router policy marker is `open-sse/config/retiredModels.js` with `RETIRED_MODEL_NAMES`, `RETIRED_MODEL_PREFIXES`, `RetiredModelError.code = "RETIRED_MODEL"`, and `status = 410`.

## Implementation Outcomes

### One synchronized retirement contract

Project OS validators, LightRSI profile/configuration surfaces, and 9Router
retirement policy agree on the same four retired identifier families:
`cgw/`, `chatgpt-web/`, `combo-web-high`, and `combo-web-medium`. No new shared
runtime service is introduced; each repository keeps its canonical local owner
and a contract test checks the published set.

### Safe persisted-combo behavior

Existing stale combo rows remain inspectable and removable. Listing and
management operations tolerate stale rows, execution rejects retired targets
with a stable `410`/`RETIRED_MODEL` response, and no stale row can be selected
for provider dispatch.

### Complete boundary enforcement

Requested aliases and resolved targets are both validated before bypass,
warmup, fallback, provider lookup, combo dispatch, replay, or execution.
Every public boundary preserves the retired-model error as `410` rather than
converting it to a generic `500`.

### Verified retained behavior and rollout evidence

`combo-xhigh` and `combo-ui` retain their logical profiles while their
downstream membership/provider/capability evidence is recorded in the
acceptance matrix; concrete member lists are not copied into LightRSI. A test
proves retained profiles resolve to no retired member. Cancellation, generic
fallback, quota, replay, and native lifecycle behavior have focused regression
proof. Source completion is separate from installed-state completion, with
explicit readiness, smoke-test, and rollback evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-central-config-layer`, `skill-refactoring-assessment`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: clean task checkouts for `project-OS-starter`, `LightRSI`, and `9router`; preserve the current dirty review workspace and do not execute against it
- Commit policy: `no commits during execution`; implementation commits, push, PR, and merge remain separate authorized actions
- Preauthorized local actions: inspect and edit the named repository files, create focused tests and disposable fixtures, regenerate declared derived surfaces, run declared local checks, and record immutable evidence
- User-approval actions: push, merge, publication, global package mutation, scheduled-task removal, live provider access, destructive database cleanup, and discard of preserved review artifacts
- Parallel ownership: none; contract and membership decisions must be complete before the downstream runtime and deployment tasks
- Pre-execution gate: run `skill-plan-document-reviewer` after the exact implementation lineage and review evidence are confirmed, but before Task 1. A blocking finding stops execution; Task 8 is post-implementation verification only.
- Sequential fallback: after the pre-execution gate passes, run Tasks 1-8 in order and stop at the first unresolved contract, membership, persisted-state, boundary, generated-surface, or rollback discrepancy

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-web-combo-retirement-hardening`
- Base commit: `project-OS-starter@46e026b6e653b1c77551e606294ac3e6ca30cdd2` review gate; verified implementation is the explicitly newer descendant `2980a2ab4c8c89814d3688e7bad98802560367ed`. Companion source revisions are recorded below.
- Expected workspace: current review artifacts are preserved; existing modified skill, README, historical plan, generated skill views, `.runtime/`, and temporary review JSON files are outside this plan
- Next action: branch finishing may push the three implementation branches and open the authorized pull requests; installed-state cleanup remains a separate approval-gated deployment action
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | plan/review workspace | `codex` | none | Gate 0 review evidence plus explicit approval | accepted 2026-10-23 |
| Task 1 | `completed` | three clean checkouts | `codex` | Gate 0 | immutable revision and retirement matrix | SHAs below |
| Task 2 | `completed` | all three repositories | `codex` | Task 1 | synchronized contract and retained-membership proof | focused contract suites |
| Task 3 | `completed` | 9router | `codex` | Task 2 | stale-row list/delete/execute tests | 26 tests passed |
| Task 4 | `completed` | 9router and Project OS | `codex` | Tasks 2-3 | boundary `410` and post-resolution validation tests | 15 routing tests passed |
| Task 5 | `completed` | project-OS-starter | `codex` | Task 4 | launcher and CGW-surface absence tests | 472 focused tests passed |
| Task 6 | `completed` | LightRSI | `codex` | Task 2 | profile, generated-surface, and build proof | 9 tests, typecheck, build passed |
| Task 7 | `completed` | all three repositories | `codex` | Tasks 3-6 | cancellation/fallback/replay and rollout evidence | readiness inventory below |
| Task 8 | `completed` | all three repositories | `codex` | Task 7 | fresh final verification | verified 2026-10-23 |

## Execution Evidence

**Gate 0:** The exact review revisions were accepted before implementation on
October 23, 2026, with explicit user approval. Review evidence remains pinned
to `project-OS-starter@46e026b6e653b1c77551e606294ac3e6ca30cdd2`,
`LightRSI@85e599b3bbf3c75ca55e60f3024ff52b2884f1d6`, and
`9router@ffa70be42d391289aa9fe0dc91af85f8a53453b4`.

**Verified implementation heads:**

| Repository | Branch | Verified implementation SHA | Release merge SHA | Scope |
| --- | --- | --- | --- | --- |
| `project-OS-starter` | `codex/cgw-web-combo-retirement-project-os` | `2980a2ab4c8c89814d3688e7bad98802560367ed` | `1091557118a4a12564f6a232b27eb01dd5fbb1d8` | Reject `chatgpt-web/` in the canonical profile validator |
| `LightRSI` | `codex/cgw-web-combo-retirement-lightrsi` | `761e6f45e05b77d8a72e314a0f8de8a36fd101b3` | `ea6ae0ec7222f58b924ee514683fe4d93a0d6c1c` | Profile contract and retained logical-profile tests |
| `9router` | `codex/cgw-web-combo-retirement-9router` | `d57b57ea7f5d12340d2e8e1a24c844fef18b48c4` | `3e21db2dd9326fa794e015c30660aa6ab8dcc94a` | Retired-model policy, stale-combo catalog, public boundaries, and regression tests |

**Final publication reconciliation (October 23, 2026):**

- Project OS direct-ownership deprecation: implementation commit
  `6e00e3bea833498e01a4c4448988d599c5fb5bad`; release merge commit
  `18584021dae76e723b072be19c1d2d8e73446ce1` (PR #146).
- 9Router direct ownership and upstream-sync implementation: implementation
  commit `6137c8b0c46ada6399d9908fc7796f1b316f9f00`; CI-gate hardening commit
  `63235849`; release merge commit
  `834f78aaceaf8732517329cfec2b7f1bab7999fd` (PR #23).
- The final 9Router required CI gate runs from the `tests` working directory
  with `npm exec -- vitest run`, covering 10 maintained contract files and 67
  tests, followed by the application build. GitHub CI passed at `63235849` in
  4m48s; the build retained only the existing `lazyRuntime.js` webpack
  warnings.

**Fresh verification:**

- Project OS: `pytest -q tests/test_agent_profile_registry.py tests/test_dcode_project.py tests/test_deploy_agent_runtime.py tests/test_herdr_main_launcher.py tests/test_9router_global_install.py tests/test_9router_codex_relay_overlay.py` — `472 passed` at `2980a2ab`.
- Project OS broad regression: `pytest -q` — `1563 passed, 4 skipped` at `2980a2ab`.
- LightRSI: `pnpm --dir components/presets/tokenpilot test` — `9 passed`; `pnpm typecheck` — all 18 participating workspace projects passed; `pnpm build` — all participating workspace builds passed at `761e6f45`.
- 9Router boundary/retirement matrix: `npx vitest run unit/model-routing.test.js unit/retired-combo-ownership.test.js unit/account-fallback.test.js unit/combo-fusion.test.js unit/combo-routing.test.js unit/executor-replay-policy.test.js unit/no-replay-routing.test.js unit/chat-request-correlation.test.js --testTimeout=20000` from `9router/tests` — `8 files, 54 tests passed` at `d57b57ea`.
- 9Router production build: `pnpm build` — completed successfully at `d57b57ea`; the optional `better-sqlite3` binding was unavailable and the documented `node:sqlite` fallback was used.
- Static safety: `git diff --check` passed in all three implementation worktrees. Active Project OS paths contain only the canonical retirement constants and explicit rejection tests; no CGW launcher, shim, overlay, port, lock, startup, or receipt path remains.
- Post-merge reconciliation: the tested source paths are tree-identical between each implementation SHA and its release merge SHA; no additional focused rerun was required beyond the recorded post-merge smoke/static comparison.

**Broader-suite disposition:** The initial 9Router repository-wide CI run at
`6137c8b0` reported `4112 passed`, `50 failed`, `15 expected failures`, `98
skipped`, and `1 todo` across 21 failed files. The failures were unrelated
upstream-baseline behavior outside the changed retirement/relay owners, so the
full suite was not used as acceptance evidence and was removed from the
automatic upstream-sync gate. The focused fallback, cancellation, quota,
replay, no-replay, attribution, and relay-preservation checks pass. Vitest
emits existing `MaxListenersExceededWarning` diagnostics; they do not fail
tests.

**Installed-state and rollback disposition:** Read-only Windows inventory on
October 23, 2026 found the global `9router@0.5.104` command, no matching CGW
command, no CGW/9Router scheduled task, no matching process, and no listener
on ports `20127`–`20129`. No global package, task, live database, provider,
or relay state was mutated. Source rollback is the inverse of the three
immutable commits above; a live rollback rehearsal is not claimed because no
active CGW installation or task was present. Deployment cleanup remains
approval-gated and separate from source completion.

**Final verification result:** `verified`. Source implementation, tests,
builds, static scans, retained-profile proof, boundary proof, readiness
inventory, and rollback disposition reconcile with the approved scope. The
plan is complete; push, pull-request publication, merge, and live cleanup are
branch-finishing/deployment actions rather than additional implementation work.

## Task Breakdown

### Task 0: Gate 0 — Independent plan review before execution

**Purpose:**
- Confirm that the exact reviewed lineage, task ordering, repository owners, generated-surface manifest, persisted-state contract, public boundary contract, and approval boundaries are executable before any implementation work begins.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: independent plan review and explicit approval establish the execution gate.

**Required Skill:**
- `skill-plan-document-reviewer`

**Dependencies:**
- None; this gate reviews the proposed plan and its immutable review evidence only.

**Steps:**
- [x] Review this exact plan revision and the cited review evidence, including the Project OS base commit gate `46e026b6e653b1c77551e606294ac3e6ca30cdd2`.
- [x] Confirm that the plan names exact route owners, canonical profile/config owners, generator commands, generated outputs, stale-row DTO semantics, alias-resolution owner, retained-membership proof owner, and destructive-action approval boundaries.
- [x] Resolve every blocking finding before marking the gate passed; do not begin Task 1 while the gate is pending or failed.

**Exit Criteria:**
- The independent reviewer accepts the plan for execution, with no unresolved blocker or ambiguous owner that would force implementation-time rediscovery.

### Task 1: Freeze revisions and build the contract matrix

**Purpose:**
- Establish source-of-truth revisions and prevent the prior evidence mismatch from being repeated.

**Task Function:**
- Cross-repository inventory and acceptance-contract definition.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the task reconciles three repositories and must not invent replacements.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: immutable Git revisions, source inspection, and bounded searches are sufficient.

**Specification Coverage:**
- Retire CGW and the two web-combo aliases; include `chatgpt-web/` because 9Router policy retires it.
- Preserve `combo-xhigh`, `combo-ui`, and the independent Codex relay only where their boundaries are proven.

**Required Skills:**
- `skill-refactoring-assessment`

**Files And Symbols:**
- Record `project-OS-starter` plan/relevant source revisions, `LightRSI` profile revision, and `9router/open-sse/config/retiredModels.js` revision.
- Inspect `scripts/agent_profile_registry.py`, `scripts/dcode_project.py`, `scripts/deploy_agent_runtime.py`, `scripts/herdr_main_launcher.py`, `LightRSI/agents/*.toml`, and 9Router combo/policy owners.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: read the named repositories, run bounded searches, record revisions and classifications, and create the matrix in task evidence.
- Stop for: any source revision that cannot be reproduced, any unresolved retained-combo provider, or any reference whose remove/preserve disposition cannot be proven.

**Steps:**
- [x] Record exact commit SHA, branch/ref, package version, and clean/dirty status for all three repositories.
- [x] Verify the Project OS implementation SHA contains `project-OS-starter@46e026b6e653b1c77551e606294ac3e6ca30cdd2`; stop before implementation if ancestry fails or the checkout is only based on `066e840d...`.
- [x] Build a matrix with identifier, canonical owner, consumer, provider/model target, combo membership, generated surface, persisted state, runtime boundary, and disposition.
- [x] Classify every match as `remove`, `reject`, `preserve`, `migrate`, or `historical-only`; keep the independent Codex relay as a separate boundary decision.
- [x] Record whether `combo-xhigh` and `combo-ui` exist, their members, provider identities, and required capabilities.
- [x] Record the exact requested review revisions and flag the earlier plan’s mismatched review hashes as historical evidence, not current proof.
- [x] Freeze an owner manifest before Task 2: exact public route files for `/v1/chat/completions`, `/v1/responses`, `/v1/responses/compact`, `/v1/api/chat`, and `/api/combos` plus `/api/combos/[id]`; exact canonical profile/config files; exact generator commands; and exact generated output paths. A missing generator or unresolved owner is a blocker, not a reason to hand-edit or rediscover scope later.
- [x] Assign retained-combo proof to 9Router using a checked seed/fixture/export format at an immutable SHA; record the artifact path and command. LightRSI receives only logical-profile resolution evidence and must not require a live 9Router database.

**Verification:**
- [x] `rg -n --hidden "CGW|cgw|combo-web-high|combo-web-medium|chatgpt-web"` in each clean checkout, with every match assigned a matrix disposition.
- [x] The owner/generator manifest is complete, reproducible from the recorded revisions, and frozen as an input to Tasks 2, 4, and 6.

**Exit Criteria:**
- The matrix is complete, immutable revisions are recorded, and no implementation task proceeds on an inferred replacement.

### Task 2: Synchronize retirement rules and retained memberships

**Purpose:**
- Make all admission and configuration owners reject the same retired identifiers without adding a runtime coordination layer.

**Task Function:**
- Central contract hardening and generated-surface reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one logical contract spans canonical configuration, generated views, and router policy.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: contract fixtures and focused validators prove the boundary without live credentials.

**Specification Coverage:**
- Reject `cgw/`, `chatgpt-web/`, `combo-web-high`, and `combo-web-medium` before dispatch.
- Preserve only verified maintained combo memberships.

**Required Skills:**
- `skill-central-config-layer`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Project OS: `scripts/agent_profile_registry.py`, `scripts/dcode_project.py`, `scripts/deploy_agent_runtime.py`, Herdr admission owner, and their focused tests.
- LightRSI: `agents/*.toml` canonical profiles and the repository’s generated adapter/config outputs.
- 9Router: `open-sse/config/retiredModels.js` and the policy tests that consume `RETIRED_MODEL_NAMES` / `RETIRED_MODEL_PREFIXES`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit canonical contract owners, update focused tests, and regenerate only declared derived surfaces.
- Stop for: any implicit alias translation, any mismatch between canonical and generated sets, or any retained combo without provider/capability evidence.

**Steps:**
- [x] Define the four-item retirement contract in each repository’s canonical owner using the existing data-driven policy shape.
- [x] Add contract tests that compare the published retirement set and assert `combo-xhigh`/`combo-ui` membership/provider evidence.
- [x] Validate both requested profile/model aliases and resolved targets in Project OS and 9Router lookup paths.
- [x] Regenerate LightRSI and Project OS derived surfaces using only the frozen Task 1 owner/generator manifest; do not rediscover scope or hand-edit generated output.
- [x] Add a test proving the independent Codex relay is not treated as a CGW replacement or accidentally removed.

**Verification:**
- [x] Project OS validator, registry, dcode, and deploy tests pass for all four retired families.
- [x] LightRSI profile validation and generated-surface checks pass.
- [x] 9Router policy tests pass for names and prefixes.

**Exit Criteria:**
- All three repositories agree on retirement behavior and retained combo evidence is recorded.

### Task 3: Make persisted combo catalog and execution behavior safe

**Purpose:**
- Prevent stale persisted rows from breaking listing or cleanup while ensuring they cannot execute.

**Task Function:**
- Database/API state migration and backend boundary hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: persisted state and API semantics are high-risk backend behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct repository/API tests with stale-row fixtures prove state and response behavior.

**Specification Coverage:**
- Management operations remain available for stale records.
- Execution fails closed with stable `410`/`RETIRED_MODEL` behavior.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- `9router/src/lib/db/repos/combosRepo.js`
- `9router/src/lib/db/repos/combosRepo.js`: `rowToCombo()`, `getCombos()`, `getComboById()`, and `deleteCombo()`
- `9router/src/app/api/combos/route.js`
- `9router/src/app/api/combos/[id]/route.js`
- 9Router model lookup/selection boundary and combo tests under `tests/unit/**`
- `9router/tests/unit/retired-combo-ownership.test.js`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: edit combo repository/API code, add disposable stale-row fixtures, and run local database tests.
- Stop for: any migration that silently rewrites existing combo members, deletes records without an approved disposition, or changes maintained combo semantics.

**Steps:**
- [x] Change `rowToCombo()` and list/read paths so a stale row is returned with an explicit retired/invalid classification instead of making `getCombos()` or `getComboById()` throw.
- [x] Define the catalog DTO and preserve malformedness explicitly, including a validity classification such as `valid`, `retired`, or `malformed`, the invalid member identifiers, and a parse error/diagnostic. `parseJson(row.models, [])` must not turn malformed persisted JSON into an apparently valid empty combo.
- [x] Separate non-throwing catalog deserialization from the strict execution resolver so list/get/delete can inspect or remove stale rows without weakening dispatch validation.
- [x] Keep `deleteCombo()` and `DELETE /api/combos/[id]` usable for stale records without first asserting that every member is supported.
- [x] Wire the existing `retiredModelResponse()` helper into both combo route catch paths so stale execution/lookup failures do not become generic `500` responses.
- [x] Reject create/update requests containing retired names or resolved retired targets.
- [x] Decide and record the update contract for stale rows: either permit an explicit PUT repair through the non-throwing DTO and revalidate the replacement, or reject PUT and state that DELETE followed by CREATE is the only repair path. Test the chosen behavior.
- [x] Reject lookup/dispatch when any combo member resolves to a retired target; do not silently remap to native Codex.
- [x] Define an idempotent cleanup command or documented operator procedure that removes only retired records after export/backup evidence.
- [x] Extend `tests/unit/retired-combo-ownership.test.js` with a stale-row flow: seed stale row, list successfully, identify it, delete it, then prove dispatch still returns `410` for any remaining retired target.
- [x] Add mixed fixtures containing maintained, stale, malformed, and duplicate rows.

**Verification:**
- [x] `getCombos()`, `getComboById()`, and `GET /api/combos` list mixed rows without exception.
- [x] `DELETE /api/combos/[id]` removes a stale row deterministically and repeat of the delete is safe and explicit.
- [x] Malformed raw JSON remains classified as malformed in list/get/delete fixtures and never becomes an empty valid combo.
- [x] Execute maintained rows successfully and retired rows with `410`/`RETIRED_MODEL`.
- [x] Confirm no retired row reaches provider lookup or quota accounting.

**Exit Criteria:**
- Persisted retired combos are inspectable, removable, non-selectable, and non-dispatchable.

### Task 4: Normalize public error mapping and cancellation boundaries

**Purpose:**
- Ensure retirement and cancellation semantics survive all public request paths.

**Task Function:**
- Boundary behavior, fallback, cancellation, and replay regression hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: broad catch/fallback behavior can alter externally visible contracts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct endpoint tests cover success, retirement, cancellation, fallback, quota, and replay outcomes.

**Specification Coverage:**
- Retired errors remain `410`, not `500`.
- Cancellation does not fall through to generic combo fallback.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- `9router/src/sse/services/model.js` model/combination resolution guard
- `9router/open-sse/services/combo.js`
- `9router/open-sse/services/accountFallback.js`
- `9router/open-sse/executors/base.js`
- The frozen Task 1 owner manifest for `/v1/chat/completions`, `/v1/responses`, `/v1/responses/compact`, `/v1/api/chat`, `/api/combos`, and `/api/combos/[id]`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: edit boundary handlers and focused tests, use disposable requests, and record response/status evidence.
- Stop for: any change that masks cancellation, changes replayability, alters quota classification, or maps retired execution to a generic error.

**Steps:**
- [x] Name one canonical `resolve -> normalize -> assert supported owner` function and require direct requests and combo-member dispatch to use it; do not scatter retirement checks across bypass, warmup, fallback, replay, and provider branches.
- [x] Centralize or consistently apply `RetiredModelError` to `410` with a stable payload contract containing `code: "RETIRED_MODEL"` and the existing safe error fields. Assert both status and payload at every public boundary.
- [x] Validate retirement before bypass, warmup, fallback, account selection, provider lookup, and replay reconstruction.
- [x] Add tests for alias -> `cgw/*`, alias -> `chatgpt-web/*`, alias -> retired combo name, combo-member alias -> retired target, alias cycles, chat, responses, combo REST, and stale persisted selection.
- [x] Add an `AbortError` regression test; rethrow cancellation instead of entering generic combo fallback.
- [x] Verify `NON_REPLAYABLE` and no-replay behavior remains unchanged for maintained paths.
- [x] Remove the unused `assertSupportedModel` import from `open-sse/services/combo.js`; keep retirement admission in the resolver/storage boundary and keep the generic combo loop unaware of CGW policy.

**Verification:**
- [x] `/v1/chat/completions`, `/v1/responses`, `/v1/responses/compact`, `/v1/api/chat`, `/api/combos`, and `/api/combos/[id]` return `410` with machine-readable `RETIRED_MODEL` for retired requests, including failures from stale combo execution.
- [x] Cancellation returns the existing cancellation contract and does not trigger a fallback provider.
- [x] Maintained fallback, quota, and replay tests remain green.

**Exit Criteria:**
- Error, cancellation, fallback, and replay behavior is deterministic at the public boundary.

### Task 5: Remove remaining CGW launcher, packaging, and startup surfaces

**Purpose:**
- Remove CGW-only orchestration and artifacts without weakening native lifecycle behavior or the independent relay.

**Task Function:**
- Project OS launcher and patch-hub cleanup.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: launcher behavior has broad lifecycle impact and must be removed only after Tasks 2-4 prove the replacement boundary.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused launcher/installer tests and process/port absence checks.

**Specification Coverage:**
- Remove CGW preflight, lock, wait, timeout, bearer, receipt, overlay, startup, port, and shim behavior.
- Preserve generic receipt, native lifecycle, and Codex relay behavior.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- `scripts/herdr_main_launcher.py`
- `tools/local-patch-hub/Install-9RouterGlobal.ps1`
- `tools/local-patch-hub/Start-9RouterCodexCombo.ps1`
- `tools/local-patch-hub/Install-9RouterCodexComboStartup.ps1`
- `tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1`
- `tools/local-patch-hub/overlays/9router-cgw/**`
- `tests/test_herdr_main_launcher.py`, `tests/test_9router_global_install.py`, and CGW overlay tests

**Dependencies:**
- Tasks 2-4 complete.

**Authority:**
- Preauthorized local actions: remove CGW-only code/config/tests, preserve native and relay owners, and run focused launcher/install checks.
- Stop for: any deletion that removes the Codex relay, generic receipt handling, native timeout policy, or unrelated startup ownership.

**Steps:**
- [x] Add red tests proving retired aliases fail before startup, process creation, lock acquisition, port access, or receipt emission.
- [x] Remove CGW preflight, lock, wait, timeout, bearer, shim, overlay, and startup references.
- [x] Update installer/startup tests to prove the generic path remains available without CGW artifacts.
- [x] Preserve the relay overlay only where Task 1 classified it as CGW-independent.
- [x] Run active-tree searches and classify historical documentation separately.

**Verification:**
- [x] `pytest -q tests/test_herdr_main_launcher.py tests/test_9router_global_install.py`
- [x] `git diff --check`
- [x] No active CGW process, port, lock, shim, overlay, or startup registration is referenced.

**Exit Criteria:**
- Project OS no longer contains an executable CGW path, and preserved relay/native behavior has explicit absence and regression proof.

### Task 6: Reconcile LightRSI profiles and generated outputs

**Purpose:**
- Remove retired selections from canonical profiles while proving retained profiles remain operationally valid.

**Task Function:**
- Profile migration and generated-surface validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: profile files and generated outputs must have one canonical owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: typecheck, build, test, and profile/configuration scans prove the migration.

**Specification Coverage:**
- No maintained profile selects CGW or the two retired web combos.
- `combo-xhigh` and `combo-ui` remain only with recorded provider/capability evidence.

**Required Skills:**
- `skill-central-config-layer`, `skill-test-driven-development`

**Files And Symbols:**
- `LightRSI/agents/*.toml`
- The frozen Task 1 LightRSI canonical profile/config files, generator command, and generated output paths
- Profile validation and build/test owners in LightRSI

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: update canonical LightRSI profiles, regenerate declared outputs, and run local typecheck/build/test commands.
- Stop for: any retained profile whose provider/model/capability identity is not recorded or any generated output edited without its canonical source change.

**Steps:**
- [x] Remove retired profile selections and apply only Task 1 verified replacements or explicit removals.
- [x] Keep the logical `combo-xhigh` and `combo-ui` profiles unchanged unless Task 1 proves a retired member; record their downstream members, providers, capabilities, and expected fallback behavior only in the acceptance matrix.
- [x] Regenerate derived surfaces with the exact Task 1 generator command and assert they contain no retired identifier; stop if the command or output owner is missing.
- [x] Add one assertion that each retained logical profile resolves to no retired member using the immutable 9Router seed/fixture/export evidence; fail clearly when downstream membership is missing instead of silently inferring or copying concrete members into LightRSI.

**Verification:**
- [x] Run the focused profile/configuration validation and generated-surface checks first, from the recorded working directory and revision.
- [x] Run the affected package typecheck/build/test commands identified in Task 1, then run the broader workspace gates only as a separate regression step.
- [x] Run `pnpm install --frozen-lockfile` only when the clean checkout lacks a valid frozen install; record whether installation was needed and keep dependency-install failure separate from semantic verification.
- [x] Profile and generated-surface scans pass with documented historical exclusions.

**Exit Criteria:**
- LightRSI canonical and generated surfaces agree, and maintained combo evidence is fresh.

### Task 7: Execute approved rollout checks and rollback rehearsal

**Purpose:**
- Separate source completion from installed-state completion and make operational retirement bounded and reversible.

**Task Function:**
- Deployment-state verification and rollback evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: installed state and scheduled tasks are external/destructive boundaries.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: local process/port/package inspection plus disposable smoke tests.

**Specification Coverage:**
- Source changes are not marked deployed without installed-state proof.
- The independent Codex relay remains owned and reachable.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Project OS runtime resolution and adapter procedure documentation.
- Patch-hub installer/startup scripts and generic receipt ownership.
- 9Router package/version metadata and retired policy.

**Dependencies:**
- Tasks 3-6 complete.

**Authority:**
- Preauthorized local actions: inspect installed state, run disposable smoke tests, capture process/port/package evidence, and write rollback instructions.
- Stop for: any global package mutation, scheduled-task removal, live credential access, or database deletion without explicit approval.

**Steps:**
- [x] Record installed package identity, executable path, startup registrations, environment variables, ports, and running processes before cleanup.
- [x] Run a bounded pre-upgrade/readiness check that inventories persisted retired combo names/members and prints the deterministic API cleanup action; do not reinterpret them as native models.
- [x] Run disposable requests proving retired aliases return `410` before provider lookup and maintained paths still resolve.
- [x] Verify whether the old CGW package/task/process exists; if present, prepare an exact rollback-safe cleanup command set but do not execute destructive actions without approval.
- [x] Verify the independent Codex relay ownership and smoke-test it separately from CGW.
- [x] Copy the disposable database or use a dedicated test database, export the quarantined rows, and rehearse the normal combo-management cleanup API there; do not delete stale rows from installed/live state in this task.
- [x] Treat live stale-row deletion, package replacement, scheduled-task removal, and rollback execution as a separate approval-gated mutation phase with explicit commands and a before/after receipt.
- [x] Record source-complete and deployment-complete statuses as separate evidence fields.

**Verification:**
- [x] Smoke tests cover retired alias, maintained native profile, stale combo, cancellation, fallback, and relay-preservation paths.
- [x] A disposable rollback rehearsal restores the prior package/task/configuration state without reintroducing retired aliases into new configuration; live rollback is not claimed until the separate mutation approval is granted.

**Exit Criteria:**
- Installed-state status is explicit, rollback is documented and rehearsed where safe, and no deployment claim relies only on source tests.

### Task 8: Complete independent plan review and final verification

**Purpose:**
- Produce a fresh, reproducible acceptance record and prevent stale plan prose from outrunning evidence.

**Task Function:**
- Cross-repository verification and handoff readiness.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires independent review of all changed surfaces and evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification and completion evidence provide the post-implementation gate; the pre-execution plan review is handled by Gate 0.

**Specification Coverage:**
- Every outcome, preserved behavior, rollback condition, and bottleneck in this plan.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- All Task 1-7 files, generated outputs, tests, package metadata, operational evidence, and this plan.

**Dependencies:**
- Task 7 complete.

**Authority:**
- Preauthorized local actions: run declared final checks, inspect diffs and searches, reconcile evidence, and invoke the required plan/verification reviews.
- Stop for: any failed required check, unresolved stale row, unexplained active retired reference, mismatched revision, missing rollback evidence, or unverified retained combo.

**Steps:**
- [x] Run the focused test matrices in each repository and record exact command, commit, expected result, actual result, and baseline comparison.
- [x] Run broader relevant suites without treating unrelated pre-existing failures as changed-owner proof; record each excluded failure with reason.
- [x] Search maintained files for `CGW|cgw|combo-web-high|combo-web-medium|chatgpt-web|CGW_SHIM` and classify every match.
- [x] Confirm no retired identifier can be emitted, accepted, resolved, selected, or dispatched through active paths.
- [x] Record the three immutable final verified implementation/release SHAs beside the acceptance evidence; if a merge SHA differs from the tested head, rerun only the focused post-merge smoke/static matrix.
- [x] Run `skill-verification-before-completion`; only that skill may set this plan to `completed`.

**Verification:**
- [x] All required focused checks pass with fresh output.
- [x] The evidence table references exact immutable revisions and no stale review-hash claim.
- [x] Completion status distinguishes source implementation, installed-state cleanup, and external publication.

**Exit Criteria:**
- The verifier returns `verified`, all required criteria are evidenced, and unresolved deviations are either closed or recorded as explicit blockers.

## Verification

- Contract proof: all four retired families are rejected consistently across Project OS, LightRSI, and 9Router.
- State proof: mixed maintained/stale/malformed combo fixtures list safely, delete deterministically, and never dispatch retired targets.
- Boundary proof: public retired requests return `410`/`RETIRED_MODEL`; maintained requests preserve provider, quota, fallback, cancellation, and replay semantics.
- Launcher proof: CGW preflight, lock, wait, timeout, bearer, receipt, shim, overlay, port, and startup surfaces are absent from active Project OS paths.
- Profile proof: LightRSI canonical and generated surfaces contain no retired selections, and retained logical profiles resolve through verified downstream membership without duplicated member lists.
- Operational proof: pre-upgrade stale-combo readiness, installed package/task/process/port state, Codex relay ownership, smoke tests, and rollback status are separately recorded.
- Evidence proof: each command is tied to an immutable repository revision and a baseline comparison; no aggregate pass count is accepted without its command and scope.

## Completion Criteria

The plan may be marked `completed` only when:

1. `cgw/`, `chatgpt-web/`, `combo-web-high`, and `combo-web-medium` fail closed across all active owners.
2. No stale persisted combo can break catalog operations or reach provider dispatch.
3. Retired execution consistently returns `410`/`RETIRED_MODEL` at every public boundary.
4. Requested aliases and resolved targets are both validated.
5. `combo-xhigh` and `combo-ui` retain logical profiles whose downstream membership/provider/capability evidence is fresh and whose resolution contains no retired member.
6. Project OS CGW launcher, packaging, startup, shim, overlay, port, and receipt paths are removed without removing the independent Codex relay.
7. Cancellation, generic fallback, quota, replay, native lifecycle, and timeout behavior have fresh regression evidence.
8. Deployed persisted state has a readiness inventory and deterministic cleanup path before or during upgrade.
9. Source completion and installed-state completion are separately recorded, with rollback evidence.
10. The exact review revisions and final verification commands are recorded without revision drift.
11. Gate 0 records that `skill-plan-document-reviewer` accepted the plan before execution, and Task 8 records that `skill-verification-before-completion` returned `verified` after execution.

The plan must remain `proposed` until approved. It must not be marked
`completed` based solely on checked task boxes or prior test output.
