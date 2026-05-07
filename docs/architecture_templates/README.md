# Architecture Metadata Templates

Use these templates only when a project has selected `managed_architecture_metadata` in `repo_config/adoption-mode.yaml`, or when executing an explicit Mode B migration plan.

Do not use these templates for Mode A starter-method-only adoption. Do not use them for Mode C legacy compatibility unless the current task is migrating the project into Mode B.

For Mode A starter-method-only adoption, start from `docs/project_templates/mode-a/` instead. That pack contains required docs, intent docs, repo config, runtime config, and folder anchors without managed architecture metadata.

## No Double-Entry Rule

Canonical truth should flow downward from upstream owning layers. Downstream layers should derive views from it rather than re-entering it.

Do not copy the same semantic fact into feature source, stage source, code metadata, docs frontmatter, and generated outputs just to make every surface look complete. Put the fact in the layer that owns it, then let generated contracts, lineage, indexes, and summaries derive from that source.

Examples:

- Feature identity, status, dependencies, invariants, and capability definitions belong in `feature.source.yaml`.
- Stage role ownership belongs in `docs/stages/<stage_id>.source.yaml`.
- A feature capability's stage participation belongs in `feature.source.yaml > stage_participation`.
- Code ownership and proof evidence belong in `@meta`, `@capability`, and `@proves` markers.
- Generated contracts, lineage, history blocks, and discovery indexes must derive from those sources.

## Capability ID Rule

Capabilities are downstream of features. In managed architecture metadata, write
capability IDs as feature-qualified IDs:

```text
<feature_id>.<capability_slug>
```

For example, use `billing-insights.billing-revenue-summary`, not
`billing-revenue-summary`. Reuse that exact feature-qualified capability ID in
`stage_participation[].capability_ids`, `@capability`, `@proves`, YAML
`# @architecture` metadata, and Markdown frontmatter.

## Copyable Human-Owned Inputs

These templates represent human-authored inputs or source metadata markers:

- `feature.source.yaml`
- `stage.source.yaml`
- `history.md`
- `python-meta.py.template`
- `python-capability.py.template`
- `python-proves-test.py.template`
- `yaml-architecture.yaml`
- `markdown-frontmatter.md`
- `mode-b-feature-migration-checklist.md`

Replace example IDs such as `billing-insights`, `analytics`, and `billing-insights.billing-revenue-summary` with canonical project IDs before use.

## Generated Outputs

Do not copy templates for generated outputs. Create or update the owning source, then run the architecture sync workflow.

In managed mode, the main generated outputs below are also validator-enforced
migration targets. The filenames alone are not enough; the generated shape must
match the current starter contract.

Generated outputs include:

- `docs/features/<feature_id>/<feature_id>.yaml`
- `docs/features/<feature_id>/lineage.generated.yaml`
- generated blocks in `docs/features/<feature_id>/history.md`
- `docs/stages/<stage_id>.yaml`
- `docs/generated/*`

## References

- [Project Adoption Migration Guide](../operating_system/project-adoption-migration-guide.md)
- [Doc System Lifecycle](../operating_system/skill-doc-system-lifecycle.md)
- [Feature Routing Guide](../operating_system/feature-routing-guide.md)

## Validation

After copying templates into real project locations, run:

```powershell
python scripts/validate_adoption_shape.py
python scripts/sync_architecture_docs.py --check
```

Run the relevant project tests before committing.
