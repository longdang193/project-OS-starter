---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: deepagents-live-probe-matrix
targets:
  - tests/test_dcode_project.py
  - tests/test_native_personal_local_workflow.py
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/superpowers/plans/2026-08-13-16-09-deepagents-live-probe-matrix-plan.md
---

# DeepAgents Live-Probe Matrix Plan

## Goal

Run smallest high-value DeepAgents probe set from approved matrix, convert
stable boundaries into deterministic regression tests, and preserve live probes
only for behavior that mocks cannot prove: installed runtime launch, delegated
task execution, Git-tracked recovery, concurrency, and cleanup after real child
completion or failure.

## Critical Review And Scope Decision

- **Conflict fixed:** Goal says smallest high-value set, while Task 3, Task 4,
  and matrix wording implied every live case. Full matrix would spend repeated
  provider calls without new boundary proof. Execute core cases selected below;
  deterministic tests own stable permutations. Run unselected matrix cases only
  when their routine or extended trigger applies.
- **Runtime gate added:** `dcode-project --print-config` and a disposable
  read-only task must pass before any mutating probe. Do not treat `dcode auth
  list` provider labels as authoritative when controller binding succeeds.
- **Evidence boundary retained:** Handoff files and fixtures remain user-local
  temporary evidence. Controller removes them only after exact evidence capture;
  starter Git never receives them.

Selected live core: `S1`, `S3`, `S9`, `B8`, `E12`, `P2`, `P3`, and `P4`.
`S6`, `S7`, `S10`, `E3`, `E4`, and remaining parallel negatives stay covered
by deterministic checks or run on their specific trigger.

## Implementation Outcomes

### Deterministic contract coverage

Existing `dcode-project` tests cover standard launch, role generation, bounded
controls, sanitized Codex MCP handoff, invalid configuration, path safety,
cleanup, and direct-MCP rejection without spending provider calls. Tests remain
canonical executable owner for stable launcher behavior and failure boundaries.

### Disposable live-probe coverage

Controller runs live probes only in disposable Git repositories under the OS
temporary directory. Probe evidence covers bounded edit, delegated task,
Git-derived checkpoint recovery, undeclared-path blocking, role-view cleanup,
sanitized handoff consumption, parallel read-only overlap, isolated parallel
writers, fan-in, and sequential final validation. Starter worktree remains
unchanged except approved test, guidance, and plan edits.

### Low-management operating procedure

Procedure documents routine and extended probe selections, common evidence
shape, stop rules, and cleanup boundary without adding a persistent registry,
probe service, new coordination state file, or DeepAgents-specific lifecycle.
Git, existing tests, plan tasks, and controller output remain SSOT.

## Execution Approach

- Mode: `parallel-capable`
- Executor: `codex`; DeepAgents is invoked only by live-probe tasks
- Required skills: `skill-executing-plans`, `skill-test-driven-development`, `skill-dispatching-parallel-agents`, `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: `current starter workspace for test/docs edits; disposable temporary Git repositories for all runtime probes; native worktrees only for parallel writer probe`
- Commit policy: `no commits during execution`
- Preauthorized local actions: `modify declared starter files; run focused tests and validators; create disposable temporary Git repositories and worktrees; invoke bounded dcode-project probes; remove only probe-owned temporary paths after evidence capture`
- User-approval actions: `commit, push, merge, publication, credential changes, provider changes, starter cleanup, destructive recovery outside probe-owned temporary paths`
- Parallel ownership: `Task 1 owns tests/test_dcode_project.py; Task 2 owns tests/test_native_personal_local_workflow.py; Task 3 owns disposable runtime evidence only; Task 4 owns disposable worktrees only; Task 5 owns procedure and this plan`
- Sequential fallback: `run Tasks 1–2 sequentially, then Tasks 3–4, then Task 5 and final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `95d023d4ae39142d8f5681c4570ead1953681669`
- Active task(s): `none`
- Expected workspace: `preserve all pre-existing modified files; add only plan and approved probe coverage changes`
- Next action: `offer authorized branch disposition`
- Blockers: `none`

