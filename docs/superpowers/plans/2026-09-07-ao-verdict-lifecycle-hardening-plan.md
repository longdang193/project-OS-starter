---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: ao-verdict-lifecycle-hardening
parent_spec: none
targets:
  - docs/operating_system/planning/planning-dispatch.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - scripts/herdr_main_launcher.py
  - scripts/validate_planning_lifecycle.py
  - tests/test_herdr_main_launcher.py
  - tests/test_validate_planning_lifecycle.py
  - tests/test_skill_chief_of_staff.py
  - generated_agents/
---

# AO Verdict Lifecycle Hardening

## Goal

Adopt four bounded lessons from `Untrivial-ai/agent-orchestrator` without
turning `project-OS-starter` into an AO clone:

1. executor-owned capability projection;
2. lane state derived from plan, Git, runtime, and review facts;
3. stable task ownership across runtime replacement;
4. owner-first CI, review, merge, and conflict feedback routing.

Plan and Git remain SSOT. Runtime agents, panes, and executor processes remain
replaceable.

## Implementation Outcomes

### Capability projection

- Validate requested executor, profile, grant, and capability selectors before
  retiring the current lane.
- Preserve native/default executor behavior when no explicit capability is
  requested.
- Fail closed for unsupported requested capabilities.
- Keep executor-specific behavior at the adapter boundary.
- `dcode-project` owns DeepAgents capability validation and child projection;
  Herdr only forwards explicit `--mcp-select` values or default `--no-mcp`.

### Derived lane state

- Do not persist `working`, `stuck`, `ready`, `needs-attention`, or equivalent
  CoS state.
- Derive state from fresh plan, Git, runtime, and applicable CI/review facts.
- Keep launcher evidence descriptive; it must not become a second task registry.

### Stable ownership

- Require an existing canonical plan binding for plan-bound replacement:
  repository identity, plan path, and plain `Task N` reference.
- Launch evidence may echo that binding but may not create a fallback identity.
- Missing or ambiguous binding blocks replacement.
- Runtime replacement changes execution surface, not task, worktree, branch, or
  PR ownership.

### Safe lifecycle transition

Use a bounded local sequence, without persistent transaction state:

```text
PREPARE -> RETIRE -> RECONCILE -> DISPATCH
```

- Failed `PREPARE` leaves current lane active.
- `RETIRE` requires affirmative process, pane, and worktree safety evidence.
- `RECONCILE` reloads plan and Git facts and prevents duplicate active work.
- `DISPATCH` reuses the same plan task identity.
- Timeout returns `TIMEOUT` only after cleanup proof; otherwise returns
  `BLOCKED`.
- Capture launch-owned process identity before pane close. Pane absence,
  malformed evidence, empty process evidence, or failed post-close inspection
  remains `BLOCKED` unless executor-specific proof establishes safe retirement.

### Failure and recovery

- Recheck plan path, HEAD, worktree, and task binding before retirement and
  before replacement dispatch.
- A competing dispatch for the same task/worktree blocks replacement.
- Retirement success followed by replacement launch failure enters recovery
  inspection; it does not silently retry.
- Lost delivery acknowledgement triggers runtime and task inspection before
  any retry.
- Recovery uses existing plan, Git, and runtime evidence only.

### Feedback routing

- Extend existing explicit-turn Attention Audit; add no observer loop.
- Route implementation fixes to the canonical task's currently bound lane.
- Preserve independent review and designated integration authority.
- Semantic conflicts follow existing escalation rules.

### Explicit non-goals

- No AO daemon.
- No SQLite or persistent orchestration database.
- No CDC, Kanban, or UI layer.
- No independent launcher-owned task identity.
- No full two-phase protocol unless tests prove the bounded sequence unsafe.

## Task Function

Implementation planning, lifecycle hardening, contract reconciliation, and
backend verification.

## Template Profile

`none (lead controller)`; implementation remains inline and plan-owned.

## Validator Profile

`review`; independently check capability projection, ownership preservation,
cleanup proof, and generated-surface parity.

## Specification Coverage

- AO review verdict: adopt selective architecture patterns only.
- Existing CoS Adaptive Runtime Grants plan: preserve transient grants,
  capability validation, and plan/Git reconciliation.
- Existing Herdr DeepAgents Observability plan: preserve pull-based evidence,
  lifecycle distinction, default-deny MCP, and cleanup proof.
- Repository SSOT, permanence, symmetry, and generated-surface rules.

## Required Skills

- `skill-executing-plans`
- `skill-code-standards`
- `skill-backend-verification`
- `skill-verification-before-completion`
- `skill-requesting-code-review`

## Files And Symbols

