# Runtime Configs

This directory is the starter-standard home for runtime and workflow
configuration.

Use `configs/` for:

- runtime defaults
- workflow settings
- smoke profiles
- environment-tuned project behavior

Do not use `configs/` for:

- publication boundaries
- adapter generation mappings
- generated outputs
- feature or stage lifecycle contracts

Those belong in:

- `repo_config/` for repo/system configuration
- `docs/features/*/*.yaml` for feature contracts
- `docs/stages/*.yaml` for stage contracts when stage-aware docs are in scope
