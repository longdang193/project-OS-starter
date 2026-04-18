---
name: doc-system-lifecycle
description: Use for designing, updating, or auditing project docs. Defines the 5-layer doc system, naming, frontmatter, sync rules, and generated discovery. Applies to NEW documents; existing docs are grandfathered
---


# Doc System Lifecycle

## When to Apply

Apply when:

- creating or revising docs
- designing doc structure
- adding or changing features
- changing architecture, routes, settings, or schemas
- reviewing docs for clarity, discoverability, or consistency

## Core Principle

> Documentation is the project’s navigation, discovery, and explanation system.  
> It should let a human or agent answer: what exists, what is current, what changed, why it changed, and where the real source of truth lives.

Docs should explain code, not mirror it.

## 5-Layer Doc System with Stage-Aware Extension

```text
code/                                → real truth
docs/stages/*.source.yaml            → human-owned stage source when stage-aware docs are in scope
docs/stages/*.yaml                   → generated stage contracts when stage-aware docs are in scope
docs/features/*/feature.source.yaml  → human-owned feature source
docs/features/*/<feature_id>.yaml    → generated current feature contract
docs/features/*/lineage.generated.yaml → generated feature-local evidence
docs/features/<feature_id>/          → feature-specific explanation + partial-generated history
docs/*.md                            → cross-cutting explanation
README.md                            → overview
docs/generated/                      → generated discovery
````

| Layer                      | Form                                      | Purpose                               | Rule                                |
| -------------------------- | ----------------------------------------- | ------------------------------------- | ----------------------------------- |
| Real Truth                 | code                                      | Actual behavior                       | Deepest truth                       |
| Stage Source               | `docs/stages/*.source.yaml`               | Human-owned stage intent              | Edit directly when stage meaning changes |
| Stage Contract             | `docs/stages/*.yaml`                      | Generated stage boundary view         | Generated only                      |
| Feature Source             | `docs/features/*/feature.source.yaml`     | Human-owned feature meaning           | Edit directly when feature meaning changes |
| Feature Contract           | `docs/features/*/<feature_id>.yaml`       | Generated current feature contract    | Generated only                      |
| Feature Local Evidence     | `docs/features/*/lineage.generated.yaml`  | Generated ownership and lineage facts | Generated only                      |
| Feature Explanation/History| `docs/features/<feature_id>/*`            | Design, flow, ops notes, history      | Feature-specific only               |
| Cross-Cutting Docs         | `docs/*.md`                               | Architecture, pipelines, shared ops   | Cross-feature only                  |
| Overview                   | `README.md`                               | Purpose and navigation                | Entry point only                    |
| Generated Discovery        | `docs/generated/*`                        | Fast lookup                           | Generated only; never edit manually |

### Layer 1 — Code

Authoritative for behavior, routes/APIs, and schema/data logic.

### Layer 2 — Stage Source And Stage Contracts

Stage-aware projects may add:

```text
docs/stages/*.source.yaml
docs/stages/*.yaml
```

Use the stage source layer for:

- stage identity
- purpose
- inputs / outputs
- architectural boundaries
- stage-to-feature relationships
- short human notes

Rules:

- stages are above features for navigation, not replacement lifecycle units
- humans edit `docs/stages/*.source.yaml`
- generated stage contracts must not duplicate full feature truth
- do not create placeholder stage files before a project-specific rollout is ready

Use the generated stage contract only as the assembled current view. Do not edit
its generated refs directly.

### Layer 3 — Feature Source, Generated Contract, And Evidence

Use `docs/features/*/feature.source.yaml` as the human-owned semantic source.
Use the generated `<feature_id>.yaml` only as the assembled current-state
contract.

Rules:

- one real feature folder per managed feature
- edit `feature.source.yaml`, not generated feature YAML
- do not keep manual feature `version`
- freshness fields such as `revision`, `latest_change_id`, and
  `last_updated_at` are generated from completed plans
- do not use `manual_refs`; refs come from metadata on the owning code, tests,
  docs, specs, plans, configs, and AML components
- use `lineage.generated.yaml` for detailed evidence, ownership, and timeline
  facts

Recommended feature-source shape:

```yaml
feature_id:
name:
status:
type:
summary:
invariants: []
domains: []
depends_on: []
capabilities: []
stage_participation: []
lineage_exceptions: []
```

### Layer 4 — Explanation + History

Use `docs/features/<feature_id>/` for focused docs such as design, flow, ops notes, and history for one feature. Use `docs/*.md` only for cross-feature architecture docs. Specs and plans continue to live under `docs/superpowers/`.

Rules:

- explanation, not duplication
- current-state docs describe current behavior
- rationale belongs here, not in YAML
- prefer small focused docs over one large doc
- `history.md` is partially generated when the feature is opted into the
  architecture system:
  - the block between `<!-- GENERATED HISTORY START -->` and
    `<!-- GENERATED HISTORY END -->` is generator-owned
  - `## Human Notes` stays human-authored
- read feature folders minimally:
  - `feature.source.yaml` first
  - generated contract only when the assembled view is needed
  - `lineage.generated.yaml` only for ownership/evidence/drift work
  - `history.md` only when narrative context matters

### Placement Table

Use this default placement:

| Information kind | Default location |
| ---------------- | ---------------- |
| Stage boundary source (when adopted) | `docs/stages/<stage_id>.source.yaml` |
| Generated stage boundary contract (when adopted) | `docs/stages/<stage_id>.yaml` |
| Feature source | `docs/features/<feature_id>/feature.source.yaml` |
| Current feature contract | `docs/features/<feature_id>/<feature_id>.yaml` |
| Generated feature evidence | `docs/features/<feature_id>/lineage.generated.yaml` |
| Feature-specific history / post-execution review | `docs/features/<feature_id>/history.md` |
| Other feature-specific explanation | `docs/features/<feature_id>/*.md` |
| Cross-cutting architecture / pipeline / shared ops | `docs/*.md` |
| Project overview / navigation | `README.md` |
| Generated lookup surfaces | `docs/generated/*` |

Do not treat `docs/*.md` as the default home for feature-specific history.

### Layer 4 — README

Must answer:

- Why
- What
- Where

Must not become:

- a feature registry
- a design dump
- a changelog

### Layer 5 — Generated Discovery

Required for fast lookup.

Minimum outputs:

```text
docs/generated/features_index.yaml
docs/generated/feature_overview.md
```

Add more only when needed, such as:

- `feature_dependency_graph.yaml`
- `feature_file_map.yaml`
- `routes_index.yaml`
- `settings_index.yaml`

Rules:

- generate from code/YAML/docs
- never edit manually
- not a source of truth
- always point back to the source

## Artifact Conventions

| Situation                                         | Update                                  |
| ------------------------------------------------- | --------------------------------------- |
| Behavior changes                                  | code                                    |
| Stage meaning changes                             | `docs/stages/<stage_id>.source.yaml`    |
| Feature meaning changes                           | `docs/features/<feature_id>/feature.source.yaml` |
| Feature-specific explanation changes              | `docs/features/<feature_id>/*.md`       |
| Architecture or cross-feature explanation changes | `docs/*.md`                             |
| Purpose/navigation changes                        | `README.md`                             |
| Human feature history notes change                | `docs/features/<feature_id>/history.md` |
| Generated surfaces stale                          | rerun the canonical architecture sync/check workflow |

## Naming

- feature contract: `docs/features/<feature_id>/<feature_id>.yaml`
- stage source when adopted: `docs/stages/<stage_id>.source.yaml`
- generated stage contract when adopted: `docs/stages/<stage_id>.yaml`
- feature source: `docs/features/<feature_id>/feature.source.yaml`
- feature docs/history: `docs/features/<feature_id>/`
- spec: `docs/superpowers/specs/YYYY-MM-DD-HH-MM-<feature>-spec.md`
- plan: `docs/superpowers/plans/YYYY-MM-DD-HH-MM-<feature>-plan.md`
- generated files: descriptive names under `docs/generated/`

## Frontmatter for Specs and Plans

```yaml
---
feature_type: modify   # add | modify | replace
feature_name: run-input-snapshot-consistency
status: building
summary: "<1-sentence goal>"
---
```

Optional:

```yaml
invariants:
  - non-negotiable constraints
```

## Sync Principle

- update code when behavior changes
- update stage source before or with stage-meaning changes
- update feature source before or with feature-meaning changes
- update docs before or with design/reasoning changes
- update README when navigation changes
- rerun `scripts/sync_architecture_docs.py` whenever architecture metadata
  sources change

Before marking work complete, name the exact docs touched:

- affected `docs/stages/<stage_id>.source.yaml` when stage-aware docs are in scope
- affected `docs/features/<feature_id>/<feature_id>.yaml`
- affected `docs/stages/<stage_id>.yaml` when stage-aware docs are in scope
- affected `docs/features/<feature_id>/feature.source.yaml`
- affected `docs/features/<feature_id>/lineage.generated.yaml` when evidence changed
- `docs/features/<feature_id>/history.md` or other focused docs under `docs/features/<feature_id>/`
- any cross-feature docs under `docs/*.md`
- `README.md` if navigation changed
- generated outputs to refresh

If a fact is generated, update the source and regenerate.

## Cross-Reference Discipline

- README links to key docs and generated discovery
- feature YAML links to docs/spec/plan/history
- generated indexes point to authoritative files
- no orphan docs
- no conflicting current-state sources

## Anti-Patterns

- duplicating facts across code, YAML, docs, and generated files
- treating stage contracts as a replacement for feature contracts
- putting long history into YAML
- putting implementation detail into README
- manually maintaining generated relationships
- editing generated files manually
- treating docs as more authoritative than code
- changing code without updating the owning feature or stage source

## Migration Policy

Applies to NEW documents only.

Existing docs are grandfathered. They do not need to be rewritten. When a feature YAML exists, it becomes the current structured truth for that feature.

