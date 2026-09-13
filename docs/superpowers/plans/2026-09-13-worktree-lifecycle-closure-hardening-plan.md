---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: worktree-lifecycle-closure-hardening
targets:
  - .agents/skills/skill-using-git-worktrees/SKILL.md
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-finishing-a-development-branch/SKILL.md
  - .agents/skills/skill-disposable-artifact-cleanup/SKILL.md
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/operating_system/templates/implementation-plan-template.md
  - scripts/herdr_main_launcher.py
  - tests/test_git_lane_lifecycle.py
  - tests/test_skill_chief_of_staff.py
  - tests/test_disposable_artifact_cleanup.py
  - tests/test_herdr_main_launcher.py
  - generated_agents/
  - .agents/rules/
  - docs/superpowers/plans/2026-09-13-worktree-lifecycle-closure-hardening-plan.md
---

# Worktree Lifecycle Closure Hardening

## Goal

Make worktree lifecycle predictable across creation, continuation, redispatch,
retirement, cleanup, and task resume without adding a registry, background
service, or new coordination state layer.

Preserve existing Git, plan, CoS, Herdr, and finishing ownership boundaries.

## Implementation Outcomes

### Canonical lane lifecycle

Document one write-capable lane as one exact branch plus one isolated worktree.
Allow healthy `CONTINUE` reuse after fresh identity checks. Require retirement
and reconciliation before redispatch or workspace reclamation for the same task.

Pin each lane to the exact plan-bound base commit. Do not derive lanes from
whatever `origin/main` contains at launch time.

### Safe closure ownership

Separate execution status from Git disposition. Reuse existing `Evidence`,
`Next action`, and finishing-report fields for closure outcomes. Keep workspace
outcomes separate from finishing results `closed | kept | blocked`.

Require positive retirement evidence for the lane, relevant descendants, and
task-owned resources before cleanup. Keep removal under
`skill-finishing-a-development-branch`.

### Correct deadline evidence

Ensure `_deepagents_completion_snapshot` marks an observation deadline exceeded
when either `process-info` or `pane read` crosses the monotonic deadline during
transport and raises `CommandTransportTimeout`.

### Generated-surface alignment

Regenerate adapter outputs only from canonical sources. Prove canonical skills,
rules, generated outputs, tests, planning contracts, and launcher behavior stay
consistent.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical files, tests, and plan; run declared sync commands, validators, and read-only preservation checks; preserve unrelated workspace state
- User-approval actions: commit, push, merge, branch deletion, worktree cleanup, destructive recovery, external writes, and edits outside listed targets
- Parallel ownership: none
- Sequential fallback: canonical lifecycle policy, closure ownership, launcher regression, adapter sync, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `fb8c9fa285d01e9162058b33e1f1fa26f3daa8c6`
- Expected workspace: preserve pre-existing untracked `.playwright-mcp/` and `db/`; do not stage, delete, or rewrite them
- Next action: retain primary checkout; no commit, merge, or worktree cleanup authorized
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | lifecycle wording and contract tests | `29 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | closure ownership and retention tests | `10 passed` |
| Task 3 | `completed` | current | `codex` | none | deadline-crossing regression tests | pre-fix `2 failed`; post-fix `121 passed` |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | sync, focused suite, aggregate validation, preservation proof | `173 passed`; aggregate validation passed; protected contents 42 files/0 changed |

## Task Breakdown

### Task 1: Align lane identity, continuation, and base rules

**Purpose:**
- Establish exact lane identity and deterministic base selection across worktree,
  CoS, and coordination contracts.

**Task Function:**
- Reconcile creation, `CONTINUE`, redispatch, base pinning, runtime binding, and
  primary-checkout rules.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation and contract-test update under inline
  controller execution.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing contract tests cover canonical wording.

**Specification Coverage:**
- One write-capable lane owns one exact branch and isolated worktree.
- Healthy `CONTINUE` reuses a live lane after identity checks.
- Redispatch requires prior-runtime retirement and Git/ownership reconciliation.
- Each lane uses the exact plan-bound base SHA.
- Primary checkout remains controller/integration workspace.

**Required Skills:**
- `skill-using-git-worktrees`
- `skill-chief-of-staff`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-using-git-worktrees/SKILL.md` sections `Detect Current Workspace`, `Handoff`, and `Cleanup Boundary`
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md` sections `Plan Binding`, `Runtime Gates`, `Lane Contract`, and `Returns And Retirement`
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Modify: the inspected canonical sections
- Modify: `tests/test_git_lane_lifecycle.py`
- Modify: `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Plan is active.
- Existing `.playwright-mcp/` and `db/` state remains preserved.

