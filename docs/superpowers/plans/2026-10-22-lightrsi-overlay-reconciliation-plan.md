---
layer: change
artifact_type: plan
contract_version: "1"
status: proposed
template_id: implementation-plan
name: lightrsi-overlay-reconciliation
targets:
  - tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1
  - tools/local-patch-hub/README.md
  - tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/c05cafe5/manifest.json
  - tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/c05cafe5/lightrsi-codex-compaction-compatibility.patch
  - tests/test_lightrsi_codex_overlay.py
  - docs/superpowers/plans/2026-10-22-lightrsi-overlay-reconciliation-plan.md
---

# LightRSI Overlay Reconciliation

## Goal

Make the LightRSI Codex overlay reconciler prove the compatibility level that
is actually installed instead of accepting a legacy hook-only overlay as a
proxy for compaction support. Refresh the compaction overlay against one
verified LightRSI source commit, preserve exact-base and reversible-install
behavior, and add executable regression coverage for overlay selection and
runtime verification.

The installed
`C:\Users\HOANG PHI LONG DANG\.local\share\lightrsi\codex-adapter\dist\tokenpilot-codex-hook.cmd`
remains generated output. It must continue to be produced by LightRSI's
`install:codex` path and must not be edited directly.

## Review Findings

- **P1 — legacy selection can mask missing compaction proof.**
  `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1:96` collects every
  reverse-applicable overlay, but the current LightRSI checkouts at
  `fedef2d1fc99657dab67353232ded5cc663644ce` and
  `7e4147674c018f0656b3840704e0d0ee8c9e9330` accept the legacy
  `c0d86ae` hook patch while the checked-in `c05cafe5` compaction patch no
  longer reverse-applies. The reconciler therefore selects the hook-only
  record at line 105 and sets `RequireCompactCompatibility` to false at line
  135, so `-VerifyOnly` can pass without proving compact behavior.
- **P1 — the checked-in compaction artifact is stale relative to the source it
  is meant to protect.** The current source has substantial changes beyond
  `c05cafe5`, including the exported `projectCompactPayload` boundary,
  cached compact-capability handling, and expanded forwarding-attempt
  evidence. The existing manifest still names
  `c05cafe502fb474ab28e29e9e184adba8446a6a1`, so no exact-base artifact
  identifies the current runtime build.
- **P2 — tests do not exercise the selection branch.**
  `tests/test_lightrsi_codex_overlay.py:10` and `:35` only assert manifest,
  patch, and script strings. They do not create a target where legacy and
  compaction overlays are simultaneously present, do not assert that the
  compaction record wins, and do not prove that a stale hook-only match is
  rejected for compact verification.
- **P2 — the generated wrapper is not the behavior owner.** The installed
  wrapper correctly delegates to `hooks-handler.js`; the compact route lives
  in the generated `cli.js` runtime started by that handler. Any direct edit
  to `tokenpilot-codex-hook.cmd` would be overwritten and would bypass the
  canonical LightRSI source and overlay flow.

## Implementation Outcomes

### Exact current-source compaction overlay

Add a new versioned, exact-base compaction overlay for the verified canonical
LightRSI source commit. The patch must cover the current compact-route,
upstream endpoint/fallback, gateway route, and focused tests without deleting
the historical `c05cafe5` artifact. The manifest records the actual source
commit, target repository, patch name, and incremented compatibility version.

### Fail-closed overlay selection

Update `Apply-LightMem2CodexOverlay.ps1` so an already-applied hook-only
overlay cannot satisfy a compact-compatibility verification. Exact-base
selection remains preferred; when reverse checks find multiple records, the
compaction-compatible record wins only when its complete patch is
reverse-applicable. If no exact-base compaction record is available, the
reconciler reports that a new exact-base overlay is required rather than
claiming compact support from the legacy wrapper patch.

### Executable regression proof

Extend `tests/test_lightrsi_codex_overlay.py` with disposable Git fixtures and
PowerShell invocations that prove exact-base apply/reverse, already-applied
selection precedence, stale hook-only rejection, `-VerifyOnly` non-mutation,
and generated runtime signature checks. Static manifest assertions remain as
cheap coverage but are no longer the only proof of the reconciler contract.

### Documentation and generated-surface boundary

