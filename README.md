# project-OS-starter

A private starter repository for carrying forward the repo operating system without coupling new projects to a specific runtime structure.

## What This Repo Owns

- `docs/operating_system/`: human-readable repo governance and procedures
- `.agents/skills/`: canonical Codex skill discovery surface
- `docs/operating_system/templates/agents/`: source templates for generated instruction outputs
- `repo_config/`: starter-level configuration for shipped starter validation and planning contracts
- `scripts/`: validation, hooks, and curated repo procedures

## Canonical Vs Generated

Canonical source layers live in:

- `AGENTS.md` and scoped `AGENTS.md` files
- `docs/operating_system/`
- `.agents/skills/`
- `docs/operating_system/templates/agents/`
- `repo_config/`
- `configs/`
- `scripts/`

Generated runtime outputs are downstream artifacts:

- `AGENTS.md`

Do not edit generated outputs directly. Regenerate them from the source layers.

Scoped `AGENTS.md` files are canonical instructions for their directories.

## Bootstrap A New Project

Start with [Project Adoption Migration](docs/operating_system/adoption/project-adoption-migration-guide.md).

First-hour flow:

1. replace the starter identity in `README.md`
2. create the standard root project docs under `docs/`:
   - `setup.md`
   - `configuration.md`
   - `usage.md`
   - `pipeline.md`
   - `architecture.md`
3. keep the required project folders in place:
   - `docs/intent/`
   - `docs/operating_system/`
   - `docs/superpowers/specs/`
   - `docs/superpowers/plans/`
   - `repo_config/`
   - `scripts/`
   - `tests/`
4. fill `docs/intent/` before deep procedure docs
5. decide whether the private/public publication procedure applies
6. review starter governance and shipped root agent docs

## Native Personal-Local Work

Ordinary trusted one-user development uses
[`native-personal-local`](docs/operating_system/procedures/personal-local-worktree-procedure.md):
native Git plus Codex or DeepAgents. Codex is default when plan omits executor.
Reuse clean checkout for small reversible work. Use a native Git worktree only
when existing worktree guidance selects isolation. Git owns workspace identity,
change evidence, and branch disposition. Shared delegated roles live in
`agents/*.toml`. User-local `dcode-project` materializes ignored DeepAgents
project subagents at launch; they are not `dcode --agent` primary profiles.
Current launcher forces `--no-mcp`; it does not mirror Codex MCP tools or
permissions. Use Codex for MCP work, then hand DeepAgents sanitized task facts.

## Agent Memory

Use official MCP Memory Server for verified reusable project knowledge. See `docs/operating_system/rules/agent-memory-rule.md` for fetch, update, privacy, precedence, and fallback policy; see `docs/operating_system/procedures/mcp-memory-server-setup.md` for client setup.

Memory data is private local state outside repository. Source code, tests, ADRs, current governance, and explicit instructions remain authoritative.

## Optional Documentation MCP

Optional Context7 supports version-specific external-library research when pinned local sources do not answer. It is advisory only. See `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md` for private Codex setup, smoke test, fallback, and removal.

## Customize First

When bootstrapping a new project, review these first:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`
- `docs/intent/README.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/templates/agents/*.template.md`
- `repo_config/planning_artifact_schema.yaml`

## Optional Nested AGENTS Templates

The starter ships with optional example templates:

- `docs/operating_system/templates/agents/example-runtime-AGENTS.template.md`
- `docs/operating_system/templates/agents/example-admin-AGENTS.template.md`

These are examples only. Keep them as optional starter guidance unless your
source repo also owns a separate generation procedure for additional agent entry
surfaces.

## Public Mirror Procedure

Use the curated publication script to prepare a public-safe export:

```powershell
.\scripts\publish_public_repo.ps1
```

Push to the configured public remote when ready:

```powershell
.\scripts\publish_public_repo.ps1 -Push
```

The default starter config keeps operating-system docs, skills, adapter sources, generated agent files, and other private-only materials out of the public mirror.

Repo/system configuration lives in `repo_config/`. Optional durable product feature documentation may live in `docs/features/`; code, configuration, schemas, and tests own executable behavior.

