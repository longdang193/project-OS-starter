---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
layer: change
distribution_tier: project
name: 9router-direct-ownership-upstream-sync
targets:
  - tools/local-patch-hub/README.md
  - tools/local-patch-hub/Apply-9RouterAttributionOverlay.ps1
  - tools/local-patch-hub/Apply-9RouterCgwOverlay.ps1
  - tools/local-patch-hub/Apply-9RouterCodexRelayOverlay.ps1
  - tools/local-patch-hub/Apply-9RouterResponsesOverlay.ps1
  - tools/local-patch-hub/Apply-9RouterSecurityOverlay.ps1
  - tools/local-patch-hub/Install-9RouterCodexComboStartup.ps1
  - tools/local-patch-hub/Install-9RouterGlobal.ps1
  - tools/local-patch-hub/Start-9RouterCodexCombo.ps1
  - tools/local-patch-hub/overlays/9router-*/**
  - tests/test_9router_cgw_overlay.py
  - tests/test_9router_codex_relay_overlay.py
  - tests/test_9router_global_install.py
  - tests/test_9router_responses_overlay.py
  - tests/test_9router_security_overlay.py
  - tests/test_local_patch_hub_deprecation.py
  - 9router:.github/workflows/ci.yml
  - 9router:.github/workflows/upstream-sync.yml
  - 9router:docs/UPSTREAM-SYNC.md
  - 9router:open-sse/handlers/chatCore*.js
  - 9router:open-sse/executors/*.js
  - 9router:open-sse/transformer/*.js
  - 9router:open-sse/translator/**/*.js
  - 9router:open-sse/utils/{error,requestLogger,stream,upstreamHeaders}.js
  - 9router:src/app/api/v1/chatgpt-web/responses/route.js
  - 9router:src/app/api/v1/responses/route.js
  - 9router:src/lib/db/{schema.js,repos/requestDetailsRepo.js,repos/usageRepo.js}
  - 9router:src/mitm/logger.js
  - 9router:src/sse/{handlers/chat.js,utils/requestCorrelation.js}
  - 9router:tests/unit/*{attribution,correlation,responses,redaction,relay}*.test.js
---

# 9router Direct Ownership and Automatic Upstream Synchronization

## Goal

Make `longdang193/9router` the canonical owner of maintained 9router source
changes and upstream synchronization while deprecating only the 9router portion
of `project-OS-starter/tools/local-patch-hub`. Preserve all OpenDesign and
LightMem2 overlay and launcher behavior. Establish a low-maintenance upstream
flow that creates one synchronization pull request, runs deterministic checks,
stops on merge conflicts, and enables auto-merge only after required checks
pass.

This plan does not delete the OpenDesign overlay, change the installed
OpenDesign runtime, or remove the installed LightRSI Codex hook. It does not
make Project OS a second 9router source tree.

## Implementation Outcomes

### Direct 9router ownership

The fork contains maintained attribution, Responses compatibility, security,
and Codex relay behavior currently represented by active 9router overlays. The
retired CGW overlay and CGW startup/install path are not ported. The fork's
source and tests become the only maintained implementation location.

### Narrow patch-hub deprecation

The 9router-specific patch scripts, overlay registries, and patch-hub tests are
removed from active Project OS maintenance. The patch-hub README points to the
fork's direct source and upstream-sync procedure. OpenDesign launchers,
OpenDesign patching, and LightMem2 overlay files remain present and covered by
their existing tests.

### Low-maintenance upstream flow

The fork contains one CI workflow and one scheduled upstream-sync workflow. The
sync workflow uses one automation branch, opens or updates one pull request,
reports conflicts through a failed workflow, and never mutates the default
branch directly. An ancestry-preserving merge commit is the only accepted
publication mode for the baseline and synchronization PRs. A repository-policy
preflight proves that auto-merge is enabled, the exact CI check is required on
`master`, the automation identity cannot bypass that requirement, and the
workflow-created PR check runs without manual approval. Privileged-path changes
and all merge conflicts remain manual-review gates.

### Durable operating procedure

`9router/docs/UPSTREAM-SYNC.md` owns the remote roles, baseline procedure,
scheduled synchronization behavior, conflict handling, auto-merge conditions,
and rollback path. Project OS only points maintainers to that procedure.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-using-git-worktrees`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-finishing-a-development-branch`
- Isolation: dedicated clean worktrees for Project OS and 9router; preserve current dirty workspaces
- Commit policy: `no commits during execution` until the user explicitly authorizes implementation commits and publication
- Preauthorized local actions: read source and Git state; create isolated worktrees; edit listed source, test, documentation, and workflow files; run listed checks; fetch configured remotes without pushing
- User-approval actions: commit, push, pull-request creation or update, pull-request merge, branch deletion, installed-runtime mutation, global package installation, scheduled-task changes, and destructive cleanup
- Parallel ownership: none; baseline reconciliation and source migration are serialized
- Sequential fallback: reconcile the 9router baseline, port canonical source behavior, retire Project OS 9router overlays, then enable scheduled synchronization and final proof

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `project-OS-starter: codex/9router-direct-ownership`; `9router: codex/9router-direct-upstream-sync`
- Base commit: `project-OS-starter origin/main 27f8e818a26212c514cda45bcc4882746ae21b28`; `9router origin/master 3e21db2dd9326fa794e015c30660aa6ab8dcc94a`
- Expected workspace: current Project OS and 9router workspaces retain unrelated dirty changes; implementation uses fresh clean worktrees
- Next action: resolve the recorded Task 1 semantic baseline blocker under explicit direction; do not begin Tasks 2–5
- Blockers: the fork is 49 commits unique to itself and upstream is 305 commits ahead; the no-commit baseline merge conflicted in package/build, routing, security/error, combo, and chat-core files, so the plan's mandatory semantic-conflict stop condition is active

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `blocked` | 9router clean worktree | `unresolved` | none | remote-role and divergence report; separate baseline merge commit; ancestry proof | remote roles and `49/305` divergence recorded; merge aborted; conflict inventory at `artifacts/upstream-baseline-conflicts.txt`; `master` unchanged |
| Task 2 | `pending` | 9router clean worktree | `unresolved` | Task 1 | source/test migration matrix and focused test output | pending |
| Task 3 | `pending` | 9router clean worktree | `unresolved` | Task 2 | CI/policy/token validation; clean/conflict/privileged-path proof | pending |
| Task 4 | `pending` | Project OS clean worktree | `unresolved` | Task 2 | deprecation and OpenDesign preservation tests; kit proof | pending |
| Task 5 | `pending` | both clean worktrees | `unresolved` | Task 3, Task 4 | fresh final verification and immutable remote evidence | pending |

## Task Breakdown

### Task 1: Establish fork ownership and reconcile the baseline

**Task Function:**
- Cross-repository Git baseline reconciliation and remote-safety setup.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through planning dispatch after the conflict surface is measured.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validate immutable remote roles, merge state, and fresh install/test/build output.

**Workspace:** fresh 9router worktree from `origin/master` at
`3e21db2dd9326fa794e015c30660aa6ab8dcc94a`.

1. Confirm `origin` is `https://github.com/longdang193/9router.git` and
   `upstream` is `https://github.com/decolua/9router.git`.
2. Remove the local `upstream` push URL and configure a failing sentinel push
   URL. All automation pushes explicitly target `origin`.
3. Record divergence:

   ```powershell
   git fetch origin --prune
   git fetch upstream --prune
   git rev-list --left-right --count origin/master...upstream/master
   git log --left-right --cherry-pick --oneline origin/master...upstream/master
   ```

4. Create `codex/9router-upstream-baseline` from `origin/master` and attempt:

   ```powershell
   git switch -c codex/9router-upstream-baseline origin/master
   git merge --no-commit --no-ff upstream/master
   ```

5. Resolve conflicts semantically in source, tests, docs, and workflows. Keep
   the fork's CGW retirement and preserve unrelated upstream behavior. Never
   resolve by accepting all ours or all theirs.
6. Before committing the merge, run:

   ```powershell
   npm ci
   npm install --prefix tests --no-audit --no-fund
   npm --prefix tests test
   npm run build
   git diff --check
   ```

7. Capture the exact unresolved-path inventory before any abort:

   ```powershell
   git diff --name-only --diff-filter=U | Tee-Object artifacts/upstream-baseline-conflicts.txt
   git status --short
   ```

   If the merge is clean, remove the temporary inventory and continue. If the
   merge is conflicted, preserve the inventory as evidence, then abort and
   leave the worktree clean.

8. After the baseline checks pass, stop at an explicit publication checkpoint.
   Once commit/publication is authorized, create the baseline with an
   ancestry-preserving merge commit and publish it before Task 2 begins:

   ```powershell
   git commit --no-edit
   git push origin codex/9router-upstream-baseline
   git merge-base --is-ancestor upstream/master HEAD
   ```

   The baseline must then land on `master` through that merge commit, not squash
   or rebase. Task 1 does not complete, and Task 2 does not begin, until the
   baseline merge is present on the fork's `master`. Record the resulting
   baseline commit and prove that `upstream/master` is an ancestor of the
   fork's `master` before enabling any synchronization workflow.

9. Stop and report exact conflicting files when an unresolved conflict touches
   CGW retirement, provider routing, account fallback, authentication, security
   logging, workflow permissions, or package/build configuration.

**Proof:** clean worktree status, remote-role report, immutable base/upstream
SHAs, separate baseline merge commit, ancestry proof, test/build output, and
conflict inventory captured before abort when blocked.

**Authority:**

- Preauthorized local actions: create the clean worktree, fetch remotes, inspect and resolve baseline conflicts, and run the listed checks.
- User-approval checkpoint: commit, publish, and merge the verified baseline PR with an ancestry-preserving merge before Task 2 starts.
- Stop for: unresolved semantic conflict, failed baseline check, unexpected remote URL, dirty worktree, missing ancestry proof, or any unauthorized push/commit/publication action.

### Task 2: Port maintained overlay behavior into 9router source

**Task Function:**
- Direct source migration with backend compatibility and regression proof.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through planning dispatch after Task 1 establishes the reconciled source shape.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validate behavior through focused source tests, fallback/replay paths, and build output.

**Workspace:** the verified 9router baseline worktree from Task 1.

Use existing patch files as behavior evidence, not as a patch application
mechanism. Implement behavior directly in the fork after the upstream baseline.

| Overlay evidence | Direct source/test owner |
| --- | --- |
| `9router-attribution` | `open-sse/handlers/chatCore*.js`, `src/lib/db/repos/requestDetailsRepo.js`, `src/lib/db/repos/usageRepo.js`, `src/lib/db/schema.js`, `tests/unit/attribution-persistence.test.js`, `tests/unit/request-details-tab.test.js` |
| `9router-responses` | `open-sse/executors/*.js`, `open-sse/transformer/*.js`, `open-sse/translator/**/*.js`, `open-sse/utils/stream.js`, and the existing Responses regression tests |
| `9router-security` | `open-sse/handlers/chatCore.js`, `open-sse/utils/error.js`, `open-sse/utils/requestLogger.js`, `src/app/api/v1/responses/route.js`, `src/lib/db/repos/requestDetailsRepo.js`, `src/mitm/logger.js`, `src/sse/handlers/chat.js`, `src/sse/utils/requestCorrelation.js`, and the security regression tests |
| `9router-codex-relay` | `src/app/api/v1/chatgpt-web/responses/route.js` and `tests/unit/chatgpt-web-responses-relay.test.js` |
| `9router-cgw` | Do not port; verify the CGW shim, startup path, receipt, and retired web-combo behavior remain absent or fail closed |

For each retained behavior:

1. Compare the exact-base patch with the reconciled upstream source.
2. Reimplement the behavior without overlay receipts, base-commit dispatch,
   global install hooks, or Project OS path assumptions.
3. Keep or add the named regression tests beside the source owner.
4. Verify the behavior works from a clean checkout without the patch hub.
5. Preserve the CGW retirement contract: no `tools/cgw-codex-shim`, no CGW
   global receipt, no CGW startup task, and no silent retired-alias remapping.

**Proof:** migration matrix checked against the final diff, focused attribution,
Responses, security, relay, fallback, cancellation, replay, and CGW-retirement
tests, plus `npm run build` and `git diff --check`.

**Authority:**

- Preauthorized local actions: edit the listed 9router source/tests and run focused tests, package install, build, and diff checks.
- Stop for: behavior that requires the retired overlay contract, failed security/fallback/replay tests, changed provider/quota semantics, or a Project OS change before direct source proof.

### Task 3: Add minimal CI and scheduled upstream synchronization

**Task Function:**
- GitHub Actions workflow design, permission minimization, and conflict-path proof.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through planning dispatch after the direct source contract is stable.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validate workflow permissions, clean/conflict fixtures, and remote run evidence.

**Workspace:** the verified 9router worktree after Task 2.

Create exactly these workflows:

#### `.github/workflows/ci.yml`

- Trigger on pull requests and pushes to `master`.
- Use `ubuntu-latest` and Node 24.
- Run `npm ci`, `npm install --prefix tests --no-audit --no-fund`,
  `npm --prefix tests test`, and `npm run build`.
- Grant only `contents: read`.
- Use a concurrency group keyed by workflow and ref with cancellation for
  superseded runs.

#### `.github/workflows/upstream-sync.yml`

- Trigger daily at `03:17 UTC` and through `workflow_dispatch`.
- Use one `upstream-sync` concurrency group with no cancellation.
- Set the workflow's `GITHUB_TOKEN` permissions to `contents: read`; do not
  grant it write access.
- Use one dedicated GitHub App installation token stored as repository secrets
  for branch pushes and PR operations; grant that identity only `contents: write`
  and `pull_requests: write`. Do not use `GITHUB_TOKEN` for the sync branch or
  PR so the resulting PR checks are not dependent on workflow-token approval
  behavior.
- Check out full history, fetch `upstream/master`, and create or refresh only
  `automation/upstream-sync` from `origin/master`.
- Attempt `git merge --no-edit --no-ff upstream/master`.
- On conflict, capture `git diff --name-only --diff-filter=U` and the current
  PR/branch SHAs as workflow artifacts and job-summary evidence before running
  `git merge --abort`. Disable auto-merge on any existing synchronization PR,
  fail the job, and leave `master` unchanged.
- On a clean merge, compute the changed-path set against `origin/master` before
  pushing. Changes to `.github/workflows/**`, local actions, dependency or
  install scripts, authentication/security surfaces, or fork-owned attribution,
  Responses, relay, and routing files must create/update the PR without
  auto-merge and require explicit review.
- For clean changes outside those privileged paths, push only
  `automation/upstream-sync` using an expected-head check and
  `--force-with-lease`; never use an unconditional force push. Create or update
  one PR titled `chore: sync upstream 9router`, verify its current head SHA, and
  enable merge-commit auto-merge only after the exact required `ci.yml` check is
  successful. Do not enable squash or rebase auto-merge. Never push directly to
  `master` and do not add an LLM approval bot.
- Before rebuilding a reused branch, identify any open synchronization PR and
  disable its auto-merge. If its head is not the expected automation-owned SHA,
  stop without rewriting it. A conflicted or superseded PR remains explicitly
  marked as requiring manual review and cannot retain auto-merge.
- Treat a failed check, conflict, privileged-path change, missing repository
  policy, missing token configuration, or unexpected branch/PR head as a
  manual intervention path.

Before enabling the workflow, verify and record the repository-level preconditions:

1. Auto-merge is enabled for the repository.
2. `master` requires the exact `ci.yml` check from the intended workflow source.
3. The automation identity cannot bypass that required check or branch rule.
4. The GitHub App installation token can push the automation branch, create or
   update the PR, and trigger its `pull_request` checks without manual approval.
5. The repository's Actions policy permits the workflow and the token strategy.

If any precondition cannot be observed or is false, stop before enabling
auto-merge and record the missing external state.

Document remote roles, the one-time baseline, schedule, branch reuse, conflict
behavior, privileged-path review, token setup, repository-policy preconditions,
ancestry checks, auto-merge conditions, and rollback in
`9router/docs/UPSTREAM-SYNC.md`. Rollback resets only the automation branch and
closes its PR after disabling auto-merge; it never resets `master`.

**Proof:** workflow review, `git diff --check`, a local clean-merge dry run with
`git merge-tree`, disposable conflict and privileged-path fixtures proving
`master` is unchanged and auto-merge is withheld, repository-policy and token
preflight output, and one manually dispatched remote run producing the expected
merge-commit PR/check state.

**Authority:**

- Preauthorized local actions: create the two workflow files and procedure; run local dry-run and syntax checks.
- User-approval/external-state checkpoint: configure the GitHub App secret and repository policy, then record the precondition evidence before enabling auto-merge.
- Stop for: workflow permission expansion, direct default-branch mutation, partial conflict branches, unverified PR CI, privileged-path auto-merge eligibility, unsafe branch rewriting, or inability to run required CI commands on a clean checkout.

### Task 4: Deprecate only Project OS 9router patch-hub surfaces

**Task Function:**
- Scoped repository deprecation with generated-surface and preserved-overlay checks.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through planning dispatch after Task 2 proves the direct 9router owners.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validate exact deletions, OpenDesign/LightMem2 preservation, and adapter/kit integrity.

**Workspace:** fresh Project OS worktree from `origin/main` at
`27f8e818a26212c514cda45bcc4882746ae21b28`.

1. Update `tools/local-patch-hub/README.md` to remove active 9router overlay
   instructions and point maintainers to the direct fork procedure. Keep the
   complete OpenDesign and LightMem2 sections unchanged.
2. Delete these obsolete 9router scripts:

   - `Apply-9RouterAttributionOverlay.ps1`
   - `Apply-9RouterCgwOverlay.ps1`
   - `Apply-9RouterCodexRelayOverlay.ps1`
   - `Apply-9RouterResponsesOverlay.ps1`
   - `Apply-9RouterSecurityOverlay.ps1`
   - `Install-9RouterCodexComboStartup.ps1`
   - `Install-9RouterGlobal.ps1`
   - `Start-9RouterCodexCombo.ps1`

3. Delete only these overlay registries:

   - `tools/local-patch-hub/overlays/9router-attribution/`
   - `tools/local-patch-hub/overlays/9router-cgw/`
   - `tools/local-patch-hub/overlays/9router-codex-relay/`
   - `tools/local-patch-hub/overlays/9router-responses/`
   - `tools/local-patch-hub/overlays/9router-security/`

4. Preserve without edits:

   - `tools/local-patch-hub/Apply-OpenDesignPatch.ps1`
   - `tools/local-patch-hub/Start-OpenDesignMcp.ps1`
   - `tools/local-patch-hub/Start-OpenDesignPatched.ps1`
   - `tools/local-patch-hub/Start-OpenDesignPatched.cmd`
   - `tools/local-patch-hub/Apply-LightMem2CodexOverlay.ps1`
   - `tools/local-patch-hub/overlays/lightrsi-codex-hook-portable/`

5. Delete patch-hub tests whose sole owner is the removed 9router mechanism:

   - `tests/test_9router_cgw_overlay.py`
   - `tests/test_9router_codex_relay_overlay.py`
   - `tests/test_9router_global_install.py`
   - `tests/test_9router_responses_overlay.py`
   - `tests/test_9router_security_overlay.py`

6. Add `tests/test_local_patch_hub_deprecation.py` asserting that the OpenDesign
   and LightMem2 owners remain present, the listed 9router scripts and
   registries are absent, and the README contains the direct-ownership pointer.
   For every file declared “Preserve without edits,” record its baseline
   SHA-256 in the preservation fixture and assert the current content matches
   that hash. Include the OpenDesign adapter and artifact-tracker regression
   tests in the focused verification; do not rely on an installed OpenDesign
   runtime being present for the preservation proof.

**Proof:** focused Project OS tests, active-path absence checks, OpenDesign and
LightMem2 preservation hash assertions, the broader OpenDesign regression tests,
and `git diff --check`. Historical plans may retain old paths as evidence and
are not rewritten.

**Authority:**

- Preauthorized local actions: edit the README and deprecation test; delete only the exact 9router files/directories listed above; run focused tests.
- Stop for: any OpenDesign or LightMem2 diff, unknown file ownership, generated-surface drift, or a live Project OS runtime dependency on a listed 9router path.

### Task 5: Final cross-repository verification and handoff

**Task Function:**
- Fresh cross-repository acceptance verification and evidence handoff.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve through planning dispatch after all implementation tasks complete.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: independently validate final Git state, required checks, and remote workflow evidence.

Run fresh proof from clean worktrees after Tasks 1–4.

**Project OS:**

```powershell
py -3 -m pytest tests/test_local_patch_hub_deprecation.py tests/test_open_design_local_patch.py tests/test_lightrsi_codex_overlay.py -q
py -3 -m pytest tests/test_opendesign_profile_adapter.py tests/test_opendesign_artifact_tracker_regression.py -q
py -B scripts/sync_agent_adapters.py --all-platforms --check
py -B scripts/build_starter_kit.py
py -B scripts/validate_starter_kit.py
git diff --check
```

**9router:**

```powershell
npm ci
npm install --prefix tests --no-audit --no-fund
npm --prefix tests test
npm run build
git diff --check
```

Confirm that `origin` is the only automation push destination, `upstream` is
fetch-only, `automation/upstream-sync` is the only sync branch, the baseline and
sync PRs use ancestry-preserving merge commits, the last synchronized upstream
SHA is an ancestor of `master`, clean merges produce one PR, conflict merges
capture their inventory before aborting and leave `master` unchanged, privileged
path changes withhold auto-merge, the exact required `ci.yml` check gates
auto-merge, PR checks run without manual approval, 9router patch-hub paths are
absent from active Project OS code/config, OpenDesign and LightMem2 paths match
their preservation hashes, CGW/web-combo surfaces remain retired, and unrelated
dirty files/runtime state/worktrees are untouched.

Record immutable workflow run IDs, PR number/head SHA, conflict-fixture output,
test/build output, and final Git status before requesting publication or cleanup.

**Authority:**

- Preauthorized local actions: run the listed checks and record output.
- Stop for: any failed required check, post-review source change, unexpected active 9router/CGW reference, OpenDesign regression, or workspace mismatch.

## Verification

- Project OS deprecation and preserved-overlay tests pass.
- Adapter drift check and starter-kit build/validation pass.
- 9router baseline reconciliation passes install, tests, and build before
  synchronization automation is enabled.
- Direct attribution, Responses, security, relay, fallback, cancellation,
  replay, and CGW-retirement tests pass in the fork.
- Clean and conflicting upstream fixtures prove no partial merge reaches the
  default branch.
- Clean and privileged-path fixtures prove that only safe changes can be
  eligible for unattended auto-merge.
- A remote workflow run proves the expected synchronization PR, required-check
  gate, PR-triggered CI, ancestry-preserving merge behavior, and stale-branch
  handling.
- OpenDesign adapter and artifact-tracker regression tests pass independently
  of whether the installed OpenDesign runtime is available.
- `git diff --check` is clean in both repositories.

## Completion Criteria

1. The one-time 9router baseline is reconciled or the exact semantic blocker is
   recorded without weakening CGW retirement.
2. Maintained 9router overlay behavior is source-owned and test-owned in the
   fork, not applied from Project OS patch files.
3. The listed 9router patch-hub scripts and registries are removed.
4. OpenDesign and LightMem2 patch files, launchers, and tests remain intact.
5. `ci.yml` and `upstream-sync.yml` are permission-minimized and proven on clean
   and conflicting merge paths.
6. The baseline and synchronization PRs use ancestry-preserving merge commits;
   the last synchronized upstream SHA is an ancestor of `master`.
7. Repository policy, authentication, and PR-triggered CI prerequisites are
   verified; privileged-path changes and conflicts cannot auto-merge.
8. The sync workflow uses one automation branch and one PR, never pushes
   directly to `master`, and auto-merges only after the exact required check.
9. `9router/docs/UPSTREAM-SYNC.md` is the canonical maintenance procedure;
   Project OS only points to it.
10. OpenDesign and LightMem2 preservation hashes and regression tests pass.
11. Fresh verification evidence is accepted by
   `skill-verification-before-completion` before branch disposition.

The plan remains `proposed` until explicitly approved for execution. It must
not be marked `completed` merely because workflow files or documentation exist;
baseline reconciliation, direct-source proof, conflict proof, and remote
workflow evidence are required.
