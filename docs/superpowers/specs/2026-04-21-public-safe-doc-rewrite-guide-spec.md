---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/operating_system/procedures/publication-procedure.md
  - docs/operating_system/
  - docs/adoption_guide.md
  - README.md
  - docs/setup.md
  - docs/configuration.md
  - docs/usage.md
  - docs/pipeline.md
  - docs/architecture.md
related_features: []
related_stages: []
---

# Public-Safe Doc Rewrite Guide Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add a dedicated guide for rewriting private starter-oriented docs into public-safe, product-facing documentation.
Reasoning: This is publication-boundary and documentation-governance work. It does not change runtime behavior, feature contracts, or architecture metadata.
Invariants:

- The private repo remains the development source of truth.
- The public repo remains a curated publication surface.
- A doc being allowed in the public mirror should depend on whether it has been rewritten for public users or contributors, not only on its filename.
- Starter adoption/bootstrap guidance remains private-only by default until intentionally rewritten.
- Public-safe rewrite guidance should distinguish repo-internal method material from product-facing documentation.

Dependencies:

- `docs/operating_system/procedures/publication-procedure.md`
- `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- `docs/adoption_guide.md`
- `repo_config/publication-config.json`

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
  - `README.md`
  - `docs/setup.md`
  - `docs/configuration.md`
  - `docs/usage.md`
  - `docs/pipeline.md`
  - `docs/architecture.md`
  - `docs/operating_system/procedures/publication-procedure.md`
- readme: `README.md`
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo now has an explicit rule that starter adoption/bootstrap docs are
private-only by default. It also says that public-facing setup, usage,
architecture, and similar docs may still be published when they are rewritten
for product users or contributors.

However, the repo does not yet have one dedicated guide that explains how to
perform that rewrite.

Right now the guidance is fragmented:

- publication workflow explains the private/public boundary
- private/public governance skill explains content classification
- adoption docs mark themselves as private-source onboarding material

What is still missing is a practical rewrite guide that shows how to convert
docs such as these into public-safe versions:

- `README.md`
- `docs/setup.md`
- `docs/configuration.md`
- `docs/usage.md`
- `docs/pipeline.md`
- `docs/architecture.md`

Without that guide, teams can understand the boundary in theory but still miss
the mechanics of making public docs stand alone.

## Goal

Create a dedicated guide for rewriting cross-cutting docs into public-safe,
product-facing documentation.

The guide should help contributors decide:

- what to remove from private starter-oriented docs
- what to keep and strengthen for public readers
- how to tell whether a doc still depends on private repo context

## Non-Goals

This spec does not make all cross-cutting docs public by default.

This spec does not rewrite the docs automatically.

This spec does not replace the existing publication-boundary rules.

This spec does not define public-safe rewriting for every possible file in the
repo.

This spec does not require public frontmatter or architecture-linkage metadata
for public-facing docs.

## Proposed Guide

Add a dedicated operating-system guide, for example:

```text
docs/operating_system/public-safe-doc-rewrite-guide.md
```

This guide should explain how to rewrite private starter-oriented docs into
public-safe docs that can stand alone in a curated public mirror.

It should be linked from:

- `docs/operating_system/procedures/publication-procedure.md`
- any future publication-boundary or governance docs where contributors need to
  move from policy to execution

## Core Rewrite Principle

A doc is public-safe when it can be understood by an external reader without
depending on:

- private repo governance layers
- starter customization order
- internal planning systems
- internal adapter/rule workflows
- private-only file paths or processes

The guide should teach contributors to rewrite docs from:

- "how to adapt the private starter repo"

into:

- "how to use, configure, contribute to, or understand the public product-facing repo"

## Required File Coverage

The guide should include dedicated rewrite sections for at least:

### `README.md`

Public-safe rewrite should:

- remove starter/bootstrap/adoption framing
- explain the product or project directly
- stand alone without references to private planning or governance docs
- link only to docs that are intended to exist in the public mirror

The guide should explicitly say to remove:

- "replace starter identity" framing
- private repo customization order
- references to `docs/operating_system/`, `docs/superpowers/`, `.agents/`,
  `.codex/`, or other private-only layers as required reading

### `docs/setup.md`

Public-safe rewrite should:

- explain how a contributor or user sets up the public project
- keep dependencies, tool versions, prerequisites, and bootstrap steps
- remove private starter-adoption sequencing and private repo customization
  instructions

### `docs/configuration.md`

Public-safe rewrite should:

- explain public-safe configuration surfaces
- keep environment-variable and config-file guidance that applies to users or
  contributors
- remove private publication workflow details, private governance references,
  and private-only path assumptions

### `docs/usage.md`

Public-safe rewrite should:

- explain how to run or use the public project after setup
- keep commands, entrypoints, and normal user/contributor flows
- remove "how to turn the starter into your repo" instructions

### `docs/pipeline.md`

Public-safe rewrite should:

- explain the product workflow or processing flow in reader-facing language
- remove internal migration guidance or internal starter-method sequencing

### `docs/architecture.md`

Public-safe rewrite should:

- explain the public-facing system architecture
- keep components, boundaries, and integrations that help readers understand
  the product
- remove internal repo-method layers unless they are genuinely part of the
  public project architecture

## Rewrite Checklist

The guide should include a concise checklist such as:

- remove starter/adoption/bootstrap framing
- remove private-only path references
- remove references to internal planning or governance surfaces
- keep only product-facing setup/configuration/usage/architecture details
- ensure the doc stands alone without private context
- ensure linked docs are also public-safe or intentionally omitted from the
  public mirror

## Red-Flag Content

The guide should name concrete rewrite red flags, for example:

- "replace starter identity"
- "first hour checklist"
- "choose adoption mode"
- references to `docs/operating_system/`
- references to `docs/superpowers/`
- references to `.agents/` or `.codex/`
- instructions about adapter sync or private publication workflow
- "how to customize the private starter repo"

The presence of these is not always automatically wrong, but they should
trigger review before a doc is treated as public-safe.

## Publication Procedure Update

Update `docs/operating_system/procedures/publication-procedure.md` to link to the new
rewrite guide from the publication review flow.

The workflow should move from:

- "public docs must be public-safe"

to:

- "here is the concrete guide for rewriting them"

## Acceptance Criteria

The implementation is complete when:

- a dedicated public-safe doc rewrite guide exists
- it covers at least `README.md`, `docs/setup.md`, `docs/configuration.md`,
  `docs/usage.md`, `docs/pipeline.md`, and `docs/architecture.md`
- it explains what to remove, what to keep, and how to judge whether a doc is
  public-safe
- publication workflow docs link to it
- the guide stays aligned with the private/public boundary already defined in
  the repo

## Open Questions

- Should the rewrite guide live only under `docs/operating_system/`, or should
  there also be a shorter link or summary from `README.md` for maintainers?
- Should a later validator or publication check scan public docs for obvious
  private-only phrases such as `docs/operating_system/` or `docs/superpowers/`?
- Should the guide eventually include before/after examples for each required
  doc type?
