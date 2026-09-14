---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: herdr-lifecycle-evidence-hardening
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/superpowers/plans/2026-09-14-12-47-herdr-lifecycle-evidence-hardening-plan.md
---

# Herdr Lifecycle Evidence Hardening

## Goal

Correct launcher evidence after partial startup, make process ownership checks
consistent and conservative, and bound DeepAgents receipt settlement without
adding a registry, supervisor, durable runtime state, or speculative Herdr API.

Preserve existing ownership boundaries: the plan owns workflow state, Git owns
repository truth, Herdr owns transient process observation, the launcher owns
delivery mechanics, and CoS owns final `PASS | FAIL | BLOCKED` acceptance.

## Implementation Outcomes

### Accurate post-start failure evidence

Failures after an attempt exists retain the original `dispatch_id`,
`attempt_id`, resolved agent, pane, and accumulated evidence. Unknown execution
or ownership remains unknown; it is never rewritten as `not_started` or
`not_required`. Confirmed pre-launch failures retain their current
`not_started` semantics.

### Consistent process ownership checks

Pane eligibility, Codex startup confirmation, failed-start reconciliation, and
retirement use one recursive process-tree interpretation with executor-specific
shell names. A new PID alone does not prove Codex ownership. Missing identity
evidence blocks prompt delivery and requires reconciliation instead of claiming
successful ownership.

### Bounded receipt settlement

DeepAgents receipt waiting starts short grace when terminal evidence appears,
remains capped by one overall observation deadline, and gives late
reconciliation probes an explicit remaining budget. No post-deadline probe runs
without a bound.

### Contract and regression alignment

Tests cover post-start failure identity, unknown states, nested descendants,
ownership uncertainty, terminal receipt grace, and late-receipt settlement.
Runtime documentation keeps launcher facts separate from CoS acceptance and
retains full auto-discovery candidate evidence. Runtime completion does not
establish task acceptance; this change must not introduce an `accepted: true`
path, and CoS retains acceptance authority.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical source, test, documentation, and plan files; run declared Python tests, validators, Herdr read-only probes, and diff checks; preserve unrelated workspace state
- User-approval actions: commit, push, merge, branch deletion, worktree cleanup, destructive recovery, external writes, and edits outside listed targets
- Parallel ownership: none; `scripts/herdr_main_launcher.py` and `tests/test_herdr_main_launcher.py` are shared sequential write surfaces
- Sequential fallback: baseline and contract map, failure evidence, process ownership, receipt settlement, documentation alignment, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `550b31c8c9405f843a4aef845ae7960229876102`
- Expected workspace: preserve pre-existing untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite them
- Next action: complete Task 5 verification and acceptance review
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | baseline suite and lifecycle map | `124 passed`; `176 passed`; preservation hashes captured; Herdr evidence table recorded |
| Task 2 | `completed` | current | `codex` | Task 1 | post-start failure regression tests | `130 passed`; identity and unknown-state regressions pass |
| Task 3 | `completed` | current | `codex` | Task 1 | recursive ownership and uncertainty tests | `130 passed`; nested ownership and retirement regressions pass |
| Task 4 | `completed` | current | `codex` | Tasks 2–3 | bounded receipt timing tests and metrics | `130 passed`; bounded settlement deadlines pass |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | docs alignment, full suite, validators, preservation proof | `182 passed`; validators and adapter parity pass; preservation unchanged |

Only the lead controller updates this ledger. A checked item records accepted
proof, not intent.

## Task Breakdown

### Task 1: Establish baseline and lifecycle contract

**Purpose:**
- Capture current repository state, launcher result ownership, existing tests,
  and runtime semantics before editing shared lifecycle code.

**Task Function:**
- Map current lifecycle facts and acceptance boundaries for safe sequential edits.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded source/test mapping with low ambiguity and direct
  repository proof.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent check that the plan edits existing lifecycle
  owners rather than adding duplicate state or result layers.

**Specification Coverage:**
- Covers preservation of attempt identity, independent lifecycle sections,
  CoS acceptance separation, full candidate evidence, and the approved
  narrow-first implementation order.

**Required Skills:**
- `skill-systematic-debugging`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_main_body`, `_build_assignment_result`, `_confirm_codex_start`, `_herdr_pane`, `_process_ids`, `_reconcile_failed_codex_start`, `_deepagents_completion_evidence`
- Inspect: `tests/test_herdr_main_launcher.py` startup, process, receipt, result-builder, and timing tests
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md:60-65`
- Verify: repository status, current `HEAD`, declared test and validator commands

**Dependencies:**
- None.

**Ownership Evidence Table:**

