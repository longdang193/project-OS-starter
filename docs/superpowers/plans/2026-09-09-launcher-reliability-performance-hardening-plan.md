---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: active
name: launcher-reliability-performance-hardening
targets:
  - repo_config/starter-kit-manifest.json
  - scripts/herdr_main_launcher.py
  - tools/local-patch-hub/Start-OpenDesignMcp.ps1
  - tools/local-patch-hub/README.md
  - tests/test_starter_kit_generation.py
  - tests/test_deploy_agent_runtime.py
  - tests/test_herdr_main_launcher.py
  - tests/test_open_design_local_patch.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
---

# Launcher Reliability And Performance Hardening

## Goal

Remove verified deployment, timeout, launch-ownership, and prompt-state
classification defects from the Herdr/Codex/DeepAgents launch path, then
measure subprocess cost before making performance changes. Preserve worker MCP
isolation, fail-closed delivery semantics, dynamic OpenDesign endpoint
discovery, and unrelated workspace artifacts.

## Follow-Up Ownership

`docs/superpowers/plans/2026-09-09-starter-verdict-follow-up-plan.md` owns
remaining gaps found after this plan’s partial implementation. It does not
remove these requirements:

| Requirement | Owner | Proof |
| --- | --- | --- |
| Attempt identity spans delivery, observation, reconciliation, and retirement | Follow-up Task 3 | attempt ID remains stable across one attempt and changes on retry |
| Completion evidence is attributable; stale, echoed, idle, or blocked output cannot prove success | Follow-up Task 3 | focused state/marker tests and bounded probe |
| Acknowledged delivery and last observed execution facts survive observation failure | Follow-up Task 3 | accepted-task plus unavailable-read test |
| Final selected-pane validation remains immediately before launch | Follow-up Task 3 | launcher test asserts final pane/cwd/process validation |
| OpenDesign readiness deadline is enforced immediately before process start | Follow-up Task 4 | mutex-delay deadline test |
| Validator scan and runtime cleanup changes retain coverage and ownership boundaries | Follow-up Tasks 2 and 4 | explicit-manifest and cleanup-preservation tests |

Pending tasks below remain source requirements until follow-up proof records
which implementation owns each item. Task status alone does not retire a
requirement.
## Implementation Outcomes

### Clean shared deployment

Generated starter-kit deployments contain `scripts/mcp_selection.py` beside
both launchers. A clean deployed bundle imports and runs without relying on the
Starter checkout.

### Bounded and safe launch lifecycle

OpenDesign uses one monotonic startup deadline and bypasses bootstrap locking
when a healthy daemon already exists. Codex name-collision recovery never
retires an unrelated same-name agent, and retries re-resolve target panes after
verified retirement. Codex prompt acceptance is reported separately from task
completion, so a long-running accepted task cannot become a false delivery
failure. Ambiguous prompt timeouts remain unknown and are never replayed
without reconciliation. DeepAgents completion observation never exceeds its
declared deadline because each subprocess call receives the remaining budget.

### Evidence-led optimization

Launcher evidence records phase timings and subprocess counts. Discovery and
observation polling changes preserve final launch validation, completion-marker
validation, process evidence, and MCP isolation. Git/MCP/version optimization
ships only when the captured baseline identifies material cost.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed source, test, manifest, and documentation files; run focused tests, validators, generated-kit builds, and bounded Windows probes; preserve existing uncommitted changes and untracked artifacts
- User-approval actions: live MCP authentication, external configuration writes, process termination outside task-owned probes, commits, pushes, merges, destructive cleanup, or edits outside listed targets
- Parallel ownership: none; launcher, wrapper, manifest, and evidence changes share acceptance contracts
- Sequential fallback: complete deployment proof, run Task 4 classification before Tasks 2–3, then apply OpenDesign/collision fixes, normalize bounded observation, measure optimizations, and run final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `ec97aa2`
- Expected workspace: tracked files clean at `ec97aa2`; preserve untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite them
- Next action: run final focused validators and preserve the verified OpenDesign probe evidence
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | generated kit and clean-bundle import tests | `35 passed`; manifest helper included; kit build and validation passed |
| Task 2 | `completed` | current | `codex` | Task 1 | OpenDesign contract tests and bounded Windows cold/warm probe | `4 passed`; PowerShell parse passed; isolated cold/warm MCP probe passed; readiness uses a fresh status pipe because sidecar IPC is request-scoped; probe-owned descendants cleaned, shared daemon preserved |
| Task 3 | `completed` | current | `codex` | Task 1 | collision and stale-pane regression tests | `87 passed`; verified retry now re-resolves session/pane and refreshes pane evidence before restart |
| Task 4 | `pending` | current | `codex` | Task 1 | Codex acceptance/completion regression tests | implementation proof exists: `85 passed`; no-wait prompt plus bounded `agent get`/`agent read`; completion ledger update pending |
| Task 5 | `pending` | current | `codex` | Tasks 1–4 | observation deadline and polling regression tests | implementation proof exists: `85 passed`; DeepAgents observer uses shared monotonic deadline; expanded timeout proof pending |
| Task 6 | `pending` | current | `unresolved` | Tasks 2–5 | phase timing baseline and measured optimization decision | pending |
| Task 7 | `pending` | current | `unresolved` | Tasks 1–6 | full focused suite, validators, diff, and runtime acceptance | pending |

