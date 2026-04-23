# Configuration

Configuration for `<project-name>` lives in versioned config files plus environment-specific values.

## Config Files

- `configs/starter-runtime.yaml`: default runtime profile, paths, and logging choices
- `<additional-config-path>`: `<purpose>`

## Environment Values

| Name | Required | Example | Purpose |
| --- | --- | --- | --- |
| `<ENV_VAR>` | yes | `<example-value>` | `<why-it-is-needed>` |
| `<OPTIONAL_ENV_VAR>` | no | `<example-value>` | `<optional-purpose>` |

Do not put private credentials in tracked files. Document where they should come from, such as a local secret manager, CI secret, or ignored environment file.

## Profiles

| Profile | Use | Command Or Setting |
| --- | --- | --- |
| `<local-profile>` | local development | `<profile-command>` |
| `<ci-profile>` | automated validation | `<profile-command>` |
| `<prod-like-profile>` | production-like rehearsal | `<profile-command>` |

## Override Rules

1. Versioned defaults come from `configs/starter-runtime.yaml`.
2. Environment variables override safe defaults.
3. Local ignored files may override developer-only paths.
4. CI and deployment systems must declare their own values explicitly.

## Reproducibility Notes

When a run depends on a config value, document the value name and the selected profile in run logs or experiment notes. This prevents hidden local state from becoming part of the result.