| Evidence | Required fact |
| --- | --- |
| Herdr fields | Record actual `api snapshot`, `agent get`, and `pane process-info` fields used by the launcher. |
| Correlation | Record how agent name, pane ID, executable, PID tree, and ancestry fields correlate. |
| Confirmed ownership | Define one exact predicate that permits prompt delivery; PID-set difference alone is insufficient. |
| Unknown ownership | Define missing, conflicting, stale, and malformed evidence that blocks delivery and requires reconciliation. |
| Supported success | Add one fixture containing every field required by the confirmed-ownership predicate. |

**Authority:**
- Preauthorized local actions: read declared files, run baseline tests and validators, inspect Herdr help/snapshot read-only, and record evidence in this plan
- Stop for: changed tracked files outside the declared targets, base mismatch, unavailable Python test runner, or any request to modify `.playwright-mcp/` or `db/`

**Steps:**
- [x] Step 1: Record absolute workspace path, `git status --short --branch`, `git rev-parse HEAD`, `git diff --name-status`, and the two preserved untracked paths.
- [x] Step 2: Before running tests, record path, size, mtime, and SHA-256 for `.playwright-mcp/` and `db/`, plus any pre-existing changes inside every allowed target file.
- [x] Step 3: Run `py -3 -m pytest tests/test_herdr_main_launcher.py -q` and record baseline output.
- [x] Step 4: Run `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py tests/test_disposable_artifact_cleanup.py tests/test_herdr_main_launcher.py tests/test_sync_agent_adapters.py -q` and record baseline output.
- [x] Step 5: Map which failures occur before `attempt_id` creation, after attempt creation, after delivery acknowledgement, and during observation.
- [x] Step 6: Confirm installed Herdr `pane run`, `pane process-info`, `agent get`, and `api snapshot` response fields without mutating panes or agents; complete the Ownership Evidence Table.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- [x] `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py tests/test_disposable_artifact_cleanup.py tests/test_herdr_main_launcher.py tests/test_sync_agent_adapters.py -q`
- [x] Preservation hash snapshot exists before the first test command.
- Expected: baseline passes; any pre-existing failure is recorded before Task 2.

**Exit Criteria:**
- Baseline, lifecycle map, Herdr response facts, and preservation state are
  recorded in this plan; no unrelated path changes.

**Accepted Evidence:**
- Workspace: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter`; `HEAD=550b31c8c9405f843a4aef845ae7960229876102`; tracked tree clean before plan edits; pre-existing untracked `.playwright-mcp/` and `db/` preserved.
- Baseline: focused launcher suite `124 passed in 0.56s`; cross-cutting suite `176 passed in 0.81s`.
- Preservation: `.playwright-mcp/` files `34`, bytes `624833`, aggregate SHA-256 `0ff735d3a2be12b62fcb9cedd34f8132b94d7390404144b42666dea7bce130c4`; `db/` files `8`, bytes `540394`, aggregate SHA-256 `079ce0aa5cb73bc2790e5bfd782e2ad6a610fecb98202e2261bb2c75c0c89826`.
- Herdr agent fields: `agent`, `agent_status`, `cwd`, `focused`, `interactive_ready`, `name`, `pane_id`, `revision`, `state_change_seq`, `tab_id`, `terminal_id`, `terminal_title`, `terminal_title_stripped`, `workspace_id`.
- Herdr process fields: `foreground_process_group_id`, `foreground_processes[].argv`, `argv0`, `cmdline`, `cwd`, `name`, `pid`, `pane_id`, and `shell_pid`; live response exposes no parent/child ancestry field.
- Confirmed Codex ownership predicate: exact agent name and pane identity; active agent status; at least one new foreground process whose resolved `argv0` or executable name matches the resolved Codex executable; matching expected cwd; PID absent from pre-start PID set. Missing, conflicting, stale, or malformed fields produce ownership `unknown`.
- Supported fixture: live `fitcv-async-task1-run-detail` agent in pane `w10:p1` returned `agent_status=idle`, matching cwd, and foreground `codex.exe` with executable path, PID, argv, and cwd.

### Task 2: Preserve post-start failure identity and unknowns

**Purpose:**
- Prevent generic failure handling from replacing an existing attempt with
  false identity and lifecycle facts.

**Task Function:**
- Repair failure-state construction at the shared launcher boundary and add
  regression proof for startup-check failures.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python control-flow change with existing result
  builder and focused tests.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: verify pre-launch and post-start failure semantics remain
  distinct and legacy fields stay mechanically consistent.

**Specification Coverage:**
- Covers accurate attempt identity, explicit unknowns, reconciliation on
  unresolved ownership, and separate CoS acceptance.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_main_body.emit_failure`, `_build_assignment_result`
