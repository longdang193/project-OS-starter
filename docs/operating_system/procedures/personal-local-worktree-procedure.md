# Native Personal-Local Worktree Procedure

Use `native-personal-local` for ordinary work by one trusted local OS user.
Git owns workspace identity and change evidence. Selected local executor is
Codex or DeepAgents; executor choice grants no extra authority. Codex is default
when plan omits executor.

## Start

Before work, record task objective, repository-relative allowed paths, base
commit, and declared checks. Missing any item means `block`.

Run every controller command with selected absolute workspace:

```powershell
$workspace = (Resolve-Path .).Path
$base = (git -C $workspace rev-parse HEAD).Trim()
git -C $workspace rev-parse --show-toplevel
git -C $workspace status --short --branch
git -C $workspace worktree list --porcelain
```

Follow
[`skill-using-git-worktrees`](../../../.agents/skills/skill-using-git-worktrees/SKILL.md):

- Reuse clean current checkout for small reversible work.
- Obtain explicit isolation consent, then create or reuse native Git worktree
  when current changes, task risk, or concurrent writers require isolation.
- Record absolute workspace, creation mechanism, branch or detached state,
  base, current `HEAD`, and preserved pre-existing changes.

Start selected local executor only from actual selected-workspace context. If
context cannot be proved, work directly in selected workspace or `block`.

For delegated roles, Codex uses parseable TOML based on shared `agents/*.toml`.
DeepAgents reads generated project subagents from `.deepagents/agents/`; those
are not `dcode --agent` primary profiles.
Both use provider and model selection from active user-local primary runtime.
Never add provider bindings, credentials, MCP config, hooks, memories, threads,
or mutable DeepAgents state to repository coordination.

## Resume In A New Task

When plan has `Coordination State`, one lead controller resumes only through
plan plus Git. Do not use Codex thread IDs, DeepAgents thread IDs, or `dcode -r`
as repository coordination state.

1. Open plan from selected workspace and identify recorded branch, base, active
   task, last checkpoint, expected workspace, next action, and blockers.
2. Run `git rev-parse --show-toplevel`, `git status --short --branch`,
   `git worktree list --porcelain`, and `git rev-parse HEAD`.
3. Compare current branch, base ancestry, `HEAD`, and workspace changes with
   plan coordination state.
4. Read task ledger. Resume recorded `active` task, or first dependency-ready
   `pending` task when no task is active.
5. Re-run declared proof for last completed task when checkpoint or current
   changes make prior evidence uncertain.
6. Record reconciled task, checkpoint, workspace, and next action in plan.
   Only lead controller updates coordination state or task ledger.
7. `block` before implementation on plan/Git mismatch, more than one active
   task, unknown checkpoint, out-of-scope changes, or unresolved blocker.

Completed task changes and lead-controller ledger update share checkpoint commit
after task-local proof. Push still requires separate explicit authorization.

## Check And Review

Run declared checks from selected workspace. Keep Git-owned evidence:

```powershell
git -C $workspace diff --name-status -z -M -C --find-copies-harder $base --
git -C $workspace diff --name-status -M -C --find-copies-harder $base --
git -C $workspace ls-files --others --exclude-standard -z
```

Review every emitted path against declared paths. For `R` or `C`, review both
source and destination paths. Include tracked, staged, unstaged, deleted,
renamed, copied, type-changed, and untracked changes.

Record `block` and preserve workspace and evidence when a declared command or
check fails; paths are unsafe or outside scope; a conflict, nested repository,
or submodule change exists; workspace context is uncertain; or required Git
evidence is missing.

When checks and scope proof pass, operator records `accept` or `block` in task
handoff. `accept` hands off only to
[`skill-finishing-a-development-branch`](../../../.agents/skills/skill-finishing-a-development-branch/SKILL.md)
for explicitly authorized keep, commit, merge, push, discard, or cleanup.
`block` changes no Git state. Recovery or destructive discard needs separate
explicit authorization.

Neither disposition commits, merges, pushes, releases, stashes, resets, cleans,
prunes, removes, or force-removes a worktree.

## Docker Boundary

Use Docker only when repository already owns declared setup or check commands.
This procedure never creates, starts, stops, or manages containers.
