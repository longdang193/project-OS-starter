---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
name: cgw-retirement-consolidated-closure
targets:
  - project-OS-starter
  - LightRSI
  - 9router
  - docs/superpowers/plans/2026-10-23-22-10-cgw-retirement-consolidated-closure-plan.md
---

# CGW Retirement Consolidated Closure

## Goal

Close the remaining CGW and web-combo retirement gaps across `project-OS-starter`,
`LightRSI`, and `9router` without reintroducing a shared runtime service or
removing the independent Codex relay capability.

The implementation must make `cgw/`, `chatgpt-web/`, `combo-web-high`, and
`combo-web-medium` fail closed after provider-alias normalization, make stale
persisted combos inspectable and removable, preserve stable `410` /
`RETIRED_MODEL` behavior, and reduce duplicated policy, relay hops, scan
exceptions, and evidence-reconciliation work.

The current review evidence is split across two inputs. The completed hardening
plan records the earlier GPT-6 and GPT-5.6 findings for persisted combos, public
error mapping, cancellation/fallback/replay behavior, retained profiles,
installed-state proof, and revision consistency. The latest GPT-5.6-Sol review
against newer pinned revisions adds the `cg/` alias-normalization bypass, the
active `chatgpt-web/*` relay exception, duplicated lexical policy lists, stale
CGW test wording, and missing launcher-boundary coverage. The completed live
GPT-6 review against the same pinned revisions confirms those retirement risks
and adds fail-closed gaps in the warmup bypass, image-generation error mapping,
model catalog filtering, alias writes, and cross-repository retained-combo
proof. It also identifies the LightRSI cold catalog lookup as a latency and
availability bottleneck, and clarifies that the native Codex relay is a typed
compatibility boundary rather than a public CGW model-selection path.

## Review Basis

- Latest GPT-5.6-Sol review: `project-OS-starter@9399437f53847513e65bbb76c04802cc65d7f57c`, `LightRSI@ea6ae0ec7222f58b924ee514683fe4d93a0d6c1c`, and `9router@ac10953d5e1c6f2acfb3c6d8515371e220c446d6`.
- Latest pinned review files: `project-OS-starter/docs/superpowers/plans/2026-10-23-cgw-web-combo-retirement-plan.md`, `project-OS-starter/scripts/agent_profile_registry.py`, `LightRSI/components/presets/tokenpilot/tests/agent-profile-contract.test.ts`, `LightRSI/components/adapters/codex/tests/context-rebase-behavior.test.ts`, `9router/open-sse/config/retiredModels.js`, and `9router/tests/unit/model-routing.test.js`.
- Completed GPT-6 high-reasoning read-only review `cgw-retirement-review-2026-10-23` against `project-OS-starter@9399437f53847513e65bbb76c04802cc65d7f57c`, `LightRSI@ea6ae0ec7222f58b924ee514683fe4d93a0d6c1c`, and `9router@ac10953d5e1c6f2acfb3c6d8515371e220c446d6`.
- GPT-6 evidence markers: `9router/open-sse/config/retiredModels.js:isRetiredModel`, `registry/chatgpt-web.js` aliases, `src/sse/services/model.js:getModelInfo`, `executors/index.js`, `imageProviders/chatgpt-web.js`, `src/sse/handlers/chat.js:handleChatInternal`, `bypassHandler.js`, `src/sse/handlers/imageGeneration.js`, `images/generations/route.js`, `combosRepo.js`, `v1/models/route.js:buildModelsList`, `models/alias/route.js:PUT`, LightRSI `upstream.ts:loadNineRouterModels` and `resolveNineRouterPayloadModel`, Project OS `runtime-adapter-procedure.md`, `tools/local-patch-hub/README.md`, and `test_9router_patch_hub_deprecation.py`.
- Prior GPT-6 and GPT-5.6 evidence retained from `docs/superpowers/plans/2026-10-23-cgw-web-combo-retirement-hardening-plan.md`: persisted-combo safety, public `410` mapping, post-resolution validation, retained-profile evidence, installed-state completion, cancellation/fallback/replay proof, and immutable final SHAs.
- Review evidence is read-only and does not authorize implementation, push, merge, package publication, live cleanup, or installed-state mutation.

## Implementation Outcomes

### Canonical retirement enforcement

`9router` owns the canonical retired-provider policy. Every direct model,
combo member, stored alias, fallback target, and resolved provider target is
normalized before the retirement gate runs. The `cg` alias cannot reach the
retired `chatgpt-web` executor through any chat or code route.

### Safe persisted state and public boundaries

Stale or malformed persisted combo rows remain listable and removable without
poisoning catalog operations. Retired execution returns `410` with
`RETIRED_MODEL` consistently at public boundaries, including alias-resolved
and combo-dispatched paths, before warmup or synthetic bypasses, and on image
generation routes, without falling through to generic provider fallback or
retry behavior. Unusable persisted combos are excluded from executable model
catalogs while remaining available to administrative inspection, and new alias
writes reject retired targets.