| Task | State | Executor | Depends On | Evidence |
| --- | --- | --- | --- | --- |
| Task 1 | `completed` | `codex` | none | `tests/test_dcode_project.py`: 42 focused tests pass; launcher handoff moves sanitized facts to stdin and forced `--no-mcp` stays covered. |
| Task 2 | `completed` | `codex` | none | `tests/test_native_personal_local_workflow.py`: Git checkpoint ancestry and dependency-ready-wave contract pass. |
| Task 3 | `completed` | `codex + deepagents` | Tasks 1–2 | Disposable fixture: `S1`, `S3`, `S9`, `B8`, `E12` pass; no owned role views remain; timeout exits `124` without workspace mutation. |
| Task 4 | `completed` | `codex + deepagents` | Tasks 1–2 | Disposable worktrees: `P2` overlapping writers change disjoint files; `P3` controller fan-in; `P4` final validator passes after fan-in. |
| Task 5 | `completed` | `codex` | Tasks 3–4 | Added compact procedure selection rule and regression test. |
| Task 6 | `completed` | `codex` | Task 5 | Focused tests `47 passed`; full suite `129 passed`; contracts and adapter check pass; `git diff --check` passes. User-authorized exact probe-root and handoff cleanup was verified absent. |

## Task Breakdown

### Task 1: Close deterministic launcher boundaries

**Purpose:**
- Map matrix cases already owned by `dcode-project` tests and add only missing deterministic regressions.

**Task Function:**
- Contract coverage and negative-path testing.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: focused Python test changes across one launcher contract with security-sensitive negative cases.

**Specification Coverage:**
- Standard cases S3, S7, S9, S10.
- Variations V1, V12, V13, V15.
- Boundaries B1–B11, B17–B26 where subprocess fakes prove behavior.
- Fragile cases E13–E19, E25, E28.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:_load_roles`, `_validate_handoff`, `_handoff_stdin`, `_reject_unmanaged_runtime_options`, `main`
- Modify: `tests/test_dcode_project.py`
- Verify: `scripts/dcode_project.py`

**Dependencies:**
- Current launcher and existing test helpers remain authoritative.
- Do not change launcher behavior unless new regression exposes behavior contradicting current documented contract.

**Authority:**
- Preauthorized local actions: add or consolidate test cases in `tests/test_dcode_project.py`; run focused pytest selections.
- Stop for: required launcher behavior change, provider binding change, credential access, or new runtime permission.

**Steps:**
- [ ] Inventory existing tests against named matrix IDs and record covered IDs in test names or concise parametrization labels, not a separate registry.
- [ ] Add missing deterministic cases for empty task rejection, capacity/provider failure propagation, timeout/crash cleanup, Unicode and spaced handoff content, stale owned role views, unowned role preservation, unsupported authority flags, and forced `--no-mcp`.
- [ ] Verify every rejected input fails before child launch or owned-view writes when contract requires early rejection.
- [ ] Verify child completion, nonzero exit, and timeout all remove only launcher-owned role views.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py`
- Expected: all deterministic launcher tests pass without network or provider calls.

**Exit Criteria:**
- Stable launcher and handoff boundaries have deterministic proof; no duplicate live probe exists for behavior fully proven by tests.

### Task 2: Close deterministic Git coordination boundaries

**Purpose:**
- Extend existing native-workflow tests for checkpoint derivation, scope detection, dependency-ready waves, and recovery decisions.

**Task Function:**
- Git coordination contract testing.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: focused multi-case Git fixture work with path-status edge cases.

**Specification Coverage:**
- Standard cases S5, S6, S8.
- Variations V3, V4, V7–V11, V14.
- Boundaries B12–B16, B19.
- Fragile cases E1–E12, E20–E22, E24, E27.

**Required Skills:**
- `skill-test-driven-development`
- `skill-using-git-worktrees`

