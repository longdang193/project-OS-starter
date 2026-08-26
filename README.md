# project-OS-starter

A private starter repository for carrying forward the repo operating system without coupling new projects to a specific runtime structure.

## What This Repo Owns

- `docs/operating_system/`: human-readable repo governance and procedures
- `.agents/skills/`: canonical project skill source, discovered by Codex and DeepAgents
- `docs/operating_system/templates/agents/`: source templates for generated instruction outputs
- `repo_config/`: starter-level configuration for shipped starter validation and planning contracts
- `scripts/`: validation, hooks, and curated repo procedures

## Canonical Vs Generated

Canonical source layers live in:

- scoped `AGENTS.md` files, when present
- `docs/operating_system/`
- `.agents/skills/`
- `docs/operating_system/templates/agents/`
- `repo_config/`
- `scripts/`

Generated and packaged outputs are downstream artifacts:

- `AGENTS.md`
- `generated_agents/`
- `.agents/rules/`
- `generated_exports/project-OS-starter-kit/`

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
native Git plus Codex, DeepAgents, or Tura. Executor and profile selection are
independent; Codex is safe default when plan omits executor or delegated benefit
is unclear. Follow `docs/operating_system/planning/planning-dispatch.md` for
advisory executor selection.
Reuse clean checkout for small reversible work. Use a native Git worktree only
when existing worktree guidance selects isolation. Git owns workspace identity,
change evidence, and branch disposition. Shared delegated roles live in
`agents/*.toml`. User-local `dcode-project --role <low|normal|high|xhigh>`
selects source profile model for primary DeepAgents launch and materializes
ignored DeepAgents project subagents; they are not `dcode --agent` primary profiles.
When bounded Tura delegation is installed, use
`project-delegate --role <low|normal|high|xhigh> -n "<task>"`. Tura uses the
same tracked roles and TL provider route (`Tura -> LightRSI -> 9router ->
provider`); Native Codex remains controller and `dcode-project` remains the
explicit DeepAgents path.
Current launcher forces `--no-mcp`; it does not mirror Codex MCP tools or
permissions. Codex controller performs MCP work, writes validated
`codex.mcp.handoff.v1` under user-local handoff root, then launches DeepAgents
with `--handoff-file <absolute-path>`. Optional `--mcp-select` narrows
provenance only; it does not grant DeepAgents MCP access.
Local setup defaults to tested `deepagents-code 0.1.59`, requires Python 3.12 or
newer, and disables child auto-update. Refresh the runtime through
`scripts/setup_deepagents_runtime.ps1`, not through `dcode --update`.
For Tura replacement, keep the configured executable path when possible, check
its nonsecret identity with `project-delegate --role normal --print-config`,
and run one bounded TL smoke before treating existing compatibility or
performance evidence as current. A moved executable needs setup rerun; an
in-place replacement does not.

## Agent Memory

Use official MCP Memory Server for verified reusable project knowledge. See `docs/operating_system/rules/agent-memory-rule.md` for fetch, update, privacy, precedence, and fallback policy; see `docs/operating_system/procedures/mcp-memory-server-setup.md` for client setup.

Memory data is private local state outside repository. Source code, tests, ADRs, current governance, and explicit instructions remain authoritative.

## Optional Documentation Capability

Version-specific external-library research is optional, advisory, and resolved
by the active executor only when pinned local sources do not answer. See
`docs/operating_system/tooling/runtime-tool-resolution.md` for capability,
evidence, permission, and fallback boundaries.

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

