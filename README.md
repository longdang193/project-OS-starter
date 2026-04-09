# project-OS-starter

A private starter repository for carrying forward the repo operating system without coupling new projects to a specific runtime structure.

## What This Repo Owns

- `docs/operating_system/`: human-readable repo governance and workflows
- `.agents/skills/`: canonical Codex skill discovery surface
- `agent-core/adapters/codex/`: source templates for generated adapter outputs
- `config/`: starter-level configuration for adapter generation and public publication
- `scripts/`: sync, verify, and curated public-mirror workflows

## Canonical Vs Generated

Canonical source layers live in:

- `docs/operating_system/`
- `.agents/skills/`
- `agent-core/adapters/codex/`
- `config/`
- `scripts/`

Generated outputs are downstream artifacts:

- `AGENTS.md`
- `docs/AGENTS.md`
- `codex/rules/*.rules`

Do not edit generated outputs directly. Regenerate them from the source layers.

## Bootstrap A New Project

1. Copy or template this repo into a new private project repository.
2. Edit `agent-core/adapters/codex/*.template.md` to match the new project.
3. Update `config/agent-adapter-mappings.json` to generate any nested `AGENTS.md` files your project needs.
4. Update `config/publication-config.json` to describe the public export boundary for the new project.
5. Run:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

## Optional Nested AGENTS Templates

The starter ships with optional example templates:

- `agent-core/adapters/codex/example-runtime-AGENTS.template.md`
- `agent-core/adapters/codex/example-admin-AGENTS.template.md`

These are examples only. They are not wired into generation until you add them to `config/agent-adapter-mappings.json`.

## Public Mirror Workflow

Use the curated publication script to prepare a public-safe export:

```powershell
.\scripts\publish_public_repo.ps1
```

Push to the configured public remote when ready:

```powershell
.\scripts\publish_public_repo.ps1 -Push
```

The default starter config keeps operating-system docs, skills, adapter sources, generated agent files, and other private-only materials out of the public mirror.


