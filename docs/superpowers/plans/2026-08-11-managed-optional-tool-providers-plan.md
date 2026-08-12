---
artifact_type: plan
template_id: implementation-plan
status: active
layer: change
name: managed-optional-tool-providers
targets:
  - repo_config/harness.yaml
  - packages/harness-core/src/harness_core/managed.py
  - packages/harness-core/src/harness_core/config_validation.py
  - packages/harness-core/src/harness_core/compatibility.py
  - packages/harness-core/tests/test_managed.py
  - packages/harness-core/tests/test_config_validation.py
  - packages/harness-core/tests/test_compatibility.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\provider_config.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_provider_config.py
  - C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - docs/operating_system/tooling/code-intelligence-tools.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
related_features:
  - managed-harness
  - optional-tool-selection
  - host-tool-providers
---

# Managed Optional Tool Providers Implementation Plan

## Goal

Add one symmetric optional-tool path for managed packets. Routes authorize
tools, controller requests select them, host resolves live non-secret bindings,
packets retain immutable binding digests, host emits sanitized generic tool
operation evidence, and core owns verification and closure.

Ship generic migration for existing host-native tools. Keep `browser.test`,
`context7`, and read-only `gitnexus_read` unavailable until each has approved
trusted transport, lifecycle, containment, cleanup, and deterministic fixture.
Keep default routes unchanged. Do not add a browser-specific lifecycle, static
`code_browser` profile, separate Playwright or DevTools lifecycle, durable
screenshot storage, `chrome.diagnose`, or Specmatic before a canonical OpenAPI
contract exists.

## Critical Review And Decisions

Review on August 12, 2026 found missing protocol and transport decisions. These
rules gate execution:

- Request API remains `5`; optional-tool packets use API `10`; dispatch host
  API and provider contract use `9`; policy schema becomes `11`. Packet API
  `9` stays readable only.
- `tool_selection` is absent or exactly `{tools: [<unique optional IDs>],
  reason: <non-empty string>}`. Empty, duplicate, unknown, or route-denied
  selection rejects before packet creation.
- Retry and escalation preserve immutable selection exactly. Selection changes
  require fresh request. Every selected optional tool must be used by eligible
  work lane; base shell use never satisfies optional selection.
- First release migrates current host-native tools to generic registry and
  binding/evidence contract. `browser`, `context7`, `gitnexus_read` remain
  unavailable until each has one approved registered launcher or endpoint
  protocol, lifecycle, cleanup design, and deterministic test fixture. Do not
  add arbitrary commands or invent MCP transport from trusted config.

## Implementation Outcomes

### Route-Authorized Optional Tools

`repo_config/harness.yaml` defines each optional tool once and identifies the
routes that may select it. A request records the controller's selected tools
and reason. Core resolves only allowed selections into an immutable packet and
preserves selection across retry and escalation successor attempts.

### One Binding And Evidence Contract

Host resolves trusted user configuration through one registered-provider
interface and returns only tool ID, provider ID, approved operation names,
schema digest, readiness, and non-secret binding digest. Core never receives
browser paths, endpoints, cookies, headers, credentials, or raw network bodies.
Every selected tool uses the same packet binding verification, drift failure,
terminal observation, and bounded `tool_operation/v1` lane-evidence envelope.

### Bounded Providers

The locked `codex-harness-host` release migrates existing `shell`, Serena,
Semble, and ast-grep bindings into one host registry. Chrome, Context7, and
read-only GitNexus remain gated until their trusted lifecycle and deterministic
fixture are approved. Their future registration must use this interface.

### Aligned Release Proof

Core, host, routing documentation, canonical agent template, generated agent
adapters, and starter-kit output agree on the same optional-tool contract.
Fresh focused and end-to-end evidence proves route denial, packet immutability,
binding drift, cleanup, sanitization, and no hidden fallback.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-writing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve unrelated changes in external host workspace
- Commit policy: cohesive verified slices; never mix unrelated host cache work
- Parallel ownership: `none`; policy, packet, evidence, and host adapter contracts are shared
- Sequential fallback: complete core compatibility and packet tests before changing host providers; complete host tests before documentation sync and release proof

## Task Breakdown

### Task 1: Establish Host Baseline And Protocol Version

**Purpose:**
- Pin the external host source and determine the next compatible request,
  packet, and host API profile before changing a shared contract.

