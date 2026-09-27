# Setup

Choose one path. Reading the project needs no setup. Source evaluation needs
Python and the repository dependencies. Runtime adoption adds user-local
configuration and an optional executor setup.

## Prerequisites

- Git
- Python 3.12 or newer
- PowerShell 7 (`pwsh`) for the optional DeepAgents Code setup script

Keep API keys, Codex configuration, runtime state, and generated user-global
files outside this repository. Do not create project secret files for runtime
setup.

## Evaluate The Source

Install core validation dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run repository contract validation:

```powershell
python scripts/validate_repo_contracts.py
```

Run the full test suite when benchmark dependencies are available:

```powershell
python -m pip install -r requirements.txt -r requirements-benchmark.txt
python -m pytest -q
```

`requirements-benchmark.txt` is evaluation-only. It is not required for basic
repository contract validation or normal runtime adoption.

## Optional Runtime Setup

DeepAgents Code is an optional executor path. Its setup script requires an
existing Codex configuration and external secret storage, pins its own runtime
version, and verifies the installed wrapper. Use the script only when this
executor is needed:

```powershell
pwsh .\scripts\setup_deepagents_runtime.ps1
```

For required secret/configuration details and the personal-local runtime
procedure, read
[`personal-local-worktree-procedure.md`](operating_system/procedures/personal-local-worktree-procedure.md).

## Adopt Project OS

To use Project OS in another repository, follow the
[Project Adoption Migration](operating_system/adoption/project-adoption-migration-guide.md).
It owns shared runtime deployment, generated starter-kit handoff, and adopted
repository validation. Do not copy runtime files manually.

## Next Step

After setup, follow [`docs/usage.md`](usage.md) for source validation or the
bounded task lifecycle.
