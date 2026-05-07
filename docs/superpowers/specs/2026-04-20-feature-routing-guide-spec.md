---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/adoption_guide.md
  - docs/features/README.md
  - docs/operating_system/skill-doc-system-lifecycle.md
  - docs/operating_system/feature-routing-guide.md
related_features: []
related_stages: []
---

# Feature Routing Guide Spec

## Problem

Future projects created from `project-OS-starter` can accidentally model repo-method work as product features.

A concrete failure mode is creating a feature such as `repo-operating-system` under `docs/features/` to track starter adoption, adapter generation, intent-layer setup, publication boundaries, or agent/rule governance. That is wrong because those concerns belong to the system method layer, not to product-specific feature architecture.

This creates several downstream problems:

- The product feature graph becomes polluted with repo-governance concepts.
- `depends_on` can incorrectly couple operating-system work to product features such as `deployment-cicd`.
- Capability IDs may become prose sentences or unscoped slugs instead of feature-qualified stable machine identifiers.
- Generated feature discovery starts treating method work as product behavior.
- Future agents get a misleading precedent and repeat the same routing error.

## Goal

Add reusable guidance that helps humans and agents decide whether a candidate belongs in:

- `docs/features/`
- `docs/stages/`
- `docs/operating_system/`
- `docs/superpowers/specs/`
- `docs/superpowers/plans/`
- `agent-core/`, `.agents/skills/`, `.codex/rules/`, `repo_config/`, or scripts

The guide should prevent operating-system adoption work from being represented as product feature metadata.

## Non-Goals

This spec does not require changing the feature/stage generator.

This spec does not require adding a validator immediately, although it should define future validator expectations.

This spec does not require restructuring existing projects that already copied the starter. Those projects can use this guide as cleanup guidance.

This spec does not make `docs/features/` mandatory for all projects. A project may have no managed features until real product/domain boundaries are clear.

## Design Principles

### 1. Product features are product/domain capabilities

A feature is eligible for `docs/features/` only when it describes product-specific behavior, a domain capability, an operator/user-facing capability, or a runtime capability that belongs in the project architecture.

A valid feature should usually be connectable to product code, runtime config, tests, docs, stages, deployment behavior, or validation evidence.

### 2. Repo method is operating-system work

The following must not be modeled as product features:

- starter adoption
- repo operating-system setup
- intent-layer setup
- planning method changes
- docs governance
- adapter generation
- generated `AGENTS.md` or generated rule sync
- agent skills, rules, or instructions
- publication allowlists and private/public repo policy
- GitNexus or private analysis-tool setup
- validation tooling for repo governance

These belong in operating-system docs, adapter sources, skills, rules, repo config, scripts, or operating-system specs/plans.

### 3. Feature dependency graphs are product graphs

Feature `depends_on` must express product/domain feature dependencies only.

Do not use feature dependencies to represent that repo governance, publication config, adapter generation, or planning methods touch product files.

Operating-system specs and plans should use `targets` to identify affected files or folders.

### 4. Capability IDs are feature-qualified stable identifiers

Capability IDs must be feature-qualified machine-readable identifiers. Use
`<feature_id>.<capability_slug>` with a kebab-case capability slug.

Good examples:

```yaml
capability_ids:
  - data-pipeline.data-ingestion
  - semantic-layer.semantic-layer-modeling
  - analytics-serving.pipeline-observability
```

Bad examples:

```yaml
capability_ids:
  - "Intent layer: project purpose and stakeholders under docs/intent/."
  - "Adapter generation: scripts render AGENTS.md and rules."
```

If a sentence is needed, it belongs in prose fields such as `summary`, docs, specs, or plans. It should not be used as a capability ID.

### 5. Source files stay source-owned

When a project adopts managed architecture docs, humans should edit source files rather than generated contracts.

Expected feature source shape:

```text
docs/features/<feature_id>/feature.source.yaml
```

Generated feature contracts and lineage should be produced by the project architecture sync workflow when that workflow exists.

## Proposed Documentation Changes

### Add `docs/operating_system/feature-routing-guide.md`

Create a dedicated routing guide with these sections:

- Purpose
- Decision Tree
- Feature Eligibility Checklist
- Stage Eligibility Checklist
- Operating-System Routing Rules
- Correct Destination Table
- Capability ID Rules
- Dependency Rules
- Bad vs Corrected Examples
- Cleanup Guidance For Misrouted Features
- Future Validator Guardrails

### Update `docs/adoption_guide.md`

Add a feature/stage routing checkpoint before the existing feature/stage creation guidance.

Required guidance:

- Read the feature routing guide before creating feature metadata.
- Do not create a feature to track starter adoption.
- Do not create a feature to track repo operating-system work.
- If the work is about how the repo plans, validates, publishes, documents, or instructs agents, route it to the operating-system layer.

### Update `docs/features/README.md`

Add a short feature eligibility gate.