**Specification Coverage:**
- Launcher remains the only runtime entrypoint.
- Host owns provider implementation and trusted user configuration.
- Existing external host work remains intact.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:_TOOL_CONTRACTS`
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:NativeToolBindingResolver`
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.verify_tool_bindings`
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter._packet_tools_used`
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py:DynamicTool`
- Inspect: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\provider_config.py:_load_provider`
- Inspect: `packages/harness-core/src/harness_core/managed.py:_adapter_capabilities`
- Inspect: `packages/harness-core/src/harness_core/compatibility.py:CURRENT_PACKET_API`
- Verify: `packages/harness-core/tests/test_compatibility.py:1`

**Dependencies:**
- None.

**Steps:**
- [ ] Confirm active runtime through `harness-core-launcher capabilities` and `harness-core-launcher preflight`.
- [ ] Record active host commit and release profile outside repository state; preserve unrelated host changes and do not reset, clean, or overwrite them.
- [ ] Inventory every current tool-name branch: core `host_kind` and `root_probe` fields, host `_TOOL_CONTRACTS`, host dynamic-tool dispatch, host probe dispatch, and adapter used-tool recovery.
- [ ] Define one new compatibility profile with one generic host capability, `optional_tool_bindings`. It covers binding resolution, operation-schema digests, sanitized evidence, and tool-call provenance; never add a core capability per provider.
- [ ] Freeze migration: request `5`, packet `10`, host/provider `9`, policy schema `11`; packet `9` stays readable only. Do not reinterpret historical packets.

**Verification:**
- [ ] `git -C C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host status --short`
- Expected: existing host changes remain visible and untouched.
- [ ] `harness-core-launcher capabilities` and `harness-core-launcher preflight`
- Expected: launcher reaches the active locked host before product changes begin.

**Exit Criteria:**
- Current host baseline is known, unrelated host work is preserved, static tool-name seams are enumerated, and one versioned generic tool protocol is selected for Tasks 2 through 5.

### Task 2: Resolve Optional Tool Selection Into Packets

**Purpose:**
- Make route authorization and controller selection the only owners of
  optional-tool admission.

**Specification Coverage:**
- Routes authorize tools; controller selects; packet records immutable result.
- No static browser profile or duplicate toolset exists.
- Successor attempts retain original selection unless controller creates an
  explicitly changed approved successor request.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml:77`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:728`
- Modify: `packages/harness-core/src/harness_core/managed.py:_normalize_tool_selection`
- Modify: `packages/harness-core/src/harness_core/managed.py:_route_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_lane_tool_use_requirement`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:CURRENT_PACKET_API`
- Modify: `packages/harness-core/tests/test_config_validation.py:1`
- Modify: `packages/harness-core/tests/test_managed.py:642`
- Modify: `packages/harness-core/tests/test_compatibility.py:1`

**Dependencies:**
- Task 1 complete.

**Steps:**
- [ ] Reduce core tool descriptors to policy facts only: tool ID, optionality, and lane access. Remove host implementation fields such as `host_kind` and `root_probe` from repository policy and packets.
- [x] Add one route-owned `optional_tools` allowlist for released host-native `ast_grep_preview`; keep every route's base toolset unchanged when no selection exists. Keep `browser`, `context7`, and `gitnexus_read` unregistered while their provider gates remain unmet.
- [ ] Add strict `tool_selection` exactly shaped as `{tools, reason}` with unique selected tool names and required reason. Reject unknown, duplicate, unapproved, or empty selections.
- [ ] Resolve base plus controller-selected optional tool IDs deterministically into packet selection metadata. Do not resolve provider, operation schema, endpoint, executable, or probe details in core routing.
- [ ] Preserve selection metadata across retry and escalation only through `prepare_attempt()`; reject every selection override. Selection changes require a fresh request.
- [ ] Require every selected optional tool from eligible work lane. Do not let base shell use satisfy selected optional tools.
- [ ] Update compatibility admission and generated fixture packets for the new request, packet, and host profile.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py -q`
- Expected: valid selection reaches immutable packets; invalid selections fail before dispatch; retry and escalation preserve selection.

**Exit Criteria:**
- One route allowlist and one request field control optional-tool selection. Core route packets contain no browser-specific branch, provider ID, host kind, or probe command.

### Task 3: Replace Static Tool Maps With Generic Provider Registry

**Purpose:**
- Make host provider registration sole owner of tool implementation, trusted
  binding resolution, operation schemas, provenance, cleanup, and sanitization.

