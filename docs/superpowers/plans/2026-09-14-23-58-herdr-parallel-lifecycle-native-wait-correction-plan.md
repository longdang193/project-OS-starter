---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: herdr-parallel-lifecycle-native-wait-correction
parent_spec: docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
targets:
  - scripts/herdr_parallel_dispatch.py
  - scripts/herdr_main_launcher.py
  - scripts/dcode_project.py
  - tests/test_herdr_parallel_dispatch.py
  - tests/test_herdr_main_launcher.py
  - tests/test_dcode_project.py
  - docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md
  - README.md
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/planning/planning-dispatch.md
---

# Herdr Parallel Lifecycle And Native Wait Correction

## Goal

Correct the bounded parallel-dispatch pilot so capacity retirement, attempt
correlation, and executor admission remain conservative, then replace repeated
DeepAgents marker polling with Herdr 0.9.0 native waits where the existing
launcher transport can use them. Keep receipts, process ownership, pane
evidence, and CoS acceptance authoritative. Add no supervisor, durable runtime
ledger,
revision-cursor API, Starter-side request ledger, raw socket client, or
automatic retry engine.

## Implementation Outcomes

### Conservative lane retirement

`run_lane()` no longer treats launcher exit code or assignment presence as
retirement proof. It preserves occupied capacity and unresolved evidence until
execution and task-owned cleanup settle, or until an explicit pre-launch failure
proves that no worker started. Task-result uncertainty may remain unresolved
without being confused with live resource ownership.

### Attempt-safe DeepAgents pilot

The parallel helper admits only `deepagents` lanes during the current pilot,
rejects preparation/final assignment attempt mismatches, preserves both raw
records for diagnosis, and never lets malformed or foreign evidence retire a
lane.

### Native wait-assisted observation

The launcher may use `pane wait-output` for bounded DeepAgents marker
observation after a compatibility gate. The Codex completion path remains
non-blocking; `_codex_completion_snapshot()` has no production caller and is
not wired to `agent wait` in this change. Receipt checks, process/descendant
checks, pane reads, and reconciliation remain required. Wait timeout or wait
success never proves task acceptance, cleanup, or safe retry. Existing bounded
pull probes remain the compatibility fallback when a wait command is
unavailable or fails at transport level. `agent wait` remains a verified Herdr
capability and documented lifecycle option, not a required launcher change.

### Aligned maintained contracts