**Files And Symbols:**
- Inspect: `tests/test_native_personal_local_workflow.py:run_git`
- Modify: `tests/test_native_personal_local_workflow.py`
- Verify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`, `docs/operating_system/templates/implementation-plan-template.md`

**Dependencies:**
- Git owns workspace, commit, ancestry, rename/copy, and untracked evidence.
- Plan owns base, active tasks, dependencies, declared paths, evidence summary, and next action.

**Authority:**
- Preauthorized local actions: create pytest temporary Git repositories and worktrees; add deterministic tests only.
- Stop for: production repository mutation, persistent state file, or new coordination parser/service.

**Steps:**
- [ ] Add helper assertions that normalize tracked, staged, untracked, deleted, renamed, copied, type-changed, nested-repository, and submodule evidence from native Git commands already documented by procedure.
- [ ] Add recovery cases proving base and latest ledger-transition checkpoint are ancestors of `HEAD`; checkpoint equality with `HEAD` is not required.
- [ ] Add task-ledger cases proving sequential modes permit one active task and parallel mode permits only one dependency-ready wave with disjoint ownership.
- [ ] Add block cases for worker ledger edits, unauthorized commits, undeclared source or destination paths, dirty unexplained recovery, wrong active wave, and validator overlap with final writer.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_native_personal_local_workflow.py`
- Expected: Git-derived acceptance and block decisions pass on temporary repositories without touching starter Git state.

**Exit Criteria:**
- Git coordination boundaries are executable tests, not manual-only guidance.

### Task 3: Run routine installed-runtime probes

**Purpose:**
- Prove installed DeepAgents runtime works through current user-local binding and tracked launcher.

**Task Function:**
- Live runtime integration and failure observation.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: real provider calls and subprocess behavior require careful evidence capture but bounded fixture scope.

**Specification Coverage:**
- Standard cases S1–S10.
- Variations V1, V2, V5, V6, V9–V16 excluding parallel writer behavior owned by Task 4.
- Boundaries B6–B10, B18–B21.
- Fragile cases E2–E5, E9–E10, E13, E19–E20, E25–E26, E28.

**Required Skills:**
- `skill-backend-verification`
- `skill-systematic-debugging` only when probe fails unexpectedly

**Files And Symbols:**
- Inspect: `scripts/dcode_project.py:main`
- Execute: user-local `dcode-project` through tracked `scripts/dcode_project.py`
- Create and remove: `%TEMP%\project-os-deepagents-probe-*`
- Preserve evidence in controller output and plan task evidence only; do not add tracked runtime artifacts.

**Dependencies:**
- Tasks 1–2 pass.
- Active user-local provider and secret bindings are already configured.

**Authority:**
- Preauthorized local actions: create disposable Git fixtures; invoke bounded `dcode-project`; create probe-owned commits and files; remove only exact resolved probe roots after evidence capture.
- Stop for: missing or invalid credentials, provider reconfiguration, personal browser/profile access, external writes, starter worktree mutation, or repeated provider failure.

**Steps:**
- [ ] Create one disposable Git fixture with canonical `agents/*.toml`, scoped root and nested `AGENTS.md`, tracked plan, declared task files, and no `.deepagents/` state.
- [ ] Run read-only summary, one-file edit, two-file edit, new-file, delegated `low`/`normal`/`high` task-function variations, sequential dependency tasks, and post-task independent Codex verification.
- [ ] Run sanitized Codex MCP handoff using already-configured read-only MCP capability; verify DeepAgents consumes facts under forced `--no-mcp` and cannot call MCP directly.
- [ ] Force one bounded nonzero or timeout outcome and verify owned role views are cleaned while Git workspace and unowned role content remain preserved.
- [ ] Run fresh-task recovery using only tracked plan and Git commands; verify correct active task, ancestry, workspace state, and next action.
- [ ] Add one undeclared tracked or untracked path, capture `block`, then leave it untouched until evidence is recorded; remove it only during exact probe-root cleanup.
- [ ] Capture command, workspace, profile, exit code, elapsed time, tool calls, changed paths, exact content checks, Git status, `git diff --check`, and controller decision for each runtime probe.

