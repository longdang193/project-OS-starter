# Setup

This guide explains how to reproduce a working local environment for `<project-name>`.

## Prerequisites

- Operating system: `<supported-os-and-version>`
- Language/runtime: `<runtime-name-and-version>`
- Package manager: `<package-manager-and-version>`
- External services: `<required-services-or-none>`

## Clone And Prepare

```powershell
git clone <repo-url>
cd <repo-folder>
<environment-create-command>
<dependency-install-command>
```

Record exact dependency sources, lockfiles, and version constraints here. Do not rely on unstated local tools.

## Local Resources

- Input data location: `<data-or-fixture-path>`
- Config template: `configs/starter-runtime.yaml`
- Secrets location: `<secret-store-or-env-file-policy>`

## Verification

Run the smallest setup check that proves the environment is ready:

```powershell
<setup-check-command>
```

Expected result: `<expected-setup-check-output>`.

## Troubleshooting

- Missing runtime: install `<runtime-name-and-version>` and rerun the dependency command.
- Missing config: copy the documented template and fill project-local values.
- Missing data: use the dataset source or fixture path documented by the project.
