---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/architecture_templates/
  - docs/operating_system/project-adoption-migration-guide.md
  - docs/operating_system/doc-system-lifecycle.md
  - docs/features/README.md
  - docs/stages/README.md
related_features: []
related_stages: []
---

# Architecture Metadata Templates Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add copy-safe templates for Mode B architecture metadata adoption.
Reasoning: This work defines repo-method guidance and starter template surfaces for managed architecture metadata. It does not create a product feature, product stage, generated contract, or downstream project migration.
Invariants:

- Templates must reinforce source ownership instead of creating double-entry metadata.
- Canonical truth should flow downward from upstream owning layers, and downstream layers should derive views from it rather than re-entering it.
- Templates must be used only when the project has selected `managed_architecture_metadata` or is executing an explicit Mode B migration plan.
- Generated outputs must not be presented as human-editable templates.
- Product/domain metadata must not be used to represent starter adoption, repo governance, adapter work, publication setup, or agent/rule work.

Dependencies:

- `docs/operating_system/doc-system-lifecycle.md`
- `docs/operating_system/project-adoption-migration-guide.md`
- `docs/operating_system/feature-routing-guide.md`
- `tools/docs/generate_architecture_metadata.py`
- `scripts/validate_adoption_shape.py`
- `scripts/sync_architecture_docs.py`

Affected stages:

- none

Affected features:

- none

Primary lens: cross-cutting

Affected docs:

- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- feature_docs: none
- cross_cutting_docs:
  - `docs/architecture_templates/README.md`
  - `docs/architecture_templates/feature.source.yaml`
  - `docs/architecture_templates/stage.source.yaml`
  - `docs/architecture_templates/history.md`
  - `docs/architecture_templates/python-meta.py.template`
  - `docs/architecture_templates/python-capability.py.template`
  - `docs/architecture_templates/python-proves-test.py.template`
  - `docs/architecture_templates/yaml-architecture.yaml`
  - `docs/architecture_templates/markdown-frontmatter.md`
  - `docs/architecture_templates/mode-b-feature-migration-checklist.md`
  - `docs/operating_system/project-adoption-migration-guide.md`
  - `docs/operating_system/doc-system-lifecycle.md`
  - `docs/features/README.md`
  - `docs/stages/README.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes
Migration needed: no
Risk level: low

## Problem

Mode B adoption now has runbooks, validation, and a one-feature example, but it still lacks copy-safe templates for the files and metadata markers an agent must create during a managed architecture metadata migration.

Without templates, adopters are likely to:

- copy generated contracts as if they were source files
- enter the same semantic fact into feature source, stage source, code metadata, docs frontmatter, and generated outputs
- confuse feature ownership with stage ownership
- use product feature metadata to represent operating-system adoption work
- invent unsupported fields in `feature.source.yaml`, `stage.source.yaml`, YAML `# @architecture` blocks, or markdown frontmatter
- forget code/test/config/doc metadata needed for generated lineage

The risk is not only missing files. The larger risk is double-entry drift: the same fact is manually maintained in multiple places, then generated discovery becomes a stale summary of contradictory sources.

## Goal

Add a template package that shows the correct human-authored surfaces for Mode B architecture metadata adoption.

The templates should make it easy to create:

- one managed feature source
- one stage source
- one feature history scaffold
- Python ownership, capability, and proof markers
- YAML `# @architecture` metadata
- Markdown explanation frontmatter
- a short Mode B migration checklist

The package should teach which layer owns each fact and which layers must derive from it.

## Non-Goals

This spec does not create a real product feature.

This spec does not create a real product stage.

This spec does not change the architecture metadata generator schema.

This spec does not change the adoption-mode validator.

This spec does not add a new adoption mode.

This spec does not add editable templates for generated files such as:

- `docs/features/<feature_id>/<feature_id>.yaml`
- `docs/features/<feature_id>/lineage.generated.yaml`
- `docs/stages/<stage_id>.yaml`
- `docs/generated/*`

Generated output shapes may be described for orientation, but they must not be provided as files users are expected to copy.

## Design Principles

### No Double-Entry Rule

Canonical truth should flow downward from upstream owning layers, and downstream layers should derive views from it rather than re-entering it.

Do not copy the same semantic fact into feature source, stage source, code metadata, docs frontmatter, and generated outputs just to make every surface look complete. Put the fact in the layer that owns it, then let generated contracts, lineage, indexes, and summaries derive from that source.

Examples:

- Feature identity, status, dependencies, invariants, and capability definitions belong in `feature.source.yaml`.
- Stage role ownership belongs in `docs/stages/<stage_id>.source.yaml`.
- A feature capability's stage participation belongs in `feature.source.yaml > stage_participation`.
- Code ownership and proof evidence belong in `@meta`, `@capability`, and `@proves` markers.
- Generated contracts, lineage, history blocks, and discovery indexes must derive from those sources.
- Capability IDs are downstream of features and must be feature-qualified as
  `<feature_id>.<capability_slug>`.