### Relay isolation and lower operational cost

The independent Codex relay remains available as an explicitly typed native
transport boundary, not as a public `chatgpt-web/*` model-selection path. The
relay uses typed metadata or a dedicated internal identity where compatible;
if protocol compatibility requires a legacy field, it is isolated to the
relay route and covered by an owned exception test rather than general model
routing. The implementation is measured for latency, retries, stream failures,
CPU, and memory before and after the change.

### Synchronized consumer contracts

Project OS and LightRSI consume a generated projection of the canonical
retirement contract rather than hand-maintaining divergent name/prefix lists.
Canonical profiles and generated adapter/config surfaces contain no retired
selection, while `combo-ui` and `combo-xhigh` retain only verified, non-retired
downstream membership. The retained profiles are checked against a bounded
9Router runtime fixture or snapshot without copying mutable combo membership
into LightRSI.

### Durable acceptance evidence

One verification record ties each repository's baseline, implementation head,
release merge head, exact commands, test scope, approved compatibility
exceptions, installed-state status, rollback evidence, and final disposition
to immutable revisions. Source completion and installed-state completion stay
separate.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-central-config-layer`, `skill-refactoring-assessment`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: clean task checkouts for `project-OS-starter`, `LightRSI`, and `9router`; preserve the current review workspace and its untracked browser/runtime artifacts
- Commit policy: `no implementation commits during execution`; coordination checkpoint commits are required by the Git-tracked rule, while implementation commits, pushes, pull requests, merges, package publication, and installed-state mutation remain separately authorized
- Preauthorized local actions: inspect and edit named repository files, create focused tests and generated projections, run declared local checks, run disposable relay/rollback measurements, and record immutable evidence
- User-approval actions: push, merge, publication, global package mutation, scheduled-task removal, live provider access, destructive database cleanup, and discard of preserved review artifacts
- Complexity guard: do not add a runtime preflight service, distributed lock, or repeated full-suite gate for retirement; use one lightweight pre-bypass check, canonical post-resolution validation, and focused table-driven boundary matrices.
- Parallel ownership: none; policy, persisted-state, relay, profile, and evidence changes are intentionally ordered to keep one lead controller as the ledger owner
- Sequential fallback: after Gate 0, execute Tasks 1-7 in order and stop at the first unresolved policy, persisted-state, boundary, generated-surface, performance, or rollback discrepancy

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/cgw-retirement-consolidated-closure`
- Base commits: `project-OS-starter@4eec2aaf6d00ddd8978eda0561fe5f31176e55aa`, `LightRSI@ea6ae0ec7222f58b924ee514683fe4d93a0d6c1c`, and `9router@ac10953d5e1c6f2acfb3c6d8515371e220c446d6`; implementation uses clean detached worktrees from these exact revisions
- Expected workspace: current Project OS checkout owns this plan and coordination state; clean worktrees under `project-OS-starter-worktrees`, `LightRSI-worktrees`, and `9router-worktrees` own implementation changes; pre-existing `.playwright-mcp/` and `.runtime/` artifacts remain untouched
- Next action: execute Task 2 in the isolated 9router worktree using disposable database fixtures and the frozen base revision
- Blockers: none for Task 2 admission; the native Codex relay remains an explicit typed compatibility boundary

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `lead controller` | none | accepted plan review and frozen revisions | user-approved; paths reconciled; repository contract validation passed |
| Task 1 | `completed` | `9router-worktree` | `lead controller` | Task 0 | canonical policy and alias matrix | source patch, generated projections, Node smoke checks, exact Vitest matrix 34/34, extended image matrix 37/37 |
| Task 2 | `active` | `9router` | `lead controller` | Task 1 | stale-combo, `410`, fallback, cancellation, and replay proof | admitted after Task 1 proof; in progress |
| Task 3 | `pending` | `9router` | `unresolved` | Tasks 1-2 | relay isolation and before/after performance evidence | pending |
| Task 4 | `pending` | `project-OS-starter` | `unresolved` | Task 1 | launcher boundary and CGW-surface absence tests | pending |
| Task 5 | `pending` | `LightRSI` | `unresolved` | Task 1 | canonical/generated profile and fixture proof | pending |
| Task 6 | `pending` | all three repositories | `unresolved` | Tasks 2-5 | synchronized verification and rollback record | pending |
| Task 7 | `pending` | all three repositories | `unresolved` | Task 6 | fresh final verification and handoff evidence | pending |

## Task Breakdown

### Task 0: Gate 0 — Review and freeze the consolidated contract

**Purpose:**
- Confirm that the plan is executable, that the relay-preservation decision is explicit, and that the review evidence is pinned to immutable revisions before implementation begins.

