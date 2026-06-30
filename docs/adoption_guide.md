# Starter Adoption Guide

Use this guide after cloning or copying `project-OS-starter` into a new project.

This guide is private-source onboarding material. It explains how to adapt the
private starter repo and should not be published to a curated public mirror
unless it has been intentionally rewritten as product-facing documentation.

The goal is to turn the starter into your project without breaking the source-of-truth model:

- `docs/intent/` owns what and why
- `docs/operating_system/` owns how the repo builds and governs work
- `docs/features/` and `docs/stages/` own product/domain architecture meaning when adopted
- `docs/superpowers/specs/` and `docs/superpowers/plans/` own execution artifacts
- generated files stay generated

## First Hour Checklist

1. Rename the project identity.
2. Fill the intent layer before changing deep workflow docs.
3. Decide whether the project needs a private/public publication split.
4. Choose an adoption mode before changing feature, stage, generated, or source metadata surfaces.
5. Read the migration and feature routing guides before creating feature or stage sources.
6. Define the first feature and stage sources only when product/domain boundaries are clear enough.
7. Update adapter templates and run adapter sync.
8. Validate the starter before the first real project commit.

## 1. Replace Starter Identity

Update the public-facing project identity first:

- `README.md`
- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`
- `docs/intent/project-charter.md`
- `docs/intent/stakeholders.md`
- `docs/intent/success-outcomes.md`
- `docs/intent/constraints-and-non-goals.md`
- repository name, package name, CI display names, or product names when present

Do not leave starter language in the README once the repo starts representing a real project.

Treat the root `docs/` folder as the standard home for cross-cutting project
docs beside `README.md`.

Required project folders:

- `docs/intent/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `repo_config/`
- `scripts/`
- `tests/`

Required root docs:

- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

These required docs should not stay as starter stubs. Before the first real
project commit, replace placeholder guidance with real project-specific setup,
configuration, usage, pipeline, and architecture content.

Optional root docs:

- `docs/dataset.md`
- `docs/api.md`
- `docs/observability.md`
- `docs/testing.md`

Conditional folders:

- `docs/features/`
- `docs/stages/`
- `docs/generated/`
- `configs/`
- `aml/components/`

Conditional folders should exist when the adopted mode or project shape needs
them, not just because the starter mentions them.

## 2. Fill The Intent Layer

Start in `docs/intent/`.

Fill these files before expanding feature or stage contracts:

- `project-charter.md`
  - what problem the project exists to solve
  - why this repo shape is useful
  - core promises the project must preserve
- `stakeholders.md`
  - who depends on the project
  - what each audience needs from the repo
- `success-outcomes.md`
  - what good looks like
  - what signals show the project is drifting
- `constraints-and-non-goals.md`
  - what the project will not try to do
  - which boundaries should remain stable

At minimum, `docs/intent/` should contain Markdown docs that make project
purpose explicit. `docs/intent/README.md` is the anchor overview, and the
other intent files can split the layer by promise, audience, outcomes, or
constraints.

The README should summarize this layer. It should not become the deepest source of truth.

## 3. Choose Private/Public Mode

If the project needs a curated public mirror:

- update `repo_config/publication-config.json`
- review `docs/operating_system/procedures/publication-workflow.md`
- keep private-only materials out of the public allowlist
- run the dry-run publish workflow before pushing public changes

If the project does not need a public mirror yet:

- keep the publication config conservative
- do not delete the workflow just because it is unused on day one
- mark publication setup as deferred in the project notes if needed

## 4. Choose Adoption Mode

Before changing feature, stage, generated discovery, or code/config/test metadata surfaces, read [docs/operating_system/adoption/project-adoption-migration-guide.md](operating_system/project-adoption-migration-guide.md), record the chosen mode in `repo_config/adoption-mode.yaml`, and choose one adoption mode:

- starter method only: adopt intent docs, operating-system docs, agent instructions, publication workflow, and repo governance without feature/stage metadata
- managed architecture metadata: migrate feature folders, source contracts, generated outputs, and source metadata together
- legacy compatibility: keep flat feature YAML temporarily and record that managed architecture metadata is not adopted yet

Follow the selected mode runbook before creating or migrating product feature metadata:

