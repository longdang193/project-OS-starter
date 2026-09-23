---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: deepagents-runtime-upgrade-074
targets:
  - scripts/setup_deepagents_runtime.ps1
  - scripts/patch_deepagents_runtime.py
  - tests/test_dcode_project.py
  - tests/test_deepagents_runtime_patch.py
  - README.md
---

# DeepAgents Runtime Upgrade Plan

## Goal

Upgrade Project OS Starter from `deepagents-code==0.1.66` to
`deepagents-code==0.1.74`, which brings `deepagents==0.7.18` on September 23,
2026.

Preserve Project OS runtime boundaries, headless MCP policy, retry-budget
behavior, Windows process behavior, explicit MCP selection, and fail-closed
unsupported-version handling.

Do not bump the package version until the local patcher supports the post-
`0.1.71` FastMCP and `langchain.mcp` architecture.

## Implementation Outcomes

### Supported DeepAgents runtime

`setup_deepagents_runtime.ps1` installs and verifies `deepagents-code==0.1.74`
with dependency resolution owned by the upstream package instead of stale
manual LangGraph overrides.

### Compatible local patch boundary

`patch_deepagents_runtime.py` handles the current DeepAgents Code source layout.
It removes obsolete pre-FastMCP patch paths, preserves only Project OS behavior
not supplied upstream, and fails clearly when a future runtime needs a new
compatibility review.

### Regression proof

Tests cover current-version patching, idempotency, installer expectations,
headless MCP behavior, retry-budget behavior, and Windows command/process
handling at the supported boundary.

### Documentation alignment

README separates the DeepAgents SDK version from the DeepAgents Code CLI
version and records the supported upgrade policy.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing tracked and untracked changes
- Commit policy: `no commits during execution`
- Preauthorized local actions: inspect declared files; edit declared runtime, test, and documentation files; create disposable local fixtures; run declared tests, validators, and Git checks
- User-approval actions: live PyPI installation, provider authentication, external MCP calls, publication, commit, push, merge, destructive cleanup, or discard of existing changes
- Parallel ownership: none
- Sequential fallback: baseline and upstream fixture → patcher migration → installer and docs → focused verification → final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `2e1aeea4b4bb8d00d0f94e500d7b06f498184c52`
- Expected workspace: preserve existing untracked changes and existing untracked plans
- Next action: none; implementation and verification complete
- Blockers: none
- Central env follow-up: DeepAgents now reads `OPENAI_API_KEY` from `~/.codex/tokenpilot.env`, the same env file Codex loads. Provider-backed MCP probe passed with explicit `--mcp-select context7`; offline MCP discovery and `dcode doctor --json` passed.

Existing workspace changes to preserve:

- `.playwright-mcp/`
- `db/`
- existing untracked plans under `docs/superpowers/plans/`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline Git state and `0.1.74` compatibility fixture | baseline recorded; current patcher failure localized before edits |
| Task 2 | `completed` | current | `codex` | Task 1 | patcher unit tests and idempotency proof | `10 passed`; real `0.1.74` fixture patched twice with exit `0` |
| Task 3 | `completed` | current | `codex` | Task 2 | installer/version/dependency tests and docs diff | focused runtime suite `148 passed`; installer/docs aligned |
| Task 4 | `completed` | current | `codex` | Task 3 | focused suite, repository validators, final Git checks | live install passed; `dcode` `0.1.74`/SDK `0.7.18`; offline MCP and wrapper checks passed; `794 passed, 1 skipped` |

## Task Breakdown

### Task 1: Establish upgrade baseline and source contract

**Purpose:**
- Confirm current runtime pins, patch assumptions, tests, generated boundaries, and pre-existing workspace state.

**Task Function:**
- Map current-to-target runtime contract and isolate compatibility facts before editing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source inspection and deterministic fixture setup.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: no independent validator needed for baseline-only work.