- `scripts/herdr_main_launcher.py`: `resolve_launch`,
  `_normalize_runtime_grant`, `_codex_watchdog_seconds`,
  `_codex_assignment_command`, `_terminate_codex_lane`, `main`.
- `tests/test_herdr_main_launcher.py`: grant projection, MCP selector,
  timeout, cleanup, redispatch, and dry-run regression tests.
- `scripts/validate_planning_lifecycle.py`: task identity, authority, and
  plan-state validation boundaries.
- `tests/test_validate_planning_lifecycle.py`: lifecycle contract regressions.
- `.agents/skills/skill-chief-of-staff/SKILL.md`: derived state, grant, and
  feedback ownership rules.
- `docs/operating_system/planning/planning-dispatch.md`: executor and grant
  boundary.
- `docs/operating_system/procedures/runtime-adapter-procedure.md`: adapter
  capability projection and evidence.
- `docs/operating_system/runtime/runtime-surfaces.md`: runtime evidence and
  lifecycle semantics.
- `generated_agents/`: regenerated adapter surfaces only; never edit directly.

## Dependencies

- Existing grant plan:
  `docs/superpowers/plans/2026-09-06-cos-adaptive-lane-grants-plan.md`.
- Existing observability plan:
  `docs/superpowers/plans/2026-09-06-herdr-deepagents-observability-plan.md`.
- Current base commit: `7bf2c762`.
- Preserve existing modified and untracked workspace paths.
- External runtime deployment was explicitly approved on September 7, 2026.
- No credentials, authentication, commits, pushes, merges, or destructive cleanup
  were authorized.

## Authority

- Plan task `Authority` remains durable maximum authority.
- Runtime grant remains transient and bounded by validated plan authority.
- Plan and Git own task identity, scope, worktree, branch, and completion.
- Runtime evidence may prove facts but may not create competing authority.
- Unsupported capability must fail before current lane retirement.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Coordination schema: `2`
- Default task executor: `codex`
- Validator executor: `review`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Branch: current working branch
- Base commit: `7bf2c762`
- Expected workspace: existing dirty and untracked state preserved
- Next action: none; final verification complete
- Blockers: none

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `current working branch`
- Base commit: `7bf2c762`
- Expected workspace: `existing dirty and untracked state preserved`
- Next action: none; final verification complete
- Blockers: none

## Task Breakdown

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | completed | current | codex | none | baseline tests and launcher dry-run | `81 passed`; live probe blocked by missing Herdr session |
| Task 2 | completed | current | codex | Task 1 | capability and default-deny tests | focused contract tests passed |
| Task 3 | completed | current | codex | Task 1 | canonical-binding docs and ownership contract tests | plan/skill contract validation passed |
| Task 4 | completed | current | codex | Task 2, Task 3 | retirement, timeout, cleanup, and recovery tests | `35 passed`; unknown process evidence blocks |
| Task 5 | completed | current | codex | Task 2, Task 3, Task 4 | canonical sync and generated parity | all-platform adapter sync passed |
| Task 6 | completed | current | codex | Task 5 | full test, validators, diff check, runtime probe | `378 passed`; all-platform runtime drift passed; adapter parity passed; Herdr DeepAgents probe delivered and returned pane to PowerShell; native Codex 1-second watchdog returned `BLOCKED` on surviving-process evidence |

## Steps

### Task 1: establish evidence baseline

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Authority:**

- Preauthorized local actions: inspect sources, tests, plans, and current runtime evidence.
- Stop for: credentials, authentication, installation, external writes, or destructive cleanup.

**Steps:**
- [x] Record workspace and current plan state.
- [x] Run focused baseline tests and launcher dry-run.
- [x] Record current capability, identity, and cleanup behavior.

- Record `git status --short` and preserve all existing dirty/untracked paths.
- Run current focused launcher and planning tests.
- Capture launcher dry-run output.
- Confirm whether canonical `task_id` already exists.
- Confirm current `mcp_select`, grant, timeout, and cleanup behavior.
- Replace no implementation until each gap maps to source or failed proof.

### Task 2: harden capability projection

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Authority:**

- Preauthorized local actions: edit declared launcher and test files; run focused tests and dry-runs.
- Stop for: changes outside declared targets, credential access, or unsupported external runtime mutation.

**Steps:**
- [x] Add or adjust capability projection tests.
- [x] Verify DeepAgents ownership remains `dcode-project`.
- [x] Verify unsupported selectors fail before retirement.

- Reuse existing launch and grant helpers.
- Test Codex and DeepAgents with no selector, supported selector,
  unsupported selector, and malformed selector.
- Reject unsupported requested capabilities before lane retirement.
- Preserve native/default behavior without explicit selection.
- Keep executor-specific projection below generic orchestration semantics.

### Task 3: preserve ownership

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Authority:**

