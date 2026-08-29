---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: chief-of-staff-update
targets:
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-using-git-worktrees/SKILL.md
  - .agents/skills/skill-finishing-a-development-branch/SKILL.md
  - .agents/skills/skill-reviewing-pull-requests/SKILL.md
  - .agents/skills/skill-requesting-code-review/SKILL.md
  - docs/operating_system/rules/git-tracked-coordination-rule.md
  - docs/operating_system/templates/implementation-plan-template.md
  - docs/operating_system/planning/planning-dispatch.md
  - tests/test_skill_chief_of_staff.py
  - tests/test_git_lane_lifecycle.py
  - tests/test_skill_reviewing_pull_requests.py
  - tests/test_native_personal_local_workflow.py
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/codex/skills/skill-executing-plans/SKILL.md
  - generated_agents/claude/skills/skill-executing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-executing-plans/SKILL.md
  - generated_agents/codex/skills/skill-using-git-worktrees/SKILL.md
  - generated_agents/claude/skills/skill-using-git-worktrees/SKILL.md
  - generated_agents/antigravity/skills/skill-using-git-worktrees/SKILL.md
  - generated_agents/codex/skills/skill-finishing-a-development-branch/SKILL.md
  - generated_agents/claude/skills/skill-finishing-a-development-branch/SKILL.md
  - generated_agents/antigravity/skills/skill-finishing-a-development-branch/SKILL.md
  - generated_agents/codex/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/claude/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/antigravity/skills/skill-reviewing-pull-requests/SKILL.md
  - generated_agents/codex/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/claude/skills/skill-requesting-code-review/SKILL.md
  - generated_agents/antigravity/skills/skill-requesting-code-review/SKILL.md
  - .agents/rules/git-tracked-coordination-rule.md
---

## Goal

Add a minimal Chief-of-Staff coordination method to Project OS without creating
new project-state, executor, profile, plugin, workflow, or Herdr-state artifacts.
The method must specialize existing approved-plan execution rather than create
a competing execution owner. It may coordinate independent top-level Codex
sessions through Herdr only when runtime capability and project identity are
verified. Assigned write-capable main agents may use a narrowly preauthorized
Git/PR lane lifecycle through existing owners; CoS itself never mutates Git or
PR state. The active plan and Git remain durable coordination truth.

## Implementation Outcomes

### Canonical CoS skill

`.agents/skills/skill-chief-of-staff/SKILL.md` defines one reusable CoS method
with explicit activation, synthesis, attention selection, main-agent reuse or
fresh-session decisions, pull-based Herdr observation, status normalization,
blocker routing, and escalation rules. It references existing execution,
coordination, runtime, and parallel-write owners instead of duplicating them.
It may allocate logical work lanes, but delegates Git, worktree, review, and
branch-finishing mechanics to their existing owners and has no autonomous Git
or PR authority. A main agent may exercise bounded lane authority only when the
active plan explicitly grants it for its exact branch/worktree.

### Git lane and PR lifecycle

Existing coordination, worktree, finishing, review-request, review, and
verification owners define one-write-agent-per-isolated-worktree, provisional
lane commits, bounded push/PR/review/merge/cleanup actions, expected-head
protection, serialized integration per base branch, and merge-aware cleanup.
No PR registry, merge queue, branch registry, or Herdr state file is added.

### Execution-owner integration

`.agents/skills/skill-executing-plans/SKILL.md` remains the owner of approved
plan execution. CoS is an optional coordination specialization: inline and
ordinary native-subagent paths remain unchanged; verified Herdr main-agent
delegation is eligible only for a `codex` task whose independent top-level
context materially benefits sustained coordination. `deepagents` and `tura`
continue through their existing peer executor paths.

### Planning and starter alignment

`planning-dispatch.md` names CoS as a coordination-method specialization of
`skill-executing-plans` only for approved Git-tracked work that needs sustained
handoffs, independent lanes, or cross-task coordination.
Adapter outputs remain generated from `.agents/skills`, and starter-kit build
verification confirms the skill ships through the existing `.agents/skills`
manifest path.

