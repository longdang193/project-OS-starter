---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: tura-bounded-worker-conformance-and-upgrade
supersedes: docs/superpowers/plans/2026-08-24-codex-tura-default-delegation-adapter-plan.md
targets:
  - scripts/dcode_project.py
  - scripts/setup_deepagents_runtime.ps1
  - tests/test_dcode_project.py
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - README.md
---

# Tura Bounded Worker Conformance And Upgrade Plan

## Goal

Finish Tura-as-a-bounded-worker direction without adding a plugin framework or
second executor schema. Reuse current `dcode-project` launcher contract as SSOT,
make Tura and DeepAgents share one lifecycle boundary, define conformance through
tests, and make compatible Tura upgrades require only binary replacement plus one
bounded TL smoke.

This plan does not create a new Tura plugin API. Current adapter already owns
executor selection, role resolution, validated handoff, provider environment,
timeout, and opaque child status. Remaining work is symmetry, proof, and upgrade
admission.

## Implementation Outcomes

### One shared bounded-worker lifecycle

`scripts/dcode_project.py` uses one private process runner for Tura and
DeepAgents. Both runtimes receive the same timeout, child-status propagation,
Windows Job Object cleanup, POSIX session isolation, and no-fallback behavior.
Executor-specific argv, task rendering, environment, and stdin behavior remain
in their existing functions.

### Conformance tests are the executable contract

`tests/test_dcode_project.py` contains one parameterized common-worker matrix
plus focused Tura and DeepAgents tests. No JSON schema, manifest, interface
package, or copied executor definition is added.

### Upgrade identity without release coupling

`project-delegate --print-config` reports configured Tura executable path and
SHA-256 identity without parsing Tura versions or release metadata. Same-path
binary replacement requires no config change. Moved binaries require the
existing setup command once.

### One compatibility admission path

Each new Tura binary identity receives existing public CLI capability checks and
one read-only `project-delegate` TL smoke. The smoke proves bounded execution,
expected marker, correct profile/model selection, clean Git state, zero process
leaks, and route through configured `TURA_PROVIDER_CONFIG`. No direct-provider,
DeepAgents, or 9router fallback is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current workspace; preserve unrelated untracked `db/`
- Commit policy: no commits during execution; final commit and push require explicit user authorization
- Preauthorized local actions: edit declared files, run focused tests and validators, inspect configured local Tura and LightRSI state, run bounded read-only worker probes
- User-approval actions: push, merge, publication, external configuration writes, destructive cleanup, discarding unrelated changes
- Parallel ownership: none; lifecycle source and conformance tests are coupled
- Sequential fallback: Task 1, then Task 2, then Task 3

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `9fe07bb`
- Active task(s): none
- Expected workspace: plan, shared lifecycle, receipt, and documentation edits; preserved unrelated untracked `db/`
- Next action: none
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused launcher tests | `69 passed`; compile passed |
| Task 2 | `completed` | current | `codex` | Task 1 | config identity and documentation tests | receipt test passed; runtime drift passed |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | deterministic suite plus bounded live probes | Tura and DeepAgents live smokes passed; route and cleanup evidence recorded |

## Task Breakdown

### Task 1: Unify bounded-worker lifecycle

**Purpose:**
- Remove duplicated process-control logic and give Tura the same proven cleanup boundary as DeepAgents.

**Task Function:**
- Refactor and harden shared subprocess lifecycle behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: tightly coupled local refactor with exact source and tests known.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused automated boundary tests provide sufficient task-local validation.

