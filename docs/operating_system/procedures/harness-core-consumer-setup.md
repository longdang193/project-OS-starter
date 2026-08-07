# Harness Core Consumer Setup

Use this procedure when a consumer repository first adopts, upgrades, or
repairs package-backed harness execution.

## Ownership

`harness-core` owns request admission, packet lifecycle, run records, and
controller decisions. `harness-core-launcher` lets legacy consumer bridge
scripts delegate to that installed package. Provider hosts own lane dispatch;
consumer scripts never implement managed execution.

## Install

Pin both packages to released source tags compatible with provider host. Current
tested pins: `harness-core-v0.1.11` and `harness-core-launcher-v0.1.0`.

```powershell
uv add "harness-core @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-v0.1.11#subdirectory=packages/harness-core"
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

Current Codex App Server policy requires `harness_core.request_api: 4` and
provider `contract_version: 3`. Core resolves packet API 4 for that pair. Do
not force request API 3 for new work: host API 3 can read historical packet API
3 evidence but cannot dispatch it. Upgrade policy, provider pin, and core pin
together; preserve old runs and create successors after migration.

## Failure Routing

| Result | Owner | Action |
| --- | --- | --- |
| `harness_core_environment_unavailable` | environment | Install or repair package environment. No packet exists. |
| `harness_core_request_api_incompatible` | consumer release pin | Upgrade or pin consumer package release. No packet exists. |
| `harness_core_host_api_incompatible` | provider host release pin | Upgrade or pin provider host and core release line. No packet exists. |
| `harness_core_packet_dispatch_incompatible` | policy/host compatibility skew | Preserve historical packet evidence. Align request API, packet API, and host contract; then create successor. |
| `execution_mode_unavailable` | provider host capability | Block or record controller waiver. Do not use generic CLI as fallback. |

Legacy `python scripts/harness_task.py ...` remains supported during migration,
but new automation uses installed `harness-core` commands or provider-host
entrypoints.