Active runtime, planning, procedure, README, and specification text describes
wait-assisted observation and fail-closed numeric Codex wall-clock grants.
Dated completed plans remain historical evidence and are not rewritten.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Execution model: `plan-bound-execution via CoS`
- Lead controller: native Codex; sole writer of `Coordination State` and task ledger
- Top-level dispatch: CoS assigns Herdr MAIN AGENT lanes; MAIN AGENTS own lane execution and evidence, but cannot change plan state or activate CoS
- Required skills: `skill-chief-of-staff`, `skill-dispatching-parallel-agents`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`, `skill-using-git-worktrees`
- Isolation: one dedicated worktree per write-capable MAIN AGENT from `c74ab34cad850d998e88f6c517e7156f5f4cd83c`; preserve lead-workspace untracked `.playwright-mcp/` and `db/`
- Commit policy: no commits during plan drafting; lane commits are implementation artifacts; lead creates one checkpoint after accepting proof and updating ledger; no push or merge authority
- Preauthorized local actions: create the declared implementation worktree, inspect and edit listed source/test/docs files, run listed tests and Herdr help/schema checks, and record proof in this plan
- Approval gate: user approves this proposed plan before lead changes status to `active` and dispatches the first write-capable MAIN AGENT; after activation, lane writes remain bounded by task authority and isolated worktrees
- User-approval actions: push, merge, publication, destructive recovery, discard, cleanup outside the task-owned implementation worktree, or mutation of `.playwright-mcp/` and `db/`
- Parallel ownership: Task 2 owns dispatcher source plus `tests/test_herdr_parallel_dispatch.py`; Task 3 owns launcher source plus `tests/test_herdr_main_launcher.py`; Task 4 owns active spec/docs; no shared write paths inside a wave
- Wave order: Tasks 1 and 6 run in parallel; Task 2 follows accepted Task 1; Task 3 follows accepted Task 1 and Task 6; Task 4 follows accepted Tasks 2–3, including an accepted Task 3 deferral; Task 5 is serialized Codex review, integration, and final verification
- Review/integration: Codex-only; no MAIN AGENT merges another lane or writes coordination state
- Sequential fallback: if native wait behavior is unavailable or incompatible, retain existing bounded pull probes and stop before adding raw socket transport or revision-cursor state

## Coordination State

- Coordination owner: `native Codex lead controller / CoS`
- Coordination mode: `plan-bound-execution`
- MAIN AGENT transport: `Herdr`
- Coordination schema: `2`
- Branch: `codex/herdr-parallel-lifecycle-native-waits`
- Base commit: `c74ab34cad850d998e88f6c517e7156f5f4cd83c`
- Expected workspace: dedicated implementation worktree from the base commit; lead workspace preserves untracked `.playwright-mcp/` and `db/`
- Next action: none; implementation and verification complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated worktree; Wave 0 baseline/contract lane | `codex` | none | focused baseline and red regression cases | Accepted commit `01997c2ae77a890a97c26974011ec2dc72cffdcc`; baseline `146 passed`; focused contract run `149 passed, 10 intentional red`; worktree clean |
| Task 6 | `completed` | isolated worktree; Wave 0 runtime-debug lane | `codex` | none | root-cause proof and focused runtime regression, or documented external blocker | Accepted external blocker: host pane probe matched CWD/Git root/HEAD; `_native_file_tool_root` matches documented `/Users/<user>/...` Windows contract; `tests/test_dcode_project.py` `122 passed`; clean worktree; no patch justified; DeepAgents virtual-mount/no-report remains external |
| Task 2 | `completed` | isolated worktree; Wave 1 dispatcher lane | `codex` | Task 1 | dispatcher lifecycle and admission tests | Accepted commit `827d4007cb72f4212775e3008144ac1e396597d2`; `23 passed`; diff clean; DeepAgents attempt timed out with no report and clean Git; Codex rebind completed on pane `w3G:p1` |
| Task 3 | `completed` | isolated worktree; Wave 1 launcher wait lane | `codex` | Tasks 1 and 6 | launcher wait/fallback tests and Herdr contract smoke | Accepted commit `2946d295ca90d95b0a5e965822e6e0b80eb5f5d4`; launcher suite `138 passed`; wait subset `4 passed`; Herdr `0.9.0`, help, and schema checks pass; clean worktree |
| Task 4 | `completed` | isolated worktree; Wave 2 active-docs lane | `codex` | Tasks 2–3 | active docs/spec consistency inspection | Accepted commit `47c2b3e`; seven docs updated; `git diff --check` passed; stale-claim search clean; Codex rebind completed on pane `w3J:p1` |
| Task 5 | `completed` | lead worktree; Wave 3 Codex review/integration lane | `codex` | Task 4 | full focused and repository verification | Integrated commits `01997c2`, `827d400`, `2946d29`, `47c2b3e`; focused `285 passed`; full `570 passed`; contract validation passed; Herdr capability checks passed; unrelated `.playwright-mcp/` and `db/` preserved |

CoS dispatches only dependency-ready waves. Executor/profile resolution:
Task 1 uses `codex` with profile `normal` after its DeepAgents attempt was
blocked by a virtual-mount mismatch. Task 6 uses `codex` with profile `high`
for runtime debugging. Tasks 2–4 use `deepagents` with profiles `high`, `high`,
and `normal` only if their assigned worktrees pass host-Git write verification;
otherwise CoS rebinds each task to `codex`. Task 5 uses native Codex lead
control with profile `none (lead controller)`.
MAIN AGENT handoff must include changed paths,
task-local proof, remaining uncertainty, and blocker state. Lead accepts or
rejects that evidence, then alone updates this ledger and creates checkpoints.

## Task Breakdown

### Task 1: Establish failing lifecycle and native-wait cases

**Purpose:**
- Turn verified verdict defects into executable regression cases before changing behavior.

**Task Function:**
- Build boundary-level regression proof for dispatcher retirement and Herdr observation contracts.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: routine bounded test work; resolve profile when execution activates.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused tests provide direct proof.

**Specification Coverage:**
- Covers attempt-correlated evidence, bounded lifecycle, honest uncertainty, and safe retry requirements in the parent spec.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:parse_launcher_records`, `scripts/herdr_parallel_dispatch.py:run_lane`, `scripts/herdr_parallel_dispatch.py:_admit_lanes`
- Modify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`
- Verify: `tests/test_herdr_parallel_dispatch.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Base commit remains `c74ab34cad850d998e88f6c517e7156f5f4cd83c`.
- Preserve existing untracked lead-workspace paths; do not include them in the worktree or test fixture changes.
- Lead records a compact baseline/contract matrix in the task handoff before dispatching Wave 1.