**Task Function:**
- Plan readiness and cross-repository contract review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the plan owns dependency order, scope, and evidence requirements.

**Validator Profile:**
- `skill-plan-document-reviewer`
- Selection basis: independent review is required before costly cross-repository edits.

**Specification Coverage:**
- All implementation outcomes, preserved Codex relay behavior, rollback boundaries, and known model-review limitations in this plan.

**Required Skills:**
- `skill-plan-document-reviewer`

**Files And Symbols:**
- `docs/superpowers/plans/2026-10-23-22-10-cgw-retirement-consolidated-closure-plan.md`
- `docs/superpowers/plans/2026-10-23-cgw-web-combo-retirement-plan.md`
- `docs/superpowers/plans/2026-10-23-cgw-web-combo-retirement-hardening-plan.md`
- The pinned review files listed in Task 1.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: inspect the plan, existing completed plans, pinned review evidence, and repository status; record plan-review findings.
- Stop for: any unresolved ownership decision, missing exact path, unpinned revision, or acceptance criterion that cannot be proven by a declared command.

**Steps:**
- [ ] Run `skill-plan-document-reviewer` against this plan before creating implementation branches.
- [ ] Confirm `9router/open-sse/config/retiredModels.js` is the canonical retirement-policy owner and that consumer projections are generated rather than hand-edited.
- [ ] Confirm the relay decision: retain the Codex transport boundary, remove `chatgpt-web/*` as its internal model identity, and preserve no public CGW selection path.
- [ ] Confirm the performance comparison uses the same stubbed workload, Node version, request count, and measurement fields before and after the relay change.
- [ ] Record the exact three implementation checkout revisions and the current generated-surface owners in the Coordination State evidence.

**Verification:**
- The plan reviewer returns an accepted result with no blocking finding, or the plan remains `proposed` and execution does not start.

**Exit Criteria:**
- The contract owner, relay boundary, generated projections, exact test commands, and stop conditions are accepted.

### Task 1: Enforce retirement after canonical provider normalization

**Purpose:**
- Close the `cg/` alias bypass and make the retired policy apply to canonical provider identity rather than raw spelling.

**Task Function:**
- Routing policy and alias-resolution hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one canonical policy owner must be updated before downstream consumers.

**Validator Profile:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`
- Selection basis: the change affects request admission, provider dispatch, and public error contracts.

**Specification Coverage:**
- Direct models, aliases, combo members, persisted aliases, fallback targets, and resolved provider targets all fail closed for the four retired identifier families.

**Required Skills:**
- `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- `9router/open-sse/config/retiredModels.js`: `RETIRED_MODEL_NAMES`, `RETIRED_MODEL_PREFIXES`, `RetiredModelError`, and the canonical contract export.
- `9router/open-sse/services/model.js`: `resolveProviderAlias`, `parseModel`, `resolveModelAliasFromMap`, `getModelInfoCore`, and `getModelInfo`.
- `9router/open-sse/providers/registry/chatgpt-web.js`: the `chatgpt-web` provider id and `cg` alias.
- `9router/open-sse/executors/index.js`: `ChatGptWebExecutor` registration.
- `9router/open-sse/imageProviders/chatgpt-web.js`: retained image executor path, if any non-CGW capability is explicitly approved.
- New generator: `9router/scripts/export-retired-model-policy.mjs`.
- Generated policy artifact: `9router/open-sse/config/retired-model-policy.json`.
- `9router/tests/unit/model-routing.test.js`.
- `9router/tests/unit/retired-combo-ownership.test.js`.

**Dependencies:**
- Task 0 complete.

**Authority:**
- Preauthorized local actions: edit the named 9router policy and routing files, add focused unit tests, and run the declared Vitest matrix from `9router/tests`.
- Stop for: any route that validates only the raw alias, any maintained model that changes provider resolution, or any public retired request that does not return `410` / `RETIRED_MODEL`.

**Steps:**
- [x] Add a canonical policy function that accepts normalized `{ provider, model }` and returns the stable retired error contract.
- [x] Add `scripts/export-retired-model-policy.mjs` to emit the canonical policy projection to `open-sse/config/retired-model-policy.json`, `project-OS-starter/repo_config/retired-model-policy.json`, and `LightRSI/components/presets/tokenpilot/retired-model-policy.json` from one source.
- [x] Call the policy after `resolveProviderAlias` in direct routing and after every alias-map resolution in `getModelInfoCore`.
- [x] Apply the same canonical check to combo members, fallback candidates, and persisted alias values before provider lookup, warmup, retry, or dispatch.
- [x] Ensure the `cg` alias cannot resolve to an active chat/code executor; remove the ChatGPT-Web image executor and registration unless a separately typed non-CGW capability is explicitly approved and tested.
- [x] Add tests for direct `cg/gpt-5-6`, direct `chatgpt-web/gpt-5-6`, `cgw/gpt-5-6`, retired combo members using `cg/`, stored aliases resolving to `cg/`, and maintained native models.
- [x] Add provider-level tests for `cg/gpt-image-2` and normalized image-provider targets so a retained alias cannot reach `ChatGptWebExecutor` or `imageProviders/chatgpt-web.js`.
- [x] Remove any unused retirement-validation import or duplicate raw-string guard left behind by the canonical gate.

