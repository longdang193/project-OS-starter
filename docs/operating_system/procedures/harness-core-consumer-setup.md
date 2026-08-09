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
tested pins: `harness-core-v0.1.20` and `harness-core-launcher-v0.1.0`.
Provider-host compatibility requires matching locked core pins, admitted host
API, and committed runtime provenance. Host package version alone is not proof
that its imported runtime contains a required host-source repair.

```powershell
uv add "harness-core @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-v0.1.20#subdirectory=packages/harness-core"
uv add "harness-core-launcher @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-launcher-v0.1.0#subdirectory=packages/harness-core-launcher"
```

Commit generated `pyproject.toml` and `uv.lock`. Provider host owns its own
compatible pins; match its committed `pyproject.toml` and lockfile. Do not copy
package internals or rewrite bridge scripts. Starter kit bridge scripts only
delegate to installed packages.

## Preflight

Run from consumer repository root:

```powershell
uv run --locked harness-core --identity
uv run --locked harness-core validate --repo-root .
```

For managed provider work, then run provider-host capability and transport
preflight from installed provider source root. For `codex_app_server`, use
`uv run --locked codex-harness-host capabilities` then
`uv run --locked codex-harness-host preflight`; provider host owns trusted user
transport configuration. Repository policy never carries endpoint,
launch-command, or credential values.

Current Codex App Server policy requires `harness_core.request_api: 5` and
provider `contract_version: 7`. Core resolves packet API 8 for host API 7 and
that pair. Packet APIs 3 through 7 remain historical evidence under declared
compatibility profiles. Packet API 8 never dispatches against host API 6.

Before packet API 8 admission, run migration preflight. Active unleased legacy
attempts must drain or receive explicit operator abandonment; terminal history
stays immutable. Core issues a finite execution lease only when `planned`
becomes `running`. Host returns bounded terminal observations, while controller
calls only `terminalize_attempt(evidence)` for terminal state mutation.
Upgrade policy, provider pin, core pin, and host release together. For
host-source repair without a release change, use committed runtime provenance;
preserve old runs and create successors after migration.

For local `codex-harness-host` development, policy/schema changes require a
published core release plus matching host `pyproject.toml` and `uv.lock` pins.
Starter-kit synchronization does not update host virtual environments. From
`project-OS-starter`, run:

```powershell
pwsh -NoProfile -File .\scripts\deploy_harness_core_to_host.ps1
```

The command runs host through `uv run --locked`, proves locked runtime identity,
rejects an editable `harness-core`, then runs host capabilities and preflight.
Do not install starter source editable into host for managed work: next `uv run`
will restore host lock source. A host run rejects a present
`repo_config/harness.yaml` when its `version` differs from loaded
`policy_schema_version`, before full policy admission or packet creation.

## Failure Routing

| Result | Owner | Action |
| --- | --- | --- |
| `harness_core_environment_unavailable` | environment | Install or repair package environment. No packet exists. |
| `harness_core_request_api_incompatible` | consumer release pin | Upgrade or pin consumer package release. No packet exists. |
| `harness_core_host_api_incompatible` | provider host runtime or release pin | Align provider host runtime, locked core release line, and host API. No packet exists. |
| `harness_core_packet_dispatch_incompatible` | policy/host compatibility skew | Preserve historical packet evidence. Align request API, packet API, and host contract; then create successor. |
| `execution_mode_unavailable` | provider host capability | Block or record controller waiver. Do not use generic CLI as fallback. |

Legacy `python scripts/harness_task.py ...` remains supported during migration,
but new automation uses installed `harness-core` commands or provider-host
entrypoints.