## Task Breakdown

### Task 1: Repair shared deployment dependency

**Purpose:**
- Make shared launcher deployment self-contained.

**Task Function:**
- Update the canonical manifest and prove generated consumers contain every
  required launcher import.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded manifest and test change with low ambiguity.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: clean-bundle contents and import behavior need independent
  verification.

**Specification Coverage:**
- `scripts/mcp_selection.py` must ship in shared `scripts` paths because both
  launchers import it.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py` import block; `scripts/dcode_project.py` import block; `scripts/deploy_agent_runtime.py` shared-path copier
- Modify: `repo_config/starter-kit-manifest.json`; `tests/test_starter_kit_generation.py`; `tests/test_deploy_agent_runtime.py`
- Verify: `generated_exports/project-OS-starter-kit/scripts/mcp_selection.py`

**Dependencies:**
- Base commit `ec97aa2` and tracked workspace clean.

**Authority:**
- Preauthorized local actions: edit manifest and deployment tests, build the generated kit, and import launcher modules from a temporary clean bundle.
- Stop for: missing generated-source ownership, unrelated tracked changes, or any request to stage/delete `.playwright-mcp/` or `db/`.

**Steps:**
 - [x] Add `scripts/mcp_selection.py` to `sharedPaths.scripts`; keep manifest as the only deployment source of truth.
 - [x] Add regression assertions that generated shared scripts include the helper and that a clean deployed launcher import succeeds.
 - [x] Build and validate the starter kit; inspect generated paths without editing generated output directly.

**Verification:**
 - [x] `py -m pytest tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py -q`
 - Expected: manifest, generated-kit, and clean-bundle import tests pass.

**Exit Criteria:**
- Clean generated bundle contains `scripts/mcp_selection.py`; no launcher import depends on source checkout.

### Task 2: Bound OpenDesign startup and add warm fast path

**Purpose:**
- Prevent cumulative timeout overruns and unnecessary mutex contention.

**Task Function:**
- Refactor existing wrapper discovery/startup flow around one deadline without changing endpoint discovery or daemon ownership semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Windows PowerShell timing and named-pipe behavior require source-first implementation and live proof.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: deadline accounting and concurrent-start behavior need independent checking.

**Specification Coverage:**
- Healthy daemon discovery bypasses bootstrap lock.
- Lock acquisition, recheck, startup, pipe discovery, readiness, and final handoff share one monotonic deadline.
- Final MCP handshake retains configured timeout margin.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `tools/local-patch-hub/Start-OpenDesignMcp.ps1:Find-OpenDesignDaemon`; startup budget and mutex block
- Modify: `tools/local-patch-hub/Start-OpenDesignMcp.ps1`; `tests/test_open_design_local_patch.py`; `tools/local-patch-hub/README.md`; `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: named-pipe discovery, mutex recheck, environment handoff, and startup-timeout documentation

**Dependencies:**
- Task 1 complete.
- Existing `OPEN_DESIGN_MCP_STARTUP_TIMEOUT_SEC` remains configuration input; do not add another timeout registry.

**Authority:**
- Preauthorized local actions: edit wrapper/docs/tests and run bounded local OpenDesign discovery probes without killing shared processes.
- Stop for: daemon termination, authentication, broad timeout increases, or endpoint behavior that cannot be proven from current runtime.