### Regression proof

Focused tests prove CoS metadata, execution precedence, required boundary
language, exact status and acceptance vocabularies, activation guidance, and
that CoS does not require or create named duplicate state artifacts. They also
prove branch/worktree isolation, bounded lane authority, and the absence of
direct CoS Git or external-write authority. Repository contract, adapter-drift,
and starter-kit checks prove canonical/generated alignment.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-writing-plans`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace` for lead edits; exact isolated branch/worktree for every delegated write-capable main-agent lane
- Commit policy: `lane commits preauthorized inside declared lanes; lead checkpoint commits remain required after accepted proof`
- Preauthorized local actions: read declared source and test files, add declared skill and test files, edit declared planning guidance, execute bounded lane Git/PR lifecycle inside exact assigned branch/worktree, merge the exact approved PR into its declared base after all gates pass, regenerate declared adapters, build disposable starter output, run declared checks
- User-approval actions: scope expansion, semantic conflict resolution, force push, direct or exceptional base-branch mutation outside the preauthorized exact-PR merge path, PR retargeting, branch-protection bypass, merging a different PR/lane, publication, destructive recovery, unknown-file disposition, discard outside an assigned lane, cleanup outside a successfully merged lane
- Parallel ownership: `none`
- Sequential fallback: complete canonical skill and focused proof before planning guidance, adapter regeneration, or starter-kit verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `1`
- Branch: `main`
- Base commit: `39984109a0c42fa1f0df13d2ce6e37ccaa51c31b`
- Expected workspace: `.playwright-mcp/` and `db/` remain preserved untracked changes; plan changes remain separate from those artifacts
- Next action: commit verified changes
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused CoS and dispatch-precedence tests | `19 passed` |
| Task 2 | `completed` | current | `codex` | Task 1 | Git-lane/PR lifecycle tests and diff inspection | `6 passed` |
| Task 3 | `completed` | current | `codex` | Task 2 | planning guidance test and diff inspection | `5 passed` |
| Task 4 | `completed` | current | `codex` | Task 3 | adapter sync, starter build, repository contract checks | `81 passed; adapter sync passed; starter output passed; repository contracts passed; planning validator passed` |

## Task Breakdown

### Task 1: Align execution ownership and add CoS specialization

**Purpose:**
- Keep `skill-executing-plans` as approved-plan execution owner while adding the narrow CoS main-agent specialization and its contract proof.

**Task Function:**
- Define execution precedence and test repository-governed coordination behavior.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct source edit with repository coordination authority and no delegated runtime benefit.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: independently check authority, lifecycle, SSOT, and forbidden-artifact boundaries in the final skill text.

