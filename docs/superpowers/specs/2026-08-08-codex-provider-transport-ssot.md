---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: codex-provider-transport-ssot
targets:
  - packages/harness-core
  - repo_config/harness.yaml
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host
  - C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit
---

# Codex Provider Transport SSOT

## Goal and Problem

### Problem

- `codex_app_server` identifies a provider capability, but current host code
  also hardcodes one WebSocket transport and endpoint.
- `AppServerClient` accepts only `ws://host:port`, performs a WebSocket upgrade,
  and connects to that port. No local listener owns `127.0.0.1:4500`.
- Canonical agent guidance repeats `ws://127.0.0.1:4500`, but does not identify
  a bridge binary, lifecycle owner, authentication source, configuration source,
  or health contract.
- consequence: a normal managed run blocks before packet creation unless an
  undocumented external daemon happens to exist. Controllers must diagnose
  machine setup rather than submit work uniformly.

### Goal

`codex_app_server` remains one provider identity. The host resolves its local
transport from one typed host configuration, owns its session lifecycle, and
proves readiness before core creates a packet. Native child transport becomes
the default only after the discovery gate proves a supported local contract.

Observable success:

- a default local Codex provider needs no hardcoded port or hidden bridge;
- an explicitly configured bridge remains admissible through same session
  contract;
- repository policy selects provider and contract, never endpoint or launch
  command;
- every supported transport produces same preflight, turn, interruption,
  evidence, and typed-failure semantics.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
| --- | --- | --- | --- | --- |
| Does host bind transport to provider identity? | Client accepts only `ws://` then opens a TCP socket and writes a WebSocket upgrade. | `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py` | high | Separate transport selection from provider identity. |
| Is endpoint owned by repository policy? | Canonical `AGENTS` invocation includes `--server-uri ws://127.0.0.1:4500`. | `AGENTS.md`; `docs/operating_system/templates/agents/root-AGENTS.template.md` | high | Remove endpoint from canonical repository guidance. |
| Is a local endpoint available? | TCP probe reports no listener at `127.0.0.1:4500`. | local provider preflight evidence, August 8, 2026 | high | Never require an ambient listener by default. |
| Is current core/policy compatible? | Installed host core is `0.1.12`; current `harness.yaml` accepts `follow_up_routes`. | host runtime proof; `repo_config/harness.yaml` | high | Keep release compatibility separate from transport readiness. |

## Required Outcomes

### Outcome: One provider/session boundary

- **Actor:** provider host, core, controller, worker, validator.
- **Required result:** every provider transport implements one session contract:
  `preflight`, `create_thread`, `complete_turn`, `interrupt_turn`, and `close`.
- **Success condition:** lane dispatch, dynamic tools, claim collection,
  cancellation, retained evidence, and validator dispatch consume the same
  `ProviderSession` behavior regardless of transport.

### Outcome: Host-owned local connection configuration

- **Actor:** host installer and local operator.
- **Required result:** one host runtime configuration selects connection data
  for each provider ID. It is outside repository packet policy and supports:
  `transport`, `lifecycle`, command or endpoint, non-secret label, and protocol
  version.
- **Success condition:** `repo_config/harness.yaml`, plans, prompts, packets,
  and generated agent guidance contain no endpoint, port, command, or secret.
  Packet evidence records only resolved non-secret transport identity and a
  configuration digest.

### Outcome: Native child transport is conditional default

- **Actor:** local Codex provider host.
- **Required result:** `codex_app_server` uses host-owned child-process
  transport only after a discovery gate proves current local Codex App Server
  command and stdio protocol. Before proof, no default transport is selected.
- **Success condition:** host preflight starts a bounded temporary child session,
  completes initialize, emits `ready`, then closes it. Each lane owns one child
  session and closes it deterministically.
- **Failure condition:** if supported local child launch cannot be proven, this
  specification remains blocked at the discovery gate. Host returns
  `provider_runtime_unavailable`; it never invents a command, binds a port, or
  falls back to a different transport.

### Outcome: Explicit external bridge transport

- **Actor:** deployments that intentionally provide a bridge.
- **Required result:** WebSocket remains an optional `transport: websocket`,
  `lifecycle: external` configuration under same provider/session interface.