- [Mode A Step-By-Step: Starter Method Only](operating_system/project-adoption-migration-guide.md#mode-a-step-by-step-starter-method-only)
- [Mode B Step-By-Step: Managed Architecture Metadata](operating_system/project-adoption-migration-guide.md#mode-b-step-by-step-managed-architecture-metadata)
- [Mode C Step-By-Step: Legacy Compatibility](operating_system/project-adoption-migration-guide.md#mode-c-step-by-step-legacy-compatibility)

Do not partially migrate architecture metadata. Either keep legacy compatibility explicit, or migrate feature folders, generated outputs, and code/config/test/doc metadata together.

If the project adopts Mode B and is also pulling forward newer starter
governance, diff the shared repo-control surfaces too rather than migrating
only product metadata. That review should include files such as:

- `repo_config/*`
- `docs/operating_system/*`
- `.agents/skills/*`
- `docs/operating_system/templates/agents/*`
- generated `AGENTS.md` and `.codex/rules/*` after sync
- validation and sync scripts

Bring over newer versions intentionally so the project inherits stronger
starter governance, sync behavior, and checks instead of letting those shared
files drift.

For Mode B, record that review in `repo_config/adoption-mode.yaml` under a
`starter_sync` block. At minimum, capture:

- `starter_baseline_ref`
- `last_shared_surface_review_at`
- `reviewed_surface_classes`
- optional `divergences` for intentional local customization

Validate the selected mode before committing adoption changes:

```powershell
python scripts/validate_adoption_shape.py
```

That validator now checks required root docs for more than path presence. It
expects a real heading, substantive guidance, and light subject coverage rather
than placeholder-only text.

## 5. Define First Features And Stages

Before creating feature or stage metadata, read [docs/operating_system/governance/feature-routing-guide.md](operating_system/feature-routing-guide.md). If this is an existing project migration, also follow [docs/operating_system/adoption/project-adoption-migration-guide.md](operating_system/project-adoption-migration-guide.md).

Create feature and stage source files only when they describe real product/domain structure.

Do not create features for starter adoption, repo operating-system work, intent-layer setup, adapter generation, agent/rule work, publication policy, private analysis tooling, or docs governance. Those belong in the operating-system layer, adapter sources, repo config, scripts, skills, rules, or operating-system specs/plans.

Use feature sources for product/domain capability meaning:

```text
docs/features/<feature_id>/feature.source.yaml
```

Use stage sources for workflow boundaries:

```text
docs/stages/<stage_id>.source.yaml
```

Rules:

- edit source files, not generated contracts
- keep generated refs derived from metadata
- do not add `manual_refs`
- avoid adding feature/stage metadata before product/domain boundaries are clear enough
- avoid mixing flat legacy feature YAML with managed feature folders

## 6. Customize Agent Instructions And Rules

Update canonical sources and mappings, not generated outputs:

- `docs/operating_system/templates/agents/root-AGENTS.template.md`
- `docs/operating_system/templates/agents/docs-AGENTS.template.md`
- `docs/operating_system/rules/*.md`
- `repo_config/agent-adapter-mappings.json`

Keep this split:

- skills hold reusable workflows and judgment
- rules hold short non-negotiable invariants
- operating-system docs hold human-readable governance

After changing adapter sources or mappings, run:

```powershell
python scripts/sync_agent_adapters.py --all-platforms
python scripts/sync_agent_adapters.py --check --all-platforms
```

Use PowerShell wrappers only for legacy generated-surface flows that still depend on them.

## 7. Validate After Customization

Before the first real project commit, run the checks that match the surfaces you changed. Always include the adoption-shape validator once `repo_config/adoption-mode.yaml` exists.

Minimum adoption and adapter check:

```powershell
python scripts/validate_adoption_shape.py
python scripts/sync_agent_adapters.py --all-platforms
python scripts/sync_agent_adapters.py --check --all-platforms
```

If publication config changed:

```powershell
.\scripts\publish_public_repo.ps1
```

If feature/stage metadata exists and your project has architecture sync tooling, run the project's architecture sync/check workflow before committing.

## Common Mistakes

Avoid these early mistakes:

- editing generated `AGENTS.md` or `.codex/rules/*.rules` directly
- making README the deepest explanation of project purpose
- copying another project's intent docs without adapting them
- adding rules for every preference instead of only hard invariants
- filling feature/stage metadata before the project has real product/domain feature or workflow boundaries
- creating a `repo-operating-system` feature to track starter adoption or repo-method work
- half-migrating features by keeping flat `docs/features/*.yaml` as authoritative while also creating managed feature folders
- turning specs and plans into the only place where project purpose is explained

## First Commit Checklist

Before the first project-specific commit, confirm:

- `README.md` names the new project and points to the right setup path
- the required root project docs exist under `docs/`
- the required project folders exist and are not just implied by the starter
- `docs/intent/` reflects the new project, not the starter
- `docs/operating_system/` still describes the repo method accurately
- generated adapter outputs are synchronized
- private/public publication config is either correct or intentionally deferred
- feature and stage source files are either defined or intentionally not adopted yet
- no generated file was hand-edited as a source of truth