**Specification Coverage:**
- Existing `shell`, Serena, Semble, and ast-grep migrate before new providers.
- Core owns generic selection, immutable binding verification, and evidence
  envelope validation; host owns provider-specific implementation details.
- Binding change follows existing `provider_configuration_changed` outcome.
- Tool use produces bounded, sanitized, provider-neutral evidence.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_adapter_capabilities`
- Modify: `packages/harness-core/src/harness_core/managed.py:prepare_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_tool_binding_evidence`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_dispatch_exception`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_lane_execution_evidence`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:CURRENT_PACKET_API`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\provider_config.py:ToolProviderConfig`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:NativeToolBindingResolver`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:_BoundTool.dynamic_tool`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.verify_tool_bindings`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter._packet_tools_used`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.collect_lane_evidence`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py:DynamicTool`
- Modify: `packages/harness-core/tests/test_managed.py:3037`
- Modify: `packages/harness-core/tests/test_terminal_observation.py:1`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_provider_config.py:1`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py:1`

**Dependencies:**
- Task 2 complete.

**Steps:**
- [ ] Add only one host capability, `optional_tool_bindings`; core accepts that generic capability once and never adds a capability name per registered provider.
- [ ] Replace `_TOOL_CONTRACTS`, `_BoundTool.dynamic_tool`, `_probe`, and `CodexAdapter._packet_tools_used` name branches with one internal provider registry. Every entry supplies binding resolution, operation schemas, dynamic-tool provenance, lane probe, cleanup, and evidence sanitizer.
- [ ] Migrate current `shell`, `serena`, `semble_codebase_search`, and `ast_grep_preview` entries into that registry before registering browser, Context7, or GitNexus. A registry entry, not adapter branching, maps every dynamic call back to its packet tool ID.
- [ ] Leave runtime `ProviderConfig` unchanged. Add `ToolProviderConfig` and loader for `~/.codex/harness-providers.toml`: `[tool_providers.<tool_id>]` contains `provider_id`, `binding_mode`, exactly one of registered `launcher_id` or explicit local `endpoint`, plus provider-owned `settings`. Reject unknown base fields, arbitrary commands, secret-named fields, secret-bearing values, unsafe paths, and endpoint modes not allowed by registered provider.
- [ ] For `browser` settings, define exact accepted fields: `channel` (`stable`, `beta`, `dev`, or `canary`), `launch_policy` (`ephemeral` only), and absolute `profile_root`. Accept external CDP only through the trusted `endpoint` base field. Canonically hash the complete validated binding configuration; return digest only outside host.
- [ ] Extend trusted user configuration with registered tool-provider bindings. Resolve only selected IDs and return exact generic fields: tool ID, provider ID, readiness, approved operation names, operation-schema SHA-256 digest, and binding SHA-256 digest. Never return endpoint, executable, profile path, cookie, credential, or raw provider config.
- [ ] During `prepare_attempt()`, resolve route-authorized selected bindings before writing packet. Persist immutable generic binding data. Re-resolve before every lane and fail drift, unavailability, probe failure, launch failure, operation failure, and cleanup failure through existing typed host terminal envelope and controller decision path.
- [ ] Add bounded `tool_operation/v1` inside normal lane execution evidence and terminal observations, never retained artifacts or artifact handoff. Provider sanitizes first; core validates generic identity, binding/schema digest, operation name, byte limit, safe artifact references, and forbidden secret/path/URL/body fields. Do not introduce browser-only evidence fields.
- [ ] Complete generic migration for current host-native tools first. Register external Chrome or MCP providers only after their transport, lifecycle, cleanup, containment, and fake-provider fixture are approved.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_terminal_observation.py packages/harness-core/tests/test_compatibility.py -q`
- Expected: generic capability admission, packet immutability, binding drift, old-packet rejection, malformed evidence rejection, and no fallback pass.
- [ ] `uv run pytest tests/test_provider_config.py tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: existing native tools execute through registry entries; test-only registered provider works without adapter branch edits; provenance and sanitization remain generic.

**Exit Criteria:**
- Adding any provider requires one host registry entry plus tests. It does not require a core capability name, a core host-kind/probe field, a dynamic dispatch branch, a probe branch, or a used-tool recovery branch.

### Deferred Task 4: Implement Chrome `browser.test` Provider

**Purpose:**
- Deliver repeatable isolated browser test actions through the generic host
  provider path.

**Specification Coverage:**
- Chrome profile is ephemeral per lane and attempt.
- Managed work never attaches to personal Chrome.
- Browser start, use, failure, cleanup, and evidence share standard host and
  core lifecycle.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\provider_config.py:ToolProviderConfig`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:NativeToolBindingResolver`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py:DynamicTool`