- Modify: `scripts/herdr_main_launcher.py:_main_body`, `_build_assignment_result` only when required to preserve existing section values
- Modify: `tests/test_herdr_main_launcher.py` startup-guard and failure-output tests
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit the declared launcher failure paths and focused launcher tests; run focused Python tests and read-only diff checks
- Stop for: public result-schema expansion beyond existing lifecycle sections, new durable registry/state, changed CoS acceptance values, or failures requiring Herdr writes

**Steps:**
- [x] Step 1: Add a failing regression for `_confirm_codex_start()` failure after `attempt_id` and resolved agent identity exist; assert no prompt delivery occurs.
- [x] Step 2: Change `emit_failure()` to accept current attempt context when present instead of generating a new attempt or default agent name.
- [x] Step 3: Report `execution.state: unknown`, `task_result.state: unverified`, and `task_result.accepted: null` for post-start ownership uncertainty; set `reconciliation_required: true` unless explicit absence proof exists.
- [x] Step 4: Preserve `execution.state: not_started` and no reconciliation only for failures proven to occur before worker startup or attempt creation.
- [x] Step 5: Keep `_build_assignment_result()` as the single compatibility-field builder; do not introduce a second reducer or acceptance layer.
- [x] Step 6: Add focused regressions for pre-start failure, unknown startup ownership, failed replacement attempt, failure after confirmed delivery, known execution or cleanup evidence followed by another error, and final output retaining task/grant binding plus accumulated performance evidence.
- [x] Step 7: Add regression assertions for `dispatch_id`, `attempt_id`, `agent_name`, `session`, `pane`, delivery state, execution state, task-result state, and reconciliation flag; assert no facts leak from a prior attempt and no known facts are overwritten by blanket `unknown` values.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: new post-start failure tests pass; existing retry and pre-launch failure tests retain their intended identity and status behavior.

**Exit Criteria:**
- Every failure path after attempt creation preserves identity and evidence;
  unresolved process ownership cannot report `not_started` or successful
  reconciliation.

### Task 3: Unify recursive process ownership evidence

**Purpose:**
- Make pane eligibility, startup confirmation, reconciliation, and retirement
  interpret nested process trees consistently and conservatively.

**Task Function:**
- Harden process-tree parsing and ownership classification without adding a
  supervisor, registry, or runtime identity database.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded helper/test change with clear process-tree fixtures.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: inspect recursion, shell-name symmetry, and uncertainty paths
  independently from implementation.

