---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
distribution_tier: project
name: cgw-web-combo-retirement
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - tests/test_9router_global_install.py
  - tools/local-patch-hub/Install-9RouterGlobal.ps1
  - tools/local-patch-hub/Start-9RouterCodexCombo.ps1
  - tools/local-patch-hub/Install-9RouterCodexComboStartup.ps1
  - tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1
  - tools/local-patch-hub/overlays/9router-cgw/**
  - tools/local-patch-hub/README.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - tests/test_9router_cgw_overlay.py
  - LightRSI: agents/*.toml and generated adapter/config surfaces that select retired models
  - 9router: tools/cgw-codex-shim/**
  - 9router: open-sse/services/accountFallback.js
  - 9router: open-sse/services/combo.js
  - 9router: open-sse/executors/base.js
  - 9router: tests/unit/account-fallback-cgw-queue.test.js
---

# CGW and Web-Combo Retirement

## Goal

Remove the CGW runtime/provider integration and retire the `combo-web-high`,
`combo-web-medium`, `cgw/*`, and `chatgpt-web/*` selection paths across
`project-OS-starter`, `LightRSI`, and `9router` without weakening the general
Project OS lifecycle, native adapter behavior, 9Router fallback/cancellation/
replay behavior, or maintained non-CGW profiles.

The implementation must fail closed for removed aliases. It must not silently
reinterpret a retired web alias as native Codex, change provider/quota
semantics, or introduce a replacement alias until the replacement has been
verified against the actual maintained profile and 9Router provider contract.

## Review Findings

- Reviewed revisions are `project-OS-starter@6440e7340ae88eb3eea83ba673c5a0f1a1633726`, `LightRSI@85e599b3bbf3c75ca55e60f3024ff52b2884f1d6`, and `9router@8376eeafd42f75f0d111bdfcf04820e65a55e507`.
- Project OS currently couples `9router` `combo-web-*` profiles to a CGW preflight endpoint, shared single-flight lock, CGW-specific timeout policy, startup scripts, receipts, and overlay installation.
- The patch-hub overlay targets 9Router `0.5.104`, while the reviewed 9Router source reports `0.5.65`; the overlay must be removed, not rebased or reapplied during this work.
- The 9Router CGW shim and its account-fallback exception are specialized behavior. Generic account fallback, combo dispatch, cancellation, quota handling, and `NON_REPLAYABLE`/no-replay semantics remain in scope for preservation tests.
- LightRSI `combo-xhigh` and `combo-ui` are not to be removed merely because they are combo profiles. Their membership must be inspected and retained when they resolve to maintained native-compatible providers.
- The superseded `2026-10-21-12-35-cgw-runtime-ownership-convergence-plan.md` remains historical evidence and must not be reactivated or edited as implementation truth.

## Implementation Outcomes

### CGW-free profile and launcher contract

No maintained profile selects `combo-web-high`, `combo-web-medium`, `cgw/*`, or
`chatgpt-web/*`; removed aliases produce an explicit unsupported/deprecated
error before dispatch. Herdr no longer performs CGW preflight, shared CGW
locking, CGW-specific waits, CGW timeout selection, startup orchestration, or
CGW receipt/bearer validation.

### Native-compatible routing and preserved generic semantics

Every retained profile has an explicit provider/model identity and verified
replacement mapping where a replacement is required. Native provider/model
identity, tool capability, session binding, quota behavior, cancellation,
generic fallback, combo dispatch, and replay classification remain unchanged
outside the retired paths.

### Removal of CGW packaging and runtime artifacts

The Project OS patch hub no longer installs or starts a CGW overlay, shim,
startup task, CGW environment template, CGW receipt, CGW bearer, or CGW port.
The reusable 9Router installer and its rollback/idempotency behavior remain
available for non-CGW package management.

### Cross-repository regression proof

Focused tests prove retired aliases fail closed, maintained native profiles still
launch, the installer has no CGW overlay dependency, 9Router generic fallback
and cancellation/replay semantics remain intact, and no tracked or generated
surface references the retired runtime after migration.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-refactoring-assessment`, `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: three clean repository checkouts or worktrees, one each for `project-OS-starter`, `LightRSI`, and `9router`; do not execute this retirement from the current dirty review workspace
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect and edit the named repository files, run bounded local tests and static searches, create disposable test fixtures, and record verification output in the plan/task evidence
- User-approval actions: push, merge, publish, delete external repositories or unrelated files, mutate a globally installed runtime, access live provider credentials, or discard the current workspace's pre-existing review artifacts
- Parallel ownership: none; cross-repository contract and alias decisions must settle before downstream removal
- Sequential fallback: run Tasks 1-8 in order and stop at the first unresolved provider/model, generated-surface, or runtime-contract discrepancy

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main` planning baseline; execution must use clean task branches selected before activation
- Base commit: `6440e7340ae88eb3eea83ba673c5a0f1a1633726`
- Expected workspace: current review artifacts are preserved; the existing modified `.agents/skills/skill-github-browser-reviews/SKILL.md` and untracked `.runtime/`, `.tmp-herdr-schema.json`, and `.tmp-herdr-snapshot-review.json` are not part of this plan
- Next action: establish clean per-repository checkouts and complete the maintained-profile inventory
- Blockers: none for planning; implementation is blocked if replacement provider/model identity cannot be proven from source and focused runtime tests

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1: Freeze and inventory retired paths | `pending` | three clean checkouts | `unresolved` | none | inventory report and clean-baseline searches | pending |
| Task 2: Resolve maintained profile replacements | `pending` | LightRSI + 9router | `unresolved` | Task 1 | profile/provider/model matrix and focused routing tests | pending |
| Task 3: Migrate Project OS consumers and launcher | `pending` | project-OS-starter | `unresolved` | Task 2 | launcher tests and fail-closed alias assertions | pending |
| Task 4: Remove patch-hub CGW installation/startup surfaces | `pending` | project-OS-starter | `unresolved` | Task 2 | installer/startup tests and absence checks | pending |
| Task 5: Remove LightRSI retired profile/config surfaces | `pending` | LightRSI | `unresolved` | Tasks 1-2 | profile validation and generated-surface checks | pending |
| Task 6: Remove 9Router shim and CGW-only fallback behavior | `pending` | 9router | `unresolved` | Task 2 | unit tests for generic fallback, cancellation, and replay | pending |
| Task 7: Reconcile documentation and historical boundaries | `pending` | all three repositories | `unresolved` | Tasks 3-6 | repository-wide searches and doc checks | pending |
| Task 8: Run cross-repository acceptance verification | `pending` | all three repositories | `unresolved` | Task 7 | final test matrix and clean diff review | pending |

## Task Breakdown

### Task 1: Freeze and inventory retired paths

**Purpose:**
- Establish the complete set of maintained consumers, generated surfaces, startup registrations, environment templates, receipts, overlays, and tests that can select or start CGW before any deletion occurs.

**Task Function:**
- Source inventory and migration-boundary analysis.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source inspection across known repositories; no implementation ambiguity is resolved by inference.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: inventory is reviewed by the lead controller against source and pinned revisions.

**Specification Coverage:**
- Freeze selection of `combo-web-high`, `combo-web-medium`, `cgw/*`, and `chatgpt-web/*`.
- Preserve `combo-xhigh`, `combo-ui`, generic fallback, cancellation, replay, and non-CGW provider behavior unless source proves they are CGW-backed.

**Required Skills:**
- `skill-refactoring-assessment`, `skill-central-config-layer`.

**Files And Symbols:**
- Inspect `project-OS-starter/scripts/herdr_main_launcher.py`: `_preflight_profile_runtime`, `_uses_shared_web_runtime`, `_shared_web_runtime_lock`, `_timeout_policy`, `_profile_timeout_policy`, launch/settlement call sites, and CGW constants.
- Inspect `project-OS-starter/tools/local-patch-hub/Install-9RouterGlobal.ps1`, `Start-9RouterCodexCombo.ps1`, `Install-9RouterCodexComboStartup.ps1`, `Apply-9RouterCgwOverlay.ps1`, overlay manifests/patches, `.env.example` files, and README sections.
- Inspect `project-OS-starter/tests/test_herdr_main_launcher.py`, `tests/test_9router_global_install.py`, and `tests/test_9router_cgw_overlay.py` for assertions that encode the current CGW contract.
- Inspect `LightRSI/agents/*.toml`, profile registries, generated launchers, and documentation for retired model/provider names.
- Inspect `9router/tools/cgw-codex-shim/**`, `open-sse/services/accountFallback.js`, `open-sse/services/combo.js`, `open-sse/executors/base.js`, package scripts, environment examples, and `tests/unit/account-fallback-cgw-queue.test.js`.

**Dependencies:**
- None; use the reviewed pinned revisions as the baseline.

**Authority:**
- Preauthorized local actions: read the three clean checkouts, manifests, generated outputs, Git metadata, and test sources; write only a disposable inventory note outside tracked source
- Stop for: an untracked or generated consumer that cannot be attributed to a repository owner, a profile whose provider identity is ambiguous, or any need to access live credentials or mutate an installed runtime

**Steps:**
- [ ] Step 1: Record each repository revision, package/version metadata, clean status, and all current CGW/web-combo references.
- [ ] Step 2: Build a matrix of profile name, provider, model, combo membership, generated launcher, startup registration, environment inputs, and downstream consumer.
- [ ] Step 3: Mark each reference as remove, migrate, preserve, or historical-only; do not delete historical plans or evidence.
- [ ] Step 4: Freeze the matrix as the input to Tasks 2-6 and record any unresolved mapping as a blocker rather than guessing.

**Verification:**
- [ ] `rg -n --hidden "CGW|cgw|combo-web-high|combo-web-medium|chatgpt-web"` in each checkout.
- Expected: every match is listed in the inventory with an owner and disposition; no unexplained match remains.

**Exit Criteria:**
- A complete, source-backed migration matrix exists and all downstream tasks have exact file/symbol ownership.

### Task 2: Resolve maintained profile replacements and contract gates

**Purpose:**
- Define explicit replacements for any retired consumers and prove that replacements preserve provider, model, quota, tools, session binding, cancellation, and replay semantics.

**Task Function:**
- Runtime contract reconciliation and replacement selection.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-impact cross-repository contract decision; only source-backed mappings are admissible.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: replacement decisions require direct source and focused runtime evidence before implementation.

**Specification Coverage:**
- Do not silently rename aliases or route retired aliases into native Codex.
- Preserve maintained LightRSI logical profiles when they are not CGW-backed.

**Required Skills:**
- `skill-backend-verification`, `skill-central-config-layer`, `skill-refactoring-assessment`.

**Files And Symbols:**
- Inspect LightRSI profile definitions and generated adapter/config output selected by Task 1.
- Inspect 9Router provider registry, combo membership, account fallback, executor capability checks, cancellation, and replay classification in `open-sse/services/combo.js`, `open-sse/services/accountFallback.js`, and `open-sse/executors/base.js`.
- Add or update only focused contract fixtures in the owning repository test directories.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: add disposable fixtures and focused tests in the named repositories, execute local provider-routing checks without credentials, and record contract observations
- Stop for: any mapping that changes quota/provider identity, drops tool capability, depends on CGW credentials, or cannot prove session/cancellation/replay behavior at the direct boundary

**Steps:**
- [ ] Step 1: Select the maintained native-compatible 9Router profile/model for each consumer of a retired alias, or mark the consumer for removal when no equivalent exists.
- [ ] Step 2: Prove native provider/model identity and capability metadata through the 9Router route and LightRSI adapter boundary.
- [ ] Step 3: Prove cancellation, generic fallback, account fallback, quota handling, and replay/no-replay behavior for the retained path.
- [ ] Step 4: Record the replacement matrix and reject any implementation that relies on implicit alias translation.

**Verification:**
- [ ] Run the owning repository's focused provider/combo tests plus a direct disposable request/selection fixture.
- Expected: retained profiles resolve to the declared native provider/model; retired names are not accepted as replacements; generic fallback and replay classification remain unchanged.

**Exit Criteria:**
- Every retained consumer has an explicit verified destination, and every unreplaceable consumer has an approved removal disposition.

### Task 3: Migrate Project OS consumers and remove CGW launcher behavior

**Purpose:**
- Remove CGW-specific launcher admission and execution behavior while retaining the general lifecycle, pane ownership, receipts, native timeout policy, and fail-closed capability handling.

**Task Function:**
- Launcher contract refactoring with regression preservation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared launcher logic has broad lifecycle impact and requires focused behavioral tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: backend boundary tests in the launcher test suite provide the validator contract.

**Specification Coverage:**
- Remove CGW preflight, shared lock, CGW-specific waits/timeouts, CGW receipts/bearer requirements, and `combo-web-*` selection.
- Retain general native launch, receipt validation, cancellation, pane ownership, and lifecycle settlement.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`.

**Files And Symbols:**
- Modify `scripts/herdr_main_launcher.py`: remove CGW constants and `_preflight_profile_runtime`, `_shared_web_runtime_lock_path`, `_shared_web_runtime_lock`, `_uses_shared_web_runtime`, and CGW branches in `_timeout_policy`, `_profile_timeout_policy`, prompt delivery, wait, and settlement call sites.
- Modify `tests/test_herdr_main_launcher.py`: remove CGW-only lock/preflight/wait fixtures and replace them with fail-closed retired-alias tests plus preserved native lifecycle tests.
- Inspect profile validation and registry loading paths to ensure unsupported aliases fail before process launch.

**Dependencies:**
- Task 2 replacement matrix complete.

**Authority:**
- Preauthorized local actions: modify the named launcher and focused tests, run local Python tests, and create disposable process/registry fixtures
- Stop for: a change to general lifecycle semantics, native timeout behavior, receipt ownership, pane locking, or any test requiring live CGW/ChatGPT-Web credentials

**Steps:**
- [ ] Step 1: Add red tests proving `combo-web-high`, `combo-web-medium`, `cgw/*`, and `chatgpt-web/*` are rejected before preflight, startup, or prompt dispatch.
- [ ] Step 2: Remove CGW-only constants, preflight, shared lock, timeout branches, shared-runtime wait, and CGW error text while leaving native policy paths intact.
- [ ] Step 3: Migrate any retained launcher consumers to the Task 2 explicit profile/model mapping.
- [ ] Step 4: Add assertions that retired aliases do not spawn processes, acquire CGW locks, consult CGW ports, or emit CGW receipts.

**Verification:**
- [ ] `pytest -q tests/test_herdr_main_launcher.py`
- Expected: focused launcher tests pass; retired aliases fail closed; maintained native profiles retain lifecycle, receipt, cancellation, and timeout behavior.

**Exit Criteria:**
- Herdr has no CGW-specific runtime branch or dependency, and all launcher tests describe the post-retirement contract.

### Task 4: Remove Project OS patch-hub CGW installation and startup surfaces

**Purpose:**
- Decouple reusable 9Router installation/rollback from the CGW overlay and remove scripts, tasks, environment templates, receipts, ports, and diagnostics that exist only to start CGW.

**Task Function:**
- Installer and operational-surface simplification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded PowerShell/configuration change with idempotency and rollback requirements.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing installer tests plus disposable filesystem fixtures cover the boundary.

**Specification Coverage:**
- Preserve generic 9Router installation, package version checks, rollback, idempotency, and non-CGW receipts.
- Remove `9router-cgw-overlay.json` coupling, CGW startup/bootstrap logic, CGW bearer requirements, and CGW port references.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`.

**Files And Symbols:**
- Modify `tools/local-patch-hub/Install-9RouterGlobal.ps1`: remove CGW receipt staging/validation and overlay-specific assumptions without changing generic install/rollback flow.
- Delete `tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1`, `Install-9RouterCodexComboStartup.ps1`, and `overlays/9router-cgw/**` after consumers are removed.
- Modify `Start-9RouterCodexCombo.ps1`, `.env.example`/environment templates, and `tools/local-patch-hub/README.md` to describe only maintained native 9Router startup and diagnostics.
- Modify `tests/test_9router_global_install.py`; delete or replace `tests/test_9router_cgw_overlay.py` with post-retirement installer/absence coverage.

**Dependencies:**
- Task 2 replacement matrix and Task 3 launcher contract complete.

**Authority:**
- Preauthorized local actions: edit named installer/startup/docs/tests, delete only listed CGW-owned files, and run PowerShell against disposable fixture directories
- Stop for: any removal that breaks generic installer rollback/idempotency, any global startup-task mutation, or any deletion of a file with a non-CGW consumer

**Steps:**
- [ ] Step 1: Add installer tests proving a non-CGW package install does not require or emit a CGW overlay receipt.
- [ ] Step 2: Remove CGW receipt staging, overlay discovery, environment validation, startup registration, and port/bearer diagnostics.
- [ ] Step 3: Preserve and test package version checks, downgrade protection, rollback, and repeated-install idempotency.
- [ ] Step 4: Delete CGW-only scripts and overlay files only after repository-wide references are migrated.

**Verification:**
- [ ] `pytest -q tests/test_9router_global_install.py`
- [ ] Run the installer in a disposable fixture with no CGW environment and inspect staged output.
- Expected: generic installation succeeds without CGW inputs; rollback/idempotency remain green; no CGW receipt or startup task is created.

**Exit Criteria:**
- Patch-hub installation and startup are independent of CGW and retain reusable generic 9Router behavior.

### Task 5: Remove LightRSI retired profile and generated configuration surfaces

**Purpose:**
- Remove retired web-combo selections from LightRSI while preserving maintained native-compatible logical profiles and regenerating only canonical derived surfaces.

**Task Function:**
- Profile registry migration and generated-surface reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: profile/config ownership is repository-specific and must follow canonical source plus required sync tooling.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: profile validation and generated-surface checks are the owning repository's acceptance boundary.

**Specification Coverage:**
- Remove `combo-web-high` and `combo-web-medium` and any CGW-backed `cgw/*`/`chatgpt-web/*` profile references.
- Preserve `combo-xhigh`, `combo-ui`, and other logical profiles when their actual provider/model membership is native-compatible.

**Required Skills:**
- `skill-central-config-layer`, `skill-code-standards`, `skill-backend-verification`.

**Files And Symbols:**
- Inspect and modify canonical LightRSI profile definitions under `agents/*.toml`, including `agents/xhigh.toml` and `agents/ui.toml` only where Task 1-2 prove a CGW dependency.
- Modify the canonical profile registry, generated launchers, adapters, docs, and tests that select retired aliases; run the repository's required generated-surface sync.
- Do not hand-edit generated agent surfaces when a canonical source and sync command exists.

**Dependencies:**
- Tasks 1-2 complete; Task 3 establishes the Project OS consumer contract.

**Authority:**
- Preauthorized local actions: edit canonical LightRSI profile/config sources, run the repository's bounded generation/sync and validation commands, and update focused tests/docs
- Stop for: a profile whose provider/model membership is not source-backed, a generated output with no canonical owner, or any change to non-CGW profile semantics beyond the approved replacement matrix

**Steps:**
- [ ] Step 1: Remove retired aliases from canonical profile sources and selection registries.
- [ ] Step 2: Apply only verified Task 2 replacements; preserve logical names whose memberships remain native-compatible.
- [ ] Step 3: Regenerate required launchers/config views using the repository-owned sync command.
- [ ] Step 4: Add profile validation asserting no retired alias can be emitted or selected.

**Verification:**
- [ ] Run LightRSI profile/config tests and the required generated-surface verification command.
- Expected: generated outputs match canonical sources; maintained profiles resolve to verified native identities; retired aliases are absent and fail clearly when requested.

**Exit Criteria:**
- LightRSI no longer publishes or selects retired CGW/web-combo profiles, and all generated surfaces are reconciled.

### Task 6: Remove the 9Router CGW shim and CGW-only fallback exception

**Purpose:**
- Delete the specialized CGW transport and its fallback exception without regressing general combo dispatch, account fallback, quota backoff, request cancellation, or replay classification.

**Task Function:**
- Provider-path deletion with direct boundary regression proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: backend behavior removal affects provider dispatch and retry semantics; use focused tests before deletion.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: 9Router unit tests and disposable route fixtures validate the retained generic path.

**Specification Coverage:**
- Remove `tools/cgw-codex-shim/**` and CGW-only queue/error handling.
- Preserve generic account fallback, combo selection, cancellation, quota behavior, and `NON_REPLAYABLE`/no-replay handling.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`.

**Files And Symbols:**
- Delete `tools/cgw-codex-shim/**` and its package/startup/config references.
- Modify `open-sse/services/accountFallback.js`: remove only CGW queue saturation/dispatch exceptions and preserve generic fallback behavior.
- Modify `open-sse/services/combo.js` and `open-sse/executors/base.js` only where retired provider/model registration or capability branches exist.
- Delete or replace `tests/unit/account-fallback-cgw-queue.test.js` with generic fallback/cancellation/replay tests owned by the surviving implementation.

**Dependencies:**
- Task 2 contract matrix complete; Task 1 inventory identifies all shim consumers.

**Authority:**
- Preauthorized local actions: add red tests, modify/delete the named 9Router CGW-only files, run focused Node tests, and inspect route/provider outputs from disposable fixtures
- Stop for: a fallback change that affects non-CGW providers, a removed queue branch that changes retry/quota behavior without a replacement test, or any live account/credential operation

**Steps:**
- [ ] Step 1: Add regression tests for generic account fallback, cancellation, quota/backoff, combo branching, and replay/no-replay behavior before deleting the CGW exception.
- [ ] Step 2: Remove the CGW queue saturation classifier and any provider-specific exception that stops fallback only for CGW.
- [ ] Step 3: Remove shim imports, route registration, package scripts, environment variables, and documentation.
- [ ] Step 4: Delete the CGW shim and its CGW-only test after the retained behavior passes.

**Verification:**
- [ ] Run the focused 9Router unit tests, including the surviving account-fallback, combo, executor, cancellation, and replay suites.
- Expected: generic fallback and replay behavior pass; no test or package path imports the deleted shim; retired provider names fail before dispatch.

**Exit Criteria:**
- 9Router has no CGW transport or CGW-only fallback exception and retains the general provider contract.

### Task 7: Reconcile maintained documentation and historical boundaries

**Purpose:**
- Update maintained operational documentation to describe the post-retirement runtime and clearly separate historical CGW evidence from active instructions.

**Task Function:**
- Documentation and operational-contract reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation changes are source-backed after implementation tasks settle.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository-wide search plus documentation checks validate the boundary.

**Specification Coverage:**
- Remove active CGW startup, ports, bearer, overlay, receipt, timeout, and fallback instructions.
- Keep the superseded CGW convergence plan as historical evidence unless repository policy explicitly requires archival relocation.

**Required Skills:**
- `skill-code-standards`, `skill-plan-document-reviewer`.

**Files And Symbols:**
- Modify `tools/local-patch-hub/README.md`, `docs/operating_system/tooling/runtime-tool-resolution.md`, and `docs/operating_system/procedures/runtime-adapter-procedure.md`.
- Update LightRSI and 9Router maintained READMEs/config docs identified by the inventory.
- Do not edit the superseded plan except to add no new implementation claims.

**Dependencies:**
- Tasks 3-6 complete.

**Authority:**
- Preauthorized local actions: update named maintained documentation and run repository-wide reference searches
- Stop for: documentation that would require inventing a replacement provider, deleting historical evidence, or contradicting source/tests

**Steps:**
- [ ] Step 1: Replace active CGW instructions with the verified native-compatible routing and failure behavior.
- [ ] Step 2: Document explicit unsupported/deprecated alias behavior and migration guidance without silent translation.
- [ ] Step 3: Remove obsolete CGW ports, bearer/env names, startup commands, overlay versions, and shim references from maintained docs.
- [ ] Step 4: Run the plan-document review before final acceptance.

**Verification:**
- [ ] `rg -n --hidden "CGW|cgw|combo-web-high|combo-web-medium|chatgpt-web|17841|20129|17667|cgw-bearer|CGW_SHIM"` across maintained files, excluding explicitly retained historical evidence.
- Expected: only approved historical references remain, each with an explicit historical/superseded disposition.

**Exit Criteria:**
- Maintained docs, config references, and operator instructions match the post-retirement source contract.

### Task 8: Run cross-repository acceptance verification

**Purpose:**
- Produce fresh evidence that the three repositories jointly eliminate CGW and retired web-combo aliases without breaking maintained native behavior.

**Task Function:**
- Final integration verification and scope reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification requires independent inspection of all changed repositories and their generated outputs.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final evidence is assembled from fresh repository tests, static searches, and direct disposable runtime checks.

**Specification Coverage:**
- All implementation outcomes and preserved-behavior requirements in this plan.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`.

**Files And Symbols:**
- Verify all Task 1-7 files and repository diffs; inspect generated outputs and package manifests in each checkout.
- Verify the historical plan remains marked `superseded` and is not referenced as active execution truth.

**Dependencies:**
- Tasks 1-7 complete.

**Authority:**
- Preauthorized local actions: run the final declared tests, static searches, disposable install/route checks, diff inspection, and evidence capture
- Stop for: any failed required check, stale generated output, unexplained retired reference, provider/model mismatch, or unrecorded scope deviation

**Steps:**
- [ ] Step 1: Run focused tests in each repository, then the broader relevant test suites.
- [ ] Step 2: Run repository-wide searches for retired aliases, CGW ports, shim paths, overlay IDs, startup tasks, and environment variables.
- [ ] Step 3: Verify retained native profile identity, tools, session binding, quota, cancellation, fallback, and replay behavior through disposable fixtures.
- [ ] Step 4: Review all diffs against the approved scope and record deviations, blockers, and rollback instructions.

**Verification:**
- [ ] Project OS: `pytest -q tests/test_herdr_main_launcher.py tests/test_9router_global_install.py`
- [ ] LightRSI: run its profile/config/generated-surface test and validation commands from the repository README/CI configuration.
- [ ] 9Router: run focused combo/account-fallback/executor/cancellation/replay tests, then the relevant unit suite.
- [ ] Run repository-wide retired-reference searches with historical exclusions documented.
- Expected: all required checks pass, no active CGW/web-combo surface remains, and maintained native behavior has fresh evidence.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; the plan records all proof paths and no unresolved required task, failed check, stale status, or scope deviation remains.

## Verification

- `pytest -q tests/test_herdr_main_launcher.py tests/test_9router_global_install.py` in `project-OS-starter` passes.
- LightRSI profile/config validation and generated-surface checks pass from its canonical repository commands.
- 9Router focused combo, fallback, executor, cancellation, and replay tests pass, followed by the relevant unit suite.
- Repository-wide searches show no active references to `CGW`, `cgw`, `combo-web-high`, `combo-web-medium`, `chatgpt-web/*`, CGW ports, CGW bearer/environment names, deleted shim paths, or CGW overlay IDs; retained historical evidence is explicitly excluded and documented.
- Disposable runtime checks confirm retired aliases fail before dispatch and retained native profiles expose the expected provider/model and capability metadata.
- Installer checks confirm generic 9Router install/rollback/idempotency without CGW overlay inputs or receipts.

## Completion Criteria

The plan is ready for completion verification when:

1. all three repositories implement the approved retirement and replacement matrix
2. every retired alias fails closed without silent native rerouting
3. Project OS lifecycle, admission, receipts, cancellation, and native timeout behavior remain covered
4. LightRSI maintained profiles and generated surfaces are reconciled from canonical sources
5. 9Router generic fallback, combo, quota, cancellation, and replay behavior remains covered
6. CGW overlay, shim, startup, environment, receipt, bearer, and port surfaces are removed from active code/config/docs
7. all task-local proof and final verification output are recorded
8. `skill-plan-document-reviewer` has accepted the plan before execution and `skill-verification-before-completion` has returned `verified` after execution

The plan may be marked `completed` only after fresh final verification confirms
the criteria above and the lead controller records any required branch
disposition separately from implementation evidence.