**Authority:**
- Preauthorized local actions: edit listed canonical lifecycle files and contract tests; run focused tests and diff checks
- Stop for: base changes, unresolved policy conflict, generated-file edits, or unrelated workspace mutation

**Steps:**
- [x] Step 1: Replace wording that requires retirement before healthy live-lane `CONTINUE`.
- [x] Step 2: State separate rules for `CONTINUE` versus redispatch/reclamation.
- [x] Step 3: Replace current-`origin/main` assumptions with plan-bound base SHA resolution and pinning.
- [x] Step 4: State primary-checkout read-mostly behavior and explicit integration exception.
- [x] Step 5: Require fresh identity, binding, HEAD, worktree, and ownership checks before continuation or replacement.
- [x] Step 6: Add contract assertions for exact branch/worktree identity, base pinning, `CONTINUE`, redispatch, and no nested worktrees.

**Verification:**
- [x] `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py -q` — `29 passed`
- Expected: all existing and new lifecycle assertions pass; assertions check
  documentation contracts only, not real process retirement.

**Exit Criteria:**
- Canonical lane identity and base rules no longer contradict `CONTINUE`,
  redispatch, or existing Git ownership contracts.

### Task 2: Harden closure, retention, and cleanup ownership

**Purpose:**
- Make closure decisions explicit and prevent unsafe worktree removal.

**Task Function:**
- Align finishing, disposable-artifact, and plan-template ownership boundaries.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded policy and contract-test update under inline
  controller execution.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing cleanup and Git lifecycle tests.

**Specification Coverage:**
- `DONE` remains execution status, not Git disposition.
- New lanes require clean expected state.
- Resumed lanes reconcile against recorded state.
- `BLOCKED`, `FAIL`, and `TIMEOUT` preserve recoverable changes.
- Cleanup requires exact authorization, verified Git disposition, retirement,
  content review, and released retention dependencies.
- Unknown ownership evidence preserves resources.
- Closure outcomes reuse existing `Evidence`, `Next action`, and finishing-report
  fields; no new mandatory lifecycle field is added.

**Required Skills:**
- `skill-finishing-a-development-branch`
- `skill-disposable-artifact-cleanup`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-finishing-a-development-branch/SKILL.md` sections `Authorization Rule`, `12. Worktree Cleanup`, and `13. Final Closure Report`
- Inspect: `.agents/skills/skill-disposable-artifact-cleanup/SKILL.md` sections `Lifecycle`, `Resource Identity And Ownership Proof`, `Cleanup Mode`, and `Producer Contract`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md`
- Modify: the inspected canonical sections
- Modify: `tests/test_disposable_artifact_cleanup.py`
- Modify: `tests/test_git_lane_lifecycle.py`

**Dependencies:**
- Task 1 complete.
- Existing cleanup ownership remains authoritative.

**Authority:**
- Preauthorized local actions: edit listed closure files and contract tests; run focused tests and diff checks
- Stop for: destructive cleanup, branch deletion, ownership ambiguity, retention uncertainty, or a new registry requirement

**Steps:**
- [x] Step 1: Remove implementation-lane self-removal ambiguity from plan and finishing wording.
- [x] Step 2: Require surviving controller handoff to `skill-finishing-a-development-branch`.
- [x] Step 3: Add exact removal gate for native-managed and manually created worktrees.
- [x] Step 4: Require review of tracked, staged, untracked, and ignored contents.
- [x] Step 5: Add recovery wording: re-establish exact identity and authorization through current plan plus validated handoff; otherwise preserve.
- [x] Step 6: Separate disposable external artifacts from durable reports, fixtures, and acceptance evidence.
- [x] Step 7: Reuse existing `Evidence`, `Next action`, and final closure-report fields for `removed`, `retained`, or `blocked` workspace outcomes.
- [x] Step 8: Keep this plan’s expected workspace disposition as `kept`; no worktree removal or commit is authorized.

