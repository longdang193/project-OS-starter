# Native Personal-Local Worktree Procedure

Use `native-personal-local` for ordinary work by one trusted local OS user.
Git owns workspace identity and change evidence. Selected local executor is
Codex or DeepAgents; Codex is default when plan omits executor. Executor choice
does not change task paths, Git acceptance, or user approval. It can change
host-enforced tool containment; current DeepAgents containment is not a Codex
permission projection.

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

For delegated roles, `agents/*.toml` owns role prompts. Codex consumes deployed
TOML. User-local `dcode-project` materializes ignored `.deepagents/agents/`
views at launch. It derives `normal` and `low` from active `*-high` controller
model; use optional local `[roles]` overrides only for a provider without that
alias pattern. It is not a `dcode --agent` primary profile.

DeepAgents auto-loads root `AGENTS.md` and discovers `.agents/skills` as
project skills. It does not directly load `.agents/rules`; those are generated
adapter views, not DeepAgents instruction inputs. When delegated work needs a
detailed rule beyond root instructions, name and read canonical
`docs/operating_system/rules/<rule>.md` in task scope. Do not create a duplicate
`.deepagents/AGENTS.md` rule bundle.

`dcode-project` reads its endpoint from active user-local Codex provider
configuration and its API key from user-local secret configuration. Never add
provider bindings, credentials, tier-model aliases, MCP config, hooks, memories,
threads, or generated `.deepagents/` files to repository coordination.

## DeepAgents Tool Boundary

Current `dcode-project` bridges canonical role prompts and active Codex model
binding, then validates a controller-owned sanitized handoff. It starts `dcode`
with `--no-mcp`; Codex MCP servers, their tool allowlists, approval policy,
sandbox mode, and shell policy do not transfer.
DeepAgents still has its own built-in filesystem, shell, task, and web tools.
Treat those as executor-local capabilities, not proof of Codex-equivalent
containment. Web search needs user-local `TAVILY_API_KEY`; its absence disables
web search and does not fall back to Codex browser or web MCPs.
Keep DeepAgents work inside trusted one-user workspace, retain controller path
checks, and verify Git scope before acceptance.

DeepAgents controller may use built-in `task` for a bounded `low`, `normal`, or
`high` project subagent. Name role in task prompt; do not use `dcode --agent`
or `dcode -r` for project coordination. Same role source, Git scope, plan
coordination, task evidence, checks, and acceptance rules apply to Codex and
DeepAgents delegates; executor containment and approval remain distinct.

`dcode-project` rejects direct model/profile, agent/thread, MCP/hook trust,
approval/Yolo, sandbox, shell/filesystem/interpreter, startup, install, and ACP
flags. It allows only bounded task flags such as `--max-turns`, `--timeout`,
`--rubric`, `--goal`, and output controls. Codex controller performs MCP calls,
then writes handoff under `%USERPROFILE%\.local\share\dcode-project\handoffs`.
Launch with `--handoff-file <absolute-path>` and optional repeatable
`--mcp-select <server[.tool][,server[.tool]...]>`; selection narrows provenance
only and never grants DeepAgents tools. Handoff schema is
`codex.mcp.handoff.v1`; controller deletes handoff after use. Never pass
credentials, tool configs, raw headers, cookies, or approval authority through
task text.

Install or refresh local DeepAgents runtime:

```powershell
./scripts/setup_deepagents_runtime.ps1 -SecretFile <local-env-file>
```

Installer writes only `%USERPROFILE%\.local\share\dcode-project\config.toml`
and `%USERPROFILE%\.local\bin\dcode-project.{cmd,ps1}`. Wrapper resolves current
Git workspace and runs tracked `scripts/dcode_project.py`. Run `dcode-project`
from selected repository workspace; do not pass `--model`. Setup fails when
`%USERPROFILE%\.deepagents\.mcp.json` exists; remove that direct DeepAgents MCP
config before setup so Codex config remains sole MCP authority.

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