**Verification:**
- [ ] `$probeRoot = (Resolve-Path $probeRoot).Path; $base = (git -C $probeRoot merge-base HEAD main).Trim()`
- [ ] `git -C $probeRoot status --short --branch`
- [ ] `git -C $probeRoot diff --name-status -M -C --find-copies-harder $base --`
- [ ] `git -C $probeRoot ls-files --others --exclude-standard -z`
- [ ] `git -C $probeRoot diff --check`
- Expected: standard probes accept; declared failure and scope-mismatch probes block; starter Git state does not gain probe artifacts.

**Exit Criteria:**
- Installed runtime, role generation, handoff, bounded editing, recovery, cleanup, and controller verification have fresh evidence.

### Task 4: Run parallel Git coordination probes

**Purpose:**
- Prove parallel preflight and isolated writer behavior without sharing mutable workspaces.

**Task Function:**
- Concurrency, worktree isolation, fan-in, and final-validation proof.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: concurrent runtime calls, multiple Git worktrees, integration ordering, and easily misread timing evidence.

**Specification Coverage:**
- Parallel cases P1–P8.
- Fragile cases E7–E8, E21–E22.

**Required Skills:**
- `skill-dispatching-parallel-agents`
- `skill-using-git-worktrees`
- `skill-backend-verification`

**Files And Symbols:**
- Create and remove: `%TEMP%\project-os-deepagents-parallel-*`
- Create: two probe-owned native Git worktrees with distinct branches and disjoint files.
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md` parallel and resume rules.

**Dependencies:**
- Tasks 1–2 pass.
- Task 3 confirms baseline installed runtime works.

**Authority:**
- Preauthorized local actions: create probe-owned branches, commits, and worktrees inside disposable fixture; run concurrent bounded tasks; integrate fixture branches; remove exact probe-owned paths after evidence capture.
- Stop for: shared starter paths, overlapping writer ownership, unresolved merge conflict, missing concurrency support, external or destructive Git action outside fixture.

**Steps:**
- [ ] Run two timed read-only tasks against immutable base inputs; require overlapping start/end intervals or elapsed time lower than sequential baseline.
- [ ] Create two native worktrees on separate fixture branches; assign one declared file to each DeepAgents writer and launch both in same parallel dispatch round.
- [ ] Verify worktree roots, branches, base ancestry, write ownership, changed paths, and task-local checks independently before fan-in.
- [ ] Integrate verified fixture commits through controller-owned Git operation; record conflict-free ancestry and final changed paths.
- [ ] Start final validator only after both writer completions and fan-in commit; verify integrated content and required checks.
- [ ] Run negative dispatch checks for same-path writers, hidden dependency, and unavailable concurrency; expect block or declared sequential fallback without fake overlap claims.

**Verification:**
- [ ] Timestamp evidence proves P1 and P2 overlap.
- [ ] `$fixtureRoot = (Resolve-Path $fixtureRoot).Path; $integrationBase = (git -C $fixtureRoot merge-base main integration).Trim(); $integrationHead = (git -C $fixtureRoot rev-parse integration).Trim()`
- [ ] `git -C $fixtureRoot worktree list --porcelain`
- [ ] `git -C $fixtureRoot log --graph --oneline --all -8`
- [ ] `git -C $fixtureRoot diff --check "$integrationBase..$integrationHead"`
- Expected: independent lanes overlap, writers remain isolated, fan-in precedes final validator, unsafe cases never dispatch concurrently.

**Exit Criteria:**
- Parallel coordination has real timing, Git isolation, fan-in, and sequential final-validation evidence.

### Task 5: Align minimal probe guidance

**Purpose:**
- Make repeatable probe selection clear without creating another orchestration surface.

**Task Function:**
- Guidance normalization and SSOT review.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: cross-reference matrix outcomes against existing procedure and tests.

**Specification Coverage:**
- Routine suite, extended suite, evidence shape, and cleanup boundary from approved matrix.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify: `docs/superpowers/plans/2026-08-13-16-09-deepagents-live-probe-matrix-plan.md` task evidence and deviations only during execution
- Verify: `docs/operating_system/procedures/runtime-adapter-procedure.md`, `docs/operating_system/runtime/runtime-surfaces.md`, `.agents/skills/skill-dispatching-parallel-agents/SKILL.md`

**Dependencies:**
- Tasks 3–4 provide actual runtime evidence and discovered limitations.

**Authority:**
- Preauthorized local actions: patch procedure and plan evidence only; run documentation and generated-surface checks.
- Stop for: new persistent registry, new probe runner, new runtime config, or behavior change not proven by probes.

**Steps:**
- [ ] Add compact `DeepAgents Probe Selection` section: routine probes after launcher/guidance changes; extended probes only after parallelism, worktree, runtime-binding, handoff, role-generation, or cleanup changes.
- [ ] Define common evidence fields in prose or one JSON example: probe ID, temporary workspace, base, executor/profile, exit code, elapsed time, changed paths, checks, decision, notes.
- [ ] State tests own deterministic boundaries; live probes own installed-runtime, provider, concurrency, and cleanup evidence.
- [ ] State probe fixtures use OS temporary directories, never starter workspace, and exact probe-root cleanup occurs only after evidence capture.
- [ ] Record failed probes and real limitations in this plan; do not normalize failures into expected success.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_native_personal_local_workflow.py`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: guidance matches current launcher and generated surfaces remain unchanged unless canonical agent inputs changed.