**Verification:**
- [x] `py -3 -m pytest tests/test_disposable_artifact_cleanup.py tests/test_git_lane_lifecycle.py -q` — `10 passed`
- Expected: cleanup ownership, ignored-content review, preservation, and closure
  outcome assertions pass; assertions check policy contracts only.

**Exit Criteria:**
- No active lane removes its own worktree.
- No cleanup occurs without exact authority, positive retirement evidence, and
  retention review.

### Task 3: Fix deadline classification during transport

**Purpose:**
- Correct inconsistent observation evidence when the deadline expires during a
  transport call.

**Task Function:**
- Harden `_deepagents_completion_snapshot` timeout classification symmetrically
  for `process-info` and `pane read`.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: localized Python behavior change with focused regression.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct unit regression covers boundary behavior.

**Specification Coverage:**
- Process-info and pane-read handlers recheck monotonic deadline after transport
  timeout.
- Transport timeout remains transport timeout when deadline is absent or still
  unexpired.
- Deadline crossing reports `observation_deadline_exceeded: true`.
- Existing evidence fields and timeout budgets remain unchanged.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`
- Modify: `scripts/herdr_main_launcher.py:_deepagents_completion_snapshot`
- Inspect: `tests/test_herdr_main_launcher.py` timeout tests near lines 2347–2388
- Modify: `tests/test_herdr_main_launcher.py`

**Dependencies:**
- None.
- Keep launcher timeout budgets and transport commands unchanged.

**Authority:**
- Preauthorized local actions: edit `_deepagents_completion_snapshot` and focused launcher tests; run launcher tests
- Stop for: changed public evidence schema, changed timeout budget, unrelated launcher behavior, or real-runtime cleanup

**Steps:**
- [x] Step 1: Add regression test first and prove it fails against current code.
- [x] Step 2: Mock process-info success while time remains before deadline.
- [x] Step 3: Invoke `pane read` with a positive timeout; advance the mocked clock past the deadline inside the mocked transport call, then raise `CommandTransportTimeout`.
- [x] Step 4: Assert `pane read` was invoked, `observation_deadline_exceeded is True`, and `observation_error == "observation deadline exceeded"`.
- [x] Step 5: Add the symmetric process-info case, preserving transport-timeout classification when deadline remains unexpired or absent.
- [x] Step 6: Apply the smallest handler fix and rerun both regression cases.

**Verification:**
- [x] `py -3 -m pytest tests/test_herdr_main_launcher.py -q` — pre-fix `2 failed`; post-fix `121 passed`
- Expected: pre-fix regression fails, post-fix regression passes, existing
  transport-timeout behavior remains passing.

**Exit Criteria:**
- Snapshot evidence cannot report a plain transport timeout after monotonic
  observation deadline expiry.

### Task 4: Regenerate adapters and complete verification

**Purpose:**
- Reconcile generated surfaces and prove final behavior without touching
  unrelated workspace state.

**Task Function:**
- Run adapter sync, focused tests, aggregate contract validation, and final
  preservation checks.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: verification-only task under inline controller execution.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: aggregate repository validator and focused test output.

**Specification Coverage:**
- Canonical sources remain the only manually edited policy sources.
- Generated agent surfaces match canonical sources.
- Existing untracked `.playwright-mcp/` and `db/` contents remain unchanged.
- No new registry, background cleanup service, or lifecycle state file exists.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: canonical files from Tasks 1–3
- Verify: `generated_agents/`
- Verify: `.agents/rules/`
- Verify: `.playwright-mcp/`
- Verify: `db/`
- Modify: `docs/superpowers/plans/2026-09-13-worktree-lifecycle-closure-hardening-plan.md` evidence and task states only

**Dependencies:**
- Tasks 1–3 complete.
- Plan is `active` and every active task executor is resolved to `codex`.

**Authority:**
- Preauthorized local actions: run one adapter sync, focused tests, aggregate contract validation, diff checks, and read-only preservation comparison; update plan evidence and terminal state
- Stop for: generated drift after sync, failed required proof, external write, destructive cleanup, or unexpected path changes

**Steps:**
- [x] Step 1: Run a bounded read-only baseline comparison for all files under `.playwright-mcp/` and `db/`; retain normalized path, size, mtime, and SHA-256 evidence in task-local temporary storage outside the repository.
- [x] Step 2: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 3: Run the focused policy, cleanup, and launcher tests.
- [x] Step 4: Run `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` as aggregate validation.
- [x] Step 5: Run `git diff --check`.
- [x] Step 6: Repeat the bounded protected-content comparison and compare path, size, mtime, and SHA-256 records.
- [x] Step 7: Confirm generated files changed only through sync and no unlisted files changed.
- [x] Step 8: Record evidence, deviations, blockers, and closure outcome `kept` for this plan’s primary checkout.
- [x] Step 9: Fresh verification returned `verified`; plan status changed to `completed`.

**Verification:**
- [x] `py -3 -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_chief_of_staff.py tests/test_disposable_artifact_cleanup.py tests/test_herdr_main_launcher.py tests/test_sync_agent_adapters.py -q` — `173 passed`
- [x] `py -3 scripts/validate_repo_contracts.py --repo-root . --fast` — passed
- [x] `git diff --check` — passed
- [x] `git status --short` — only approved canonical, generated, test, launcher, and plan paths changed; `.playwright-mcp/` and `db/` preserved
- [x] Live Herdr → `dcode-project` boundary probe — first cold run delivered but crossed the 60-second observation deadline; warm retry on `herdr 0.9.0` and `deepagents-code 0.1.59` returned exit `0`, `status=completed`, `task_result.state=reported_completed`, `worker_exit_code=0`, valid `dcode-project.result.v1` receipt with `descendant_state=terminated`, `cleanup_state=removed`, `role_views_state=removed`, marker present, and shell-only pane after completion; probe pane `w2H:p2` closed with exit `0`
- Expected: focused tests and aggregate validation pass; generated outputs are
  synchronized; protected-content baseline and postflight hashes match; only
  approved canonical, generated, test, launcher, and plan paths change.

**Exit Criteria:**
- Fresh verification supports every implementation outcome.
- Plan ledger, Git state, generated surfaces, and test evidence agree.
- Plan status is `completed` only after `skill-verification-before-completion`
  returns `verified`.

## Non-Goals

- No worktree registry, lease database, heartbeat, supervisor, or background cleanup service.
- No automatic cleanup after timeout, silence, missing observation, or ambiguous ownership.
- No branch deletion or `git worktree prune` as routine closure.
- No recursive deletion of worktree directories.
- No change to Herdr timeout budgets, process commands, runtime providers, or model selection.
- No cleanup of pre-existing `.playwright-mcp/` or `db/` contents.
- No manual edits to generated agent surfaces.
- No new durable coordination state outside the active plan and Git.

## Verification

- Focused policy and lifecycle contract tests.
- Focused Herdr launcher regression suite.
- One adapter regeneration through `scripts/sync_agent_adapters.py`.
- Aggregate repository contract validation through `scripts/validate_repo_contracts.py --fast`.
- `git diff --check`.
- Read-only protected-content baseline and postflight comparison.
- Final workspace and changed-file inspection.

## Completion Criteria

1. Worktree rules distinguish healthy `CONTINUE` from redispatch/reclamation.
2. Write-capable lanes use one exact branch and isolated worktree.
3. Lane bases use exact plan-bound commits.
4. `DONE` remains separate from commit, merge, publication, and cleanup disposition.
5. Resumed dirty state is reconciled, not deleted to satisfy cleanliness.
6. Cleanup requires exact authority, positive retirement, content review, and released proof/recovery/handoff dependencies.
7. Retirement covers top-level lanes, relevant descendants, and task-owned resources.
8. Closure outcomes reuse existing evidence, next-action, and finishing-report fields.
9. Deadline crossing during `process-info` or `pane read` reports the correct observation flag and error.
10. Focused tests and aggregate repository validation pass with fresh output.
11. Generated outputs match canonical sources.
12. Pre-existing `.playwright-mcp/` and `db/` contents remain unchanged, or uncertainty is reported and plan stays non-completed.
13. Plan status transitions `proposed → active → completed` only at the defined lifecycle gates.
