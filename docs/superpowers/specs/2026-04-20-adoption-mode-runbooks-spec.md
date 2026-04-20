---
layer: operating_system
artifact_type: spec
status: proposed
parent_workstream: none
targets:
  - docs/adoption_guide.md
  - docs/operating_system/project-adoption-migration-guide.md
related_features: []
related_stages: []
---

# Adoption Mode Runbooks Spec

## Problem

The starter now defines adoption modes and validation guardrails, but the project adoption guide does not yet give agents a clear step-by-step procedure for each mode.

That gap is especially risky for Mode B, because managed architecture metadata is an all-layer adoption path. An agent can easily make the project look partially migrated by creating feature folders while forgetting generated contracts, source metadata references, capability ID normalization, code/config/test metadata, or validation.

Observed failure patterns this spec is designed to prevent:

- creating a method-layer pseudo-feature such as `repo-operating-system`
- leaving product features as flat `docs/features/*.yaml` files after choosing managed metadata
- creating feature folders without required source and generated files
- using product feature dependencies to represent operating-system adoption work
- normalizing docs while forgetting code/config/test metadata that feeds generated lineage
- changing the guide but not giving an agent an executable sequence for Mode B

## Goal

Add mode-specific runbooks to the adoption guidance so a future agent can adopt the starter from scratch or halfway through an existing project without inventing the migration sequence.

The runbooks should make these decisions explicit:

- which adoption mode to select first
- which files are authoritative in that mode
- which files must not be created in that mode
- how to migrate into managed architecture metadata safely
- what validation marks the mode as coherent

## Non-Goals

This spec does not add a new adoption mode.

This spec does not change the adoption-mode validator.

This spec does not migrate any downstream project.

This spec does not define a full architecture generator contract.

This spec does not require every project to adopt managed feature/stage metadata. Mode A remains valid when the project only wants the repo operating-system method.

## Design Principles

Every adoption path must start by declaring the intended mode in `repo_config/adoption-mode.yaml`.

Every adoption path must end with `python scripts/validate_adoption_shape.py`.

The guide should treat managed architecture metadata as a whole-project contract, not as a cosmetic folder layout.

The guide should prefer deriving downstream metadata from upstream sources instead of asking users or agents to manually enter the same fact in several places.

Operating-system adoption work must stay in the operating-system layer. It must not be represented as a product feature, stage, capability, or product dependency.

## Proposed Documentation Changes

Update `docs/operating_system/project-adoption-migration-guide.md` with three explicit runbook sections:

```text
## Mode A Step-By-Step: Starter Method Only
## Mode B Step-By-Step: Managed Architecture Metadata
## Mode C Step-By-Step: Legacy Compatibility
```

Update `docs/adoption_guide.md` to point adopters to the mode-specific runbooks before they create or migrate product feature metadata.

## Mode A Runbook Requirements

Mode A is for projects that want the repo operating-system method without adopting product feature/stage metadata yet.

The runbook should instruct the agent to:

1. Set `repo_config/adoption-mode.yaml` to `starter_method_only`.
2. Fill or update intent docs for the project purpose, constraints, stakeholders, and success outcomes.
3. Adopt operating-system docs, agent instructions, rules, adapter sync, publication guidance, and memory guidance as needed.
4. Avoid creating product feature folders, stage contracts, generated architecture indexes, or code/config/test feature metadata.
5. Represent method-layer changes as operating-system specs/plans with explicit `targets`.
6. Run adapter sync and verification if adapter, agent instruction, or generated rule surfaces changed.
7. Run `python scripts/validate_adoption_shape.py`.
8. Commit only after the repo has no accidental product architecture metadata.

The runbook should include a stop condition:

- if the project needs product feature lineage, stage ownership, or generated feature contracts, create a Mode B migration plan instead of adding one-off feature files.

## Mode B Runbook Requirements

Mode B is for projects that want managed architecture metadata for product features, stages, capabilities, generated contracts, and traceability.

The runbook should be the most detailed path and should instruct the agent to:

1. Set `repo_config/adoption-mode.yaml` to `managed_architecture_metadata`.
2. Inventory existing product docs, flat feature YAML files, stage docs, generated files, code metadata, config metadata, test metadata, and pipeline/component metadata.
3. Classify each candidate as product feature, product stage, product capability, cross-cutting product doc, or operating-system method material.
4. Remove or re-home method-layer pseudo-features. Operating-system adoption belongs in `docs/operating_system/` and operating-system specs/plans, not `docs/features/`.
5. Create one folder per real product feature under `docs/features/<feature_id>/`.
6. Move human-owned feature meaning into `docs/features/<feature_id>/feature.source.yaml`.
7. Ensure generated feature outputs use `docs/features/<feature_id>/<feature_id>.yaml` and `docs/features/<feature_id>/lineage.generated.yaml`.
8. Normalize capability IDs to feature-qualified stable identifier form, such as `<feature_id>.<capability_slug>`, not prose sentences or unscoped slugs.
9. Update stage source files so `primary_features` and `supporting_features` describe stage ownership.
10. Update code, config, tests, AML components, scripts, and docs that feed lineage to reference canonical feature IDs and feature-qualified capability IDs.
11. Refresh generated architecture surfaces from source using the project generator when one exists.
12. Verify no authoritative flat `docs/features/*.yaml` files remain outside feature folders.
13. Run `python scripts/validate_adoption_shape.py`.
14. Run the relevant test suite and `git diff --check`.
15. Commit only after the managed metadata, generated files, source metadata, and tests agree.

The runbook should include an explicit warning:

- do not switch to Mode B just because one feature folder was created. Mode B means the project has adopted the managed metadata contract across docs and source metadata.

## Mode C Runbook Requirements

Mode C is for existing projects that already have legacy feature contracts and need a safe temporary holding pattern.

The runbook should instruct the agent to:

1. Set `repo_config/adoption-mode.yaml` to `legacy_compatibility`.
2. Record `migration_follow_up.required: true` and point it at the plan or issue that will migrate the project to Mode A or Mode B.
3. Inventory existing flat feature contracts and identify which are product features versus method-layer material.
4. Keep legacy flat feature contracts as the temporary current truth.
5. Do not create managed feature folders, generated feature contracts, or generated lineage files until a Mode B migration plan is executed.
6. Re-home obvious method-layer pseudo-features into operating-system docs/specs/plans when safe.
7. Run `python scripts/validate_adoption_shape.py`.
8. Treat validator warnings as migration debt unless the guide documents why they are intentionally allowed in Mode C.
9. Commit only after the legacy state is explicit and the migration follow-up is discoverable.

The runbook should include a stop condition:

- if the work requires generated lineage or capability-level code tracing, do not keep extending Mode C. Move to a Mode B migration plan.

## Acceptance Criteria

The migration guide contains all three mode-specific step-by-step sections.

The Mode B section explicitly covers feature folder packing, required files, capability ID normalization, stage ownership, source metadata updates, generated refresh, validator checks, tests, and diff checks.

The Mode A section clearly says not to create product feature/stage/generated metadata.

The Mode C section clearly says legacy compatibility is temporary and requires a migration follow-up.

The adoption guide links to the mode-specific runbooks before telling users to adjust feature or stage metadata.

No code, validator, or config changes are required by this spec.

`git diff --check` passes after the documentation update.

## Open Questions

Should the guide include a short Mode B example migration for one feature, or should that stay in a separate example document?

Should the Mode C runbook allow deleting method-layer pseudo-features immediately, or should it require a separate operating-system cleanup plan when the downstream project is large?

Should the validator later require a migration follow-up link for every `legacy_compatibility` project, or is documentation enough for now?