**Authority:**
- Preauthorized local actions: edit only the two named test files and run focused Python tests plus mocked subprocess checks.
- Stop for: changed lifecycle semantics not covered by the parent spec, live worker execution, or any required new runtime/API contract.

**Steps:**
- [x] Step 1: Add a test where launcher exits `0` without final assignment; expect `unresolved=True` and `capacity="occupied"`.
- [x] Step 2: Add a test with final assignment present but execution `unknown`, cleanup `unverified`, or ownership reconciliation required; expect unresolved evidence and occupied capacity.
- [x] Step 3: Add tests for a valid settled assignment, explicit pre-launch `launch_failed`, direct unsupported-executor rejection, mapping-input admission bypass rejection, and preparation/final attempt mismatch.
- [x] Step 4: Add launcher tests that capture gated `pane wait-output` command construction, bounded timeout behavior, and fallback behavior without upgrading uncertainty to success; do not require production `agent wait` calls.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: new regression cases fail only where implementation is not yet corrected; existing tests remain otherwise unchanged.

**Exit Criteria:**
- Every verified defect and native-wait contract has a named failing or boundary test with exact expected state.

### Task 6: Diagnose and harden DeepAgents host-worktree boundary

**Purpose:**
- Find why DeepAgents edits landed in a virtual filesystem while host Git and pytest saw a clean worktree, then patch the repository boundary only when source evidence proves ownership.

**Task Function:**
- Perform systematic debugging, trace shared callers and path propagation, and add focused regression proof for any repository-owned fix.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: runtime-boundary failure with potential cross-component cause; use Codex MAIN lane for host filesystem evidence.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent root-cause and regression review.

