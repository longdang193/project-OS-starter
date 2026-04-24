# <project-name>

Short public-safe summary of what this project does, who it serves, and what result it produces.

## Status

- Adoption mode: starter method only
- Runtime profile: `<runtime-profile>`
- Primary entrypoint: `<run-command>`

## What This Includes

This project starts from the Mode A starter pack. It adopts repo governance, intent docs, adapter mapping, publication boundaries, runtime config, and required project docs without adopting managed architecture metadata.

Mode A is intentionally lighter than managed architecture metadata. It should
not require managed feature folders, generated architecture discovery, or the
full architecture sync/generator toolchain unless the project later opts into
managed mode.

As the repo grows, the validator may still warn if obvious prose anchors are
missing. The most common early warnings are:

- add `docs/features/README.md` once the repo has meaningful product/runtime surface
- add `docs/api.md` once the repo clearly exposes an external interface

Those are Mode A discovery warnings, not managed-metadata requirements by
themselves.

Treat the maturity ladder as:

`starter_method_only -> lightweight anchors -> managed_architecture_metadata`

So these docs are early anchors, not the mature end-state for a repo with
durable product features or interfaces.

If the repo keeps growing after those anchors exist, the validator may also
warn that the project appears to have outgrown lightweight anchors and should
start planning migration to `managed_architecture_metadata`.

Fill the placeholders in this file and the mirrored files under `docs/`, `repo_config/`, `configs/`, `scripts/`, and `tests/`. Keep reproducibility details such as dependency versions, setup commands, config names, and run commands in the public-safe docs instead of deleting them.

## Quick Start

1. Install prerequisites from `docs/setup.md`.
2. Configure environment values from `docs/configuration.md`.
3. Run the project with the commands in `docs/usage.md`.
4. Review workflow stages in `docs/pipeline.md`.

## Repository Map

- `docs/setup.md`: reproducible setup steps and dependencies
- `docs/configuration.md`: config files, environment values, and override rules
- `docs/usage.md`: normal run commands after setup
- `docs/pipeline.md`: workflow or processing stages
- `docs/architecture.md`: system components and boundaries
- `docs/intent/`: purpose, constraints, stakeholders, and success outcomes
- `repo_config/`: adoption mode, publication boundary, and adapter mappings
- `configs/`: runtime and workflow settings
- `scripts/`: project automation entrypoints
- `tests/`: validation and regression checks