**Steps:**
- [x] Add a monotonic deadline and remaining-milliseconds helper using PowerShell stopwatch timestamps.
- [x] Run `Find-OpenDesignDaemon` before mutex acquisition; pass remaining budget to each pipe connect/read operation.
- [x] Acquire mutex only when no healthy daemon is found, recheck readiness after lock acquisition, start only when still absent, and release mutex in every path.
- [x] Keep readiness below configured client startup timeout and document the single-deadline contract.
- [x] Add contract tests for fast path, shared deadline, bounded pipe calls, recheck, dynamic endpoint handoff, and fresh status connection.

**Verification:**
- [x] `py -m pytest tests/test_open_design_local_patch.py -q`
- [x] Bounded Windows probe: isolated cold OpenDesign startup and successful MCP handoff.
- [x] Bounded Windows probe: wrapper start against healthy daemon; verify no bootstrap wait before handoff.
- Expected: no duplicate daemon launch, no cumulative timeout beyond configured budget, and valid dynamic endpoint variables.

**Exit Criteria:**
- Warm starts skip mutex contention; cold concurrent starts serialize safely; all wrapper work shares one deadline.

### Task 3: Make Codex collision recovery ownership-safe

**Purpose:**
- Prevent unrelated agents from being closed and prevent retries from targeting retired panes.

**Task Function:**
- Narrow recovery to proven launch ownership and re-resolve target state after retirement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: destructive cleanup path requires precise source and test control.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: ownership and fail-closed behavior require independent regression review.

