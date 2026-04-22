# Repo Governance

This document defines how a private project repo is organized for humans and agents.

## Repo Roles

- Private repo:
  - full development source of truth
  - internal docs, workflows, specs, plans, and tooling are allowed
- Public repo:
  - curated product-facing mirror
  - receives only intentionally published code and docs

Normal development happens only in the private repo.

## Structure Model

The repo uses four distinct internal layers:

1. `docs/operating_system/`
- human-readable repo rules and workflows
- publication policy
- doc-system and planning rules
- internal tooling pilots
- agent memory under `docs/operating_system/agent_memory/`

2. `agent-core/`
- shared agent-facing source material
- small principles
- structured policy intent
- adapter source files

3. `.agents/skills/`
- repo-local Codex skill discovery surface
- focused execution workflows

4. `.codex/agents/`
- optional repo-local Codex subagent configuration
- narrow specialist executor roles only
- subordinate to `AGENTS.md`, `docs/operating_system/`, and `.agents/skills/`

5. adapter outputs
- `AGENTS.md`
- nested `AGENTS.md`
- `.codex/rules/*.rules`
- sync and verification scripts under `scripts/`

The repo now uses `.codex/` as its active Codex config/generated root, while
still splitting Codex ownership by role:

- `AGENTS.md` for repo-wide Codex instructions
- `.agents/skills/` for canonical Codex skills
- `docs/operating_system/` for human governance
- `.codex/` for repo-local Codex config and generated outputs

The repo also splits configuration ownership by purpose:

- `repo_config/`
  - repo/system configuration such as publication boundaries and adapter generation mappings
- `configs/`
  - runtime/workflow configuration such as training, monitoring, assets, and smoke profiles
- `docs/features/*/feature.source.yaml` and `docs/stages/*.source.yaml`
  - human-owned feature and stage lifecycle sources, not generic runtime config buckets
- `docs/features/*/*.yaml`, `docs/features/*/lineage.generated.yaml`, and `docs/stages/*.yaml`
  - generated lifecycle outputs assembled from the human-owned sources plus metadata

The architecture-lineage system is now steady-state repo policy:

- edit `docs/features/<feature_id>/feature.source.yaml` for human semantic changes
- edit `docs/stages/<stage_id>.source.yaml` for human stage-boundary changes
- treat generated feature contracts, generated stage contracts,
  `lineage.generated.yaml`, generated history blocks, and current managed
  generated discovery indexes as standard generated outputs
- use `scripts/sync_architecture_docs.py` as the canonical sync/check workflow
- use `scripts/validate_repo_contracts.py` as the canonical repo-wide contract validation workflow
- use the canonical sync/check workflow to catch malformed metadata, missing required `@meta`, and disallowed manual reference bridges before commit/push
- treat lineage completeness enforcement as a standing requirement, not a rollout-only concern
- treat feature-history generation as part of the same sync/check workflow; completed
  plans update the generated history block automatically
- keep feature refs metadata-derived; `manual_refs` is not accepted in
  `feature.source.yaml`
- treat the managed-mode contract shapes validated by
  `scripts/validate_adoption_shape.py` as migration targets rather than loose
  generated suggestions

The repo also expects a small standard root documentation surface for projects
beneath `docs/`:

- required:
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
- optional:
  - `docs/dataset.md`
  - `docs/api.md`
  - `docs/observability.md`
  - `docs/testing.md`

These root docs are cross-cutting project docs, not replacements for
`docs/intent/`, `docs/operating_system/`, feature-local docs, stage docs, or
generated discovery. The normal validation and hook path should fail when the
required set is missing.

Required root-doc validation is intentionally light but real. The normal
validation path now checks:

- required paths exist
- each required doc has a top-level heading
- each required doc has more than heading-only stub content
- each required doc covers its intended subject at a lightweight semantic level
- obvious placeholder-only text does not pass