- Verify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py:1`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_app_server.py:1`
- Modify: `repo_config/harness.yaml:172`

**Dependencies:**
- Task 3 complete plus an approved trusted Chrome transport, containment,
  cleanup design, and deterministic fake-provider fixture.

**Steps:**
- [ ] Register `browser` as one read-only tool entry with provider ID `chrome`, no route-specific lifecycle, and no adapter branch. Expose exactly one `DynamicTool` named `packet_browser` with provenance `packet_tool="browser"`.
- [ ] Define `packet_browser` input as `{operation, arguments}`. `operation` is packet-binding enum `["test"]`; `arguments` validates against `test` schema. A future `diagnose` release adds one enum/schema branch to this same dynamic tool, never another browser tool or lifecycle.
- [ ] Resolve Chrome channel, CDP endpoint-or-launch policy, and isolated-profile root only from trusted user configuration. Emit resolved operation schema digest and binding digest only to core.
- [ ] Launch one Chrome session and ephemeral profile per lane and attempt inside borrowed lease containment. Place it at validated host-owned `profile_root/<attempt_id>/<lane_id>` outside packet Git checkout; reject personal-profile attachment, workspace-relative roots, symlink escape, and any profile path outside configured root. Implement only `browser.test` navigation, interaction, accessibility snapshot, viewport check, and screenshot hash.
- [ ] Sanitize browser operation evidence through generic provider sanitizer before host returns it. Store sanitized URL without query or fragment, viewport, console errors, failed request summaries, screenshot hash, and result summary; do not persist screenshot files or expose local screenshot paths in this release.
- [ ] Emit normal terminal observations for unavailable Chrome, binding drift, launch failure, operation failure, cancellation, timeout, and cleanup failure.

**Verification:**
- [ ] `uv run pytest tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: browser registration needs no adapter map edit; isolated profiles, containment, cleanup, operation-schema enforcement, and sanitized generic evidence pass.

**Exit Criteria:**
- `browser.test` works through ordinary packet selection, generic provider registry, binding verification, and host lifecycle. No Chrome DevTools provider or second browser lifecycle exists.

### Deferred Task 5: Implement Context7 And Read-Only GitNexus Providers

**Purpose:**
- Add bounded documentation and code-graph assistance through the same optional
  tool protocol without changing source, test, contract, or runtime ownership.

**Specification Coverage:**
- Context7 answers version-specific external documentation questions only.
- GitNexus is private, freshness-gated, and read-only.
- Selected-provider failure stays visible; no ambient fallback runs.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\provider_config.py:ToolProviderConfig`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\native_tools.py:NativeToolBindingResolver`
- Verify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py:1`
- Modify: `repo_config/harness.yaml:77`
- Modify: `packages/harness-core/tests/test_managed.py:3037`

**Dependencies:**
- Tasks 2 and 3 complete plus approved trusted transport, lifecycle, cleanup,
  and deterministic fixtures for each provider.

**Steps:**
- [ ] Register read-only `context7` and `gitnexus_read` entries in generic provider registry and allow them only on routes where their advisory evidence is relevant. Do not add core or adapter provider-name branches.
- [ ] Implement Context7 registered operations with pinned-library query inputs and sanitized bounded results. Do not make results contract, source, test, or runtime truth.
- [ ] Implement GitNexus registered read-operation allowlist: query, context, impact, API impact, route map, shape check, and tool map. Deny rename, group sync, registry mutation, or any write operation.
- [ ] Require repository match and freshness proof before GitNexus binding succeeds. A stale or unavailable selected provider produces typed generic evidence and controller-directed successor handling.

**Verification:**
- [ ] `uv run pytest tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: Context7 and GitNexus cannot write workspace; GitNexus rejects stale or mismatched indexes; unselected providers never run; neither provider needs adapter dispatch or evidence changes.
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_managed.py -q`
- Expected: selected-provider absence does not trigger hidden fallback and preserves terminal evidence.

**Exit Criteria:**
- Documentation and graph queries use the same selection, binding, evidence, and closure path as browser testing while remaining advisory and read-only.

### Task 6: Align Canonical Guidance, Generated Surfaces, And Releases

**Purpose:**
- Publish one durable optional-tool contract and prove the released host matches
  it without exposing user-local runtime configuration.