- Preauthorized local actions: edit declared canonical files and tests; run lifecycle validators.
- Stop for: new persistence, new task registries, generated-file edits, or external writes.

**Steps:**
- [x] Require canonical repository, plan, and `Task N` binding.
- [x] Reject missing or ambiguous replacement binding.
- [x] Verify feedback routes to bound task lane.

- Reuse existing plan task identity.
- Add launch evidence `task_id` only if no canonical identity exists.
- Test runtime replacement preserving task, plan, worktree, branch, and PR
  ownership.
- Test CI, review, merge, and conflict feedback routing to the same owner.
- Prevent launcher evidence from becoming a second source of truth.

### Task 4: prove lifecycle safety

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Authority:**

- Preauthorized local actions: edit launcher tests and lifecycle code; run bounded local process and pane probes.
- Stop for: unrelated process termination, unrelated cleanup, credentials, or unbounded runtime actions.

**Steps:**
- [x] Capture launch-owned process identity before close.
- [x] Verify executor-specific retirement after close.
- [x] Test stage changes, competing dispatch, launch failure, and lost acknowledgement recovery.

- Validate executor, profile, grant, and capability before retirement.
- Require affirmative process-tree, pane, and worktree cleanup evidence.
- Distinguish cleanup success from failed probes and missing processes.
- Return `TIMEOUT` only when cleanup is proven; otherwise return `BLOCKED`.
- Reconcile plan and Git before redispatch.
- Reject duplicate active work.
- Keep failed preparation from destroying the current lane.

### Task 5: update canonical surfaces

**Template Profile:**
- Controller-selected: `none (lead controller)`

**Authority:**

- Preauthorized local actions: edit canonical docs and skills; run `scripts/sync_agent_adapters.py` and validators.
- Stop for: direct generated-file edits, publication, commits, pushes, or merges.

**Steps:**
- [x] Update canonical docs and skills.
- [x] Run adapter synchronization.
- [x] Verify generated parity.

- Update canonical planning, runtime, and CoS skill documents.
- State derived-state and ownership invariants explicitly.
- Document adapter-boundary capability projection.
- Document affirmative cleanup evidence.
- Regenerate agent adapters with `scripts/sync_agent_adapters.py`.
- Do not edit `generated_agents/` directly.

### Task 6: review and verify

**Template Profile:**
- Controller-selected: `review`

**Authority:**

- Preauthorized local actions: inspect diff; run declared tests, validators, and checks; record evidence.
- Stop for: implementation edits during review, status promotion without proof, commits, pushes, or merges.

**Steps:**
- [x] Run independent review.
- [x] Run focused and full verification.
- [x] Record fresh evidence.
- [x] Resolve shared runtime deployment drift or obtain explicit deployment authority.
- [x] Start or attach approved Herdr session and rerun live runtime probe.

- Request independent review against this plan.
- Resolve unsupported claims, stale paths, and generated drift.
- Record fresh evidence in this plan.
- Keep plan status `completed` after shared runtime deployment drift is reconciled
  and full verification passes.

## Verification

### Focused tests

```powershell
python -m pytest -q tests/test_herdr_main_launcher.py tests/test_validate_planning_lifecycle.py tests/test_skill_chief_of_staff.py
```

Expected: all focused tests pass, including capability, ownership,
redispatch, timeout, and cleanup cases.

### Repository validators

```powershell
python scripts/validate_planning_lifecycle.py
python scripts/validate_repo_contracts.py
python scripts/validate_generated_header_format.py
python scripts/validate_agent_runtime_drift.py
```

Expected: no lifecycle, contract, generated-header, or runtime-drift findings.

### Runtime evidence

- launcher dry-run with native/default grant;
- supported and unsupported capability probes;
- timeout with verified cleanup;
- timeout with failed cleanup proof;
- redispatch after plan/Git reconciliation;
- feedback routing with stable task identity.

### Final repository checks

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; existing unrelated dirty/untracked state
preserved; no generated drift.

## Completion Criteria

1. Unsupported requested capabilities fail closed before retirement.
2. Native/default executor behavior remains unchanged without explicit
   capability selection.
3. No competing task identity or persisted derived lane state is introduced.
4. Runtime replacement preserves plan task and feedback ownership.
5. Failed preparation preserves current lane.
6. Timeout status reflects affirmative cleanup evidence.
7. Redispatch reconciles plan and Git and cannot duplicate active work.
8. Canonical docs, tests, validators, and generated adapters agree.
9. AO daemon, database, UI, CDC, and Kanban scope remains excluded.
10. Fresh focused tests, full validators, diff checks, and runtime probes pass.

The plan may move from `active` to `completed` only after
`skill-verification-before-completion` returns `verified` against fresh
repository evidence.