In `managed_architecture_metadata` mode, those required root docs also become
validator-enforced metadata-linked docs. They must carry frontmatter with a
canonical `doc_id`, a non-empty `doc_type`, and an `explains` mapping that
links the doc back to the relevant managed feature, stage, config, or component
surface. `docs/pipeline.md` in particular must keep `explains.stages`.

Outside managed mode, required root docs still do not need frontmatter by
default. Frontmatter remains optional for other Markdown docs unless they are
meant to participate in architecture linkage.

The repo also expects a lean required folder surface:

- `docs/intent/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `repo_config/`
- `scripts/`
- `tests/`

Minimum file expectations for those required folders:

- `docs/intent/`
  - at least one Markdown file
  - `README.md` is the recommended anchor overview
- `docs/operating_system/`
  - governing repo-method docs such as `repo-governance.md` and `doc-system-lifecycle.md`
- `docs/superpowers/specs/`
  - bounded design artifacts when needed
- `docs/superpowers/plans/`
  - bounded execution artifacts when needed
- `repo_config/`
  - repo/system config, with `adoption-mode.yaml` as the required anchor file
- `scripts/`
  - repo workflow executables such as validation, sync, and setup helpers
- `tests/`
  - executable verification surfaces

Conditional folders remain conditional:

- `docs/features/`
- `docs/stages/`
- `docs/generated/`
- `configs/`
- `aml/components/`
- `docs/architecture_templates/`
- `.agents/skills/`
- `.codex/`
- `setup/`

The normal validation and hook path should fail when the required folder
surface is missing, while conditional folders should be required only when the
project shape or adopted workflow actually uses them.

When a task touches a feature folder, agents should read minimally rather than
loading every file by default:

- start with `feature.source.yaml`
- open the generated `<feature_id>.yaml` only when the assembled current-state contract is needed
- open `lineage.generated.yaml` for ownership, evidence, drift, or traceability work
- open `history.md` only when narrative context or chronology is needed

`history.md` manual edits are required only when a change needs explanation that
generated plan metadata cannot provide on its own, such as operator meaning,
rollout nuance, or cloud-proof interpretation. Do not hand-edit the generated
history block.

## Ownership Rules

### `docs/operating_system/`

Owns:

- repo operating rules
- workflow governance
- publication workflow
- tool adoption policy
- operational agent memory

Does not own:

- product behavior
- runtime code contracts
- task playbooks

`docs/operating_system/agent_memory/` stores compact operational memory for agents. It does not replace feature docs, specs, plans, or generated rules.

### `agent-core/`

Owns:

- shared agent-facing material that may be rendered into adapter-specific files

Does not own:

- the full human governance layer
- public product docs

### `.agents/skills/`

Owns:

- reusable execution workflows
- the canonical Codex skill discovery surface in phase 2

Does not own:

- publication policy
- repo-wide governance
- adapter syntax

Formal shape is governed by `docs/operating_system/skills-governance.md`.

### `.agents/agents/`

Owns:

- optional lightweight repo-local playbooks for task-specialized subagent roles

Does not own:

- repo-wide governance
- canonical instructions
- reusable workflow skills

Rules:

- this layer is optional, not required
- if adopted, `.agents/agents/` is the only repo-local playbook surface
- do not introduce both `agents/` and `.agents/agents/`
- playbooks must stay smaller and lighter than skills
- playbooks must remain subordinate to `AGENTS.md`, `docs/operating_system/`, and `.agents/skills/`
- this repo does not need repo-local playbooks until a real repeated specialization gap is proven

### `.codex/agents/`

Owns:

- optional repo-local Codex subagent configuration
- narrow specialist executor definitions for repeated workflows

Does not own:

- repo-wide governance
- canonical workflow skills
- agent memory

Rules:

- this layer is optional, not required
- first-pass subagents should stay read-only
- subagents must remain narrower than skills and subordinate to `AGENTS.md`, `docs/operating_system/`, and `.agents/skills/`
- `.codex/agents/` is the only repo-local Codex subagent surface

### `.codex/rules/`

Owns:

- generated Codex rules outputs
- adapter-rendered rule files consumed by Codex tooling

Does not own:

- canonical skill definitions
- agent memory
- repo governance

`.codex/rules/` is a generated surface created by repo scripts under the
active `.codex/` root. That root does not replace `.agents/skills/` as the
canonical skill surface.

### `repo_config/`

Owns:

- repo/system configuration
- publication boundary configuration
- adapter generation mappings

Does not own:

- runtime workflow defaults
- feature or stage contracts
- generated outputs

### `configs/`

Owns:

- runtime and workflow configuration
- smoke profiles
- training, monitoring, release, and asset settings used by repo workflows

Does not own:

- repo governance
- publication boundaries
- generated outputs
- feature or stage lifecycle contracts

## Private / Public Boundary

The following are private-only by default:

- `docs/operating_system/`
- `agent-core/`
- `.codex/`
- root and nested `AGENTS.md`
- `.agents/`
- `.cursor/`
- `docs/superpowers/`
- `logs/`
- `sample/`

Feature-local generated lineage is also private by default when it references
`docs/superpowers/`, `docs/operating_system/`, agent metadata, or other internal
development paths. Public publication can include generated feature contracts or
aggregate discovery only when those files stand alone without private-only
dependencies.

The public repo must not depend on these files to understand or use the product.

## GitNexus Freshness Policy

GitNexus is an optional private-only analysis layer for repo navigation,
cross-file tracing, and impact analysis. It is useful, but it is never stronger
than the current source code, tests, and active docs.

Before higher-trust GitNexus use, check freshness with:

```powershell
.\scripts\get_gitnexus_freshness.ps1
```

Working rules:

- if GitNexus is `fresh`, it may be used normally for exploration and as a
  higher-trust aid for impact analysis
- if GitNexus is `stale`, exploration may still use it as advisory lookup only
- if GitNexus is `stale`, debugging may still use it as advisory only and any
  conclusions should be labeled accordingly
- if GitNexus is `stale`, higher-risk refactor or impact work should refresh
  first when possible
- if refresh fails, continue source-first with code, tests, and active docs
  rather than blocking safe work
- if GitNexus output conflicts with current source or tests, trust the source
  and tests

This repo treats stale GitNexus as an advisory tool state, not as a reason to
stop normal source-first engineering work.

## Current Phase

Phase 2 keeps `.agents/skills/` as the canonical skill source.

This avoids breaking current Codex skill discovery while the new `agent-core/` and adapter sync layer stabilizes.

Subagents, when used, complement the skill layer rather than replacing it.

Longer term, `agent-core/skills/` may become canonical, with `.agents/skills/` generated or synchronized from it.

## Adapter Workflow

When changing:

- `agent-core/adapters/*`
- `agent-core/policies/*`
- generated `AGENTS.md`
- generated `.codex/rules/*.rules`

run:

```powershell
.\scripts\sync_agent_adapters.ps1
.\scripts\verify_agent_adapters.ps1
```

## Hook Workflow

The repo hook workflow is part of normal enforcement.

Installed local hooks should call the repo-contract validator in its hook-facing
subset mode:

```powershell
.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast
```

Use `scripts/sync_architecture_docs.py` separately when you need to regenerate
feature, stage, or discovery outputs before rerunning the validator.

The `--fast` flag is not a no-op quick check. It still runs the architecture
sync check path and skips only the extra validator-specific pytest pass.

CI is expected to run adapter verification, baseline checks, and publication-boundary validation on push and pull request events so drift and broken changes are caught before merge.

When hooks expose repeated or important failures:

- summarize the reusable lesson in `docs/operating_system/agent_memory/`
- then promote important recurring failures into stronger guardrails when appropriate:
  - a repo rule
  - a script check
  - a test
  - or an explicit follow-up plan

