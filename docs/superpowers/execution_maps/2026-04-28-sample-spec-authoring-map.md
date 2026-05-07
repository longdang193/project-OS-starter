---
layer: change
artifact_type: execution_map
status: proposed
parent_workstream: starter-adoption-experience
map_type: spec_authoring
threads:
  - starter-adoption-experience.prompt-template-metadata-and-validation
  - starter-adoption-experience.adoption-prompt-discoverability-without-duplication
specs:
  - docs/superpowers/specs/2026-04-28-planning-lineage-minimal-metadata-and-validator-spec.md
  - docs/superpowers/specs/2026-04-28-derived-thread-linkage-via-planning-lineage-spec.md
---

# Sample Spec-Authoring Map

## Scope

- the next detailed-spec authoring sequence under
  `starter-adoption-experience`
- one thread focused on prompt-template metadata and validation
- one thread focused on prompt discoverability without duplication

## Dependency Graph

- detailed-spec work for prompt-template metadata and validation should come
  first because later prompt-surface refinement depends on the clarified
  lineage and metadata boundary
- prompt discoverability refinement can follow once the metadata contract is
  stable enough to reference consistently

## Authoring Waves

### Wave 1

- detailed spec for prompt-template metadata and validation

### Wave 2

- detailed spec for adoption-prompt discoverability without duplication

## Authoring Lanes

### Lane A

- metadata and validation spec first

### Lane B

- no parallel authoring lane yet; this sample stays sequential because both
  specs touch the same prompt/governance surfaces

## Shared-Surface Risks

- `docs/operating_system/prompt_templates/`
- `docs/operating_system/governance/repo-governance.md`
- `.agents/skills/`

## Recommended Next Detailed-Spec Sequence

1. finish the metadata and validation spec
2. confirm wording and lineage boundaries
3. then write the discoverability follow-up spec

## Orchestration Notes

- keep this artifact about detailed-spec authoring order only
- move actual design reasoning into the detailed specs themselves
- once the detailed specs are approved, create a separate implementation
  execution map if implementation sequencing is still non-trivial