**Specification Coverage:**
- Upgrade target is `deepagents-code==0.1.74` with transitive `deepagents==0.7.18`.
- Current `0.1.66` patcher is pre-FastMCP and cannot be trusted against target source.
- Existing workspace changes remain untouched.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/setup_deepagents_runtime.ps1:$DeepAgentsCodeVersion`
- Inspect: `scripts/setup_deepagents_runtime.ps1:uv tool install`
- Inspect: `scripts/patch_deepagents_runtime.py:patch_mcp_tools`
- Inspect: `scripts/patch_deepagents_runtime.py:patch_stdio_lookup`
- Inspect: `scripts/patch_deepagents_runtime.py:patch_windows_lookup`
- Inspect: `scripts/patch_deepagents_runtime.py:patch_model_retry_budget`
- Inspect: `tests/test_dcode_project.py`
- Inspect: `tests/test_deepagents_runtime_patch.py`
- Inspect: `README.md:Open-Source Ecosystem` and `README.md:Local Adoption`
- Verify: `git status --short`, `git branch --show-current`, `git rev-parse HEAD`

**Dependencies:**
- Upstream release references: [DeepAgents `0.7.18`](https://github.com/langchain-ai/deepagents/releases/tag/deepagents%3D%3D0.7.18) and [DeepAgents Code changelog](https://github.com/langchain-ai/deepagents/blob/main/libs/code/CHANGELOG.md).

**Authority:**
- Preauthorized local actions: inspect source, read release metadata, create disposable fixtures outside tracked paths, and record existing changes.
- Stop for: unknown workspace identity, required edits outside declared targets, or any request to discard existing changes.

**Steps:**
- [x] Step 1: Record branch, `HEAD`, tracked changes, and untracked paths.
- [x] Step 2: Confirm current pins: `0.1.66`, `langgraph-api==0.13.0`, `langgraph-runtime-inmem==0.33.3`, and `uvicorn==0.51.0`.
- [x] Step 3: Extract or otherwise obtain a disposable `0.1.74` source fixture and record package dependency requirements.
- [x] Step 4: Run current patcher against the fixture; preserve failure evidence as migration input.

**Verification:**
- [x] `git status --short; git branch --show-current; git rev-parse HEAD`
- [x] `py -3 -m pytest tests/test_deepagents_runtime_patch.py tests/test_dcode_project.py -q` before edits when environment permits
- Expected: baseline is recorded; current patcher failure is localized to post-FastMCP source assumptions, not hidden by a version-only edit.

**Exit Criteria:**
- Current and target runtime contracts, patch failures, and workspace boundaries are recorded.

### Task 2: Migrate compatibility patcher

**Purpose:**
- Make local compatibility patches work with `deepagents-code==0.1.74` without preserving dead source-shape assumptions.

**Task Function:**
- Refactor narrow source compatibility checks and preserve Project OS-specific runtime guards.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material backend/runtime behavior with narrow file scope.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local tests provide deterministic validation.

**Specification Coverage:**
- FastMCP and `langchain.mcp` own MCP transport in the target runtime.
- Existing config-path handling is upstream-integrated and must not receive duplicate patching.
- Existing headless MCP exception and retry budget remain Project OS behavior unless current source proves upstream equivalence.
- Missing obsolete Windows utility module must not cause setup to fail after target migration.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_mcp_tools`
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_stdio_lookup`
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_windows_lookup`
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_windows_process`
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_headless_mcp_guard`
- Inspect/Modify: `scripts/patch_deepagents_runtime.py:patch_model_retry_budget`
- Modify: `tests/test_deepagents_runtime_patch.py`
- Verify: disposable `deepagents-code==0.1.74` fixture and patcher exit status

**Dependencies:**
- Task 1 source-contract evidence.

**Authority:**
- Preauthorized local actions: edit patcher and its focused tests; use disposable package fixtures; run local tests.
- Stop for: behavior requiring provider credentials, external MCP access, or a redesign of Project OS authority boundaries.

**Steps:**
- [x] Step 1: Remove duplicate config-path patching when target source already uses `Path(explicit_config_path).expanduser()`.
- [x] Step 2: Replace old stdio patch assumptions with a target-version-aware FastMCP boundary check, or retire the patch if upstream behavior satisfies the invariant.
- [x] Step 3: Remove hard dependency on deleted `mcp/os/win32/utilities.py`; validate Windows behavior at the actual supported boundary or mark it as an explicit unsupported-version stop.
- [x] Step 4: Preserve headless MCP read-only probe exception and retry total-delay cap only where target source still lacks them.
- [x] Step 5: Make patch application idempotent and fail closed on unknown source layouts.

**Verification:**
- [x] `py -3 -m pytest tests/test_deepagents_runtime_patch.py -q`
- [x] Run patcher twice against the `0.1.74` fixture.
- Expected: first run succeeds or reports explicit supported no-op; second run is idempotent; no obsolete path lookup remains; unsupported layouts produce actionable errors.

**Exit Criteria:**
- Patcher applies cleanly to target source, preserves required Project OS behavior, and has regression coverage for current and unsupported layouts.

### Task 3: Update installer, tests, and documentation

**Purpose:**
- Align runtime installation, version assertions, dependency resolution, and public documentation with target releases.

**Task Function:**
- Reconcile configuration and maintained documentation after patcher migration.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded configuration, test, and documentation edits.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused installer and documentation tests.