**Specification Coverage:**
- CoS is normal Codex lead-controller behavior plus `skill-chief-of-staff`.
- `skill-executing-plans` remains owner of approved-plan execution and existing executor dispatch.
- CoS owns only situational synthesis, attention selection, main-agent versus ordinary execution choice, main-agent reuse or fresh-session choice, neutral independent-lane briefs, Herdr observation, return normalization, blocker routing, escalation, and briefing.
- Herdr is runtime observation and main-agent session supervision only; it never becomes task acceptance or durable coordination truth.
- For `Executor: codex`, lead inline and ordinary native-subagent paths remain unchanged; verified Herdr main-agent delegation is a CoS specialization only when an independent top-level context materially benefits sustained coordination.
- `Executor: deepagents` continues through `dcode-project`; `Executor: tura` continues through `project-delegate`. Herdr never wraps or addresses their internal workers.
- CoS activation requires deterministic plan binding from the approved execution context. Validate plan status, repository/worktree/branch identity, and task ledger before dispatch; resolve behavior through `parent_spec` when present, otherwise the plan's specification coverage or approved direct scope.
- Resolve plan binding in this order: explicit supplied plan path; plan already bound by current execution context; exactly one active plan matching current repository/worktree; otherwise `BLOCKED` with candidate evidence. Never choose newest filename, first match, or conversation-only inference.
- Missing, stale, mismatched, or ambiguous plan binding blocks; CoS does not scan globally and guess.
- Herdr/Codex parity is a concrete runtime gate: on relevant executable/configuration/provider/tooling change verify expected `herdr` and `codex` versions, `CODEX_HOME`, provider/model, required MCP/tool surface, sandbox, approval policy, and startup/trust prompts. Reuse that result until relevant runtime inputs change; every launch/reuse performs a cheap lane-identity check.
- Every main-agent launch/reuse verifies repository root, Git common directory, exact worktree, exact branch, HEAD, expected base, lane ownership, and launched process cwd. A mismatch blocks before write-capable launch.
- V1 attention is pull-based on an explicit CoS turn or verified polling/subscription; Herdr lifecycle state never proves acceptance.
- Main-agent returns use `DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED`; CoS acceptance uses `PASS | FAIL | BLOCKED`.
- Existing coordination, runtime-resolution, parallel-write, authority, and verification rules remain owners; CoS references them rather than restating or replacing them.
- CoS must not require, create, or treat `identity.md`, `cos.yaml`, fleet, heartbeat, supervisor, workflow database, model registry, or Herdr-state files as coordination state.
- CoS may allocate a logical lane only after task activation; every write-capable main agent receives one exact branch and isolated worktree, while same-workspace writers remain sequential and concurrent writers require disjoint ownership and a dependency-ready wave.
- `skill-using-git-worktrees` owns worktree creation/reuse and identity checks; `skill-requesting-code-review` owns review dispatch; `skill-verification-before-completion` owns final evidence; `skill-finishing-a-development-branch` owns authorized branch/worktree disposition.
- CoS does not commit, push, create or update PRs, submit reviews, merge, delete branches, or remove worktrees directly. An assigned write-capable main agent may exercise explicit lane authority through those existing owners for its exact branch/worktree. A lane commit, opened PR, or merged PR never completes a task or updates the ledger automatically.
- CoS grants one dependency-ready integration action at a time for each base branch to one designated main agent; reuse implementation-main or select a fresh integration main agent when context isolation materially helps. No permanent integration role is introduced.
- After accepted or merged lane work, CoS prevents new writes, retires/stops the Herdr main-agent session, confirms no live process owns the worktree, then invokes finishing cleanup. An agent never removes the worktree from which it is running.

**Required Skills:**
- `skill-code-standards`
- `skill-executing-plans`
- `skill-using-git-worktrees`
- `skill-requesting-code-review`
- `skill-finishing-a-development-branch`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-subagent-driven-development/SKILL.md:Handling Implementer Status`
- Inspect: `docs/operating_system/rules/git-tracked-coordination-rule.md`
- Inspect: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Inspect: `docs/operating_system/templates/implementation-plan-template.md:Execution Approach`
- Inspect: `.agents/skills/skill-executing-plans/SKILL.md:executor dispatch`
- Inspect: `.agents/skills/skill-using-git-worktrees/SKILL.md:worktree ownership`
- Inspect: `.agents/skills/skill-requesting-code-review/SKILL.md:review ownership`
- Inspect: `.agents/skills/skill-verification-before-completion/SKILL.md:final evidence ownership`
- Inspect: `.agents/skills/skill-finishing-a-development-branch/SKILL.md:branch and worktree disposition`
- Create: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Create: `tests/test_skill_chief_of_staff.py`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md:codex dispatch precedence`
- Modify: `tests/test_native_personal_local_workflow.py:executor dispatch assertions`

**Dependencies:**
- Direct approved scope from the critical verdict review.
- Existing lifecycle, coordination, executor, profile, and runtime rules remain authoritative.

**Authority:**
- Preauthorized local actions: create the declared skill and focused test; run focused read-only checks.
- Stop for: any need to add project-specific state, change executor/profile schemas, alter root authority, invent Herdr commands or event semantics, route `deepagents`/`tura` through Herdr, or grant CoS autonomous Git/PR/external-write authority.