**Specification Coverage:**
- Covers write-capable lane evidence, host Git identity, worktree ownership, and fail-closed runtime behavior.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py`, `scripts/herdr_main_launcher.py`, shared `~/.agents/project-os/scripts/dcode_project.py`, `tests/test_dcode_project.py`, and launcher/runtime evidence from failed Task 1 attempt
- Modify: `scripts/dcode_project.py`, `tests/test_dcode_project.py` only when root cause is repository-owned
- Verify: focused dcode-project tests, host Git status, and one bounded Herdr reproduction

**Dependencies:**
- Failed DeepAgents Task 1 evidence is the initial reproduction; Task 1 Codex redispatch may continue independently.
- Do not edit Task 1 test files or Task 3 launcher files in this lane.

**Authority:**
- Preauthorized local actions: read runtime and repository source, reproduce in this isolated worktree, modify only declared dcode-project files, and run focused tests.
- Stop for: external-only defect, missing root-cause proof, host/worktree identity ambiguity, or any fix requiring changes outside declared ownership.

**Steps:**
- [x] Step 1: Reproduce the failed DeepAgents dispatch and record exact agent-visible path, host-visible path, Git root, `HEAD`, file writes, and result receipt state.
- [x] Step 2: Trace `dcode-project` wrapper/runtime path propagation and compare with recent Git history and existing tests; identify shared callers and same-defect surfaces before proposing a fix.
- [x] Step 3: If repository-owned, implement the smallest fail-closed fix and add a focused regression test; if external-only, leave source unchanged and record concrete remediation needed from runtime owner.
- [x] Step 4: Run focused tests and one bounded reproduction; report root cause, patch or external blocker, changed paths, commit SHA, and residual risk.

**Verification:**
- [x] `python -m pytest -q tests/test_dcode_project.py`
- Expected: focused runtime-boundary tests pass, or exact external blocker is recorded without claiming a fix.
- [x] `git status --short --branch`
- Expected: only declared lane files change; host Git observes same changes as agent runtime.

**Exit Criteria:**
- Root cause is proven and patched with regression proof, or external ownership is proven and documented as a blocker for CoS acceptance.

### Task 2: Correct dispatcher retirement, correlation, and pilot admission

**Purpose:**
- Make capacity state depend on resource retirement evidence instead of process exit or assignment presence.

**Task Function:**
- Implement conservative lane result classification at the dispatcher boundary.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: cross-field lifecycle reasoning with high correctness impact; resolve profile when execution activates.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: focused dispatcher tests and final backend verification.

**Specification Coverage:**
- Covers safe admission, attempt-safe evidence, bounded capacity, uncertain retry blocking, and sibling evidence preservation.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `scripts/herdr_parallel_dispatch.py:parse_launcher_records`, `scripts/herdr_parallel_dispatch.py:run_lane`, `scripts/herdr_parallel_dispatch.py:run_parallel`
- Modify: `scripts/herdr_parallel_dispatch.py:_admit_lanes`, `scripts/herdr_parallel_dispatch.py:parse_launcher_records`, `scripts/herdr_parallel_dispatch.py:run_lane`
- Verify: `tests/test_herdr_parallel_dispatch.py`

**Dependencies:**
- Task 1 tests define exact expected states.
- Existing `capacity` and `unresolved` fields remain public compatibility fields.

**Authority:**
- Preauthorized local actions: modify only dispatcher implementation and its focused tests; preserve tagged JSONL shape and two-lane limit.
- Stop for: new persistent coordination state, a second lifecycle schema, automatic cleanup/retry, or changes to launcher receipt ownership.

**Steps:**
- [x] Step 1: Reject any lane whose `executor` is not exactly `deepagents` before write-capable launch; preserve deterministic rejection reason.
- [x] Step 2: Make parser retain preparation and final records but refuse to treat a final assignment as valid when its `attempt_id` is missing or differs from preparation evidence; preserve foreign/malformed evidence for diagnostics.
- [x] Step 3: Close both admission bypasses: validate mapping input with an existing `admitted` list in `run_parallel()` and reject unsupported direct `run_lane()` input before launch.
- [x] Step 4: Add one local classifier in `run_lane()` that separates `capacity` from overall `unresolved`: retire only on explicit pre-launch failure or settled execution plus settled descendants/cleanup; keep unknown, running, preserved, unverified, and missing final evidence occupied.
- [x] Step 5: Keep task-result uncertainty separate from resource lifetime: settled resources may retire capacity while unresolved task evidence still sets `unresolved=True` and nonzero coordinator status; do not require `task_result.accepted == true` for resource retirement.
- [x] Step 6: Repair weak `status: completed` fixtures so status cannot stand in for settled process/cleanup evidence; preserve sibling results, timeout occupancy, tagged records, and launch-failure behavior.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py`
- Expected: valid settled assignment retires; missing/mismatched/uncertain evidence stays unresolved; Codex lane is rejected; timeout remains occupied; sibling evidence survives.

**Exit Criteria:**
- Dispatcher never retires a potentially active or foreign attempt from exit code, assignment presence, or malformed evidence alone.

### Task 3: Gate DeepAgents native waits without weakening evidence rules

**Purpose:**
- Use installed Herdr wait primitives to reduce repeated polling while keeping current reconciliation and compatibility behavior.

**Task Function:**
- Replace repeated DeepAgents marker sleeps with a compatibility-gated bounded native wait at the existing launcher observation boundary; leave Codex completion non-blocking.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: runtime command integration with fallback and timeout semantics; resolve profile when execution activates.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: mocked command capture plus local Herdr help/schema smoke.