**Specification Coverage:**
- Installer pins `deepagents-code==0.1.74`.
- Upstream package owns compatible LangGraph dependency resolution.
- SDK `0.7.18` and CLI `0.1.74` remain explicitly distinguished.
- Version checks and tests reject accidental rollback to `0.1.66`.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/setup_deepagents_runtime.ps1:$DeepAgentsCodeVersion`
- Modify: `scripts/setup_deepagents_runtime.ps1:uv tool install`
- Modify: `tests/test_dcode_project.py:test_setup_launcher_uses_current_repository_source`
- Modify: `README.md:Open-Source Ecosystem`
- Modify: `README.md:Local Adoption`
- Verify: `repo_config/starter-kit-manifest.json` remains aligned if touched files affect generated starter output

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: edit declared installer, tests, and README; run local dependency metadata checks and focused tests.
- Stop for: live installation failure caused by credentials/provider state, generated-surface drift outside declared targets, or dependency changes requiring a new product decision.

**Steps:**
- [x] Step 1: Set default `DeepAgentsCodeVersion` to `0.1.74`.
- [x] Step 2: Remove stale manual `langgraph-api` and `langgraph-runtime-inmem` overrides; retain only overrides proven necessary by target runtime smoke tests.
- [x] Step 3: Update test assertions for target version and installer behavior.
- [x] Step 4: Document separate runtime versions, Python `>=3.12` requirement, and upgrade rule: version bump requires patcher compatibility proof.
- [x] Step 5: Check generated/starter-kit boundaries before adding any generated output.

**Verification:**
- [x] `py -3 -m pytest tests/test_dcode_project.py tests/test_deepagents_runtime_patch.py -q`
- [x] `rg -n "0\.1\.66|0\.1\.74|0\.7\.18|langgraph-api|langgraph-runtime-inmem" scripts tests README.md`
- Expected: no stale `0.1.66` assertions or unsupported dependency pins remain in maintained runtime surfaces.

**Exit Criteria:**
- Installer, tests, and docs agree on target versions and dependency ownership.

### Task 4: Final runtime and repository verification

**Purpose:**
- Prove installation, patching, runtime boundaries, and repository integrity before acceptance.

**Task Function:**
- Execute final verification and record evidence without claiming provider success from source inspection alone.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic final verification with optional live boundary proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill owns independent acceptance gate.

**Specification Coverage:**
- Direct runtime boundary proves version, patching, success, failure, idempotency, and cleanup behavior.
- Live provider/MCP evidence remains distinct from local source and unit-test evidence.
- Existing unrelated workspace changes remain preserved.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/setup_deepagents_runtime.ps1`
- Verify: `scripts/patch_deepagents_runtime.py`
- Verify: `tests/test_dcode_project.py`
- Verify: `tests/test_deepagents_runtime_patch.py`
- Verify: `README.md`
- Verify: `git diff --check` and `git status --short`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: run declared tests, validators, fixture probes, and Git checks; record evidence.
- Stop for: live install/auth/MCP probe without approval, failed cleanup, ambiguous process ownership, or unrelated test failures requiring scope expansion.

**Steps:**
- [x] Step 1: Run focused runtime tests.
- [x] Step 2: Run repository validators and full test suite if baseline permits.
- [x] Step 3: Run disposable target install; `dcode` resolves `0.1.74`, SDK `0.7.18`, and setup exits `0`.
- [x] Step 4: Run offline MCP discovery, `dcode doctor --json`, and provider-backed MCP probe with explicit `--mcp-select context7`; all passed after central env alignment.
- [x] Step 5: Run final Git checks and record deviations, blockers, and deferred live evidence.

**Verification:**
- [x] `py -3 -m pytest tests/test_deepagents_runtime_patch.py tests/test_dcode_project.py tests/test_project_os_runtime.py -q`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/validate_repo_config.py`
- [x] `py -3 -m pytest -q`
- [x] `git diff --check`
- Expected: required checks pass; live evidence is either recorded or explicitly deferred with reason; no unrelated changes are altered.

**Exit Criteria:**
- All required local checks pass, target runtime compatibility is proven, and any unrun external boundary proof is documented as a blocker or approved deferral.

## Verification

- `py -3 -m pytest tests/test_deepagents_runtime_patch.py tests/test_dcode_project.py tests/test_project_os_runtime.py -q`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_repo_config.py`
- `py -3 -m pytest -q`
- `git diff --check`
- Optional approved live proof: disposable install with `deepagents-code==0.1.74`, `dcode --version`, patcher run, and read-only explicit-MCP probe.

## Completion Criteria

The plan is ready for completion verification when:

1. `deepagents-code==0.1.74` and `deepagents==0.7.18` are the documented and tested target versions.
2. Installer no longer forces dependency versions below upstream target requirements.
3. Patcher handles FastMCP-era source layout and has no deleted-path dependency.
4. Headless MCP and retry-budget Project OS invariants remain covered.
5. Focused tests, repository validators, and final Git checks pass.
6. Live package/provider evidence is recorded separately, or its absence is explicitly documented as an approved deferral.
7. Existing unrelated workspace changes remain preserved.
8. `skill-verification-before-completion` returns `verified` before plan status changes to `completed`.
