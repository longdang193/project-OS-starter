---
artifact_type: plan
template_id: implementation-plan
status: proposed
layer: change
name: codex-provider-transport-ssot
spec_ref: docs/superpowers/specs/2026-08-08-codex-provider-transport-ssot.md
targets:
  - packages/harness-core
  - repo_config/harness.yaml
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host
  - C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit
---

# Codex Provider Transport SSOT Implementation Plan

## Goal

Replace undeclared default WebSocket dependency with one host-owned provider
transport configuration and one `ProviderSession` contract. Default local
Codex operation uses proven child-process transport. Explicit external bridges
remain supported with same contract and no fallback.

## Implementation Outcomes

### Provider/session symmetry

Every transport implements identical preflight, initialize, turn, interrupt,
dynamic-tool, retained-evidence, and cleanup behavior. Lanes receive isolated
sessions.

### Local configuration SSOT

Host runtime configuration alone selects transport, lifecycle, command or
endpoint, protocol, and non-secret label. Repository policy selects provider
identity and contract only.

### Safe migration

New policy selects packet API 5 / host-provider contract 4 after core and host
release proof.
Historical packet/run evidence remains readable. No Task 1 writer action occurs
during this migration.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-systematic-debugging`, `skill-central-config-layer`,
  `skill-test-driven-development`, `skill-backend-verification`,
  `skill-verification-before-completion`
- Isolation: two explicit repository workspaces. Every packet, test, and release
  command uses one repository root; no packet spans starter and host roots.
- Commit policy: no commits or tags during implementation. Release/push needs
  explicit authorization after fresh verification.
- Parallel ownership: none. Core compatibility, host capability, transport
  evidence, release pin, and generated guidance share one boundary.
- Sequential fallback: stop at Task 1 if native child transport cannot be
  proven. Do not substitute an invented WebSocket bridge.

## Task Breakdown

### Task 1: Prove or reject native App Server launch candidate

**Purpose:**
- Establish whether a supported child command, stdio framing, authentication
  inheritance, initialize response, turn lifecycle, and shutdown behavior exist.

**Specification Coverage:**
- Native child transport discovery gate.
- Discovery gate and authentication assumptions.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-repository-research`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py:AppServerClient`
- Inspect: installed Codex runtime executable, configuration, and local logs.
- Record: controller handoff evidence with non-secret launcher identity,
  protocol result, authentication state, and cleanup result.
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_app_server.py`

**Dependencies:**
- None.

**Steps:**
- [ ] Identify installed Codex App Server launch entry point from current local
  runtime evidence; record a non-secret launcher identity, never raw command
  arguments in repository files.
- [ ] Run bounded child-process protocol probe for initialize, one ephemeral
  thread, interruption, and close.
- [ ] Classify unavailable executable, protocol mismatch, or authentication
  absence with raw local evidence.
- [ ] Stop and mark plan blocked if no supported stdio child contract exists.

**Verification:**
- [ ] One repeatable local probe records launch command identity, protocol,
  initialization result, authentication state, and exit cleanup.
- Expected: proven child transport inputs or typed external blocker.

**Exit Criteria:**
- Exact native launch contract is available for host registration/tests, or this
  plan is blocked before any native default is implemented.

### Task 2: Add packet API 5 and exact provider-contract 4 admission

**Purpose:**
- Make transport-ready request API 4 to packet API 5 selection explicit while
  preserving packet APIs 3 and 4 as historical evidence.

**Specification Coverage:**
- Provider/session boundary.
- Explicit protocol evolution.
- Typed readiness and compatibility evidence.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/compatibility.py`
- Inspect: `packages/harness-core/src/harness_core/managed.py:admit_managed_operation`
- Inspect: `packages/harness-core/src/harness_core/config_validation.py`
- Modify: `packages/harness-core/src/harness_core/compatibility.py`
- Modify: `packages/harness-core/src/harness_core/managed.py`
- Modify: `packages/harness-core/src/harness_core/config_validation.py`
- Modify: `packages/harness-core/src/harness_core/api.py`
- Modify: `packages/harness-core/tests/test_compatibility.py`
- Modify: `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Task 1 proves native provider contract.

**Steps:**
- [ ] Write failing compatibility and admission tests for exact matrix rows:
  host 2/packet 3, host 3/provider 3/packet 4 legacy dispatch, and host
  4/provider 4/packet 5 new dispatch; deny every other pair.
- [ ] Centralize new relation in core compatibility matrix; do not create host
  fallbacks or duplicate policy constants.
- [ ] Permit host API 3/provider contract 3 packet API 4 dispatch only through
  `--run-id` continuation of an already planned legacy attempt. Reject new
  request resolution to that row.