- **Success condition:** preflight proves endpoint protocol and bridge identity.
  No default endpoint exists. No automatic stdio-to-WebSocket or
  WebSocket-to-stdio fallback occurs.

### Outcome: Typed readiness and compatibility evidence

- **Actor:** core and controller.
- **Required result:** host capability and preflight evidence include provider
  ID, host API, provider contract, resolved transport, lifecycle, protocol,
  configuration digest, and readiness result.
- **Success condition:** core distinguishes `provider_runtime_unavailable`,
  `provider_protocol_incompatible`, `provider_auth_unavailable`, and
  `provider_preflight_failed`. No packet exists after a failed provider gate.

### Outcome: Explicit protocol evolution

- **Actor:** core release, host release, consumer policy, historical run
  recovery.
- **Required result:** move active `codex_app_server` policy to provider
  contract 4 and host API 4. Request API 4 emits packet API 5 because packet
  API 5 adds immutable provider-runtime binding.
- **Success condition:** host API 4 with provider contract 4 dispatches packet
  API 5 only after exact runtime-binding validation. Host API 3/provider
  contract 3 dispatches historical packet API 4 only for existing planned
  attempts. Packet APIs 3 and 4 remain readable evidence; policy never selects
  host API 3 or packet API 4 for new work.

## Design Decisions

### Ownership and Data Contract

### Core owns

- provider ID and provider-contract admission;
- host/packet compatibility matrix and historical-read rules;
- immutable packet fields and run-record evidence schema;
- controller-only acceptance, retry, escalation, block, and waiver decisions.

### Host owns

- `ProviderSession` protocol and all transport implementations;
- local provider configuration loading and schema validation;
- executable discovery, child spawning, endpoint connection, authentication
  inheritance, and session cleanup;
- resolved transport capability/preflight evidence.

### Repository policy owns

- `runtime_provider_id: codex_app_server` selection;
- provider contract requirement, route eligibility, capabilities, lane mode,
  and packet checks;
- no machine-local connection values.

### Local provider configuration

The host owns one trusted user-level source:
`~/.codex/harness-providers.toml`. Managed `run` and `preflight` always load
that resolved path; packet, repository, working-directory, and environment
values cannot override it. Host-only `config init`, `config validate`, and
`config show --redacted` may accept an explicit absolute path for an operator
command, never for managed dispatch.

The resolved file must be regular, non-symlinked, under the current user home,
and outside a repository root. It contains no credentials. Authentication is
inherited from the launched provider process or negotiated by an explicitly
configured external endpoint.

Conceptual shape:

```toml
[providers.codex_app_server]
transport = "stdio"             # stdio | websocket; no value before discovery
lifecycle = "host_spawn"        # host_spawn | external
protocol = "app-server-v1"
launcher_id = "installed_codex_app_server"
label = "local-codex"
```

`launcher_id` resolves through a host-source registry; configuration never
supplies an executable path or arbitrary arguments. For `websocket`, `endpoint`
replaces `launcher_id`; authentication material is forbidden. The host stores a
redacted connection fingerprint and a SHA-256 digest of canonical validated
configuration in packet/run evidence. Schema rejects contradictory, missing,
secret-bearing, untrusted-path, or unsupported fields.

## Invariants

1. Provider identity is not transport identity.
2. One `ProviderSession` contract covers every admissible transport.
3. No automatic transport fallback exists.
4. No endpoint, command, credential, or raw local config enters packet policy.
5. Preflight precedes packet creation and has a short independent timeout.
6. Core stores immutable `provider_runtime_binding` in packet API 5. Host
   compares it with current trusted configuration before every lane; mismatch
   returns `provider_configuration_changed` before provider or product work.
7. Each lane gets isolated provider session state; parallel lanes never share a
   child process unless a later provider contract explicitly permits it.
8. Failed provider readiness changes no product files, run packet, or controller
   decision beyond typed block evidence.
9. Historical evidence remains immutable and readable; migration never rewrites
   old packets or old provider observations.

## State and Error Behavior

