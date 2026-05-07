---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
  - docs/operating_system/procedures/publication-workflow.md
  - repo_config/publication-config.json
related_features: []
related_stages: []
---

# Starter Adoption Doc Publication Boundary Spec

## Triage

Layer: operating_system
Feature type: ADD
Summary: Clarify that starter adoption and bootstrap docs are private-only by default and should not be published to curated public mirrors unless explicitly rewritten as product-facing docs.
Reasoning: This is publication-boundary governance for a private-source/public-mirror workflow. It does not alter runtime behavior or product architecture.
Invariants:

- The private repo remains the development source of truth.
- The public repo remains a curated downstream publication surface.
- Starter adoption/bootstrap guidance is repo-internal method material, not product-facing documentation.
- Cross-cutting project docs such as setup and usage may still be public when they are genuinely product-facing.
- Publication rules should stay allowlist-first and explicit rather than depend on contributors remembering unwritten norms.

Dependencies:

- `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- `docs/operating_system/procedures/publication-workflow.md`
- `repo_config/publication-config.json`
- `docs/operating_system/governance/repo-governance.md`

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
  - `docs/adoption_guide.md`
  - `docs/operating_system/procedures/publication-workflow.md`
- readme: none
- generated: none

Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Problem

The repo already has a private/public boundary model, but it does not yet
explicitly classify starter adoption or bootstrap docs as private-only by
default.

That gap is subtle today because the current publication config only exports
`README.md`. However, once a project broadens its public allowlist, it becomes
easy to publish docs that are useful for private repo onboarding but not
appropriate for a product-facing public mirror.

Examples:

- `docs/adoption_guide.md`
- starter migration runbooks
- clone/bootstrap instructions for turning the starter into a private project
- repo-internal guidance about which starter layers to customize first

These docs explain how to adapt the starter as an internal engineering
workspace. They are not the same thing as public setup, usage, architecture, or
API docs for the product itself.

## Goal

Make the publication boundary explicit:

- starter adoption/bootstrap docs are private-only by default
- product-facing cross-cutting docs may still be public
- the skill and publication governance docs should teach this boundary clearly

## Non-Goals

This spec does not classify every file under `docs/` as private.

This spec does not forbid public setup, configuration, usage, pipeline, or
architecture docs when they are written for the public product-facing repo.

This spec does not require a new publish script or a new publication system.

This spec does not require immediate changes to the current allowlist if the
repo is already safe by default.

## Proposed Classification Rule

Treat starter adoption and bootstrap docs as `always_private` by default.

This includes docs whose primary purpose is:

- how to clone or adapt the starter
- how to replace starter identity or starter structure
- how to choose starter adoption modes
- how to migrate from starter scaffolding into a project-specific repo shape
- how to customize internal repo method layers after cloning the starter

Concrete examples in this repo:

- `docs/adoption_guide.md`
- starter-specific migration guides when they are about internal repo adoption

## Public-Safe Exception Rule

A doc that began life as starter adoption guidance may be made public only if
it is intentionally rewritten as product-facing documentation and no longer
depends on private repo context.

A doc should remain private if it:

- refers to the starter as starter infrastructure
- teaches internal repo customization order
- depends on private governance layers such as `docs/operating_system/`,
  `docs/superpowers/`, `.agents/`, or `.codex/`
- describes internal publication or adapter workflows

## Skill Update

Update `.agents/skills/skill-private-public-repo-governance/SKILL.md` so it
explicitly includes starter adoption/bootstrap docs in the `always_private`
examples.

The skill should also warn that:

- public mirrors should not contain "how to customize the private starter repo"
  docs
- setup/usage docs can still be public when they are rewritten for product
  users or contributors rather than private starter adopters

## Publication Workflow Update

Update `docs/operating_system/procedures/publication-workflow.md` to explicitly name
starter adoption/bootstrap docs as private-only by default.

The workflow should teach contributors to distinguish:

- repo-internal adoption docs
- public product-facing docs

This distinction matters because both may live under `docs/`, but they do not
belong to the same publication class.

## Publication Config Consideration

`repo_config/publication-config.json` may not need an immediate behavioral
change if the current allowlist already excludes the relevant docs.

However, the spec should allow either of these follow-ups:

- document the boundary only, leaving config unchanged for now
- add an explicit forbidden-path entry for starter adoption docs if the repo
  wants stronger defense in depth

## Acceptance Criteria

The implementation is complete when:

- the private/public governance skill explicitly treats starter adoption or
  bootstrap docs as private-only by default
- `docs/operating_system/procedures/publication-workflow.md` teaches the same rule
- the docs clearly distinguish private starter-adoption guidance from
  potentially public product-facing docs under `docs/`
- the resulting rule does not accidentally classify all cross-cutting docs as
  private
- any config change, if made, remains aligned with the allowlist-first publish
  model

## Open Questions

- Should `docs/adoption_guide.md` be added explicitly to
  `repo_config/publication-config.json` forbidden paths for defense in depth, or
  is doc/skill guidance enough while the public allowlist remains narrow?
- Are there other starter-only docs that should be grouped under the same rule,
  such as future bootstrap checklists or migration runbooks outside
  `docs/operating_system/`?