**Exit Criteria:**
- One concise procedure tells future controllers which probes to run and what evidence to capture, with no new admin surface.

### Task 6: Run final verification and reconcile plan

**Purpose:**
- Confirm deterministic tests, repository contracts, runtime probes, and Git evidence agree before completion claim.

**Task Function:**
- Independent completion verification and plan reconciliation.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: final assessment combines code tests, live provider evidence, concurrency evidence, Git scope, and guidance consistency.

**Specification Coverage:**
- Entire approved probe matrix at routine or extended depth defined by Tasks 1–5.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `tests/test_dcode_project.py`
- Verify: `tests/test_native_personal_local_workflow.py`
- Verify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Verify: `scripts/dcode_project.py`
- Reconcile: `docs/superpowers/plans/2026-08-13-16-09-deepagents-live-probe-matrix-plan.md`

**Dependencies:**
- Tasks 1–5 complete or explicitly blocked with preserved evidence.

**Authority:**
- Preauthorized local actions: run declared checks; inspect diffs and temporary probe evidence; update plan status only after verified result.
- Stop for: unresolved failed required probe, stale provider evidence, unexplained starter changes, missing cleanup evidence, or destructive/external action.

**Steps:**
- [ ] Run focused test files, repository contracts, generated adapter check, and full pytest suite.
- [ ] Reconcile every routine and extended probe result with task evidence; distinguish expected negative result, environmental block, and product defect.
- [ ] Confirm no `.deepagents/`, handoff payload, credential, endpoint, probe fixture, or temporary evidence file is tracked in starter.
- [ ] Inspect starter changed paths against plan targets and preserve all unrelated pre-existing work.
- [ ] Mark plan `completed` only after `skill-verification-before-completion` returns `verified`.

**Verification:**
- [ ] `py -3 -m pytest -q tests/test_dcode_project.py tests/test_native_personal_local_workflow.py`
- [ ] `py -3 scripts/validate_repo_contracts.py`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `py -3 -m pytest -q`
- [ ] `git diff --check`
- [ ] `git status --short --branch`
- Expected: all required checks pass; environmental limitations are explicitly recorded; no runtime secret or probe state enters Git.

**Exit Criteria:**
- Fresh deterministic and live evidence supports completion; unresolved required failures remain blocked rather than waived silently.