| Condition | Host result | Core/controller effect |
| --- | --- | --- |
| Local config missing or invalid | `provider_runtime_unavailable` | Block before packet. |
| Child command absent or exits before initialize | `provider_runtime_unavailable` | Block before packet. |
| Transport connects but initialize/protocol differs | `provider_protocol_incompatible` | Block before packet. |
| Provider requests unavailable authentication | `provider_auth_unavailable` | Block before packet. |
| External bridge endpoint unavailable | `provider_preflight_failed` | Block before packet. |
| Trusted config changes after packet binding | `provider_configuration_changed` | Block before lane dispatch. |
| Ready session cannot start a lane | normalized terminal observation | Existing packet failure policy applies. |

## Compatibility and Migration

- `harness-core` releases transport evidence/admission changes as a new immutable
  package tag. Host pins that tag and regenerates `uv.lock` before deployment.
- Compatibility matrix is exact: host API 2 dispatches packet API 3; host API 3
  / provider contract 3 dispatches historical packet API 4; host API 4 /
  provider contract 4 dispatches packet API 5; every other dispatch pair is
  denied. Packet APIs 3 and 4 remain readable evidence under declared matrix
  rows only.
- Current host/core `0.1.12` and host API 3 must not claim provider-contract 4
  capability. New policy moves request API 4 to packet API 5 and host/provider
  contract 4 only after host conformance passes.
- Legacy `--server-uri` is removed from canonical invocation. If retained during
  migration, it is explicit websocket configuration input only; it cannot set a
  default or bypass local provider configuration validation.

## Non-Goals

- Shipping an undocumented bridge executable.
- Creating or storing authentication secrets in repository files, packets, or
  run evidence.
- Automatically starting arbitrary executables discovered on `PATH`.
- Retrying, resuming, or changing Task 1 during transport migration.
- Changing product route behavior, policy authority, lane semantics, or artifact
  retention behavior beyond transport evidence.

## Acceptance Criteria

1. A host configuration using a proven stdio command preflights, runs one fake
   or live session, interrupts a turn, and closes the child with direct tests.
2. An explicit websocket configuration passes same shared transport conformance
   vectors without a hardcoded endpoint.
3. Missing config, failed child launch, unavailable endpoint, protocol mismatch,
   and authentication absence return distinct typed pre-packet failures.
4. Core exactly enforces packet API 5 / host API 4 / provider contract 4 for
   new policy; host API 3 / provider contract 3 historical packet API 4
   dispatch and packet API 3/4 evidence reads remain covered.
5. Packet and run evidence include resolved non-secret transport identity,
   trusted config digest, and runtime binding; host rejects a changed binding
   before lane dispatch.
6. Canonical and generated guidance invoke host preflight without `4500` or a
   raw `--server-uri` default.
7. Host `config init`, `config validate`, and `config show --redacted` prove
   trusted config bootstrap without exposing endpoint credentials or arbitrary
   command execution.
8. Host release pin, lockfile, installed module, and consumer config validate as
   one release proof.
9. Fresh native local proof is required before Task 1 recovery changes state.

## Assumptions and Open Questions

- **Discovery gate:** exact supported local Codex App Server child command and
  stdio framing must be proven from installed runtime evidence before host code
  registers a native launcher or selects a default transport.
- **Authentication:** exact child authentication inheritance must be observed;
  host must report typed absence rather than adding credentials.
- **Bridge deployments:** if any durable bridge already exists, its ownership,
  installation, authentication, and protocol must be documented before it is
  admitted as `transport: websocket`.

## Validation Plan

- Unit and conformance tests prove every transport against identical session
  vectors.
- Config tests prove repository, packet, environment, and working-directory
  values cannot select launchers, paths, or endpoints; binding-change tests
  prove no lane starts after preflight/config drift.
- Integration proof validates host capability, preflight, packet admission,
  dynamic tools, interrupt, claim, and cleanup with a real supported local
  session where available.
- Release/deployment proof validates source tag, lockfile resolution, installed
  module path/version, and consumer policy admission.

## Completion Criteria

1. Every required outcome and invariant has direct automated proof.
2. Native child transport becomes default only after it completes a live bounded
   preflight without an ambient WebSocket listener.
3. Explicit WebSocket remains a tested opt-in transport, never a default or
   fallback.
4. Core, host, policy, generated guidance, installed runtime, and starter kit
   agree on exact packet API 5 / host API 4 / provider-contract 4 release line.
5. No unresolved discovery, authentication, transport, or release blocker
   remains before Task 1 recovery is reopened.