**Specification Coverage:**
- One lifecycle SSOT.
- Symmetric timeout, status, and process-tree behavior.
- No runtime fallback or output rewriting.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_run_tura_worker`
- Inspect: `scripts/dcode_project.py:_run_deepagents_worker`
- Inspect: `scripts/dcode_project.py:_create_windows_job`
- Modify: `scripts/dcode_project.py:_run_bounded_worker`
- Modify: `scripts/dcode_project.py:_run_tura_worker`
- Modify: `scripts/dcode_project.py:_run_deepagents_worker`
- Modify: `tests/test_dcode_project.py`

**Dependencies:**
- Current committed launcher behavior at `9fe07bb`.
- Existing Tura argv, environment, task rendering, and DeepAgents stdin contracts remain unchanged.

**Authority:**
- Preauthorized local actions: private helper refactor, focused tests, temporary child-process probes.
- Stop for: public CLI change, new dependency, new executor, changed fallback policy, credential handling change.

**Steps:**
- [x] Add one private `_run_bounded_worker` accepting argv, environment, repository root, optional stdin text, timeout, and runtime label.
- [x] Move common `Popen`, Windows Job Object, POSIX session, timeout termination, wait, and opaque exit-code propagation into helper.
- [x] Keep `_run_tura_worker` and `_run_deepagents_worker` as thin compatibility wrappers with unchanged call sites.
- [x] Preserve Tura without stdin and DeepAgents optional validated handoff stdin.
- [x] Parameterize tests for normal zero exit, nonzero exit, timeout, and cleanup across both wrappers.
- [x] Retain focused tests for Windows grandchild cleanup and no executor fallback.

**Verification:**
- [ ] `py -m pytest tests/test_dcode_project.py -q`
- Expected: all launcher tests pass; both executors prove identical common lifecycle behavior.
- [ ] `py -m compileall -q scripts/dcode_project.py`
- Expected: launcher compiles without error.

**Exit Criteria:**
- One private lifecycle implementation owns both worker paths; executor-specific behavior remains separate and unchanged.

### Task 2: Add release identity and minimal upgrade workflow

**Purpose:**
- Bind compatibility evidence to tested Tura binary without adding version gates or release-specific adapter code.

**Task Function:**
- Extend existing configuration receipt and document same-path upgrade procedure.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small deterministic configuration and documentation change.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: unit and documentation contract tests are sufficient.

**Specification Coverage:**
- Starter remains role, executor, and provider-path SSOT.
- Compatible Tura releases require minimal management.
- TL remains configured through `TURA_PROVIDER_CONFIG`; 9router remains unchanged.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:main`
- Modify: `scripts/dcode_project.py:main --print-config payload`
- Modify: `tests/test_dcode_project.py:test_print_config_reports_selected_role_effective_model`
- Inspect: `scripts/setup_deepagents_runtime.ps1:Tura capability probe`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `README.md`

**Dependencies:**
- Task 1 complete.
- Existing setup already owns Tura executable/provider-config paths and public CLI capability probe.

**Authority:**
- Preauthorized local actions: stdlib SHA-256 calculation, receipt test, documentation edits.
- Stop for: automatic downloads, release API calls, semantic-version branches, copied binaries, provider-config rewrite, 9router modification.

**Steps:**
- [x] Add Tura executable SHA-256 to `--print-config` only when configured executable exists.
- [x] Keep executable path and provider-config path as existing user-local SSOT; do not persist another identity file.
- [x] Test deterministic hash receipt and absent-Tura behavior without reading or printing credentials.
- [x] Document same-path replacement as zero-config upgrade and moved-path replacement as one setup rerun.
- [x] Document one post-upgrade compatibility smoke; do not run capability or provider probes on every delegated task.
- [x] State explicitly that compatibility admission and efficiency claims are separate; performance evidence becomes stale after binary identity changes.

**Verification:**
- [ ] `py -m pytest tests/test_dcode_project.py -q`
- Expected: config receipt includes correct binary hash and no secret data.
- [ ] `py scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- Expected: canonical runtime documentation and generated agent surfaces remain aligned.

**Exit Criteria:**
- New Tura release at same path needs no adapter/config edit; operator can identify tested binary and run one documented smoke.

### Task 3: Run bounded conformance admission

**Purpose:**
- Prove shared lifecycle and current Tura compatibility through deterministic and real-boundary evidence.

**Task Function:**
- Execute backend boundary verification and reconcile plan evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: ordinary multi-command validation with external runtime observations and no design ambiguity.

**Validator Profile (optional):**
- Controller-selected: `normal`
- Selection basis: independently check process, Git, route, marker, and receipt evidence.

**Specification Coverage:**
- Tura works as bounded TL worker.
- DeepAgents remains compatible after shared-runner refactor.
- No process leak, tracked mutation, fallback, or 9router change.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/dcode_project.py`
- Verify: `tests/test_dcode_project.py`
- Verify: user-local `project-delegate` and `dcode-project` wrappers
- Verify: configured Tura executable and `TURA_PROVIDER_CONFIG`
- Verify: LightRSI provider/request telemetry

