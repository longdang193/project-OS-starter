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
tested pins: `harness-core-v0.1.14` and `harness-core-launcher-v0.1.0`.

```powershell
uv add "harness-core @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-v0.1.14#subdirectory=packages/harness-core"
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

For managed provider work, then run provider-host capability and transport
preflight. For `codex_app_server`, use `codex-harness-host capabilities` then
`codex-harness-host preflight`; provider host owns trusted user transport
configuration. Repository policy never carries endpoint, launch-command, or
credential values.

Current Codex App Server policy requires `harness_core.request_api: 4` and
provider `contract_version: 4`. Core resolves packet API 5 for host API 4 and
that pair. Packet API 4 remains historical evidence and dispatches only with
host API 3 / provider contract 3; packet API 3 remains historical evidence.
Upgrade policy, provider pin, and core pin together; preserve old runs and
create successors after migration.

For local `codex-harness-host` development, policy/schema changes require an
explicit runtime deployment. Starter-kit synchronization does not update host
virtual environments. From `project-OS-starter`, run:

```powershell
pwsh -NoProfile -File .\scripts\deploy_harness_core_to_host.ps1
```

The command installs only editable `harness-core` into the host environment,
proves its import origin and runtime identity, then runs host capabilities and
preflight. A host run rejects a present `repo_config/harness.yaml` when its
`version` differs from loaded `policy_schema_version`, before full policy
admission or packet creation.

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
