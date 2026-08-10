# Harness Core Consumer Setup

Use this procedure when a consumer repository first adopts, upgrades, or
repairs package-backed harness execution.

## Ownership

`harness-core` owns request admission, packet lifecycle, run records, and
controller decisions. `harness-core-launcher` lets legacy consumer bridge
scripts delegate to that installed package. Provider hosts own lane dispatch;
consumer scripts never implement managed execution.

## Install

Install the organization-managed `harness-core-launcher` release channel. Do
not copy release tags, host paths, host APIs, packet APIs, or provider contract
values into consumer repositories. Host source owns its locked core dependency;
the active local runtime pointer proves their exact compatible release profile.

Consumer policy owns only route intent and `harness_core.request_api`. Do not
copy package internals or rewrite bridge scripts.

## Preflight

Run from consumer repository root:

```powershell
uv run --locked harness-core --identity
uv run --locked harness-core validate --repo-root .
```

For managed provider work, use the active local runtime only:

```powershell
harness-core-launcher doctor
harness-core-launcher capabilities
harness-core-launcher preflight
```

`harness-core-launcher` selects one verified pointer-owned host root. Never
invoke bare `codex-harness-host`; PATH can select stale runtime. Provider host
owns trusted user transport configuration. Repository policy never carries
endpoint, launch-command, or credential values.
For `stdio` plus `host_spawn`, provider host requires Windows Job containment
and rejects unsupported hosts before child creation with
`containment_unavailable`; configure trusted external WebSocket transport
instead. Host lifecycle and recovery evidence rules live in
[`managed-execution-adapter-contract.md`](managed-execution-adapter-contract.md).

Core derives provider compatibility from its runtime protocol profile. Legacy
provider `contract_version` is diagnostic-only; current policy must not add a
second compatibility table. Historical packets remain readable without profile
backfill and never become current dispatch evidence.

Migration preflight reports active unleased legacy attempts as isolated. They
cannot dispatch or resume, but do not block new leased-packet admission. Preserve
their packet bytes. External operator creates signed
`legacy_cleanup_attestation/v1` with `harness-core sign-legacy-cleanup`, using
an Ed25519 key outside repository and agent workspace. Current trusted public
records live only in `~/.codex/harness-authorities.toml`; migrate an existing
old file with `harness-core migrate-harness-authorities` before validation.
Controller submits canonical `terminalize-attempt --input <envelope.json>`.
The temporary `--evidence <legacy-attestation.json>` wrapper accepts only a
policy-defined historical legacy attestation. `--auto-block` is retired. Core
validates signature, scope, identity, and freshness, records a block-only
`attempt_outcome/v2`, then policy auto-finalizes one `attempt_terminal_receipt/v3`.
Direct legacy abandonment is retired. Ambiguous outcomes require an external
`sign-controller-authorization` signature and an outcome envelope; raw actor
or approval flags are rejected. Core issues a finite execution lease only when
`planned` becomes `running`; host returns bounded terminal observations while
controller alone invokes `terminalize_attempt(envelope)`.

Upgrade host and core through one staged release profile. Preserve old runs and
create successors after migration; never mutate historical packet evidence.

For local `codex-harness-host` development, policy/schema changes require a
published core release plus matching host `pyproject.toml` and `uv.lock` pins.
Starter-kit synchronization does not update host virtual environments. From
`project-OS-starter`, run:

```powershell
pwsh -NoProfile -File .\scripts\deploy_harness_core_to_host.ps1
```

The bridge stages and verifies the host release profile, atomically activates
the local pointer, then runs doctor and preflight. It never resolves host from
PATH. A host run rejects a present `repo_config/harness.yaml` when its version
differs from loaded `policy_schema_version`, before packet creation.

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
