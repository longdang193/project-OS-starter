---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cos-runtime-autonomy
targets:
  - scripts/validate_planning_lifecycle.py
  - docs/operating_system/templates/implementation-plan-template.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - tests/test_validate_planning_lifecycle.py
  - tests/test_starter_lifecycle_contract.py
  - tests/test_native_personal_local_workflow.py
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - tests/test_skill_chief_of_staff.py
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
---

# CoS Runtime Autonomy

## Verdict Review

**Review verdict:** ready with required fixes.

The supplied verdict identifies the correct root cause: CoS has runtime-target
discovery missing, not broad task authority missing. It preserves the stronger
ownership boundary: CoS selects approved work, the repository launcher resolves
and mutates runtime targets, Herdr supplies transient observation, and plan/Git
remain durable truth.

### Findings

### [P2] DeepAgents launch path forwards `HERDR_ENV`

**Problem:** `resolve_launch()` uses `_herdr_environment()` for DeepAgents
preflight, but `main()` uses `os.environ.copy()` for the actual DeepAgents
subprocess.

**Why it matters:** controller metadata can leak into Herdr child execution and
recreate the false runtime-gate failure this work is intended to remove.

**Evidence:** `scripts/herdr_main_launcher.py:resolve_launch` selects the cleaned
environment; `scripts/herdr_main_launcher.py:main` assigns the inherited
environment in the DeepAgents branch; the existing test covers only the helper.

**Preserve:** `HERDR_ENV` is inherited runtime metadata, never CoS authority,
dispatch permission, or proof.

**Smallest safe correction:** use `_herdr_environment()` for every repository
launcher Herdr subprocess and add an actual `main()` regression test.

### [P2] Launcher requires runtime target IDs unavailable to native CoS

**Problem:** `--session` and `--pane` are required exact identifiers, while
native Codex CoS has no reliable target discovery surface.

**Why it matters:** policy permits native Codex CoS, but launcher invocation
stops before dispatch because the controller cannot supply runtime IDs.

**Evidence:** `build_parser()` requires both arguments; `resolve_launch()` calls
`_herdr_pane()` only after receiving them; the current launcher plan requires
pre-discovered session and pane values.

**Preserve:** explicit exact target launches and fail-closed pane validation.

**Smallest safe correction:** accept `auto` for both flags, discover existing
eligible targets in the launcher, and reject mixed `auto`/exact selectors.

### [P2] CoS scheduling contract unnecessarily serializes eligible waves

**Problem:** plan-bound CoS says to select one dependency-ready task even when
the active plan declares `parallel-capable` execution.

**Why it matters:** valid disjoint implementation lanes cannot run concurrently,
so CoS autonomy remains below the existing plan contract.

**Evidence:** `.agents/skills/skill-chief-of-staff/SKILL.md` contains the
single-task dispatch rule; `planning-dispatch.md` already defines parallel
fan-out with isolated worktrees and disjoint ownership.

**Preserve:** inline sequential and subagent-ready plans remain single-task;
one lead controller remains the sole coordination-state writer.

**Smallest safe correction:** allow one dependency-ready isolated wave only when
the plan is `parallel-capable` and dependencies, ownership, worktrees, and
authority prove independence.

### [P1] Adaptive dispatch conflicts with current task-contract validation

**Problem:** pending tasks cannot currently leave `Executor` or `Template
Profile` unresolved. The validator requires concrete values before activation,
which forces routine dispatch choices before native CoS can resolve them.

**Why it matters:** requiring executor and profile decisions up front creates
the same manual handoff failure this plan is meant to remove.

**Evidence:** `scripts/validate_planning_lifecycle.py` validates task profiles
against discovered profiles and task executors against `codex`, `deepagents`,
and `tura`; the plan template documents concrete values.

**Preserve:** `unresolved` is a lifecycle marker only. The executor enum remains
`codex | deepagents | tura`, and active, blocked, and completed tasks retain
concrete resolved values.

**Smallest safe correction:** permit unresolved values only on pending tasks,
then require CoS to write concrete executor/profile resolution into the same
task record before activation and launch.

### [P2] Runtime grant durability must remain split by ownership

**Problem:** durable task resolution and transient effective runtime grants are
different facts, but the proposed SSOT wording combines them.