**Verification:**
- [x] From `9router/tests`, run `npx vitest run unit/model-routing.test.js unit/retired-combo-ownership.test.js --testTimeout=20000`.
- [x] Assert that every retired request returns `410`, error code `RETIRED_MODEL`, zero provider-dispatch calls, and zero generic-fallback attempts.

**Execution Evidence (2026-10-23):**
- Source revision: isolated `9router` worktree at frozen base `ac10953d5e1c6f2acfb3c6d8515371e220c446d6` with uncommitted Task 1 changes; no implementation commit created.
- Passed: `node --check` for all changed JavaScript files, direct `parseModel` smoke (`cg/gpt-image-2` → `RETIRED_MODEL/410`; `codex/gpt-5.6` remains routed to `codex`), identical generated policy projections, and `git diff --check`.
- Passed: after user approval, transient `npm install --no-save --no-package-lock vitest` restored the test runner without changing tracked package metadata; the exact required matrix `npx vitest run unit/model-routing.test.js unit/retired-combo-ownership.test.js --testTimeout=20000` passed with 2 files and 34 tests, and the extended matrix including `unit/image-provider-retirement.test.js` passed with 3 files and 37 tests.

**Exit Criteria:**
- All raw and normalized paths share one canonical retirement decision, and the alias matrix passes without changing maintained provider routing.

### Task 2: Make stale persisted combos safe at every public boundary

**Purpose:**
- Preserve catalog usability and deterministic cleanup when persisted combos contain retired, malformed, or unresolved members.

**Task Function:**
- Persisted-state safety and public API contract hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: persisted state must be made safe before relay and rollout changes.

**Validator Profile:**
- `skill-test-driven-development`, `skill-backend-verification`
- Selection basis: catalog reads, deletes, execution, fallback, cancellation, and replay are behaviorally coupled.

**Specification Coverage:**
- Stale rows can be listed and deleted, retired rows cannot self-lock the catalog, public boundaries preserve `410` / `RETIRED_MODEL`, and maintained requests preserve fallback/cancellation/replay semantics.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- `9router/src/lib/db/repos/combosRepo.js`: `rowToCombo`, `getCombos`, `getComboById`, and `deleteCombo`.
- `9router/src/app/api/combos/**`.
- `9router/src/app/api/v1/models/route.js`: `buildModelsList` and executable catalog filtering.
- `9router/src/app/api/models/alias/route.js`: alias write validation.
- `9router/open-sse/services/combo.js`.
- `9router/open-sse/services/accountFallback.js`.
- `9router/open-sse/executors/base.js`.
- `9router/src/sse/handlers/chat.js`: `handleChatInternal` and early bypass ordering.
- `9router/src/sse/handlers/imageGeneration.js` and `9router/src/app/api/v1/images/generations/route.js`.
- `9router/src/sse/handlers/bypassHandler.js`.
- `9router/tests/unit/retired-combo-ownership.test.js`.
- `9router/tests/unit/account-fallback.test.js`.
- `9router/tests/unit/combo-routing.test.js`.
- `9router/tests/unit/executor-replay-policy.test.js`.
- `9router/tests/unit/no-replay-routing.test.js`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit the named combo repositories, API handlers, executor guards, and focused tests using disposable database fixtures only.
- Stop for: any live database deletion, any stale row that cannot be listed or removed, any retired target that reaches provider dispatch, or any cancellation/replay regression.

**Steps:**
- [ ] Make row conversion preserve stale members as inspectable data with a stable invalid-member marker instead of throwing during list or delete.
- [ ] Make `getComboById` and `deleteCombo` operate on stale rows without requiring every member to resolve to an active provider.
- [ ] Reject retired or unresolved targets before warmup, fallback selection, provider lookup, retry, or replay; retain generic fallback only for maintained provider failures.
- [ ] Run a lightweight retirement check on the original request identifier before `handleBypassRequest`, then keep canonical post-resolution validation before dispatch; do not add a new runtime service or lock for this ordering fix.
- [ ] Map `RetiredModelError` consistently to `410` / `RETIRED_MODEL` on image-generation and every other model-capable public route instead of allowing a `500`.
- [ ] Exclude retired, malformed, and unresolved combos from `/v1/models` executable catalog output while preserving administrative inspection and deletion.
- [ ] Reject new `/api/models/alias` writes whose targets resolve, directly or transitively, to retired providers.
- [ ] Add mixed maintained/stale/malformed fixtures that list, delete, execute, cancel, and replay deterministically.
- [ ] Add warmup/naming bypass tests for direct retired names and aliases, image-generation boundary tests, catalog filtering tests, and alias-write rejection tests.
- [ ] Re-run the focused combo/fallback/replay matrix and record the exact command, revision, and result.