**Steps:**
- [x] Step 1: Modify `skill-executing-plans` so it remains execution owner and defines CoS precedence for `Executor: codex` without changing `deepagents` or `tura` paths.
- [x] Step 2: Create CoS metadata with zero or one unconditional `required_reads` entry; use `docs/operating_system/rules/git-tracked-coordination-rule.md` as the one unconditional read and place planning, runtime, and execution references under `Conditional References`.
- [x] Step 3: Write CoS sections for activation, ownership boundaries, situational synthesis, attention selection, main-agent reuse/fresh choice, neutral lanes, Herdr observation, return normalization, blocker routing, and escalation. Reference existing execution, coordination, runtime, parallel-write, and verification owners.
- [x] Step 4: Define deterministic plan binding: supplied path, current execution binding, or exactly one active repository/worktree match; use `parent_spec`-first behavior resolution and return `BLOCKED` with candidates on ambiguity.
- [x] Step 5: Define heavy Herdr/Codex parity proof on relevant runtime/configuration change, cached until inputs change, plus cheap lane identity proof on every main-agent launch/reuse.
- [x] Step 6: Add Git-lane boundaries: one write-capable agent per branch/worktree, existing skill ownership for worktrees/review/verification/finishing, no direct CoS Git/PR mutation, and only explicit bounded lane authority for the assigned main agent.
- [x] Step 7: Add focused assertions for execution precedence, exact vocabularies, deterministic binding, parity and lane identity gates, scoped non-creation language, CoS-versus-lane-agent authority, and no autonomous event-supervision claim; extend native personal-local workflow assertions for executor routing.

**Verification:**
- [x] `py -m pytest tests/test_skill_chief_of_staff.py tests/test_native_personal_local_workflow.py -q`
- Expected: all focused assertions pass; tests fail if metadata, ownership precedence, boundary language, status mapping, scoped artifact exclusions, or Git-lane authority boundaries regress.

**Exit Criteria:**
- Execution owner and CoS specialization are unambiguous, canonical skill owns no duplicated project state, and focused tests pass.

### Task 2: Define bounded Git lane and PR lifecycle

**Purpose:**
- Remove manual lifecycle gaps without giving CoS direct Git/PR authority or adding a registry, queue, daemon, or state file.

**Task Function:**
- Align canonical worktree, coordination, plan-template, branch-finishing, and PR-review owners around one explicitly preauthorized lane contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-owner contract change affecting isolated writes, Git disposition, PR review, and merge cleanup.

**Validator Profile (optional):**
- Controller-selected: `xhigh`
- Selection basis: independently challenge authority boundaries, expected-head protection, checkpoint semantics, merge serialization, and cleanup safety.