**Why it matters:** putting `grant_digest` or effective runtime values into the
plan would violate Git-tracked coordination rules and create duplicate runtime
state.

**Evidence:** `git-tracked-coordination-rule.md` defines Runtime Grants and
`grant_digest` as transient; launcher evidence already records effective values.

**Preserve:** task `Authority` owns durable grant bounds; launcher evidence owns
effective runtime values and digest; plan/Git remain durable coordination truth.

**Smallest safe correction:** record only resolved executor/profile and task
authority in the plan before launch. Keep effective grant details in launcher
evidence.

### [P3] Runtime ownership wording needs one symmetric boundary

**Problem:** guidance risks conflating read-only CoS observation with mutating
pane control.

**Why it matters:** forbidding all direct observation conflicts with the runtime
SSOT, while allowing direct mutation bypasses launcher evidence and cleanup.

**Evidence:** `runtime-adapter-procedure.md` assigns read-only Herdr observation
to the controller; `runtime-surfaces.md` assigns lifecycle and delivery
mechanics to launcher/Herdr.

**Preserve:** CoS may use bounded read-only observation; CoS cannot create,
repurpose, close, or otherwise mutate Herdr sessions or panes directly.

**Smallest safe correction:** state observation and mutation as separate,
symmetric responsibilities in the CoS skill and runtime docs.

## Goal

Give native Codex CoS durable, in-plan dispatch resolution, deterministic
runtime-target discovery, and bounded parallel scheduling without adding a
second authority, runtime ledger, adaptive executor enum, or automatic runtime
creation.

## Implementation Outcomes

### Launcher target discovery

`scripts/herdr_main_launcher.py` accepts `--session auto --pane auto`, discovers
one eligible existing target for the requested repository cwd, records target
resolution evidence, and keeps exact session/pane launches unchanged. Zero
eligible targets and multiple eligible targets remain machine-readable runtime
outcomes; CoS maps them to its workflow statuses.

### Runtime environment invariant

Every Herdr subprocess launched by the repository launcher receives the cleaned
environment. `HERDR_ENV` never grants, denies, proves, or selects CoS dispatch
authority.

### CoS scheduling autonomy

Plan-bound CoS may select a dependency-ready isolated wave only for
`parallel-capable` plans with proven disjoint ownership, dependencies,
worktrees, and task authority. Other execution modes remain sequential.

### Durable dispatch resolution

Pending CoS tasks may hold `Executor: unresolved` and `Template Profile:
unresolved`. Native Codex CoS resolves pinned or adaptive executor/profile
values from `planning-dispatch.md`, records concrete values in the same task
record, and activates the task only after resolution. Effective runtime grants
remain launcher evidence, not plan state.

### Documentation and generated surfaces