**Specification Coverage:**
- Covers bounded observation, delivery/completion separation, receipt correlation, timeout uncertainty, and no automatic acceptance/retry.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_codex_completion_snapshot`, `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`, `scripts/herdr_main_launcher.py:_run`, `scripts/herdr_main_launcher.py:_result`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `scripts/herdr_main_launcher.py:_deepagents_completion_evidence`
- Verify: `tests/test_herdr_main_launcher.py`, local `herdr` command surface

**Dependencies:**
- Task 1 command-capture tests exist.
- Task 6 host-worktree boundary investigation is accepted; consume its patch or documented external limitation before changing launcher observation behavior.
- Local Herdr reports `0.9.0`; CLI commands are `agent wait` and `pane wait-output`; only the latter is a required implementation candidate for this launcher path.
- Existing `_run` remains the subprocess boundary; do not add a socket client.

**Authority:**
- Preauthorized local actions: modify launcher observation helpers and focused tests; run `herdr --version`, command help, and bundled schema inspection.
- Stop for: missing wait semantics, live write-capable worker execution, raw socket transport, revision cursor state, or acceptance/retry changes.

**Steps:**
- [x] Step 1: Gate `pane wait-output` compatibility before using it; if command shape, marker semantics, or transport behavior cannot be proven, accept the task with existing pull probes unchanged and record the deferral.
- [x] Step 2: Define observation ordering as receipt read, bounded wait only when marker is not already present, receipt reread, then process/descendant and pane probes; skip repeated waits for an already-present marker.
- [x] Step 3: Bound every wait and probe by absolute observation and settlement deadlines; convert timeout/transport failure to explicit observation uncertainty without upgrading state.
- [x] Step 4: Retain receipt grace handling because file receipts do not necessarily wake Herdr waits; add proof for the actual post-`pane run` settlement path and stale-marker behavior.
- [x] Step 5: Do not add production `agent wait`, `events.subscribe`, or `events.wait` calls to this launcher change; verify `agent wait` as installed capability only, and keep direct socket transport as separate future work.

**Verification:**
- [x] `herdr --version`
- Expected: output contains `herdr 0.9.0` or a newer compatible version.
- [x] `herdr agent wait --help`
- Expected: help exposes `--until` and `--timeout`.
- [x] `herdr pane wait-output --help`
- Expected: help exposes `--match` or `--regex` and `--timeout`.
- [x] `herdr api schema --json | rg 'agent\.wait|pane\.wait_for_output'`
- Expected: both native wait methods remain present; `events.subscribe` and `events.wait` are informational, not mandatory acceptance checks.
- [x] `python -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: gated wait success, wait timeout, fallback, receipt delay, stale output, post-`pane run` settlement, and unknown-state tests pass without any new acceptance path; an accepted compatibility deferral keeps pull-probe tests green.

**Exit Criteria:**
- Launcher observation uses native target/output waits when available, retains bounded pull/reconciliation evidence, and never upgrades wait completion into task acceptance or safe retry.

### Task 4: Align active specification and operating documentation

**Purpose:**
- Remove contradictory watchdog/polling claims and document the actual native wait boundary.

**Task Function:**
- Reconcile maintained contract text with launcher behavior and Herdr 0.9.0 capability evidence.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded canonical documentation update; resolve profile when execution activates.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: source/doc consistency inspection.