- [ ] Validate exact adapter provider ID/contract match and preflight evidence
  shape before packet creation; reject missing, secret-bearing, contradictory,
  or policy-mismatched transport fields.
- [ ] Add immutable packet API 5 `provider_runtime_binding`; make host API 4
  dispatch require binding equality before every lane.
- [ ] Keep failed provider readiness pre-packet and controller-owned.

**Verification:**
- [ ] `uv run pytest packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py -q`
- Expected: only declared matrix rows dispatch; packet APIs 3/4 remain readable;
  failed readiness or binding creates no packet/lane.

**Exit Criteria:**
- Core owns one exact packet API 5 / host API 4 / provider-contract 4
  admission/evidence schema with direct regression proof.

### Task 3: Create host local provider-config SSOT and session factory

**Purpose:**
- Replace host-level `--server-uri` default with validated local provider
  configuration and one transport-neutral session factory.

**Specification Coverage:**
- Host-owned local connection configuration.
- One provider/session boundary.
- Typed readiness and compatibility evidence.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/cli.py:_preflight`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/provider_config.py`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/launchers.py`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/provider_session.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/cli.py`
- Create: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_provider_config.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_cli.py`

**Dependencies:**
- Task 1 complete.
- Task 2 core evidence schema fixed.

**Steps:**
- [ ] Write failing config-schema tests for valid stdio/external-WebSocket
  configurations and invalid field combinations, secret fields, absent
  lifecycle owner, untrusted path, symlink, repository-local source, or
  arbitrary command fields.
- [ ] Implement trusted managed-run resolution only from
  `~/.codex/harness-providers.toml`. Allow explicit absolute paths only for
  host-only `config init`, `config validate`, and `config show --redacted`.
- [ ] Implement `launcher_id` registry in host source. Config selects only a
  registered launcher; it never supplies executable paths or arguments.
- [ ] Introduce `ProviderSession` and a factory that resolves one provider ID to
  exactly one configured transport; return typed failures before dispatch.
- [ ] Change capability/preflight commands to emit transport, lifecycle,
  protocol, configuration digest, trusted config path class, and readiness
  evidence.

**Verification:**
- [ ] `uv run pytest tests/test_provider_config.py tests/test_cli.py -q`
- Expected: one trusted SSOT selects connection; no repository input can select
  executable, endpoint, config path, or authentication material.

**Exit Criteria:**
- Host has one trusted configuration path, safe bootstrap commands, registered
  launchers, and one transport-neutral session factory with direct failure proof.

### Task 4: Implement conditional stdio and explicit WebSocket transports

**Purpose:**
- Implement native child transport only when Task 1 proves it; preserve
  explicitly configured bridge deployments under same session contract.

**Specification Coverage:**
- Native child transport conditional default.
- Explicit external bridge transport.
- Session symmetry and lane isolation.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py:AppServerClient`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_app_server.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_adapter.py`

**Dependencies:**
- Tasks 1–3 complete.

**Steps:**
- [ ] Write shared conformance vectors for initialize, turn completion, dynamic
  tool result, interrupt, retained artifacts, and close.
- [ ] Extract protocol framing from current WebSocket client behind
  `ProviderSession`; preserve its behavior only for explicit external
  configuration.
- [ ] Implement stdio child session using Task 1’s proven command/framing;
  enforce bounded spawn, initialization, per-lane process ownership, and close.
- [ ] Reject automatic transport fallback and ensure parallel lanes create
  separate sessions.
- [ ] Re-read trusted configuration before every lane and reject changed
  `provider_runtime_binding` before provider or product work.

**Verification:**
- [ ] `uv run pytest tests/test_app_server.py tests/test_adapter.py -q`
- Expected: same conformance vectors pass for stdio and WebSocket fixtures;
  unavailable child/endpoint and post-preflight binding drift report typed
  failures before lane work.

**Exit Criteria:**
- Both admissible transports share one behavior contract; native default exists
  only after Task 1 proof and has no port dependency.

### Task 5: Integrate transport evidence, policy, and release pins

**Purpose:**
- Select packet API 5 / host/provider contract 4 for new work and ship matching
  immutable core/host releases without recreating source/package drift.

**Specification Coverage:**
- Explicit protocol evolution.
- Typed readiness evidence.
- Host/core release compatibility.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml`
- Modify: `packages/harness-core/pyproject.toml`
- Modify: `uv.lock`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/pyproject.toml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/uv.lock`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_runtime_dependencies.py`

**Dependencies:**
- Tasks 2–4 complete.