**Specification Coverage:**
- Covers nested child detection, executor-specific shell names, PID-generation
  evidence, and fail-closed ownership uncertainty.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`, `_confirm_codex_start`, `_reconcile_failed_codex_start`, `_process_ids`, `_terminate_codex_lane`
- Modify: `scripts/herdr_main_launcher.py:_process_ids` and callers; preserve recursive traversal while accepting the executor-specific shell set
- Modify: `tests/test_herdr_main_launcher.py` process-tree and startup ownership fixtures
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit declared process helpers and focused fixtures; run mocked ownership tests and read-only Herdr schema probes
- Stop for: unavailable ancestry/command-line evidence needed to prove Codex identity, destructive process termination, new Herdr API assumptions, or changes to unrelated cleanup behavior

**Steps:**
- [x] Step 1: Add nested process fixtures containing shell → shell → non-shell and shell-only trees; assert pane eligibility rejects active non-shell descendants.
- [x] Step 2: Parameterize shared recursive process interpretation with `_SHELL_PROCESS_NAMES` or `_DEEPAGENTS_SHELL_PROCESS_NAMES` instead of hardcoding one executor’s shell set.
- [x] Step 3: Use the shared recursive interpretation in `_herdr_pane`, `_confirm_codex_start`, `_reconcile_failed_codex_start`, and `_terminate_codex_lane`.
- [x] Step 4: Preserve before/after PID-set evidence as observation-generation evidence only; do not call it a process-generation identifier or treat a new PID alone as proof of Codex identity.
- [x] Step 5: Apply the Task 1 confirmed-ownership predicate. Classify missing, conflicting, stale, or malformed identity evidence as ownership `unknown`; block prompt delivery and require reconciliation rather than claiming ownership.
- [x] Step 6: Add tests for unrelated `python.exe`, nested descendants, shell-only panes, matching successful startup evidence, and ownership uncertainty.
- [x] Step 7: Add retirement regressions where the original Codex PID disappears but a shell has a new live non-shell child; require `verified: false` and a non-shell process state. Distinguish malformed or missing process information from valid shell-only evidence.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: all nested descendants are detected; shell-only panes remain eligible; unrelated non-shell processes cannot satisfy Codex ownership confirmation.

**Exit Criteria:**
- All four lifecycle paths use the same recursive interpretation and no path
  claims ownership from PID difference alone.

### Task 4: Bound receipt settlement and retain phase boundaries

**Purpose:**
- Keep the existing 60-second observation allowance plus one explicit 5-second
  total settlement extension, while avoiding unnecessary receipt waits and
  keeping delivery, observation, execution, task result, and cleanup evidence
  independent.

**Task Function:**
- Refine DeepAgents settlement timing with one overall deadline and measured
  phase evidence; preserve current Codex non-blocking dispatch behavior.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded timing logic with existing monotonic-clock tests and
  explicit performance regression proof.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independently verify deadline arithmetic, late receipt
  handling, and no unbounded post-deadline command.

**Specification Coverage:**
- Covers short grace after terminal evidence, explicit late-reconciliation
  budget, delivery/observation separation, and measured latency claims.

**Deadline Model:**

| Boundary | Required decision |
| --- | --- |
| Observation deadline | Preserve the existing 60-second observation allowance. |
| Overall settlement deadline | Keep the existing additional 5 seconds; total settlement deadline is observation deadline plus 5 seconds. |
| Terminal receipt grace | End at the earlier of terminal observation plus 5 seconds or the overall settlement deadline. |
| Reconciliation commands | Use remaining overall settlement budget; never restart the clock or pass an unbounded deadline. |
| Budget exhausted | Return available evidence and unresolved uncertainty without another runtime command. |

**Required Skills:**
- `skill-test-driven-development`, `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`, `_deepagents_completion_evidence`, `_DEEPAGENTS_COMPLETION_WAIT_SECONDS`, `_DEEPAGENTS_RECEIPT_GRACE_SECONDS`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_evidence` and only timing/result fields required to preserve independent lifecycle sections
- Modify: `tests/test_herdr_main_launcher.py` delayed report, terminal-without-receipt, late receipt, and deadline-crossing tests
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Tasks 2 and 3 complete.

**Authority:**
- Preauthorized local actions: edit declared settlement logic and timing tests; run mocked-clock tests, focused suite, and read-only Herdr probes
- Stop for: changing the 60-second observation budget without measured evidence, unbounded post-deadline probing, or introducing a new `--phase`, reservation, or durable observation API

**Steps:**
- [x] Step 1: Record current timing baseline from the existing mocked-clock case: terminal evidence immediately available, missing receipt, 60-second observation budget, 5-second grace.
- [x] Step 2: Preserve the 60-second observation deadline and define one overall settlement deadline at observation deadline plus 5 seconds.
- [x] Step 3: Start receipt grace when terminal evidence first appears; end at the earlier of terminal observation plus 5 seconds or the overall settlement deadline.
- [x] Step 4: Keep late receipt reconciliation inside the remaining overall settlement budget; never restart the clock or issue a runtime command after the budget is exhausted.
- [x] Step 5: Preserve confirmed delivery when observation fails; do not rewrite delivery evidence from receipt or pane-read uncertainty.
- [x] Step 6: Add timing assertions for terminal evidence at the start, near the observation deadline, and at the deadline; late receipt with insufficient time for fresh process verification; missing receipt; and deadline-crossing transport errors.
- [x] Step 7: Record comparable before/after metrics for receipt settlement latency and subprocess count; do not claim broader parallelism improvement in this plan.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: immediate terminal evidence settles within short grace, delayed work respects the overall deadline, late reconciliation remains bounded, and existing deadline evidence remains correct.

**Exit Criteria:**
- Receipt settlement has one bounded clock model, no unbounded late probe, and
  lifecycle sections remain independent.

### Task 5: Align documentation and complete verification

**Purpose:**
- Reconcile maintained runtime documentation with shipped behavior and produce
  fresh acceptance evidence without touching unrelated workspace state.

**Task Function:**
- Validate source, tests, documentation, generated surfaces, and preservation
  boundaries as one final artifact.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: controller-owned final verification with repository-wide
  contract checks and no implementation ambiguity.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of plan coverage, contract wording, and
  final evidence.