**Specification Coverage:**
- Covers runtime-surface ownership, no unsupported watchdog claims, wait-as-signal semantics, and preserved CoS acceptance authority.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/superpowers/specs/2026-09-14-parallel-deepagents-dispatch-spec.md:Current State and Evidence`, `README.md:Herdr controller visibility`, `docs/operating_system/runtime/runtime-surfaces.md`, `docs/operating_system/tooling/runtime-tool-resolution.md`, `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/procedures/personal-local-worktree-procedure.md`, `docs/operating_system/planning/planning-dispatch.md`
- Modify: all inspected active maintained files listed above
- Verify: `docs/superpowers/plans/` dated completed plans remain unchanged

**Dependencies:**
- Tasks 2–3 establish final field names, wait fallback behavior, and runtime ownership.
- Task 3 may complete as an explicit native-wait deferral when compatibility proof fails; Task 4 must document that result instead of claiming integration.
- Historical dated plans are evidence, not active canonical instructions.

**Authority:**
- Preauthorized local actions: edit only active maintained docs and the parent spec; preserve generated agent surfaces and historical completed plans.
- Stop for: a required generated-surface sync, contradictory canonical source, or a proposed public/private boundary change.

**Steps:**
- [x] Step 1: Update the active spec to record native target/output waits as available observation capabilities, while retaining the no-generic-revision-cursor and no-atomic-delivery conclusions.
- [x] Step 2: Replace pull-only wording with wait-assisted observation followed by pull-based proof only where Task 3 accepted integration; otherwise document pull probes as the compatibility path.
- [x] Step 3: Document `agent wait` and `pane wait-output` as bounded inspection signals, while stating that current launcher integration is DeepAgents-only if Task 3 accepted it; receipts, process/cleanup evidence, reconciliation, and CoS acceptance remain authoritative.
- [x] Step 4: Remove active claims that numeric Codex wall-clock grants use a Herdr watchdog; state fail-closed behavior matching `_normalize_runtime_grant()`.
- [x] Step 5: Do not rewrite dated completed plans or add a docs generator.

**Verification:**
- [x] `rg -n -i 'numeric Codex wall-clock grants use|numeric Codex wall-clock values use|pull-based' README.md docs/operating_system`
- Expected: no active text claims unsupported numeric Codex watchdog enforcement; remaining pull wording explicitly allows native waits or refers to historical behavior.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Maintained docs, active spec, and executable launcher agree on wait capability, watchdog rejection, and evidence authority.

### Task 5: Run final verification and reconcile scope

**Purpose:**
- Prove corrected behavior across focused tests, full tests, CLI capability, and final diff.

**Task Function:**
- Perform final backend verification and plan-integrity review.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification and evidence reconciliation; resolve profile when execution activates.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independent plan/document review required before activation or handoff.

**Specification Coverage:**
- Covers all parent-spec completion criteria plus corrected native-wait capability wording.

**Required Skills:**
- `skill-plan-document-reviewer`
- `skill-verification-before-completion`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: all plan targets and current Git status
- Modify: none unless verification identifies an in-scope defect
- Verify: all plan targets and exact base/branch identity

**Dependencies:**
- Tasks 1–4 and Task 6 complete with accepted task-local proof.
- No unrelated tracked or untracked workspace changes are included.

**Authority:**
- Preauthorized local actions: run named tests, CLI/schema checks, `git diff --check`, and inspect final diff/status.
- Stop for: failed required proof, stale Herdr capability, unexpected scope, base mismatch, or unresolved lifecycle semantics.

**Steps:**
- [x] Step 1: Run focused dispatcher and launcher tests.
- [x] Step 2: Run the full repository test suite with the project’s configured command.
- [x] Step 3: Re-run Herdr version/help/schema checks and confirm native wait methods remain available; treat `events.*` as optional informational capability.
- [x] Step 4: Inspect diff, status, active-doc wording, and preservation of `.playwright-mcp/` and `db/`.
- [x] Step 5: Record any deferred raw-socket events integration, request idempotency, or revision-cursor work as explicit non-goals rather than partial implementation.

**Verification:**
- [x] `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- Expected: focused lifecycle and wait tests pass.
- [x] `python -m pytest -q`
- Expected: repository suite passes with no unrelated failures introduced.
- [x] `git diff --check`
- Expected: no whitespace errors.
- [x] `git status --short --branch`
- Expected: only declared plan-target changes appear in implementation worktree; lead-workspace untracked paths remain untouched.

**Exit Criteria:**
- `skill-verification-before-completion` can return `verified`; no required task, proof item, scope deviation, or active-doc contradiction remains.

## Verification

- `python -m pytest -q tests/test_herdr_parallel_dispatch.py tests/test_herdr_main_launcher.py`
- `python -m pytest -q`
- `herdr --version`
- `herdr agent wait --help`
- `herdr pane wait-output --help`
- `herdr api schema --json | rg 'agent\.wait|pane\.wait_for_output'`
- `git diff --check`
- `git status --short --branch`

## Completion Criteria

The plan is ready for completion verification when:

1. dispatcher regression tests prove conservative capacity retirement, executor admission, and attempt correlation
2. launcher tests prove native wait use or accepted compatibility deferral, bounded timeout uncertainty, receipt preservation, and pull-probe fallback
3. active docs and parent spec match executable behavior and reject unsupported numeric Codex watchdog claims
4. no new daemon, event database, request ledger, revision cursor, raw socket client, scheduler, or automatic retry path exists
5. focused and full test commands pass
6. Herdr 0.9.0 capability checks pass, or Task 3 records accepted compatibility deferral with pull-probe proof
7. final diff contains only declared plan-target changes and preserves unrelated workspace state
8. Task 6 proves and patches the runtime boundary, or records accepted external ownership and fail-closed behavior
9. `skill-verification-before-completion` returns `verified` before lead marks execution complete; lead changes `proposed` to `active` before first CoS dispatch
