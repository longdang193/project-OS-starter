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
tested pins: `harness-core-v0.1.32` and `harness-core-launcher-v0.1.0`.
Provider-host compatibility requires matching locked core pins, admitted host
API, and committed runtime provenance. Host package version alone is not proof
that its imported runtime contains a required host-source repair.

```powershell
uv add "harness-core @ git+https://github.com/longdang193/project-OS-starter.git@harness-core-v0.1.32#subdirectory=packages/harness-core"
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
For `stdio` plus `host_spawn`, provider host requires Windows Job containment
and rejects unsupported hosts before child creation with
`containment_unavailable`; configure trusted external WebSocket transport
instead. Host lifecycle and recovery evidence rules live in
[`managed-execution-adapter-contract.md`](managed-execution-adapter-contract.md).

Current Codex App Server policy requires `harness_core.request_api: 5` and
provider `contract_version: 7`. Core resolves packet API 8 for host API 7 and
that pair. Packet APIs 3 through 7 remain historical evidence under declared
compatibility profiles. Packet API 8 never dispatches against host API 6.

Migration preflight reports active unleased legacy attempts as isolated. They
cannot dispatch or resume, but do not block new packet API 8 admission. Preserve
their packet bytes. External operator creates signed
`legacy_cleanup_attestation/v1` with `harness-core sign-legacy-cleanup`, using
an Ed25519 key outside repository and agent workspace. Current trusted public
records live only in `~/.codex/harness-authorities.toml`; migrate an existing
old file with `harness-core migrate-harness-authorities` before validation.
Controller submits canonical `terminalize-attempt --input <envelope.json>`.
The temporary `--evidence <legacy-attestation.json>` wrapper accepts only a
readable packet API 8 legacy attestation. `--auto-block` is retired. Core
validates signature, scope, identity, and freshness, records a block-only
`attempt_outcome/v2`, then policy auto-finalizes one `attempt_terminal_receipt/v3`.
Direct legacy abandonment is retired. Ambiguous outcomes require an external
`sign-controller-authorization` signature and an outcome envelope; raw actor
or approval flags are rejected. Core issues a finite execution lease only when
`planned` becomes `running`; host returns bounded terminal observations while
controller alone invokes `terminalize_attempt(envelope)`.

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
