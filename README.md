# project-OS-starter

A private starter repository for carrying forward the repo operating system without coupling new projects to a specific runtime structure.

## What This Repo Owns

- `docs/operating_system/`: human-readable repo governance and workflows
- `.agents/skills/`: canonical Codex skill discovery surface
- `docs/operating_system/templates/agents/`: source templates for generated instruction outputs
- `repo_config/`: starter-level configuration for shipped starter validation and planning contracts
- `configs/`: starter-level runtime and workflow configuration
- `scripts/`: validation, hooks, and curated repo workflows

## Canonical Vs Generated

Canonical source layers live in:

- `docs/operating_system/`
- `.agents/skills/`
- `docs/operating_system/templates/agents/`
- `repo_config/`
- `configs/`
- `scripts/`

Generated outputs are downstream artifacts:

- `AGENTS.md`
- `docs/AGENTS.md`
- `.codex/rules/*.rules`

Do not edit generated outputs directly. Regenerate them from the source layers.

## Bootstrap A New Project

Start with [docs/adoption_guide.md](docs/adoption_guide.md).

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
4. fill `docs/intent/` before deep workflow docs
5. decide whether the private/public publication workflow applies
6. define initial feature/stage sources only when the project shape is clear
7. review starter governance and shipped root agent docs before adding any
   source-only factory workflows

## Agent Memory

The starter includes `docs/operating_system/agent_memory/` as a compact repo-memory layer for:

- stable invariants
- recurring workflow patterns
- important failures that should become guardrails
- open questions that may affect future agent behavior

Keep this layer short and operational. Add memory when a lesson is likely to help future sessions, and promote repeated failures into rules, tests, hooks, or explicit follow-up work.

## Hook Workflow

The starter includes `.github/workflows/repo-hooks.yml` as a default CI hook layer.

It checks:

- repo-contract validation
- generated-file drift for shipped starter surfaces
- a baseline test command
- publication-boundary dry runs when that workflow is adopted

The default workflow assumes a Python-style test command. Update the baseline-test step during project bootstrap if your repo uses a different test runner or no `tests/` directory.

## Customize First

When bootstrapping a new project, review these first:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`
- `docs/intent/README.md`
- `docs/operating_system/governance/repo-governance.md`
- `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- `docs/operating_system/templates/agents/*.template.md`
- `repo_config/planning_artifact_schema.yaml`
- `repo_config/adoption-mode.yaml`
- `.github/workflows/repo-hooks.yml`

## Optional Nested AGENTS Templates

The starter ships with optional example templates:

- `docs/operating_system/templates/agents/example-runtime-AGENTS.template.md`
- `docs/operating_system/templates/agents/example-admin-AGENTS.template.md`

These are examples only. Keep them as optional starter guidance unless your
source repo also owns a separate generation workflow for additional agent entry
surfaces.

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

The starter now separates configuration by role:

- `repo_config/` for repo/system configuration
- `configs/` for runtime/workflow configuration
- `docs/features/*/*.yaml` and `docs/stages/*.yaml` for human-authored lifecycle contracts

## Reusable Documentation Update Prompt

Use this reusable prompt when updating docs in any project:

- `docs/prompts/docs-update-prompt.md`

Keep it generic and repo-agnostic. Apply with a separate README-only prompt when needed.