## Approved Probe Matrix

Run every case in a disposable Git repository. Record: probe ID, absolute fixture
path, base commit, executor and template profile, command, exit code, elapsed
milliseconds, DeepAgents tool calls/output, changed paths, exact assertions,
Git status, `git diff --check`, and controller `accept` or `block` decision.
Do not run destructive cases against starter or active worktree.

### Standard Cases

| ID | Case | Probe | Expected Result | Required Evidence |
| --- | --- | --- | --- | --- |
| S1 | Direct bounded edit | Change one allowed file | Only declared file changes | Exit `0`; exact content; one changed path |
| S2 | Read and summarize | Read declared files without edits | Working tree stays clean | Source-grounded output; clean status |
| S3 | Delegated task | Controller asks DeepAgents built-in `task` to complete bounded work | Child returns bounded result | Task call and result visible |
| S4 | Sequential tasks | Make Task 2 depend on Task 1 | Task 1 finishes before Task 2 starts | Plan states; Git transitions; final content |
| S5 | Git checkpoint | Commit task output and ledger transition together | Checkpoint derives from Git | `$planPath = "docs/plans/probe-plan.md"; git log -1 --format=%H -- $planPath` identifies transition commit |
| S6 | New-task recovery | Resume from tracked plan plus Git only | Correct active task and next action | Root, branch, ancestry, `HEAD`, task ledger |
| S7 | Codex MCP handoff | Codex calls MCP, creates valid sanitized handoff, DeepAgents consumes it | Facts arrive with forced `--no-mcp` | Valid handoff; direct MCP unavailable |
| S8 | Final verification | Codex independently runs declared checks | Executor claim alone never accepts | Fresh check output and Git scope proof |
| S9 | Clean role-view lifecycle | Complete normal launcher run | Owned role views disappear | `.deepagents/agents` owned content removed |
| S10 | Failed role-view lifecycle | Cause bounded child failure or timeout | Owned views still disappear | Nonzero/timeout evidence; cleanup confirmed |

### Variations

| ID | Base | Variation | Expected Result | Main Risk |
| --- | --- | --- | --- | --- |
| V1 | S1 | Run `low`, `normal`, and `high` task prompts | Same scope and acceptance contract | Profile becomes fixed task-function mapping |
| V2 | S1 | Edit two declared files | Both and only both change | Partial or extra edit |
| V3 | S1 | Create declared new file | Allowed untracked output detected and accepted | Untracked output ignored |
| V4 | S1 | Rename declared file | Source and destination reviewed | Only destination reviewed |
| V5 | S2 | Read nested scoped `AGENTS.md` | Nested instructions apply | Root guidance only read |
| V6 | S3 | Research, debug, review, plan, validate, design | Controller chooses profile from task needs | Fixed profile mapping |
| V7 | S4 | Three-task dependency chain | Each task waits for predecessor | Wrong activation order |
| V8 | S4 | One blocked and one independent task | Dependency-ready task can proceed | Unrelated work stops |
| V9 | S5 | Add later ledger-neutral commit | Checkpoint need only be ancestor of `HEAD` | `HEAD` equality assumption |
| V10 | S6 | Clean checkout | Resume in current checkout | Unneeded worktree creation |
| V11 | S6 | Existing unrelated changes | Preserve or use authorized isolation | Existing work overwritten |
| V12 | S7 | Multiple facts and sources | All valid inputs arrive intact | Ordering/truncation loss |
| V13 | S7 | Unicode content and paths | Handoff remains correct | Windows encoding/path error |
| V14 | S8 | Material backend change | Codex direct boundary proof required | UI/executor claim substitutes proof |
| V15 | S9 | Pre-existing unowned role content | Owned views removed; custom content preserved | Cleanup deletes user content |
| V16 | S3 | Two independent delegated reads | Overlap only when runtime supports it | Sequential calls claimed parallel |

### Parallel Git Coordination