**Verification:**
- From `9router/tests`, run `npx vitest run unit/retired-combo-ownership.test.js unit/account-fallback.test.js unit/combo-routing.test.js unit/executor-replay-policy.test.js unit/no-replay-routing.test.js --testTimeout=20000`.
- Verify zero provider calls for retired and unresolved members, stable public errors, and unchanged maintained fallback/cancellation/replay behavior.

**Exit Criteria:**
- Stale persisted state is manageable, retired execution is fail-closed, and no catalog or execution path self-locks on retired data.

### Task 3: Isolate the Codex relay and measure the operational trade-off

**Purpose:**
- Preserve the independent Codex relay while removing its active `chatgpt-web/*` model identity and reducing unnecessary forwarding overhead.

**Task Function:**
- Relay contract migration and performance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the relay is an explicit compatibility boundary and must not be removed by a lexical CGW cleanup.

**Validator Profile:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`
- Selection basis: relay changes require latency/resource evidence and direct no-replay/cancellation proof.

**Specification Coverage:**
- The Codex relay remains reachable, no public model-selection path accepts retired identifiers, and the implementation does not retain a permanent scan exception.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- `9router/src/app/api/v1/chatgpt-web/responses/route.js`.
- `9router/tests/unit/chatgpt-web-responses-relay.test.js`.
- `9router/open-sse/providers/registry/chatgpt-web.js`.
- `9router/open-sse/executors/index.js`.
- `LightRSI/components/adapters/codex/src/upstream.ts`: `loadNineRouterModels` and `resolveNineRouterPayloadModel`.
- `LightRSI/components/adapters/codex/tests/**` for cold/warm catalog lookup coverage.
- New benchmark owner: `9router/scripts/benchmarks/codex-relay-retirement.mjs`.

**Dependencies:**
- Tasks 1-2 complete.

**Authority:**
- Preauthorized local actions: update the relay route and focused tests, add the deterministic local benchmark, run stubbed relay/direct comparisons, and record measurements.
- Stop for: any public model-selection route that still selects `chatgpt-web/*`, any untyped relay exception, any loss of no-replay or cancellation guarantees, any benchmark using live credentials, or any performance conclusion without identical before/after workloads.

**Steps:**
- [ ] Change the relay contract to carry typed relay metadata or a dedicated internal `codex-relay` identity; do not pass relay requests into general model routing. If a legacy `chatgpt-web/*` protocol field must remain, isolate it to this route and record the explicit native-relay exception.
- [ ] Update `chatgpt-web-responses-relay.test.js` to prove the relay boundary is preserved, the route is not a public model-selection interface, and the legacy field is never resolved by retired-model routing.
- [ ] Remove the provider/executor registration from general chat routing when the relay no longer depends on it; retain a separately typed capability only if an existing non-chat path proves it is required.
- [ ] Add `scripts/benchmarks/codex-relay-retirement.mjs` with 100 deterministic stubbed streaming requests per path and JSON output for P50/P95 TTFT, total latency, CPU time, peak RSS, retry count, stream disconnects, and error classes.
- [ ] Compare the loopback relay with the direct adapter under the same Node version and request payloads. Accept relay removal only when P95 TTFT does not regress and the direct path removes a hop without changing no-replay, cancellation, or error classification; otherwise keep the relay with the typed identity and document the measured reason.
- [ ] Measure LightRSI cold and warm catalog lookup for explicitly declared `combo-ui` and `combo-xhigh`, plus missing-catalog and outage behavior. Avoid discovery for an exact, contract-validated logical combo only when the measurement and tests show the shortcut preserves routing semantics; retain discovery for ambiguous names.

**Verification:**
- Run the relay unit test and benchmark twice per path from the same clean checkout.
- Record the workload, Node version, environment, sample count, metrics, threshold decision, and retained/removed relay disposition in the final evidence table.

**Exit Criteria:**
- The Codex relay is independently proven, any legacy namespace field is confined to the typed native boundary and never enters general model routing, and the latency/resource decision is evidence-backed.

### Task 4: Close Project OS launcher and boundary-test gaps

**Purpose:**
- Prove that retired profiles are rejected before preflight, process launch, or prompt dispatch and remove remaining active CGW launcher references without editing generated projections directly.

**Task Function:**
- Launcher contract and generated-surface cleanup.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Project OS owns profile admission and launcher boundary behavior.

**Validator Profile:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`
- Selection basis: the change affects admission, transport, and diagnostic side effects.

**Specification Coverage:**
- Retired profiles fail before runtime acquisition, maintained profiles preserve native behavior, and no active Project OS overlay/shim/startup path remains.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- `project-OS-starter/scripts/agent_profile_registry.py`: retired policy and profile validation.
- `project-OS-starter/scripts/herdr_main_launcher.py`: `_profile` and preflight/launch boundary.
- `project-OS-starter/tests/test_agent_profile_registry.py`.
- `project-OS-starter/tests/test_herdr_main_launcher.py`.
- `project-OS-starter/scripts/sync_agent_adapters.py` and its generated adapter outputs.
- `project-OS-starter/repo_config/retired-model-policy.json` generated by `9router/scripts/export-retired-model-policy.mjs`.
- `project-OS-starter/docs/operating_system/tooling/runtime-tool-resolution.md`.
- `project-OS-starter/docs/operating_system/procedures/runtime-adapter-procedure.md`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: update canonical Project OS validators, launcher tests, and owned documentation; regenerate adapter projections with `scripts/sync_agent_adapters.py`.
- Stop for: any direct edit to a generated projection, any retired request that acquires a lock or starts a process, or any maintained native profile regression.

**Steps:**
- [ ] Replace the local lexical policy with the generated retirement-contract projection and preserve the four retired families plus the maintained `combo-ui` and `combo-xhigh` profiles.
- [ ] Add a table-driven launcher test for `combo-web-high`, `combo-web-medium`, `cgw/gpt-5.6-sol`, and `chatgpt-web/gpt-5.6-sol` that asserts no preflight, transport, lock, or prompt-dispatch mock is called.
- [ ] Search and remove remaining active CGW overlay, shim, startup, port, receipt, and installer paths while preserving the independent Codex relay documentation.
- [ ] Reconcile maintained documentation with final ownership: mark the old installer/overlay claims as superseded, link to `tools/local-patch-hub/README.md` for direct-fork ownership, and fix the broken Herdr Observation sentence in `runtime-adapter-procedure.md`.
- [ ] Regenerate adapter projections and run the adapter drift check instead of editing generated files manually.

**Verification:**
- Run `python -m pytest -q tests/test_agent_profile_registry.py tests/test_herdr_main_launcher.py tests/test_9router_global_install.py tests/test_9router_codex_relay_overlay.py`.
- Run `python scripts/sync_agent_adapters.py --all-platforms --check`.
- Search maintained Project OS files for `CGW|cgw|combo-web-high|combo-web-medium|chatgpt-web|CGW_SHIM` and classify only canonical policy, historical evidence, or preserved relay-boundary references as allowed matches.

**Exit Criteria:**
- Project OS fails closed before runtime side effects, generated surfaces are synchronized, and active CGW launcher/install paths are absent.

### Task 5: Synchronize LightRSI profiles and remove stale contract wording

**Purpose:**
- Align LightRSI canonical and generated profile/configuration surfaces with the canonical retirement contract and remove misleading CGW fixture language.

**Task Function:**
- Profile migration, generated-surface reconciliation, and contract hygiene.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical LightRSI profiles own the generated adapter/config projections.

**Validator Profile:**
- `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`
- Selection basis: profile identity and generated output ownership must remain one-to-many and auditable.

**Specification Coverage:**
- No canonical or generated LightRSI profile selects a retired family; retained logical profiles resolve to no retired member; generic adapter tests do not preserve retired names as behavior contracts.

**Required Skills:**
- `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- `LightRSI/agents/*.toml`.
- `LightRSI/components/presets/tokenpilot/tests/agent-profile-contract.test.ts`.
- `LightRSI/components/adapters/codex/tests/context-rebase-behavior.test.ts`.
- `LightRSI/components/adapters/**` and `LightRSI/components/products/**` generated adapter/config surfaces owned by the canonical profile generator.
- `LightRSI/repo_config/**` generator/configuration inputs.
- Generated retirement projection: `LightRSI/components/presets/tokenpilot/retired-model-policy.json`.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: update canonical LightRSI profiles and test fixtures, regenerate the named projections, and run the package typecheck, build, and focused test commands recorded during Task 1 inventory.
- Stop for: any generated output changed without a canonical source change, any retained logical profile without provider/capability evidence, or any profile that resolves to a retired member.

**Steps:**
- [ ] Replace duplicated retired-name/prefix literals with the generated projection and assert the contract version matches the 9router owner.
- [ ] Preserve `combo-ui` and `combo-xhigh` as logical profiles only when the acceptance matrix records fresh downstream provider/capability evidence with no retired member.
- [ ] Add a bounded cross-repository contract check that resolves `combo-ui` and `combo-xhigh` against a declared 9Router fixture or runtime snapshot, recursively validates members and aliases, and proves intended provider identity/capabilities without copying mutable member lists into LightRSI.
- [ ] Rename the no-replay fixture message at `context-rebase-behavior.test.ts` from `CGW request was dispatched` to provider-neutral wording and assert the no-replay marker, dispatch state, status, and retry count instead of the retired name.
- [ ] Regenerate all LightRSI adapter/config outputs from their canonical inputs and scan canonical plus generated files for retired selections.
- [ ] Run the exact package typecheck, build, and focused profile tests from the frozen checkout, then run the broader workspace suite separately.

**Verification:**
- `agent-profile-contract.test.ts` rejects all four retired families and proves retained logical profiles resolve to no retired member.
- The focused adapter test passes without a CGW fixture exception, and typecheck/build outputs are recorded against the immutable revision.

**Exit Criteria:**
- LightRSI canonical and generated surfaces agree, retained profiles remain usable, and no generic behavior test treats CGW as a supported runtime contract.

### Task 6: Consolidate evidence, readiness, and rollback proof

**Purpose:**
- Replace split plan evidence and noisy aggregate claims with one reproducible acceptance record and separate source/deployment status.

**Task Function:**
- Cross-repository evidence reconciliation and operational readiness.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one controller owns the acceptance ledger and immutable evidence.

**Validator Profile:**
- `skill-backend-verification`
- Selection basis: source, installed-state, side-effect, and rollback evidence must be reconciled independently.

**Specification Coverage:**
- Exact implementation/release SHAs, focused commands, approved exceptions, relay measurements, stale-row readiness, installed-state status, and rollback evidence are recorded once.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- This plan's `Execution Evidence` section.
- The three repository release/verification records.
- Project OS runtime resolution and adapter procedure documentation.
- 9router package/version metadata and relay benchmark output.
- Disposable combo database fixture/export and rollback rehearsal artifacts.

**Dependencies:**
- Tasks 2-5 complete.

**Authority:**
- Preauthorized local actions: inspect installed state, run disposable smoke tests, capture process/port/package evidence, create rollback instructions, and update this plan's immutable evidence table.
- Stop for: global package mutation, scheduled-task removal, live credentials, live database deletion, or rollback execution without explicit approval.

**Steps:**
- [ ] Record one row per repository with baseline SHA, implementation SHA, release merge SHA, branch, exact focused commands, result, and generated-surface status.
- [ ] Record the relay benchmark workload and metrics beside the relay disposition; do not use aggregate suite pass counts without command and scope.
- [ ] Search all maintained files and classify every remaining retired identifier as policy definition, historical evidence, explicitly typed transport boundary, or unexpected active behavior.
- [ ] Classify every remaining `chatgpt-web` occurrence as public selection, live executor/provider, typed native relay transport, historical evidence, or documentation; any typed relay exception must name its owner and test.
- [ ] Record warmup bypass, image-boundary, catalog-filtering, alias-write, cross-repository combo, and cold-catalog findings in the same evidence record rather than splitting them across plans.
- [ ] Inventory installed package identity, executable paths, startup registrations, environment variables, ports, processes, and persisted combo rows before any cleanup.
- [ ] Export stale rows and rehearse list/delete/rollback against a disposable database or fixture; leave live deletion, package replacement, and scheduled-task removal approval-gated.
- [ ] Record source-complete and deployment-complete statuses separately.

**Verification:**
- The evidence table is reproducible from immutable SHAs and exact commands, and every approved exception has a named owner and test.
- Rollback rehearsal restores the prior disposable package/configuration state without reintroducing retired aliases.

**Exit Criteria:**
- No completion claim depends on a split plan, a stale revision, an unexplained exception, or source tests standing in for installed-state proof.

### Task 7: Final verification and handoff gate

**Purpose:**
- Produce the final independent acceptance record and prevent the plan from being marked complete based only on task checkboxes.

**Task Function:**
- Cross-repository final verification and handoff readiness.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance spans all changed surfaces and preserved behaviors.

**Validator Profile:**
- `skill-verification-before-completion`
- Selection basis: only the verification skill may return `verified` and permit terminal plan status.

**Specification Coverage:**
- Every implementation outcome, preserved behavior, performance threshold, rollback condition, and evidence requirement in this plan.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- All Task 1-6 files, generated projections, tests, package metadata, evidence records, and this plan.

**Dependencies:**
- Task 6 complete.

**Authority:**
- Preauthorized local actions: run the declared final checks, inspect diffs/searches, reconcile the evidence table, and invoke the final verification skill.
- Stop for: any failed required check, unresolved active retired identifier, mismatched revision, missing relay proof, missing rollback evidence, or unverified retained profile.

**Steps:**
- [ ] Run the focused Project OS, LightRSI, and 9router matrices first and record fresh output.
- [ ] Run broader suites separately; classify unrelated pre-existing failures without treating them as retirement proof.
- [ ] Confirm no retired identifier can be emitted, accepted, resolved, selected, dispatched, retried, or persisted through an active path.
- [ ] Exercise retired direct names and aliases through warmup/naming, image-generation, model catalog, alias-write, combo, fallback, cancellation, and replay boundaries; verify no synthetic `200`, unexpected `500`, unusable catalog entry, or generic retry path remains.
- [ ] Confirm maintained native routing, generic fallback, cancellation, replay, quota, timeout, and Codex relay behavior with fresh regression evidence.
- [ ] Confirm the native Codex relay is separately typed and authenticated, and that any surviving legacy protocol field is an explicit route-level exception rather than a general CGW selection path.
- [ ] Confirm LightRSI retained combos avoid unnecessary cold catalog discovery only where exact-name validation and outage behavior are proven.
- [ ] Confirm source and installed-state statuses are distinct and that the final evidence references exact immutable revisions.
- [ ] Run `skill-verification-before-completion`; only a `verified` result may change this plan from `proposed` to `completed`.

**Verification:**
- All required focused checks pass, the evidence table is internally consistent, and the verifier returns `verified` or an explicit `incomplete` / `blocked` result.

**Exit Criteria:**
- The plan is ready for handoff only when all required evidence is fresh, reproducible, and tied to the final implementation revisions.

## Verification

- Policy proof: direct `cg/`, `chatgpt-web/`, `cgw/`, retired combo names, combo members, stored aliases, and normalized provider targets all fail with `410` / `RETIRED_MODEL`.
- State proof: stale and malformed combo rows list and delete deterministically and never reach provider dispatch.
- Boundary proof: warmup/naming bypasses, image-generation, model catalog, alias writes, combo dispatch, fallback, cancellation, and replay all preserve the stable retired-model contract while maintained requests preserve provider resolution and generic fallback.
- Relay proof: the Codex relay remains independently reachable and authenticated, is not a public `chatgpt-web/*` model-selection path, and its measured latency/resource trade-off is recorded.
- Catalog proof: stale executable combos are hidden from `/v1/models`, administrative inspection remains available, and exact retained LightRSI combos do not incur unnecessary cold catalog lookup without a proven reason.
- Launcher proof: Project OS rejects retired profiles before preflight, lock, transport, process launch, or prompt dispatch; CGW overlay/shim/startup paths are absent.
- Profile proof: LightRSI canonical and generated surfaces contain no retired selections, retained logical profiles have fresh downstream evidence, and generic fixtures use provider-neutral wording.
- Operational proof: source completion, installed-state inventory, disposable stale-row cleanup, smoke tests, rollback rehearsal, and external mutation approvals are recorded separately.
- Evidence proof: every command is tied to an immutable revision, exact scope, actual result, and named exception owner.

## Completion Criteria

The plan may be marked `completed` only when:

1. `cgw/`, `chatgpt-web/`, `combo-web-high`, and `combo-web-medium` fail closed after canonical provider normalization across all active owners, including warmup, naming, image, combo, and alias paths.
2. The `cg` provider alias cannot bypass retirement through direct routing, combos, stored aliases, fallback, or resolved targets.
3. Stale persisted combos remain inspectable and removable, and no stale row reaches provider dispatch or self-locks catalog operations.
4. Retired public requests consistently return `410` / `RETIRED_MODEL` without synthetic `200`, unexpected `500`, generic fallback, retry, or replay fallthrough.
5. Retired or unresolved combos are absent from executable model catalogs, stale rows remain administratively inspectable/removable, and new aliases cannot target retired providers.
6. The independent Codex relay remains available as a separately typed native boundary with explicit authentication and no public CGW model-selection path; any legacy protocol field has an owner, test, and documented exception, and the measured relay decision is recorded.
7. Project OS rejects retired profiles before runtime side effects and has no active CGW launcher, shim, overlay, packaging, startup, port, or receipt path.
8. LightRSI canonical and generated surfaces contain no retired selections, while `combo-ui` and `combo-xhigh` remain backed by fresh recursive non-retired evidence and do not pay an avoidable cold catalog lookup.
9. Cancellation, generic fallback, quota, replay, native lifecycle, timeout, image, catalog, alias-write, and maintained provider-routing behavior have fresh regression proof.
10. One immutable evidence record reconciles all repository revisions, commands, exceptions, installed-state status, relay and catalog metrics, and rollback evidence.
11. Gate 0 records `skill-plan-document-reviewer` acceptance before execution, and Task 7 records `skill-verification-before-completion` as `verified` after execution.

The plan must remain `proposed` until approved. It must not be marked
`completed` based only on checked task boxes, prior review prose, or aggregate
test counts without exact command and revision evidence.