**Specification Coverage:**
- Covers runtime contract alignment, CoS acceptance separation, full candidate
  discovery evidence, generated-surface ownership, and completion proof.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md:60-65`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` only where current wording contradicts shipped evidence semantics
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`, generated adapter parity, `.playwright-mcp/`, `db/`

**Dependencies:**
- Tasks 2–4 complete and accepted by the lead controller.

**Authority:**
- Preauthorized local actions: edit the declared runtime documentation, run all declared tests and validators, run `git diff --check`, and compare preserved paths read-only
- Stop for: documentation requiring a new runtime API, generated drift requiring direct generated-file edits, failed required proof, or any mutation of `.playwright-mcp/` or `db/`

**Steps:**
- [x] Step 1: Document that runtime completion does not establish task acceptance, this change must not introduce an `accepted: true` path, and CoS retains `PASS | FAIL | BLOCKED` authority; retain full auto-discovery candidate evidence and one attempt identity across lifecycle sections.
- [x] Step 2: Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check` if canonical skill or runtime surfaces require adapter parity; do not edit generated outputs manually.
- [x] Step 3: Run focused and cross-cutting test suites.
- [x] Step 4: Run `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`.
- [x] Step 5: Run `git diff --check` and inspect `git status --short`.
- [x] Step 6: Compare pre-task and post-task path, size, mtime, and SHA-256 records for `.playwright-mcp/` and `db/`.
- [x] Step 7: Record deviations, blockers, deferred async-dispatch work, and exact final evidence in this plan; do not mark status `completed` until `skill-verification-before-completion` returns `verified`.

**Verification:**
- [x] `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py tests/test_disposable_artifact_cleanup.py tests/test_herdr_main_launcher.py tests/test_sync_agent_adapters.py -q`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `git diff --check`
- Expected: all required tests and validators pass; generated surfaces remain aligned; unrelated untracked paths remain byte-identical.

**Accepted Evidence:**
- `182 passed in 0.80s` for the cross-cutting suite; focused launcher suite remains `130 passed`.
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` passed; `py -3 scripts/sync_agent_adapters.py --all-platforms --check` passed; `git diff --check` passed.
- `.playwright-mcp/`: `34` files, `624833` bytes, aggregate SHA-256 `0ff735d3a2be12b62fcb9cedd34f8132b94d7390404144b42666dea7bce130c4`; `db/`: `8` files, `540394` bytes, aggregate SHA-256 `079ce0aa5cb73bc2790e5bfd782e2ad6a610fecb98202e2261bb2c75c0c89826`; current per-file hashes match captured preservation records.
- No generated adapter edits; no new runtime API, supervisor, registry, `accepted: true` path, or async-dispatch behavior. Async-dispatch parallelization remains deferred to a separate specification.
- Verification result: `verified`.

**Exit Criteria:**
- Source, tests, docs, generated surfaces, plan ledger, and preservation proof
  agree; final verification is fresh; async DeepAgents dispatch remains either
  proven by existing runtime evidence or explicitly deferred to a follow-up
  specification.

## Verification

- `py -3 -m pytest tests/test_herdr_main_launcher.py -q`
- `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py tests/test_disposable_artifact_cleanup.py tests/test_herdr_main_launcher.py tests/test_sync_agent_adapters.py -q`
- `py -3 scripts/validate_repo_contracts.py --repo-root . --fast`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `git diff --check`
- Read-only preservation comparison for `.playwright-mcp/` and `db/`
- `skill-verification-before-completion` returns `verified` before plan status changes to `completed`

## Completion Criteria

The plan is ready for completion verification when:

1. Post-start failure results preserve the original attempt and resolved agent identity.
2. Unknown execution or ownership remains unknown and triggers reconciliation when evidence is incomplete.
3. Recursive process-tree checks cover eligibility, startup, reconciliation, and retirement with executor-specific shell sets.
4. PID generation evidence is not treated as sufficient Codex identity proof.
5. DeepAgents receipt settlement uses bounded grace and explicit late-reconciliation time.
6. Delivery, execution, observation, task result, cleanup, and performance remain independent sections.
7. Runtime completion does not establish task acceptance; no new `task_result.accepted: true` path exists, and CoS retains `PASS | FAIL | BLOCKED` authority.
8. Full auto-discovery candidate evidence remains documented and tested.
9. Focused and cross-cutting tests, contract validators, adapter parity checks, and diff checks pass.
10. Pre-existing `.playwright-mcp/` and `db/` contents remain unchanged.
11. Deferred async-dispatch API work is recorded as a concrete follow-up decision, not silently shipped or implied.
12. `skill-verification-before-completion` returns `verified` before the lead controller changes plan status to `completed`.

This plan does not add a new `--phase` interface, reservation registry,
background supervisor, or durable runtime state. Full DeepAgents dispatch/observe
parallelization requires a separate specification after Herdr exposes or proves
delivery acknowledgement semantics distinct from worker completion.