### Template Files Are Human-Owned Inputs

Every template file should represent a human-authored source or source metadata marker.

Generated files should be referenced by name, but the template package should not include copyable generated file templates.

### Mode B Only

The template package is for `managed_architecture_metadata` mode or explicit Mode B migration work.

Mode A projects should not copy these templates into `docs/features/`, `docs/stages/`, code metadata, configs, or tests.

Mode C projects should not create managed feature folders from these templates until a Mode B migration plan is being executed.

### Schema-Aligned, Not Exhaustive

Templates should include fields already supported by the generator and validators. They should avoid speculative fields that would require schema changes.

The examples should be short and realistic enough to copy, but they should not try to model every possible project.

## Proposed Files

Create:

```text
docs/architecture_templates/
  README.md
  feature.source.yaml
  stage.source.yaml
  history.md
  python-meta.py.template
  python-capability.py.template
  python-proves-test.py.template
  yaml-architecture.yaml
  markdown-frontmatter.md
  mode-b-feature-migration-checklist.md
```

Update:

```text
docs/operating_system/project-adoption-migration-guide.md
docs/operating_system/doc-system-lifecycle.md
docs/features/README.md
docs/stages/README.md
```

Do not update generated discovery for this documentation-only package unless the implementation adds metadata that the architecture generator intentionally reads.

## Template Requirements

### `docs/architecture_templates/README.md`

The README should:

- state that templates are for Mode B only
- link to `docs/operating_system/project-adoption-migration-guide.md`
- link to `docs/operating_system/doc-system-lifecycle.md`
- include the no-double-entry rule
- explain which files are copyable human-owned inputs
- list generated files that must be produced by tooling, not copied
- tell adopters to run:

```powershell
python scripts/validate_adoption_shape.py
python scripts/sync_architecture_docs.py --check
```

### `docs/architecture_templates/feature.source.yaml`

The feature source template should use supported fields only:

```yaml
feature_id: billing-insights
name: Billing Insights
status: active
type: workflow
summary: Summarize billing activity for operator reporting.
domains:
  - billing
depends_on: []
invariants:
  - invariant_id: billing-inputs-validated
    name: Billing Inputs Validated
    statement: Billing reports use validated billing records only.
    state: active
capabilities:
  - capability_id: billing-insights.billing-revenue-summary
    name: Billing Revenue Summary
    summary: Summarize billed revenue by account and reporting period.
    state: active
stage_participation:
  - stage_id: analytics
    role: primary
    capability_ids:
      - billing-insights.billing-revenue-summary
lineage_exceptions: []
```

The template should not include generated freshness fields such as `revision`, `latest_change_id`, or `last_updated_at`.

The template should not include `manual_refs`.

### `docs/architecture_templates/stage.source.yaml`

The stage source template should show stage-owned role semantics and use stage ID format compatible with the generator:

```yaml
stage_id: analytics
name: Analytics
status: active
purpose: Transform validated product data into reporting-ready outputs.
primary_features:
  - billing-insights
supporting_features: []
inputs:
  - validated billing records
outputs:
  - reporting-ready billing summaries
notes:
  - Stage ownership is declared here; feature capability participation stays in feature.source.yaml.
```

The template should state that `docs/stages/<stage_id>.yaml` is generated and must not be copied from a template.

### `docs/architecture_templates/history.md`

The history template should include generated-history markers and a human-owned notes section:

```md
# Billing Insights History

<!-- GENERATED HISTORY START -->
<!-- GENERATED HISTORY END -->

## Human Notes

- Add context that cannot be derived from specs, plans, code, tests, or generated lineage.
```

The template should warn against duplicating machine-readable lineage facts in human notes.

### `docs/architecture_templates/python-meta.py.template`

The file metadata template should show top-of-file ownership metadata:

```python
"""
@meta
name: billing_reporting
type: module
domain: billing
responsibility:
  - Build billing reporting datasets.
features:
  - billing-insights
stages:
  - analytics
capabilities:
  - billing-insights.billing-revenue-summary
lifecycle:
  status: active
"""
```

The template should explain when capability-first linkage can avoid a second manual feature list if the generator derives feature ownership from the capability.

### `docs/architecture_templates/python-capability.py.template`

The capability marker template should show canonical implementation evidence for one capability:

```python
def build_revenue_summary(records: list[BillingRecord]) -> RevenueSummary:
    """
    @capability billing-insights.billing-revenue-summary
    """
    ...
```

The template should prefer one canonical capability owner rather than scattering the same `@capability` marker across helper functions.