**Dependencies:**
- Tasks 1-2 complete.
- Live environment provides current Tura executable, TL provider file, LightRSI, provider credentials, and network access.

**Authority:**
- Preauthorized local actions: read-only worker probes, process inspection, Git before/after checks, redacted local telemetry inspection.
- Stop for: missing live prerequisites, provider/config mutation, direct-provider fallback, 9router changes, tracked file mutation, credential exposure.

**Steps:**
- [x] Record `git status --short`, Tura configuration readiness, and relevant process baseline.
- [x] Run one read-only Tura `normal` smoke through `project-delegate` with explicit marker and bounded timeout. Marker: `TURA_BOUNDED_WORKER_OK`; exit `0`.
- [x] Verify requested profile/model, `Tura -> LightRSI -> 9router -> provider` route, provider success, marker, opaque child status, and zero descendants. Receipt: `normal -> combo-normal`; provider log `base_url=http://127.0.0.1:17667/v1`; active 9router listener `0.0.0.0:20128`; cached input `28160`; pre-existing `tura_session_db` processes were older than probe.
- [x] Run one equivalent read-only DeepAgents `normal` smoke through `dcode-project` to verify shared-runner compatibility and zero descendants. Marker: `DEEPAGENTS_SHARED_RUNNER_OK`; exit `0`; no matching DeepAgents/LangGraph process remained.
- [x] Confirm final Git status matches baseline and no tracked mutation occurred. Unrelated untracked `db/` preserved.
- [x] Record live prerequisite failure as `BLOCKED`; do not invent fallback or weaken acceptance.

**Verification:**
- [x] `py -m pytest tests/test_dcode_project.py tests/test_native_personal_local_workflow.py -q` — `80 passed`.
- [x] `py scripts/validate_agent_runtime_drift.py --skip-deploy-check` — passed.
- [x] `py scripts/validate_template_required_sections.py` — passed.
- [x] Native process inspection after DeepAgents live probe — no matching DeepAgents/LangGraph descendant remained.
- [x] Native process inspection after Tura live probe — no new Tura worker, DeepAgents, or LangGraph descendants; pre-existing session DB processes retained.

**Exit Criteria:**
- Deterministic suite passes; both live workers complete or an exact external blocker is recorded; Tura TL route and cleanup are proven without 9router or direct-provider changes.

## Verification

- `py -m pytest tests/test_dcode_project.py tests/test_native_personal_local_workflow.py -q`
- `py -m compileall -q scripts/dcode_project.py`
- `py scripts/validate_agent_runtime_drift.py --skip-deploy-check`
- `py scripts/validate_template_required_sections.py`
- `git diff --check`
- Controller review of redacted live marker, route, Git-state, binary-identity, and process-cleanup receipts

No `10x2` efficiency benchmark belongs in this conformance plan. Run a separate
`skill-performance-optimization` plan only when making latency, token, cache, or
billing claims.

## Completion Criteria

The plan is ready for completion verification when:

1. one private process runner owns common Tura and DeepAgents lifecycle behavior
2. both wrappers preserve existing argv, environment, handoff, output, and exit-code contracts
3. Tura normal exit, failure, timeout, and descendant cleanup have automated proof
4. DeepAgents remains compatible under the shared runner
5. `--print-config` exposes nonsecret Tura binary identity from existing config
6. same-path Tura upgrade needs no config or adapter edit
7. one bounded post-upgrade TL smoke is documented and proven for current binary identity
8. no plugin framework, second schema, copied role/provider config, automatic release lookup, fallback route, or 9router change exists
9. final verification commands pass and unrelated `db/` remains untouched

The plan may be marked `completed` only after
`skill-verification-before-completion` runs fresh proof and reconciles the task
ledger, current Git state, blockers, and any recorded deviations.