Required guidance:

- `docs/features/` is for product/domain capabilities.
- Repo-method work belongs elsewhere.
- If no product/domain features are clear yet, leave the folder with only the README.
- Human-owned feature inputs should use `docs/features/<feature_id>/feature.source.yaml` when managed architecture docs are adopted.

### Update `docs/operating_system/skill-doc-system-lifecycle.md`

Add an explicit anti-pattern:

- Do not create `docs/features/repo-operating-system.yaml` or similar features for operating-system adoption work.

Clarify that operating-system specs/plans should use `targets` rather than product feature dependencies when they affect cross-cutting repo files.

## Decision Tree

Use this routing decision before creating feature or stage metadata:

```text
Is this about product/domain behavior delivered by the project?
  yes -> candidate feature
  no -> continue

Is this about a product/domain workflow boundary or lifecycle stage?
  yes -> candidate stage
  no -> continue

Is this about how the repo plans, validates, publishes, documents, or instructs agents?
  yes -> operating_system layer
  no -> continue

Is this a bounded design or implementation artifact?
  yes -> spec or plan with layer metadata
  no -> keep as prose or project notes until ownership is clear
```

## Correct Destination Table

| Work Type | Correct Home | Avoid |
| --- | --- | --- |
| Product/domain capability | `docs/features/<feature_id>/feature.source.yaml` | `docs/operating_system/` |
| Product workflow stage | `docs/stages/<stage_id>.source.yaml` | feature dependency workaround |
| Repo governance | `docs/operating_system/*.md` | `docs/features/repo-operating-system.yaml` |
| Agent workflow | `.agents/skills/` | product feature metadata |
| Hard agent invariant | adapter rule source and generated `.codex/rules/` | feature capability |
| Adapter generation | `agent-core/adapters/`, `repo_config/`, scripts | product feature |
| Publication boundary | `repo_config/publication-config.json` and operating-system docs | product feature |
| One-time design | `docs/superpowers/specs/*.md` | permanent feature |
| One-time execution | `docs/superpowers/plans/*.md` | permanent feature |
| Private analysis tooling | operating-system docs or private tool config | public/product feature |

## Bad vs Corrected Example

Bad feature contract:

```yaml
repo-operating-system:
  feature_id: repo-operating-system
  depends_on:
    - deployment-cicd
  capabilities:
    - "Adapter generation: scripts render AGENTS.md and rules."
```

Problems:

- `repo-operating-system` is a method layer concern, not a product feature.
- `deployment-cicd` becomes incorrectly coupled to repo governance.
- The capability entry is prose, not a stable ID.

Correct operating-system plan metadata:

```yaml
---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/intent/
  - docs/operating_system/
  - agent-core/adapters/
  - repo_config/
  - scripts/
related_features: []
related_stages: []
---
```

Correct operating-system prose destination:

```text
docs/operating_system/project-os-adoption.md
```

## Cleanup Guidance For Misrouted Features

When a project already has a method-layer feature such as `repo-operating-system`:

1. Move durable method guidance into `docs/operating_system/`.
2. Move bounded design/execution history into specs/plans with `layer: operating_system`.
3. Remove the misrouted feature contract from `docs/features/`.
4. Remove feature dependency edges that point from method work to product features.
5. Regenerate feature discovery if the project has architecture sync tooling.
6. Confirm product feature indexes no longer include the operating-system artifact.

## Future Validator Guardrails

A future validation script may reject or warn on these patterns:

- feature IDs such as `repo-operating-system`, `agent-rules`, `docs-governance`, or `publication-workflow`
- feature contracts whose refs mostly point to `docs/operating_system/`, `agent-core/`, `.agents/`, `.codex/`, `repo_config/`, or scripts
- `depends_on` edges from product features to repo-method concepts
- capability IDs containing spaces, colons, backticks, or sentence punctuation
- human-created generated feature contracts when the adopted convention expects `feature.source.yaml`

The validator should be advisory at first unless the project has explicitly adopted managed architecture metadata.

## Acceptance Criteria

The implementation is complete when:

- `docs/operating_system/feature-routing-guide.md` exists and includes decision, eligibility, dependency, and capability-ID rules.
- `docs/adoption_guide.md` links to the routing guide before feature/stage creation instructions.
- `docs/features/README.md` states that features are product/domain capabilities only.
- `docs/operating_system/skill-doc-system-lifecycle.md` explicitly warns against modeling repo-method work as features.
- The bad `repo-operating-system` pattern is documented as an anti-pattern.
- The guide shows the corrected `layer: operating_system` spec/plan metadata shape.
- The starter remains valid even when no product features have been created yet.

## Open Questions

- Should the starter include `scripts/validate_doc_routing.py` now, or keep that as a later hardening step?
- Should feature routing validation be a warning by default and an error only when managed architecture docs are enabled?
- Should the starter include an example product feature, or would that increase copying risk for unrelated projects?