| ID | Case | Setup | Expected Result | Required Evidence |
| --- | --- | --- | --- | --- |
| P1 | Parallel read-only preflight | Two immutable-input investigations | Calls overlap | Timestamp intervals or elapsed-time proof |
| P2 | Parallel isolated writers | Two worktrees, branches, disjoint paths | Writers complete without conflict | Worktree roots, branches, diffs |
| P3 | Writer plus read-only validator | Validator reads immutable base only | Safe overlap | Input commit recorded; no mutable dependency |
| P4 | Fan-in | Two verified writer branches | Controller reconciles outputs | Commit ancestry and integration proof |
| P5 | Sequential final validation | Fan-in completes before validator starts | Validator checks integrated state | Validator start after writer finish |
| P6 | Sequential fallback | Concurrency unavailable | Declared fallback order runs | No fake concurrency claim |
| P7 | Shared-path writers | Two tasks own one file or symbol | Parallel dispatch blocks | No writer launch; conflict report |
| P8 | Hidden dependency | Task B needs Task A output | Controller serializes | Dependency recorded before dispatch |

### Boundary and Edge Cases

| ID | Boundary | Probe Input | Expected Result |
| --- | --- | --- | --- |
| B1 | Empty task | Empty or whitespace task text | Reject before DeepAgents launch |
| B2 | No role templates | Fixture omits `agents/*.toml` | Clear configuration failure; no residue |
| B3 | Invalid role template | Unsupported TOML field | Reject before child launch |
| B4 | Missing provider | Absent local provider binding | Clear failure; no fallback |
| B5 | Missing API key | Empty local secret binding | Reject without secret leak |
| B6 | Provider unavailable | Network/provider failure | Nonzero result; workspace preserved |
| B7 | Provider capacity | Capacity response | No silent model/provider switch |
| B8 | Timeout | Long task with short timeout | Controlled timeout; cleanup |
| B9 | Child crash | Forced child failure | Nonzero result; workspace preserved |
| B10 | Non-Git location | Launch outside Git | Repository-context rejection |
| B11 | Wrong workspace | Launch from sibling/parent repo | Proven repo only or reject |
| B12 | Detached `HEAD` | Detached worktree fixture | State recorded; contract followed |
| B13 | Empty Git history | No initial commit | Block when base required |
| B14 | Nested repository | Changed path contains `.git` | Block before acceptance |
| B15 | Submodule mutation | Change pointer/content | Block unless explicitly declared |
| B16 | Symlink/junction escape | Target escapes fixture root | Reject before launch or acceptance |
| B17 | Long Windows path | Deep nested target | Exact success or clear failure |
| B18 | Spaces in path | Fixture path includes spaces | No quoting/path error |
| B19 | Unicode path | Non-ASCII target | Correct read/write and Git proof |
| B20 | Large output | Long agent response | Required evidence intact |
| B21 | Missing Tavily key | Attempt executor web search | Explicit unavailable; no Codex fallback |
| B22 | Direct DeepAgents MCP config | User-local `.deepagents/.mcp.json` in isolated home | Setup rejects duplicate authority |
| B23 | Unsupported runtime flag | Shell/MCP/model/agent/resume override | Reject before child launch |
| B24 | Stale owned role views | Owned generated views pre-exist | Safely replace then remove |
| B25 | Unowned role views | Custom content pre-exists | Preserve custom content |
| B26 | Interrupted cleanup | Stop launcher during execution | Next launch safely handles owned residue |

### Easily Broken Cases