**Specification Coverage:**
- `skill-using-git-worktrees` makes an isolated branch/worktree mandatory for every write-capable Herdr main-agent lane; ordinary execution keeps conditional isolation.
- One write-capable main agent owns one exact branch/worktree; validate repository root, base, branch, worktree, HEAD, and lane-owned paths before launch or reuse.
- An approved plan may explicitly preauthorize the assigned main agent to create/reuse its lane, commit lane-owned changes, push only its lane branch, create/update its PR, respond to review comments, submit an assigned review, merge only after required gates, and clean only its verified-clean successfully merged lane.
- The preauthorized merge path is only the exact approved PR into its declared base after required gates; direct base push/update, PR retargeting, branch-protection bypass, semantic conflict resolution, and merging another PR/lane remain user-authorized.
- Never preauthorize force push, direct protected/base-branch push, unrelated branch/worktree mutation, semantic conflict resolution, destructive recovery, unknown-file discard, publication, or scope expansion.
- `git-tracked-coordination-rule.md` distinguishes provisional lane commits from lead-owned coordination checkpoint commits; task acceptance and ledger transitions remain explicit and durable in the active plan plus Git.
- Integration targeting one base branch is serialized; merge requires expected reviewed head, required review/proof, clean state, and no post-review lane commit. Open or merged PR state never auto-completes a task.
- New `skill-reviewing-pull-requests` owns independent PR review; `skill-requesting-code-review` remains topology-neutral review dispatch owner; `skill-receiving-code-review` remains feedback evaluation owner.
- Project OS review evidence is distinct from GitHub approval. Review results include repository, PR number, base ref/SHA when material, head ref/SHA, verdict, checks inspected, and known limits. GitHub `APPROVE` is attempted only when reviewer identity is eligible and repository rules allow it; otherwise use `COMMENT` or no GitHub action. Required distinct-identity approval yields `BLOCKED`.
- CoS retires the implementation or review main-agent session before finishing removes its former worktree; cleanup confirms no live process owns that path.
- One designated main agent receives each serialized integration action; no permanent integration role or registry is added.
- `skill-finishing-a-development-branch` accepts exact plan-granted lane authority while retaining safety gates and explicit approval for exceptional or destructive actions.
- The implementation-plan template documents lane authority as a bounded exception to ordinary user-approval actions; it does not change plan schema or executor values.

**Required Skills:**
- `skill-using-git-worktrees`
- `skill-requesting-code-review`
- `skill-receiving-code-review`
- `skill-verification-before-completion`
- `skill-finishing-a-development-branch`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-using-git-worktrees/SKILL.md:workspace isolation and authorization`
- Inspect: `.agents/skills/skill-requesting-code-review/SKILL.md:review dispatch`
- Inspect: `.agents/skills/skill-receiving-code-review/SKILL.md:feedback handling`
- Inspect: `.agents/skills/skill-verification-before-completion/SKILL.md:proof ownership`
- Modify: `.agents/skills/skill-using-git-worktrees/SKILL.md:mandatory Herdr lane isolation and plan-granted authority`
- Modify: `.agents/skills/skill-finishing-a-development-branch/SKILL.md:bounded lane lifecycle and merge-aware cleanup`
- Modify: `.agents/skills/skill-requesting-code-review/SKILL.md:topology-neutral review dispatch`
- Create: `.agents/skills/skill-reviewing-pull-requests/SKILL.md`
- Modify: `docs/operating_system/rules/git-tracked-coordination-rule.md:lane commits, serialized integration, expected-head and cleanup gates`
- Modify: `docs/operating_system/templates/implementation-plan-template.md:bounded lane authority wording`
- Create: `tests/test_git_lane_lifecycle.py`
- Create: `tests/test_skill_reviewing_pull_requests.py`

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit declared canonical owners, create declared PR-review skill and focused tests, run read-only Git fixtures and focused checks.
- Network actions remain unavailable to this plan execution; document exact push/PR/merge commands and gates without running them.
- Stop for: direct CoS Git mutation, broad protected-branch authority, force-push or conflict automation, new persistent state, changed executor/profile schema, or any unrelated workspace mutation.

**Steps:**
- [x] Step 1: Add explicit distinction between CoS coordination authority and assigned main-agent lane authority, including exact-PR merge as the only preauthorized base write.
- [x] Step 2: Make Herdr write-capable main-agent isolation mandatory and bind launch to exact verified branch/worktree identity.
- [x] Step 3: Define plan-granted lane lifecycle and forbidden actions in worktree and branch-finishing owners; distinguish exact gated PR merge from exceptional base mutation.
- [x] Step 4: Define provisional lane commits, lead checkpoint commits, serialized base integration, expected reviewed head, and merge-aware cleanup in the Git coordination rule.
- [x] Step 5: Make review dispatch topology-neutral, add independent PR-review evidence bound to exact head SHA, separate Project OS review from GitHub approval identity, and route request, review, feedback, verification, retirement, and finishing responsibilities without overlap.
- [x] Step 6: Align implementation-plan template authorization wording and add focused assertions for authority, lifecycle, gates, and no registry/state artifacts.

**Verification:**
- [x] `py -m pytest tests/test_git_lane_lifecycle.py tests/test_skill_reviewing_pull_requests.py -q`
- Expected: tests prove mandatory Herdr lane isolation, exact bounded actions, forbidden actions, owner references, expected-head/merge/cleanup gates, and no persistent registry/state requirement.
- [x] `git diff --check`
- Expected: no whitespace errors in canonical owner changes.

**Exit Criteria:**
- Assigned main agents can complete only their explicitly granted lane lifecycle through existing owners; CoS remains non-mutating; merge and cleanup require durable evidence and exact-head safety gates.

### Task 3: Add CoS activation guidance to planning dispatch

**Purpose:**
- Connect CoS selection to existing planning policy as a coordination method without changing plan schema, executor values, or root authority.

**Task Function:**
- Add one `Coordination Method Selection` section for sustained coordination.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow documentation change governed by existing planning policy.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: check that activation remains conditional and does not create fixed task-function-to-profile or task-function-to-executor mapping.

**Specification Coverage:**
- Use CoS as a specialization of `skill-executing-plans` only for approved Git-tracked work needing sustained handoffs, independent lanes, or cross-task coordination.
- Use existing execution skills for ordinary single-lane or local work.
- Keep `Executor` values limited to `codex`, `deepagents`, and `tura`; Herdr is not an executor and `skill-executing-plans` remains execution owner.
- Keep root authority, plan/Git ownership, and user-approval boundaries unchanged.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/planning/planning-dispatch.md:Executor Selection`
- Inspect: `docs/operating_system/governance/repo-governance.md:Planning Ownership`
- Modify: `docs/operating_system/planning/planning-dispatch.md:Coordination Method Selection`
- Verify: `tests/test_skill_chief_of_staff.py:planning activation assertions`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: edit the declared planning-dispatch section and extend the focused test.
- Stop for: any proposed root `AGENTS.md` authority change, plan-contract field, executor value, or Herdr provider default.