Update `tools/local-patch-hub/README.md` with the new exact-base refresh
procedure, the distinction between source-only verification and installed
runtime verification, and the explicit prohibition on editing generated
`dist/tokenpilot-codex-hook.cmd` files. Do not modify generated agent files,
the installed LightRSI runtime, Codex configuration, startup files, or the
untracked `.runtime` evidence directory.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: disposable Git fixture targets; read-only inspection of external LightRSI checkouts; current Project OS workspace for canonical edits
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect source and runtime provenance, edit the listed Project OS overlay/tests/docs, create disposable fixture directories, run declared read-only verification and focused external tests
- User-approval actions: install or rebuild the global LightRSI runtime, modify Codex configuration or startup files, edit external LightRSI source, delete `.runtime` artifacts, commit, push, merge, publish, or clean worktrees
- Parallel ownership: none; reconciler, overlay artifact, tests, and documentation share one behavioral contract
- Sequential fallback: establish canonical source provenance, add failing fixture tests, refresh the exact-base overlay, harden selection, update docs, then run final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `02b70a0`
- Expected workspace: preserve the pre-existing modification to `docs/superpowers/plans/2026-10-20-17-21-native-semantic-residual-correctness-plan.md` and all untracked `.runtime` artifacts; add only the approved plan and later in-scope implementation files
- Next action: resolve canonical LightRSI source/build provenance before creating the refreshed patch
- Blockers: none for planning; execution must stop if source-map/build provenance cannot identify one canonical source commit without modifying external or installed files

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current plus read-only external LightRSI checkouts | `unresolved` | none | canonical source commit, installed build provenance, and clean disposable fixture | pending |
| Task 2 | `pending` | current plus disposable Git fixture | `unresolved` | Task 1 | failing regression tests for overlay precedence, stale hook-only selection, and non-mutation | pending |
| Task 3 | `pending` | current overlay tree plus clean detached LightRSI source | `unresolved` | Tasks 1-2 | exact-base compaction patch applies and reverse-applies cleanly | pending |
| Task 4 | `pending` | current workspace | `unresolved` | Task 3 | reconciler selects compact record and verifies compact runtime signatures | pending |
| Task 5 | `pending` | current workspace | `unresolved` | Task 4 | README, plan ledger, focused tests, repository validators, and diff integrity reconcile | pending |

Allowed states: `pending`, `active`, `blocked`, `completed`.

## Task Breakdown

### Task 1: Establish canonical source and installed-runtime provenance

**Purpose:** Identify the one LightRSI source commit that owns the generated
runtime represented by the installed wrapper and compact `cli.js` before
refreshing any patch.

**Task Function:** Read-only repository, external checkout, source-map, and
runtime inventory.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded source and runtime provenance inspection with no implementation writes

**Required Skills:** `skill-code-standards`.

**Files And Symbols:**

- Inspect `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/c0d86ae/manifest.json`.
- Inspect `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/c05cafe5/manifest.json`.
- Inspect `C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI`.
- Inspect `C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI-lightrsi-native-result-reader`.
- Inspect installed `dist\cli.js`, `dist\hooks-handler.js`, source maps, and `dist\tokenpilot-codex-hook.cmd` under `C:\Users\HOANG PHI LONG DANG\.local\share\lightrsi\codex-adapter`.
- Inspect `components/adapters/codex/src/proxy-runtime.ts:projectCompactPayload`, `startCodexResponsesProxy`, and `components/adapters/codex/src/upstream.ts:requestUpstreamResponses` in the selected external source.

**Dependencies:** None.

**Authority:**

- Preauthorized local actions: read the named source, manifests, source maps, Git metadata, and installed file hashes; create no external or global writes
- Stop for: ambiguous source/build provenance, dirty external source that cannot be reproduced in a clean detached checkout, missing compact symbols, or any need to edit the installed runtime

**Steps:**

1. Record `git rev-parse HEAD`, tracked status, and relevant file paths for
   both external LightRSI checkouts.
2. Compare installed source-map inputs and compact runtime signatures with the
   two checkouts; record which source commit can reproduce the installed
   `cli.js` behavior.
3. Create a clean detached disposable checkout at the selected commit without
   changing either existing external checkout.
4. Record the selected commit and source paths in the task evidence and use it
   as the only base for the new overlay.

**Verification:** The selected checkout contains the current compact route,
endpoint resolver, fallback capability cache, gateway route, and focused tests;
the installed wrapper remains unchanged.

**Exit Criteria:** One reproducible source commit is identified, or the task is
blocked with the exact competing commits and the missing provenance evidence.

### Task 2: Add failing behavioral fixture coverage

**Purpose:** Lock the observed selection defect before changing the reconciler.