| ID | Fragile Contract | Probe | Correct Decision |
| --- | --- | --- | --- |
| E1 | Worker edits plan | Executor changes work plus ledger | `block`; controller alone writes ledger |
| E2 | Worker commits | Executor creates unauthorized commit | `block`; preserve evidence |
| E3 | Out-of-scope tracked edit | Modify undeclared tracked file | `block` |
| E4 | Out-of-scope untracked file | Create undeclared file | `block` |
| E5 | Rename escape | Allowed source to undeclared destination | `block` |
| E6 | Wrong deletion | Delete file when change requested | `block` unless declared |
| E7 | Base mismatch | Plan base not ancestor of `HEAD` | `block` before work |
| E8 | Wrong active wave | Multiple active tasks lack independence | `block` |
| E9 | Stale task state | Git already has claimed output | Reconcile before work |
| E10 | Dirty recovery | Unexplained workspace changes | `block` or preserve via authorized isolation |
| E11 | Checkpoint self-reference | Plan copies result commit SHA | Contract/test failure |
| E12 | Checkpoint equals `HEAD` | Later commit follows checkpoint | Accept checkpoint ancestry |
| E13 | Direct MCP use | DeepAgents calls Codex MCP | Unavailable under forced `--no-mcp` |
| E14 | Unsanitized handoff | Token, cookie, auth header, secret-like value | Reject before launch |
| E15 | Stale handoff | Payload exceeds allowed age | Reject |
| E16 | Oversized handoff | Excess bytes/sources/facts/depth | Reject |
| E17 | Handoff path escape | Traversal, symlink, outside root | Reject |
| E18 | Unknown MCP selection | ID absent from Codex capability set | Reject before launch |
| E19 | Assumed task tool | Prompt assumes shell/filesystem capability | Report unavailable; do not invent evidence |
| E20 | Executor claim accepted | Agent says checks passed without output | Codex verifies independently |
| E21 | Shared-worktree writers | Two writers share worktree | Controller prevents dispatch |
| E22 | Validator/writer overlap | Validator reads mutable integrated state | Delay until fan-in |
| E23 | Personal-profile attachment | Browser/tool uses personal profile | Reject; use isolated runtime |
| E24 | Implicit cleanup | Remove worktree/evidence without approval | Stop for authorization |
| E25 | Provider fallback | Runtime silently switches on failure | Reject or report failure |
| E26 | Role-function hardcoding | Guidance maps task function to profile | Guidance/test failure |
| E27 | Generated-source edit | Adapter changed instead of canonical source | Sync check fails |
| E28 | Runtime state tracked | `.deepagents/` enters Git | Git/contract check fails |

### Routine and Extended Selections

Routine probe suite: `S1`, `S3`, `S6`, `S7`, `S9`, `S10`, `E3`, `E4`,
`E11`, `E12`, `E13`, `E20`.

Extended suite after parallelism, worktree, runtime-binding, handoff,
role-generation, or cleanup changes: `P1`–`P8`, `B2`–`B9`, `B12`–`B26`, and
`E1`–`E28`.

Matrix cases are selection and evidence contract, not a new runtime registry.
Tests own deterministic cases. Live probes own installed-runtime, provider,
concurrency, and real cleanup evidence.
## Verification

- `py -3 -m pytest -q tests/test_dcode_project.py tests/test_native_personal_local_workflow.py`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 -m pytest -q`
- `git diff --check`
- Controller review of routine and parallel live-probe evidence from disposable Git fixtures.

## Completion Criteria

The plan is ready for completion verification when:

1. deterministic tests cover stable launcher, handoff, cleanup, and Git coordination boundaries without unnecessary provider calls
2. routine installed-runtime probes prove bounded edit, delegation, sanitized handoff, recovery, scope blocking, cleanup, and independent Codex verification
3. parallel probes prove immutable-input overlap, isolated writers, controller fan-in, sequential final validation, and unsafe-case fallback or block
4. probe guidance identifies routine versus extended triggers, evidence fields, fixture boundary, and cleanup rule without new persistent orchestration state
5. every failed or skipped probe has a concrete environmental or contract reason and no required defect is hidden
6. full verification passes and starter Git contains no runtime secrets, `.deepagents/` state, handoff payloads, or probe fixtures

The plan may be marked `completed` only when `skill-verification-before-completion` runs fresh final checks, reconciles probe evidence and repository state, returns `verified`, and updates plan status.