**Steps:**
- [x] Step 1: Add `## Coordination Method Selection` after artifact selection and before executor selection.
- [x] Step 2: Add one conditional row selecting `skill-chief-of-staff` as a specialization of `skill-executing-plans` only for approved sustained top-level coordination.
- [x] Step 3: State that ordinary execution and all executor choices remain with existing execution policy; Herdr remains runtime supervision, not executor selection.
- [x] Step 4: Assert exact activation language and unchanged executor vocabulary in the focused test.

**Verification:**
- [x] `py -m pytest tests/test_skill_chief_of_staff.py -q`
- Expected: coordination-method section exists, remains conditional, and does not introduce `herdr` as an executor or a second execution owner.

**Exit Criteria:**
- Planning dispatch points to CoS without duplicating authority or expanding the planning schema.

### Task 4: Regenerate adapters and verify starter propagation

**Purpose:**
- Rebuild generated agent surfaces from canonical sources and prove the new skill reaches the starter kit through existing packaging.

**Task Function:**
- Synchronize generated surfaces and run repository contract verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: generated-output ownership and final repository verification require controller authority.

**Validator Profile (optional):**
- Controller-selected: `review`
- Selection basis: inspect generated drift, starter inclusion, and unrelated workspace preservation.

**Specification Coverage:**
- `.agents/skills` remains canonical.
- Generated adapter files are regenerated, never hand-edited.
- Starter-kit output includes the new skill through `repo_config/starter-kit-manifest.json`.
- Existing untracked `.playwright-mcp/` and `db/` artifacts remain untouched.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`
- Inspect: `scripts/build_starter_kit.py`
- Verify: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-executing-plans/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-executing-plans/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-executing-plans/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-using-git-worktrees/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-using-git-worktrees/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-using-git-worktrees/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-finishing-a-development-branch/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-finishing-a-development-branch/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-finishing-a-development-branch/SKILL.md`
- Verify: `generated_agents/codex/skills/skill-reviewing-pull-requests/SKILL.md`
- Verify: `generated_agents/claude/skills/skill-reviewing-pull-requests/SKILL.md`
- Verify: `generated_agents/antigravity/skills/skill-reviewing-pull-requests/SKILL.md`
- Verify: `.agents/rules/git-tracked-coordination-rule.md`
- Verify: `out/project-OS-starter-kit/.agents/skills/skill-chief-of-staff/SKILL.md`
- Verify: `out/project-OS-starter-kit/.agents/skills/skill-reviewing-pull-requests/SKILL.md`
- Verify: `out/project-OS-starter-kit/.agents/skills/skill-using-git-worktrees/SKILL.md`
- Verify: `out/project-OS-starter-kit/.agents/skills/skill-finishing-a-development-branch/SKILL.md`

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: regenerate declared adapters, create disposable `out/` starter output, and run declared checks.
- Stop for: generated drift outside declared skill outputs, changes to preserved untracked artifacts, or any failed contract check requiring unrelated fixes.