Canonical CoS, planning, runtime-surface, and runtime-adapter guidance uses one
controller/launcher/Herdr/plan ownership model. Generated agent adapters are
regenerated from canonical sources and validated for drift.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-writing-plans`, `skill-executing-plans`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing user changes and untracked `.playwright-mcp/` and `db/`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical code/docs/tests; regenerate declared adapters; run declared local validators and tests; use Herdr read-only discovery probes if available
- User-approval actions: create or delete Herdr sessions/panes; create or remove worktrees outside declared task authority; install/authenticate tools; push, merge, publish, destructive cleanup, or discard
- Parallel ownership: none; launcher, policy, tests, and generated outputs have one dependency chain
- Sequential fallback: complete Tasks 1–4 in order; run Task 5 only after focused tests and adapter checks pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `506a0bd15d2e75f75095d1943e9d8d28bc28611a`
- Expected workspace: current tracked CoS guidance edits preserved; untracked `.playwright-mcp/` and `db/` preserved; no unrelated cleanup
- Next action: none
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | lifecycle validator and template tests | `149 focused tests passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | focused launcher environment tests | `149 focused tests passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | target-resolution unit tests and launcher CLI tests | `launcher tests passed; --help passed` |
| Task 4 | `completed` | current | `codex` | Task 3 | CoS and planning contract tests | `149 focused tests passed` |
| Task 5 | `completed` | current | `codex` | Task 4 | adapter sync, repository validation, diff checks | `deployment, drift, contracts, and diff checks passed` |

## Task Breakdown

### Task 1: Make pending dispatch resolution explicit

**Purpose:**
- Let pending CoS tasks defer routine executor and profile selection without
  weakening the concrete runtime contract required at activation.

**Task Function:**
- Reconcile planning lifecycle validation, template wording, and execution
  instructions around one durable task record.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded validator, template, and policy contract change.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of state-dependent validation and SSOT boundaries.

**Specification Coverage:**
- Findings `[P1] Adaptive dispatch conflicts with current task-contract validation`
  and `[P2] Runtime grant durability must remain split by ownership`.
- `unresolved` remains a lifecycle marker, not an executor or profile.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/validate_planning_lifecycle.py:validate_plan_file`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md:Task Breakdown`
- Inspect: `.agents/skills/skill-executing-plans.md:Select Next Action`
- Modify: `scripts/validate_planning_lifecycle.py`
- Modify: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `tests/test_validate_planning_lifecycle.py`
- Modify: `tests/test_starter_lifecycle_contract.py`
- Modify: `tests/test_native_personal_local_workflow.py`

**Dependencies:**
- Current `codex | deepagents | tura` executor values and discovered
  `agents/*.toml` profile names remain canonical.
- Current Git coordination rules remain unchanged for authority, grant digests,
  and sole-ledger ownership.

**Authority:**
- Preauthorized local actions: edit named validator, template, execution skill, and tests; run focused planning tests.
- Stop for: adding `unresolved` to the executor schema enum, adding a second state file, changing Runtime Grant durability, or changing completed-plan compatibility semantics.

**Steps:**
- [x] Step 1: Permit `unresolved` for `Executor` and `Template Profile` only when the task ledger row is `pending`.
- [x] Step 2: Require concrete executor/profile values for `active`, `blocked`, and `completed` rows; retain explicit pins and `none (lead controller)`.
- [x] Step 3: Document that CoS resolves executor/profile through `planning-dispatch.md`, writes them into the same task record before activation, and leaves effective grants in launcher evidence.
- [x] Step 4: Update execution guidance to resolve pending values before launcher dispatch without allowing profile selection to choose an executor.
- [x] Step 5: Add regression tests for pending unresolved, active unresolved rejection, explicit pins, and unchanged executor enum.

**Verification:**
- [x] `py -m pytest -q tests/test_validate_planning_lifecycle.py tests/test_starter_lifecycle_contract.py tests/test_native_personal_local_workflow.py`
- Expected: pending unresolved tasks pass; active/blocked/completed unresolved tasks fail; existing historical plans retain compatibility.

**Exit Criteria:**
- Plan validation and execution guidance support one unresolved-then-resolved task record without introducing new durable state.

### Task 2: Normalize launcher environment handling

**Purpose:**
- Eliminate the DeepAgents-only environment asymmetry and lock the
  `HERDR_ENV` invariant at the actual subprocess boundary.

**Task Function:**
- Correct a runtime-boundary defect and add direct regression proof.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded Python change with known symbol and test seams.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent inspection of subprocess environment behavior.

**Specification Coverage:**
- Findings `[P2] DeepAgents launch path forwards HERDR_ENV` and the runtime
  environment invariant.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_herdr_environment`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`
- Modify: `scripts/herdr_main_launcher.py:main`
- Modify: `tests/test_herdr_main_launcher.py:test_main_deepagents_environment`
- Verify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Existing `_herdr_environment()` behavior and current external-controller
  regression remain unchanged.

**Authority:**
- Preauthorized local actions: edit launcher and focused launcher tests; run focused Python tests.
- Stop for: Herdr CLI contract changes, provider/auth changes, or any request to restore `HERDR_ENV` into launcher child environments.

**Steps:**
- [x] Step 1: Change the DeepAgents execution branch in `main()` to use `_herdr_environment()`.
- [x] Step 2: Add a test that sets `HERDR_ENV`, stubs launch resolution and subprocess execution, invokes DeepAgents `main()`, and asserts the `_run()` environment omits `HERDR_ENV`.
- [x] Step 3: Keep Codex `CODEX_HOME` behavior and all existing evidence fields unchanged.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: existing launcher tests and the new actual-subprocess environment regression pass.

**Exit Criteria:**
- Codex and DeepAgents launcher paths use the same cleaned Herdr environment invariant.

### Task 3: Add deterministic `auto/auto` target resolution

**Purpose:**
- Let native Codex CoS dispatch through the repository launcher without
  manually supplying Herdr session and pane IDs.

**Task Function:**
- Extend launcher target binding while preserving exact-target behavior.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: runtime topology, failure semantics, and compatibility need higher reasoning depth than the environment-only patch.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent review of ambiguous-target and subprocess safety boundaries.

**Specification Coverage:**
- Findings `[P2] Launcher requires runtime target IDs unavailable to native CoS`.
- Preserve launcher-owned runtime mechanics and Git-owned repository identity.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:build_parser`
- Inspect: `scripts/herdr_main_launcher.py:_herdr_pane`
- Inspect: `scripts/herdr_main_launcher.py:resolve_launch`
- Modify: `scripts/herdr_main_launcher.py:build_parser`
- Modify: `scripts/herdr_main_launcher.py:resolve_launch`
- Add: `scripts/herdr_main_launcher.py:_resolve_target_selector` and the smallest helper set needed for Herdr snapshot parsing
- Modify: `tests/test_herdr_main_launcher.py`
- Verify: `scripts/herdr_main_launcher.py --help` and focused launcher tests

**Dependencies:**
- Task 2 complete.
- Use the verified installed Herdr `api snapshot`, `pane list`, and
  `pane process-info` surfaces; capture one redacted fixture from the current
  runtime before finalizing the parser shape.

**Authority:**
- Preauthorized local actions: add existing-target discovery, deterministic filtering, evidence, and tests; run read-only Herdr discovery probes.
- Stop for: session/pane creation or deletion, runtime schema changes not supported by installed Herdr, ambiguous target selection, or worktree selection beyond requested `--cwd`.

**Steps:**
- [x] Step 1: Accept `auto` as a selector value while retaining required `--session` and `--pane` arguments; reject mixed exact/`auto` pairs before Herdr mutation.
- [x] Step 2: Add launcher-owned discovery using Herdr runtime topology: exact resolved pane cwd, no agent state, and shell-only foreground process.
- [x] Step 3: Sort candidates deterministically by session and pane ID; select exactly one candidate and preserve explicit target behavior byte-for-byte where practical.
- [x] Step 4: Emit `target_resolution.status` as `selected`, `not_found`, or `ambiguous`, with candidate count and selected target when applicable. Keep workflow mapping out of launcher internals.
- [x] Step 5: Add tests for explicit/explicit, auto/auto selected, zero candidates, multiple candidates, mixed selectors, cwd mismatch, agent occupancy, and conflicting foreground process.

**Verification:**
- [x] `py -m pytest -q tests/test_herdr_main_launcher.py`
- Expected: target resolution tests prove fail-closed selection and explicit-target compatibility.
- [x] `py -B scripts/herdr_main_launcher.py --help`
- Expected: help documents `auto` selector support without adding session/pane creation flags.

**Exit Criteria:**
- Launcher can resolve one existing eligible target from native CoS context and never guesses among multiple targets.

### Task 4: Expand CoS scheduling and ownership guidance

**Purpose:**
- Give CoS autonomy to schedule proven independent waves while keeping
  read-only observation and launcher-owned mutation distinct.

**Task Function:**
- Reconcile policy wording and executable contract tests with existing plan semantics.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation and contract-test update.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: policy consistency and generated-surface ownership review.

**Specification Coverage:**
- Findings `[P2] CoS scheduling contract unnecessarily serializes eligible waves` and `[P3] Runtime ownership wording needs one symmetric boundary`.
- Task 1 owns adaptive executor/profile lifecycle resolution; this task does not
  add another selection mechanism.
- No automatic session/pane creation in this scope.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-chief-of-staff/SKILL.md` plan-bound dispatch and Herdr observation sections
- Modify: `docs/operating_system/planning/planning-dispatch.md` coordination and parallel-wave sections
- Modify: `tests/test_skill_chief_of_staff.py`
- Verify: `.agents/skills/skill-dispatching-parallel-agents/SKILL.md` for unchanged Herdr fan-out ownership

**Dependencies:**
- Task 3 defines launcher target-resolution evidence.
- Existing `parallel-capable`, isolated-worktree, disjoint-ownership, and sole-ledger-writer rules remain authoritative.

**Authority:**
- Preauthorized local actions: edit canonical CoS/planning guidance and focused contract tests.
- Stop for: new plan fields, adaptive executor/profile semantics, direct pane mutation by CoS, or changes to Git authority.

**Steps:**
- [x] Step 1: Replace the single-task rule with smallest dependency-ready action semantics; allow an isolated dependency-ready wave only for `parallel-capable` plans with proven independence.
- [x] Step 2: State that CoS may perform bounded read-only Herdr observation but all target resolution and pane/session mutation remains launcher-owned.
- [x] Step 3: State that native Codex controller dispatch does not require `HERDR_ENV`; launcher evidence is the dispatch proof.
- [x] Step 4: Update contract tests for sequential fallback, valid parallel wave, invalid same-workspace overlap, read-only observation, and `HERDR_ENV` non-gating.

**Verification:**
- [x] `py -m pytest -q tests/test_skill_chief_of_staff.py`
- Expected: policy tests prove no direct subagent dispatch, no adaptive runtime override, valid wave autonomy, and correct controller/runtime boundary.

**Exit Criteria:**
- CoS guidance grants useful scheduling autonomy without expanding task authority or bypassing launcher evidence.

### Task 5: Reconcile runtime documentation and generated adapters

**Purpose:**
- Remove remaining provider-facing contradictions and preserve generated-surface parity.

**Task Function:**
- Update canonical runtime ownership documentation and regenerate projections.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: deterministic documentation and generated-output maintenance.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: source/generated parity and repository contract validation.

**Specification Coverage:**
- Runtime surface ownership, observation boundaries, launcher target resolution,
  and generated adapter integrity.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/runtime/runtime-surfaces.md`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Regenerate: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`
- Regenerate: `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`
- Regenerate: `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`
- Verify: `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`, and `scripts/validate_agent_runtime_drift.py`

**Dependencies:**
- Tasks 1–4 complete and focused tests pass.
- Canonical `.agents/skills` and `docs/operating_system` sources are final before sync.

**Authority:**
- Preauthorized local actions: edit named canonical docs, run adapter sync and validators, inspect generated diffs.
- Stop for: manual generated-surface edits, provider installation/authentication, or changes outside named targets.

**Steps:**
- [x] Step 1: Update runtime-surface ownership from profile projection only to profile projection plus existing-target resolution through the launcher.
- [x] Step 2: Separate read-only Herdr observation from launcher-owned target resolution, start, cleanup, and other mutating lifecycle operations.
- [x] Step 3: Run `py scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 4: Verify generated outputs contain canonical guidance and no manual drift.

**Verification:**
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: adapter outputs are current.
- [x] `py -B "$HOME/.agents/project-os/scripts/validate_repo_contracts.py" --repo-root . --fast`
- Expected: repository contract validation passes.
- [x] `py scripts/validate_agent_runtime_drift.py --all-platforms`
- Expected: factory runtime drift validation passes.

**Exit Criteria:**
- Canonical and generated guidance describe one consistent CoS → launcher → Herdr ownership chain.

## Verification

- `py -m pytest -q tests/test_herdr_main_launcher.py tests/test_skill_chief_of_staff.py tests/test_sync_agent_adapters.py`
- `py scripts/sync_agent_adapters.py --all-platforms --check`
- `py -B "$HOME/.agents/project-os/scripts/validate_repo_contracts.py" --repo-root . --fast`
- `py scripts/validate_agent_runtime_drift.py --all-platforms`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. DeepAgents and Codex launcher subprocesses use the same cleaned Herdr environment invariant.
2. `--session auto --pane auto` resolves exactly one existing eligible target or emits machine-readable not-found/ambiguous evidence.
3. Explicit session/pane launches retain existing behavior and validation.
4. CoS may schedule only proven independent waves in `parallel-capable` plans.
5. CoS read-only observation and launcher-owned mutation are documented symmetrically.
6. Executor/profile resolution remains one durable task-record decision; effective grants and runtime topology remain transient launcher/Herdr facts, with automatic runtime creation out of scope.
7. Focused tests, adapter sync, repository validation, drift validation, and diff checks pass.
8. Existing uncommitted user changes and untracked `.playwright-mcp/` and `db/` remain preserved.

Plan completed after repository implementation, approved global deployment,
fresh runtime drift validation, repository contract validation, focused tests,
and diff checks.