**Steps:**
- [ ] Write failing release/deployment tests requiring packet API 5, exact host
  API/provider-contract 4 match, immutable runtime binding, and installed core
  support for consumer policy.
- [ ] Change policy only after core and host conformance pass; preserve exact
  API 3/4 historical-read and legacy-dispatch matrix assertions.
- [ ] Increment core package version, create immutable release tag only after
  fresh proof, then update host source pin/lock and run `uv sync`.
- [ ] Prove installed host module/version/commit validates consumer policy and
  reports configured transport.

**Verification:**
- [ ] `uv run pytest packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py -q`
- [ ] `uv run pytest tests/test_runtime_dependencies.py tests/test_adapter.py tests/test_app_server.py -q`
- Expected: release source, lockfile, installed module, host capability, and
  consumer policy agree on one contract.

**Exit Criteria:**
- No release identity can claim packet API 5 / provider contract 4 while
  resolving an older core, undeclared transport, or changed runtime binding.

### Task 6: Replace copied endpoint guidance and sync distributions

**Purpose:**
- Make generated guidance direct controllers to host capability/preflight rather
  than a hardcoded local endpoint.

**Specification Coverage:**
- Host configuration SSOT.
- No repository-owned endpoint or launch command.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `.agents/skills/skill-systematic-debugging/SKILL.md`
- Modify: `tests/test_sync_agent_adapters.py`
- Verify: `generated_agents/**`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit`

**Dependencies:**
- Task 5 complete.

**Steps:**
- [ ] Write failing drift test asserting generated agent surfaces contain no
  `ws://127.0.0.1:4500` default and direct callers to host preflight.
- [ ] Update canonical guidance with provider lifecycle/error rules and no
  copied transport values; document trusted host config bootstrap/validation and
  the no-arbitrary-command boundary.
- [ ] Run adapter sync, starter-kit build/sync, and local runtime deployment.
- [ ] Verify generated and kit surfaces derive transport behavior from host
  capabilities rather than hardcoded prose.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --check`
- [ ] `uv run pytest tests/test_sync_agent_adapters.py tests/test_deploy_agent_runtime.py -q`
- [ ] `python scripts/validate_repo_contracts.py --fast`
- Expected: canonical, generated, deployed, and kit guidance contain one
  provider preflight rule and no endpoint drift.

**Exit Criteria:**
- Documentation and generated surfaces use host-owned trusted transport
  discovery only.

### Task 7: Run live provider proof and reopen recovery gate

**Purpose:**
- Prove real native provider readiness before allowing read-only Task 1
  diagnosis to resume through normal policy.

**Specification Coverage:**
- All acceptance criteria.
- Fresh native local proof before Task 1 state changes.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/cli.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests`
- Verify: `packages/harness-core/tests`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/JOB-PROJECT/repo_config/harness.yaml`

**Dependencies:**
- Tasks 1–6 complete.
- Authenticated local Codex provider available through host configuration.

**Steps:**
- [ ] Run host `capabilities` and preflight against default local configuration.
- [ ] Run bounded live read-only provider proof: initialize, thread, turn,
  interruption, close, and transport evidence.
- [ ] Verify core admits packet API 5 / host API 4 / provider contract 4 and
  consumer policy without packet creation on any failed gate.
- [ ] Only after fresh provider proof, authorize normal `friction-report` path
  for Task 1 in a separate request.

**Verification:**
- [ ] Focused core and host suites pass.
- [ ] Host live preflight returns `ready` with stdio transport evidence.
- [ ] `python scripts/validate_repo_contracts.py --fast`
- [ ] `git diff --check`
- Expected: real provider session is ready without `127.0.0.1:4500`; Task 1
  remains unchanged until separate controller request.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; controller may
  submit a separate read-only Task 1 recovery request.

## Verification

- `uv run pytest packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py -q`
- `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run pytest tests/test_provider_config.py tests/test_app_server.py tests/test_adapter.py tests/test_runtime_dependencies.py tests/test_cli.py -q`
- `python scripts/sync_agent_adapters.py --check`
- `python scripts/validate_repo_contracts.py --fast`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. native child transport has a proven local command/protocol or the plan is
   explicitly blocked at Task 1;
2. stdio and explicit WebSocket configurations pass same session conformance
   vectors;
3. new provider policy selects packet API 5 / host API 4 / provider contract 4
   without endpoint or launch-command values;
4. core, host source pin, lockfile, installed module, consumer policy, and
   immutable runtime binding share one release identity;
5. canonical, generated, deployed, and kit guidance have no hardcoded `4500`;
6. live provider preflight returns `ready` with transport evidence; and
7. `skill-verification-before-completion` returns `verified`.