**Steps:**
- [x] Step 1: Run `py scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Run `py scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 3: Run `py scripts/build_starter_kit.py --output-root out`.
- [x] Step 4: Verify starter output contains updated `.agents/skills/skill-chief-of-staff/SKILL.md`, `.agents/skills/skill-executing-plans/SKILL.md`, `.agents/skills/skill-using-git-worktrees/SKILL.md`, `.agents/skills/skill-finishing-a-development-branch/SKILL.md`, and `.agents/skills/skill-reviewing-pull-requests/SKILL.md`; verify private/generated factory paths remain excluded according to the manifest.
- [x] Step 5: Run focused and repository contract checks; inspect `git diff --check` and `git status --short`.

**Verification:**
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: no adapter drift.
- [x] `py scripts/validate_repo_contracts.py --fast`
- Expected: repository contract validation passes.
- [x] `py -m pytest tests/test_skill_chief_of_staff.py tests/test_git_lane_lifecycle.py tests/test_skill_reviewing_pull_requests.py tests/test_native_personal_local_workflow.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_agent_metadata_schema.py tests/test_validate_planning_lifecycle.py -q`
- Expected: all selected tests pass.
- [x] `git diff --check`
- Expected: no whitespace errors.
- [x] `git status --short`
- Expected: only declared plan, canonical source, planning guidance, focused test, and regenerated adapter changes; `.playwright-mcp/` and `db/` remain unchanged untracked paths.

**Exit Criteria:**
- Canonical and generated skill files match, starter output contains the skill, all declared checks pass, and no unrelated changes appear.

## Verification

- `py scripts/sync_agent_adapters.py --all-platforms --check`
- `py scripts/validate_repo_contracts.py --fast`
- `py -m pytest tests/test_skill_chief_of_staff.py tests/test_git_lane_lifecycle.py tests/test_skill_reviewing_pull_requests.py tests/test_native_personal_local_workflow.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_agent_metadata_schema.py tests/test_validate_planning_lifecycle.py -q`
- `git diff --check`
- `git status --short`

## Completion Criteria

The plan is ready for completion verification when:

1. `skill-executing-plans` remains the sole approved-plan execution owner and defines unambiguous CoS precedence
2. the canonical CoS skill implements its attention, synthesis, topology, status, escalation, runtime-observation, and CoS-versus-lane-agent Git/PR boundaries without duplicating existing owners
3. planning dispatch activates CoS only for sustained approved coordination
4. generated adapters and starter output match canonical skill sources
5. focused and repository checks pass with fresh output
6. bounded lane Git/PR lifecycle, expected-head integration, serialized base updates, and merge-aware cleanup are owned by existing canonical skills
7. no autonomous CoS Git/PR/external-write authority, root authority change, executor/profile schema, Herdr state artifact, or unrelated workspace change was introduced

The plan became `active` after explicit execution approval, and the lead
updated the ledger before each task transition. Fresh completion proof returned
verified; no branch disposition was requested.
