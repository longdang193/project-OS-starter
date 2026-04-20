# Stages

This folder holds stage-level documentation for repos that adopt the managed architecture-doc workflow.

Human-owned inputs live in `docs/stages/*.source.yaml`.
Generated outputs live beside them as `docs/stages/*.yaml`.

For a copy-safe Mode B stage source template, see [docs/architecture_templates/stage.source.yaml](../architecture_templates/stage.source.yaml). Generated stage contracts must come from the architecture generator, not from copied templates.

If a starter repo has not defined any managed stages yet, this folder may contain only this README.
