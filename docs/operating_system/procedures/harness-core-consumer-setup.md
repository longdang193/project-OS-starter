# Harness Core Consumer Setup

Use this procedure when a consumer repository first adopts, upgrades, or
repairs package-backed harness execution.

## Ownership

`harness-core` owns request admission, packet lifecycle, run records, and
controller decisions. `harness-core-launcher` lets legacy consumer bridge
scripts delegate to that installed package. Provider hosts own lane dispatch;
consumer scripts never implement managed execution.

## Install

Pin both packages to their released source tags. Current compatible pins:
`harness-core-v0.1.4` and `harness-core-launcher-v0.1.0`.

```powershell
uv add "harness-core @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-v0.1.4#subdirectory=packages/harness-core"
uv add "harness-core-launcher @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-launcher-v0.1.0#subdirectory=packages/harness-core-launcher"
```

Commit generated `pyproject.toml` and `uv.lock`. Provider host owns its own
compatible pins; match its committed `pyproject.toml` and lockfile. Do not copy
package internals or rewrite bridge scripts. Starter kit bridge scripts only
delegate to installed packages.

## Preflight

Run from consumer repository root:

```powershell
uv run harness-core --identity
uv run harness-core validate --repo-root .
```

For managed provider work, then run provider-host capability preflight. For
`codex_app_server` use `codex-harness-host capabilities`; provider host owns
the exact command and endpoint configuration.

## Failure Routing

| Result | Owner | Action |
| --- | --- | --- |
| `harness_core_environment_unavailable` | environment | Install or repair package environment. No packet exists. |
| `harness_core_request_api_incompatible` | consumer release pin | Upgrade or pin consumer package release. No packet exists. |
| `harness_core_host_api_incompatible` | provider host release pin | Upgrade or pin provider host and core release line. No packet exists. |
| `execution_mode_unavailable` | provider host capability | Block or record controller waiver. Do not use generic CLI as fallback. |

Legacy `python scripts/harness_task.py ...` remains supported during migration,
but new automation uses installed `harness-core` commands or provider-host
entrypoints.