**Specification Coverage:**
- Generated default names are unique before first launch.
- Explicit same-name collision fails without cleanup.
- Verified owned retirement re-resolves session/pane before retry.
- Uncertain ownership remains fail-closed.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_reconcile_failed_codex_start`; `scripts/herdr_main_launcher.py:_unique_agent_name`; `scripts/herdr_main_launcher.py:resolve_launch` retry loop
- Modify: `scripts/herdr_main_launcher.py`; `tests/test_herdr_main_launcher.py`
- Verify: pane list/process evidence, cleanup verification, retry target resolution, assignment evidence

**Dependencies:**
- Task 1 complete.
- Preserve `reconciliation_required` and no-auto-kill behavior for transport uncertainty.

**Authority:**
- Preauthorized local actions: edit launcher and focused tests; use mocked Herdr responses and bounded task-owned pane probes.
- Stop for: process termination outside explicitly task-owned test lanes, uncertain attempt ownership, or retry after unverified cleanup.

**Steps:**
- [x] Generate unique names for launcher-created agents before the first `agent start`.
- [x] When caller supplies `--name` and Herdr returns `agent_name_taken`, return conflict evidence without invoking pane cleanup.
- [x] Keep cleanup allowed only for a verified owned failed attempt; after successful retirement call `_resolve_target_selector` again and refresh pane evidence before retry.
- [x] Preserve evidence updates for the final agent name, target, retry, and reconciliation result.
- [x] Add tests for unrelated same-name agent preservation, unique default names, stale-pane re-resolution, verified cleanup, and uncertain cleanup.

**Verification:**
- [x] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: same-name collision never calls `_terminate_codex_lane`; verified owned retry uses a newly resolved pane; uncertain state returns fail-closed evidence. Confirmed by `87 passed`.

**Exit Criteria:**
- No recovery path retires an agent based only on matching name; no retry uses a pane proven unavailable.

### Task 4: Separate Codex prompt acceptance from task completion safely

**Purpose:**
- Prevent long-running accepted Codex tasks from being reported as failed delivery when the prompt command times out while waiting for completion.

**Task Function:**
- First correct current `--wait` classification, then move Codex to prompt submission plus separate `agent get`/`agent read` observation only after the acceptance contract is proven.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct state-classification bug with existing Herdr observation commands and clear regression behavior.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: acceptance, progress timeout, and completion evidence must remain distinct.

**Specification Coverage:**
- `herdr agent prompt` submission is an acceptance barrier, not a task-completion barrier.
- While `--wait` remains, known pre-submission rejection reports `prompt_accepted: false`; timeout, connection loss, and other phase-ambiguous errors report `prompt_accepted: null`.
- Prompt success reports `submission: acknowledged` and accepted delivery even when later task progress times out.
- Completion is tracked separately through Herdr status/output observation.
- A prompt transport failure remains uncertain and fail-closed; a task-progress timeout is not relabeled as delivery failure.
- Submission, execution, observation, result, and cleanup use separate lifecycle fields; `blocked` and `idle` are not task success, and cancellation request is not verified retirement.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_codex_assignment_command`; `scripts/herdr_main_launcher.py:main` Codex assignment branch; Herdr `agent prompt`, `agent get`, and `agent read` command contracts
- Modify: `scripts/herdr_main_launcher.py`; `tests/test_herdr_main_launcher.py`; `docs/operating_system/runtime/runtime-surfaces.md`; `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Verify: accepted delivery evidence, progress status/read evidence, timeout classification, and retry/reconciliation state

**Dependencies:**
- Task 1 complete. Run this classification patch before Tasks 2 and 3.
- Existing task-progress budget remains separate from prompt submission; dispatch
  must not wait for task completion or reuse completion timeout as delivery status.

**Authority:**
- Preauthorized local actions: edit launcher/docs/tests and run mocked Herdr acceptance/completion tests plus one bounded long-task probe in a task-owned lane.
- Stop for: treating silence as completion, auto-retrying accepted work, weakening transport-uncertainty handling, or changing Herdr semantics outside the launcher contract.

**Steps:**
- [ ] Add a structured Herdr response decoder for `agent prompt`; classify known pre-submission rejection as false and `timeout`, connection loss, `agent_prompt_failed`, and malformed/ambiguous responses as unknown unless phase evidence proves rejection before submission.
- [ ] Preserve `reconciliation_required` and forbid automatic replay whenever prompt acceptance is unknown; do not classify every Herdr `timeout` as completion timeout because Herdr uses that code for submission and wait failures.
- [ ] Generate an attempt identifier at launch and bind it to assignment evidence, reconciliation, status observation, and retirement; task and grant hashes remain content evidence, not attempt identity.
- [ ] Keep `--wait` during classification patch and prove state mapping with mocked structured responses before changing the command barrier.
- [ ] Remove `--wait` and task-duration `--timeout` from Codex prompt submission only after acceptance proof exists; retain a separate task-progress budget for completion observation.
- [ ] Rename the current 30-second prompt timeout constant to a task-progress timeout and apply that budget to the separate Codex completion observer, while allowing explicit wall-clock grants to override it under existing rules.
- [ ] Add a separate bounded Codex completion snapshot using `agent get` for status and `agent read` for output; keep it non-blocking in dispatch and apply the task-progress budget per observation call.
- [ ] Emit compact lifecycle fields: submission `acknowledged|rejected|unknown`, execution `running|blocked|terminal|unknown`, observation `available|timed_out|unavailable`, result `verified_success|verified_failure|unknown`, and cleanup `not_requested|verified|unverified`.
- [ ] Preserve last observed execution state and observation timestamps; an observation failure cannot rewrite an earlier acknowledgment or execution fact.
- [ ] Require attributable task-specific completion and verification evidence; a marker or echoed terminal text alone cannot prove success, `blocked`, `idle`, silence, and cancellation request cannot produce success, and a fast task need not expose an observed `working` transition.
- [ ] Add focused tests for accepted task beyond 30 seconds, known rejection, ambiguous timeout, lost acknowledgment, blocked worker, execution failure after acceptance, stale idle/output, echoed completion marker, `agent get/read` failure, and deadline cancellation with failed cleanup.

**Verification:**
- [ ] `py -m pytest tests/test_herdr_main_launcher.py -q`
- [ ] Herdr contract check: `herdr agent prompt --help`, `herdr agent get --help`, and `herdr agent read --help` confirm separate submission and observation commands.
- [ ] Bounded classification probe while `--wait` remains: ambiguous Herdr timeout reports `prompt_accepted: null` and no replay.
- [ ] Bounded long-task probe after separate observation is implemented: prompt acceptance remains true; any progress timeout is reported as completion timeout, not delivery failure.
- Expected: acceptance reflects submission evidence only; completion fields reflect task progress only; ambiguous state never becomes false acceptance or duplicate dispatch.

**Exit Criteria:**
- A prompt accepted by Herdr cannot be classified as undelivered solely because worker completion exceeds the prompt command timeout.

### Task 5: Normalize bounded observation across executors

**Purpose:**
- Make the 60-second completion-observation contract real, preserve prior lifecycle facts, and apply the same evidence rules to Codex and DeepAgents without adding a new service.

**Task Function:**
- Bound every observation subprocess call by remaining deadline and normalize executor-specific launch, execution, result, and cleanup evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: localized polling change with explicit failure semantics.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: deadline and false-success behavior need independent validation.

**Specification Coverage:**
- Observation deadline includes subprocess execution time.
- Process evidence and expected completion marker remain mandatory.
- Observation timeout never becomes success and never triggers unsafe retry.
- `agent start` and `pane run` distinguish request issued, process observed, readiness/execution observed, result evidence, and cleanup; readiness or observation timeout does not imply request rejection.
- Blocked execution remains active state; cancellation requested remains unverified until retirement is proven.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`; `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`; Codex start/assignment branches
- Modify: `scripts/herdr_main_launcher.py`; `tests/test_herdr_main_launcher.py`; `docs/operating_system/runtime/runtime-surfaces.md`
- Verify: completion evidence state, observation errors, marker validation, timeout classification

