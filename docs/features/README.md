# Features

This folder holds feature-level documentation for repos that adopt the managed architecture-doc workflow.

## Feature Eligibility Gate

Use `docs/features/` only for product/domain capabilities.

A feature should describe product-specific behavior, a domain capability, an operator/user-facing capability, or runtime capability that belongs in the project architecture.

Do not create features for repo-method work such as starter adoption, repo operating-system setup, intent-layer setup, adapter generation, agent skills/rules, publication policy, GitNexus/private tooling setup, validation tooling, or docs governance.

If the work is about how the repo plans, validates, publishes, documents, or instructs agents, route it to `docs/operating_system/`, `agent-core/`, `.agents/skills/`, `.codex/rules/`, `repo_config/`, scripts, or operating-system specs/plans instead.

Read [docs/operating_system/governance/feature-routing-guide.md](../operating_system/feature-routing-guide.md) before creating feature metadata.

## Adoption Modes

Before creating feature metadata in an existing project, choose an adoption mode in [docs/operating_system/adoption/project-adoption-migration-guide.md](../operating_system/project-adoption-migration-guide.md) and record it in `repo_config/adoption-mode.yaml`.

In managed architecture metadata mode, feature folders are required and flat `docs/features/*.yaml` files are not authoritative. Run `python scripts/validate_adoption_shape.py` before committing feature-shape changes.

In that mode, the generated `<feature_id>.yaml` contract, the generated-history
boundary shape in `history.md`, and the current generated discovery indexes are
part of the validator-enforced managed target.

In legacy compatibility mode, flat `docs/features/*.yaml` files may remain temporarily, but do not mix them with generated feature-folder contracts.

## Managed Feature Shape

Human-owned inputs live in `docs/features/<feature_id>/feature.source.yaml`.
Generated outputs live beside them, including `<feature_id>.yaml`, `lineage.generated.yaml`, and partial generated sections in `history.md`.

Those generated outputs should come from the sync workflow, not hand edits, and
their schema should match the current starter-managed contract shape.

For a copy-safe Mode B feature source template, see [docs/architecture_templates/feature.source.yaml](../architecture_templates/feature.source.yaml). Use it only after selecting managed architecture metadata or while executing an explicit Mode B migration plan.

If a starter repo has not defined any managed product/domain features yet, this folder may contain only this README.

If an existing project still uses flat feature YAML files, treat them as legacy compatibility until a managed migration plan packs each feature into its folder, adds `feature.source.yaml`, refreshes generated outputs, and updates source metadata.