**Task Function:** Regression-test design and red-phase execution.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: focused cross-process fixture work with PowerShell and Git behavior

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:**

- Modify `tests/test_lightrsi_codex_overlay.py`.
- Exercise `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1`.
- Use disposable fixture paths under the test temporary directory only.

**Dependencies:** Task 1.

**Authority:**

- Preauthorized local actions: add fixture helpers and tests in the named test file, invoke PowerShell against disposable Git repositories, and inspect exit/output
- Stop for: tests that require global installation, external source mutation, live Codex configuration, or deletion of retained evidence

**Steps:**

1. Add a fixture that contains both the legacy hook patch and the refreshed
   compaction patch in its post-apply state.
2. Assert that the reconciler selects the compaction-compatible record and
   requires both target and installed compact runtime signatures.
3. Add a fixture where only the legacy hook patch reverse-applies against a
   newer source; assert that compact verification fails closed and instructs
   the operator to register an exact-base compaction overlay.
4. Add `-VerifyOnly` assertions for no file mutation, exact error output, and
   unchanged target `HEAD`.
5. Run the new tests and confirm they fail against the current reconciler for
   the intended reason before implementation.

**Verification:** The red phase fails only on the missing precedence/provenance
behavior, not on fixture setup or environment discovery.

**Exit Criteria:** The regression tests demonstrate the current false-positive
selection path and are ready to pass after Tasks 3-4.

### Task 3: Refresh the exact-base compaction overlay

**Purpose:** Package the current compact behavior without editing generated
`dist` output or the installed runtime.

**Task Function:** Overlay extraction and exact-base packaging.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: bounded patch packaging across known files with exact-base verification

**Required Skills:** `skill-code-standards`.

**Files And Symbols:**

- Add a new versioned directory under `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/` for the selected commit.
- Add its `manifest.json` and compaction patch.
- Preserve `c05cafe5` and `c0d86ae` unchanged for historical rollback.

**Dependencies:** Tasks 1-2.

**Authority:**

- Preauthorized local actions: export the minimal current-source diff into the new manifest/patch and run `git apply --check` plus reverse checks on disposable clean targets
- Stop for: patch hunks that include unrelated context-history changes, generated dist edits, package downgrades, external source mutation, or a patch that cannot reverse cleanly

**Steps:**

1. Rebase the compact-route changes from the selected source commit onto the
   clean detached target and export only the canonical source/test files.
2. Set the manifest `baseCommit` to the exact 40-character selected commit and
   increment the overlay version from `1.4.0` to `1.5.0`.
3. Include current implementations of `projectCompactPayload`, compact route
   admission, `/responses/compact` endpoint selection, cached `404` fallback,
   and the current gateway route contract.
4. Include focused compact-route and upstream tests that prove native compact
   forwarding, fallback stripping, capability caching, and ordinary-route
   history preservation.
5. Verify clean forward and reverse application, then verify the restored
   target `HEAD` and clean status.

**Verification:** `git apply --check` and reverse checks succeed against the
selected exact base; the patch does not touch generated `dist` files.

**Exit Criteria:** The new artifact is independently reversible and represents
the current source behavior rather than a partially applicable historical diff.

### Task 4: Harden reconciler selection and runtime verification

**Purpose:** Prevent a legacy hook-only match from being treated as proof of
compact compatibility.