**Specification Coverage:**
- Repository policy remains SSOT for allowed tools and route selection.
- Host configuration remains outside repository policy and packet input.
- Generated agent surfaces derive from canonical documentation.

**Required Skills:**
- `skill-code-standards`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md:408`
- Modify: `docs/operating_system/tooling/code-intelligence-tools.md:1`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md:1`
- Verify generated: `AGENTS.md:1`
- Verify generated: `.agents/rules/agent-memory-rule.md:1`
- Verify: `tests/test_sync_agent_adapters.py:50`
- Verify: `tests/test_starter_kit_generation.py:144`

**Dependencies:**
- Tasks 1 through 3 complete.

**Steps:**
- [ ] Document one ownership boundary: repository policy authorizes tool IDs and lane access; controller request selects allowed optional IDs; host registry owns provider ID, operation schema, trusted configuration, probe, cleanup, provenance, and sanitization.
- [ ] Document `optional_tool_bindings` as one generic compatibility capability, immutable packet binding/schema digests, generic tool-operation evidence, and typed no-fallback failure. Do not document provider-specific core capabilities, host kinds, probe commands, endpoint values, or credentials.
- [ ] Document external tool providers as deferred. Chrome diagnosis and
  Specmatic remain blocked until their approval gates are met.
- [ ] Run agent-adapter sync from canonical template. Do not hand-edit generated `AGENTS.md` or generated rule surfaces.
- [ ] Build and activate the committed host release through launcher. Re-run capabilities and preflight before fresh managed native-tool probes. Verify host registry advertises only generic capability and selected non-secret binding records.
- [ ] Run a fresh managed `harness-core-launcher run` probe before any host or launcher tag/push. Record active core/host identity, packet and attempt creation, provider work, terminal observation, and changed-behavior proof. Pre-packet or pre-provider failure blocks release qualification.

**Verification:**
- [ ] `\.venv\Scripts\python.exe scripts\sync_agent_adapters.py`
- Expected: generated agent surfaces match canonical documentation.
- [ ] `\.venv\Scripts\python.exe -m pytest tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- Expected: generated surfaces and starter-kit distribution include policy changes without user-local host configuration.
- [ ] `harness-core-launcher capabilities` and `harness-core-launcher preflight`
- Expected: active released host advertises `optional_tool_bindings` once and proves selected generic binding support without provider-specific core capability names.

**Exit Criteria:**
- Core, host, documentation, generated adapters, and starter-kit output describe one optional-tool system with no duplicated lifecycle, tool-name dispatch map, or configuration ownership.

## Verification

- `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests -q`
- `uv run pytest tests/test_provider_config.py tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- `\.venv\Scripts\python.exe -m pytest tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- `\.venv\Scripts\python.exe scripts\validate_planning_lifecycle.py`
- `\.venv\Scripts\python.exe scripts\validate_repo_contracts.py`
- `harness-core validate --repo-root C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter`
- `harness-core-launcher capabilities`
- `harness-core-launcher preflight`
- `git diff --check`

## Completion Criteria

1. Routes, controller requests, and packets have one non-duplicated optional-tool selection path; base toolsets remain separate from runtime optional selection.
2. Each selected tool has one host-registry entry, one host-resolved non-secret binding and operation-schema digest, one per-lane verification path, and one typed terminal-failure path.
3. Existing host-native tools run only through selected packet bindings. Browser,
   Context7, and GitNexus remain unavailable until their deferred provider gates
   are met; no ambient tool or personal browser profile is used.
4. Tool-operation evidence exists only in lane execution evidence or terminal observation, remains bounded and sanitized, and contains no secret, raw network body, unredacted URL query or fragment, local screenshot path, or binary screenshot content.
5. Existing `shell`, Serena, Semble, and ast-grep bindings run through host registry entries. No static core host-kind/probe field, host tool contract map, adapter tool-name map, or provider-specific core capability remains.
6. Core and host compatibility profiles reject historical incompatible packets rather than guessing semantics.
7. Chrome diagnosis, durable screenshots, Specmatic, and unapproved GitNexus mutation remain absent from this release.
8. Fresh core, host, documentation, generated-surface, starter-kit, launcher, whitespace, and managed-dispatch evidence passes before `skill-verification-before-completion` marks this plan completed. Local tests, direct probes, `doctor`, `capabilities`, and `preflight` cannot replace managed proof or qualify release.