**Dependencies:**
- Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: edit launcher/docs/tests and run mocked completion-observation tests plus bounded pane probes.
- Stop for: weakening marker/process validation, automatic retry after observation uncertainty, or replacing evidence with unverified Herdr wait semantics.

**Steps:**
- [ ] Create one monotonic observation deadline in `_deepagents_completion_evidence`.
- [ ] Pass remaining timeout to both `process-info` and `pane read`; return bounded observation evidence when budget expires.
- [ ] Poll process state every second and terminal output every 2–3 seconds; read output immediately after process exit.
- [ ] Require valid process evidence, no observation error, and attributable task evidence before success; completion markers support correlation but cannot prove success alone.
- [ ] Preserve prior submission acknowledgment and last observed execution state when later observation fails; record observation timestamps and separate cleanup state.
- [ ] Apply equivalent phase fields to Codex `agent start` and DeepAgents `pane run` without requiring a `working` transition.
- [ ] Add tests for slow subprocesses, process exit without marker, delayed marker, read failure, stale output, echoed marker, blocked state, and observation deadline expiry.

**Verification:**
- [ ] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: no observation command runs past remaining budget; invalid or incomplete reports remain non-success.

**Exit Criteria:**
- DeepAgents observation honors its deadline and preserves fail-closed completion semantics.

### Task 6: Add evidence, then apply measured reductions

**Purpose:**
- Establish comparable performance evidence before changing Git, discovery, MCP, or version subprocess behavior.

**Task Function:**
- Instrument existing launcher evidence and make only reductions supported by measured cost.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: performance work requires baseline, workload, metric, and threshold before optimization.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: timing comparability and correctness preservation need independent review.

**Specification Coverage:**
- Existing evidence records preflight, target discovery, worker initialization, assignment acknowledgment, retirement, and subprocess counts.
- Discovery keeps final selected-pane validation.
- MCP discovery remains fresh; version caching requires executable/environment invalidation.
- Git consolidation preserves identity validation and error handling.

