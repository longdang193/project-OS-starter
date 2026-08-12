# Native Personal-Local Worktree Procedure

Use `native-personal-local` for ordinary work by one trusted local OS user.
Git owns workspace identity and change evidence. Codex native work is advisory.

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

Start Codex native work only from actual selected-workspace context. If context
cannot be proved, work directly in selected workspace or `block`.

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