### `docs/architecture_templates/python-proves-test.py.template`

The proof marker template should show test evidence:

```python
def test_build_revenue_summary_groups_by_account() -> None:
    """
    @proves billing-insights.billing-revenue-summary
    """
    ...
```

The template should state that test proof evidence belongs in tests, not in feature source refs.

### `docs/architecture_templates/yaml-architecture.yaml`

The YAML metadata template should show `# @architecture` metadata for configs, AML components, fixtures, or contracts:

```yaml
# @architecture
# owner: billing-insights
# features:
#   - billing-insights
# stages:
#   - analytics
# capabilities:
#   - billing-insights.billing-revenue-summary
# role: config
# canonical: true
```

The template should avoid repeating the same ownership fact in multiple fields unless the generator requires that field. If additive non-owner feature linkage is needed later, it should use a supported schema rather than overloading `features`.

### `docs/architecture_templates/markdown-frontmatter.md`

The Markdown frontmatter template should show docs explanation metadata:

```md
---
doc_id: billing-insights-operator-guide
doc_type: guide
explains:
  features:
    - billing-insights
  capabilities:
    - billing-insights.billing-revenue-summary
  stages:
    - analytics
---

# Billing Insights Operator Guide
```

The template should state that frontmatter is for docs that materially explain a feature, capability, stage, config, component, or operator workflow. It should not be added to every markdown file by default.

### `docs/architecture_templates/mode-b-feature-migration-checklist.md`

The checklist should provide an operational sequence:

1. Confirm `repo_config/adoption-mode.yaml` is `managed_architecture_metadata`.
2. Classify the candidate as a real product feature.
3. Create `docs/features/<feature_id>/`.
4. Create `feature.source.yaml` from the template.
5. Use feature-qualified capability IDs: `<feature_id>.<capability_slug>`.
6. Create `history.md` from the template.
7. Create or update stage source.
8. Add code `@meta` and canonical `@capability` markers.
9. Add test `@proves` markers.
10. Add YAML `# @architecture` metadata only where configs/components materially participate.
11. Add markdown frontmatter only to docs that materially explain the feature/stage/capability.
12. Run generator/sync.
13. Run validation and tests.
14. Commit only when generated outputs and source metadata agree.

## Guide Updates

### Project Adoption Migration Guide

Add a short section or link near Mode B:

- point to `docs/architecture_templates/`
- state that the templates are for Mode B migration only
- include the no-double-entry rule or link to the canonical version
- warn not to copy generated outputs

### Doc System Lifecycle

Add `docs/architecture_templates/` to the source-of-truth model as operating-system guidance, not product architecture truth.

Clarify that templates are examples of human-authored inputs and metadata markers, not a parallel schema.

### Feature README

Add a short link to the template package from the managed feature shape section.

State that the feature source template should be copied only when Mode B is selected or a Mode B migration plan is executing.

### Stage README

Add a short link to the stage source template.

State that generated stage contracts must come from the generator, not from a copied template.

## Validation

Implementation should verify:

```powershell
python scripts/validate_adoption_shape.py
python scripts/sync_architecture_docs.py --check
git diff --check
pytest -q
```

If the template package uses file extensions that make the generator or validators scan the examples as real architecture metadata, implementation must either:

- place templates where validators intentionally ignore them, or
- adjust validators to ignore `docs/architecture_templates/`, with tests.

Do not weaken validation for real managed metadata surfaces.

## Acceptance Criteria

- `docs/architecture_templates/README.md` exists and explains Mode B-only usage.
- The README includes the no-double-entry rule.
- Templates exist for feature source, stage source, history, Python `@meta`, Python `@capability`, Python `@proves`, YAML `# @architecture`, Markdown frontmatter, and a Mode B feature migration checklist.
- Templates avoid unsupported fields.
- Templates do not include copyable generated contract or generated lineage files.
- The adoption migration guide links to the template package from Mode B guidance.
- The doc-system lifecycle doc identifies the template package as operating-system guidance.
- Feature and stage READMEs link to the relevant templates without duplicating the full template guidance.
- `python scripts/validate_adoption_shape.py` passes.
- `python scripts/sync_architecture_docs.py --check` passes.
- `pytest -q` passes.
- `git diff --check` passes.

## Open Questions

Should templates live under `docs/architecture_templates/`, or under `docs/operating_system/architecture-templates/`?

Python templates should use neutral `.py.template` filenames so the architecture generator does not treat them as live code metadata. Should YAML templates also use neutral extensions later, or keep `.yaml` while validators ignore this guidance directory?

Should the generator explicitly ignore `docs/architecture_templates/`, or should the template directory be designed so no validator needs a special case?

Should a future helper script scaffold a new feature from these templates, or should templates remain copy/manual guidance for now?