**Required Skills:**
- `skill-performance-optimization`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`; existing evidence output; `_git_identity`; `_codex_runtime_mcp_servers`; `_version`; `_resolve_target_selector`
- Modify: `scripts/herdr_main_launcher.py`; `tests/test_herdr_main_launcher.py`
- Verify: JSON evidence fields, subprocess counts, phase timing monotonicity, selection freshness

**Dependencies:**
- Tasks 2–5 complete.
- Capture baseline before optimization using identical Windows workload and environment.

**Authority:**
- Preauthorized local actions: add bounded evidence fields and make measured local optimizations within launcher/test files.
- Stop for: persistent cache, new scheduler/registry, removal of final pane validation, or optimization without baseline evidence.

**Steps:**
- [ ] Record five phase durations and relevant subprocess counts in existing launcher evidence; do not add a parallel metrics store.
- [ ] Capture baseline for concurrency `1` and `2`, cold and warm OpenDesign, with worker correctness and retirement checks.
- [ ] Reduce observation/discovery subprocess work only where baseline shows material cost; retain final pane check and completion proof.
- [ ] Consolidate compatible Git queries only if process startup dominates; preserve exact worktree, branch, HEAD, common-dir, and expected-base validation.
- [ ] Keep MCP listing fresh; reuse version evidence only when executable path and runtime environment match captured evidence.

**Verification:**
- [ ] Run identical baseline and candidate probes; compare phase timing, subprocess count, overlap-after-ack, MCP child count, and retirement outcome.
- Expected: no correctness regression; any performance claim names workload, environment, metric, and observed delta.

**Exit Criteria:**
- Evidence supports each shipped optimization, or the optimization is explicitly deferred without speculative cache/orchestration code.

### Task 7: Final verification and handoff

**Purpose:**
- Reconcile source, tests, generated kit, documentation, and runtime evidence.

**Task Function:**
- Run fresh final proof and record deviations without changing unrelated workspace state.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification-only task.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: final diff and proof review.

**Specification Coverage:**
- All implementation outcomes and preserved invariants in this plan.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all task-owned diffs, generated kit, runtime evidence, and plan ledger
- Modify: task ledger/evidence only when proof is accepted or a deviation is recorded
- Verify: repository status, generated drift, focused tests, validators, and diff integrity

**Dependencies:**
- Tasks 1–6 complete with task-local proof.

**Authority:**
- Preauthorized local actions: run final tests, validators, kit build/check, diff inspection, and bounded evidence reconciliation.
- Stop for: failed required proof, stale plan state, unrelated tracked changes, destructive cleanup, commit, push, or merge.

**Steps:**
- [ ] Run focused launcher, OpenDesign, deployment, and MCP tests.
- [ ] Build and validate starter kit; run adapter/runtime drift checks.
- [ ] Run repository contract/config validators and `git diff --check`.
- [ ] Confirm `.playwright-mcp/` and `db/` remain untouched and untracked.
- [ ] Update task ledger evidence; leave plan `proposed` until execution is explicitly authorized and completed verification returns `verified`.

**Verification:**
- [ ] `py -m pytest tests/test_mcp_selection.py tests/test_herdr_main_launcher.py tests/test_open_design_local_patch.py tests/test_starter_kit_generation.py tests/test_deploy_agent_runtime.py -q`
- [ ] `py scripts/build_starter_kit.py`
- [ ] `py scripts/validate_starter_kit.py`
- [ ] `py scripts/validate_repo_contracts.py --repo-root . --fast`
- [ ] `py scripts/validate_repo_config.py --repo-root .`
- [ ] `py scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`
- [ ] `py scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `git diff --check`
- Expected: all required checks pass; final evidence contains no unsupported performance claim.

**Exit Criteria:**
- Fresh verification is accepted, plan deviations are recorded, generated surfaces match SSOT, and unrelated artifacts remain preserved.

## Non-Goals

- No new MCP registry, provider classification, scheduler, resource manager, or janitor.
- No persistent MCP/version cache without an explicit invalidation boundary and measured benefit.
- No broad timeout increase.
- No concurrent candidate inspection unless baseline proves discovery is a material bottleneck and final validation remains equivalent.
- No generic process cleanup, retry after uncertain ownership, or retry after observation uncertainty.
- No live MCP authentication or external configuration writes as part of implementation.

## Verification

- Focused test suite listed in Task 7.
- Starter-kit build and validation.
- Repository contract/config/runtime drift validators.
- Adapter drift check.
- `git diff --check`.
- Bounded Windows probes for OpenDesign cold/warm startup, collision recovery, completion observation deadlines, concurrency `1`/`2`, MCP child counts, and owned retirement.

## Completion Criteria

1. Clean shared deployment contains `scripts/mcp_selection.py` and imports both launchers successfully outside the Starter checkout.
2. OpenDesign warm path bypasses bootstrap mutex; cold concurrent starts use one startup owner and one shared monotonic deadline.
3. Codex collision recovery never closes unrelated same-name agents and re-resolves targets after verified retirement.
4. Codex prompt acceptance and task completion are separate evidence states; accepted long tasks are not reported as delivery failures, and ambiguous timeouts remain unknown without replay.
5. Every launch attempt carries an attempt identifier across assignment, observation, reconciliation, and retirement; task/grant hashes remain content evidence only.
6. DeepAgents completion observation bounds every subprocess call and requires valid process evidence plus expected marker for success.
7. Evidence records five phase timings and subprocess counts for comparable workloads.
8. Discovery retains final selected-pane validation; MCP discovery remains fresh; version/Git reductions are measurement-backed.
9. Focused tests, validators, generated-kit checks, adapter drift checks, and bounded runtime probes pass.
10. Existing untracked `.playwright-mcp/` and `db/` artifacts remain unchanged.
11. No commit, push, merge, destructive cleanup, or unrelated change occurs without explicit authorization.