**Task Function:** PowerShell reconciler implementation.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: cross-file behavior change with fail-closed selection and direct command proof

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`.

**Files And Symbols:**

- Modify `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1:Get-OverlayRecords` and overlay-selection branches around lines 91-145.
- Preserve `Test-WindowsHookWrapper` and generated-wrapper ownership.

**Dependencies:** Tasks 2-3.

**Authority:**

- Preauthorized local actions: edit the reconciler and its named fixture tests, run source-only and installed-runtime verification against disposable targets, and preserve all unrelated workspace changes
- Stop for: direct edits to `tokenpilot-codex-hook.cmd`, implicit 3-way application, automatic stale-overlay rebasing, global installation, or any compact claim without an exact-base/current-runtime signature

**Steps:**

1. Validate every manifest's required fields and classify records by
   compatibility level before reverse checks.
2. Prefer an exact-base compaction record when the target `HEAD` matches it.
3. For already-applied targets, require the complete compaction patch to
   reverse-apply before enabling compact verification; do not fall back to the
   legacy hook-only record when compact proof is requested by the selected
   runtime contract.
4. Reject ambiguous matches with the matching overlay IDs and target `HEAD`
   instead of selecting the first record returned by filesystem order.
5. Keep `-VerifyOnly` read-only and make its success output identify the
   selected overlay ID, overlay version, source `HEAD`, wrapper path, handler
   path, and compact runtime signature state.
6. Keep normal apply behavior exact-base only; require `-SkipInstall` for
   source-only checks and never invoke `install:codex` during fixture tests.

**Verification:** The Task 2 fixtures pass; the reconciler selects the new
compaction overlay when both records are active and fails closed when only the
legacy record is detectable.

**Exit Criteria:** `-VerifyOnly` cannot report compact compatibility from the
legacy wrapper patch alone, and no generated or installed file is directly
edited.

### Task 5: Reconcile documentation and perform final verification

**Purpose:** Align maintained guidance, plan evidence, and fresh command output.

**Task Function:** Documentation and completion verification.

**Template Profile:**

- Controller-selected: `normal`
- Selection basis: final evidence reconciliation and maintained-documentation alignment

**Required Skills:** `skill-verification-before-completion`.

**Files And Symbols:**

- Modify `tools/local-patch-hub/README.md`.
- Update this plan's task ledger and verification sections only after proof is
  accepted.
- Inspect the pre-existing modified plan and `.runtime` artifacts without
  changing them.

**Dependencies:** Tasks 1-4.

**Authority:**

- Preauthorized local actions: update overlay procedure documentation, run named validators/tests, inspect Git status/diff, and record accepted evidence in this plan
- Stop for: failed focused tests, stale exact-base metadata, generated-surface drift, unexpected file changes, global runtime mutation, or unresolved source provenance

**Steps:**

1. Document the exact-base refresh workflow, compact-overlay precedence, and
   source-only versus installed-runtime verification commands.
2. Keep the README statement that generated `dist/tokenpilot-codex-hook.cmd`
   files are not hand-edited.
3. Run the focused Project OS tests and the selected external LightRSI adapter
   typecheck/test suite from the clean detached checkout.
4. Run repository planning/template validators and `git diff --check`.
5. Inspect the final diff and confirm only the plan and declared overlay,
   reconciler, test, and README files changed; leave the existing plan edit and
   `.runtime` artifacts untouched.
6. Keep this plan `proposed` until a later approved execution and fresh
   verification cycle; do not mark it completed from planning evidence alone.

**Verification:**

- `py -B -m pytest -q tests/test_lightrsi_codex_overlay.py`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-22-lightrsi-overlay-reconciliation-plan.md`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `git diff --check`
- `pnpm --dir C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI-lightrsi-native-result-reader --filter @lightrsi/codex typecheck`
- `pnpm --dir C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI-lightrsi-native-result-reader --filter @lightrsi/codex test`

**Exit Criteria:** All declared checks pass with fresh output, the exact-base
overlay and reconciler behavior are proven, no installed/global runtime is
mutated, and the plan remains proposed for approval.

## Verification

- `py -B -m pytest -q tests/test_lightrsi_codex_overlay.py`
- `py -B scripts/validate_planning_lifecycle.py --plan docs/superpowers/plans/2026-10-22-lightrsi-overlay-reconciliation-plan.md`
- `py -B scripts/validate_template_required_sections.py --repo-root . --require-template-selection`
- `git diff --check`
- `pnpm --dir C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI-lightrsi-native-result-reader --filter @lightrsi/codex typecheck`
- `pnpm --dir C:\Users\HOANG PHI LONG DANG\repos\longdang193\LightRSI-lightrsi-native-result-reader --filter @lightrsi/codex test`

## Completion Criteria

1. The canonical source commit and installed runtime provenance are recorded,
   or execution is explicitly blocked with the competing evidence.
2. A new exact-base compaction overlay applies and reverse-applies cleanly,
   while `c05cafe5` and `c0d86ae` remain available for historical rollback.
3. Legacy hook-only reverse applicability cannot satisfy compact compatibility
   verification.
4. Ambiguous overlay matches fail closed with actionable diagnostics.
5. Behavioral tests prove selection precedence, stale-match rejection,
   non-mutation, generated-wrapper ownership, compact fallback behavior, and
   ordinary-route preservation.
6. No direct edit or global installation of
   `C:\Users\HOANG PHI LONG DANG\.local\share\lightrsi\codex-adapter\dist` occurs.
7. Focused tests, external adapter typecheck/tests, planning validators, and
   `git diff --check` pass from the execution workspace.
8. The plan remains `proposed` until approved for execution and later fresh
   verification.
