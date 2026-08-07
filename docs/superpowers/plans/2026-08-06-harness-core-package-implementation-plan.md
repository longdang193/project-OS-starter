---
artifact_type: plan
template_id: implementation-plan
status: proposed
layer: change
parent_spec: docs/superpowers/specs/2026-08-06-harness-core-package.md
targets:
  - packages
  - repo_config/harness.yaml
  - repo_config/starter-kit-manifest.json
  - scripts
  - tests
  - docs/operating_system
  - README.md
related_features:
  - harness-core-package
  - managed-harness
  - codex-host-adapter
---

# Harness Core Package Implementation Plan

## Goal

Move executable harness behavior from copied consumer scripts into one
versioned `harness-core` package. Keep `harness-core-launcher` separate so an
absent core returns typed environment evidence. Move `codex-harness-host` to
package imports, integer host API admission, packet-first preflight, and one
bounded provider-neutral terminal-observation contract.

## Implementation Outcomes

### One Package Runtime

`harness-core` becomes sole executable owner of packet, validation, lifecycle,
and controller semantics. Consumer scripts remain non-executable bridges only.

### Uniform Provider Evidence

All admitted host lanes use one package-owned compatibility identity and one
bounded terminal-observation contract before controller decision.

## Execution Boundary

- This is a cross-repository release plan. Do not add `coordination` frontmatter:
  current coordination manifests admit one repository root only and do not
  provide a cross-repository lock, queue, or scheduler.
- Execute tasks serially. `project-OS-starter` and
  `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host` have overlapping
  release/runtime dependency. No simultaneous controllers.
- Before Task 4, maintainers must provide immutable package Git tags from the
  canonical `project-OS-starter` remote. Current local starter checkout has no
  configured `origin`; do not replace this prerequisite with a machine-specific
  path dependency, copied source, or runtime download.
- Git source is release-only. Managed execution never downloads or upgrades a
  package. Host `pyproject.toml` declares PEP 440 ranges; `uv.lock` pins the
  immutable tagged source used by that release.
- Preserve unrelated modified files and untracked host build artifacts. No task
  cleans them as part of this migration.

## Canonical Ownership

| Fact | Owner | Consumer |
| --- | --- | --- |
| PEP 440 package dependency ranges and locked sources | package/host `pyproject.toml`, `uv.lock` | installer, `uv` |
| Request, packet-read, current-packet, host API support | `harness_core.compatibility` | launcher, policy validation, host adapter |
| Packet resolution, plan parsing, lifecycle, verification, controller decisions | `harness-core` | direct CLI, provider hosts |
| Missing or unloadable core failure | `harness-core-launcher` | direct CLI, provider hosts |
| Route policy and required request API | consumer `repo_config/harness.yaml` | `harness-core` |
| Provider transport, workspace, tools, App Server connection | `codex-harness-host` adapter | `harness-core` through adapter protocol |
| Terminal observation schema, bounds, normalization, and persistence | `harness_core.terminal_observation` | provider hosts, controller, verifier |
| Mutable run evidence | consumer `.harness/runs/<run-id>/run.json` | controller and verifier |

## Release Contract

- `harness-core` and `harness-core-launcher` are separate installable Python
  distributions in one `uv` workspace under `packages/`.
- `harness-core` owns exactly one compatibility matrix:

  ```python
  SUPPORTED_REQUEST_APIS = {2, 3}
  SUPPORTED_PACKET_READ_APIS = {3}
  CURRENT_PACKET_API = 3
  SUPPORTED_HOST_APIS = {2}
  ```

- Consumer policy uses `harness_core.request_api: 3`. Missing or malformed
  value fails `harness_core_request_api_invalid`; unsupported value fails
  `harness_core_request_api_incompatible`.
- Launcher reports missing/unloadable package as
  `harness_core_environment_unavailable` with `failure_class: environment`.
  It never reads consumer core source or writes `.harness` state.
- New packets record package release, request API, packet API, and host API.
  Existing unversioned packets are historical-only. A planned old packet cannot
  resume; controller records a block then creates successor attempt from stored
  request/plan binding.
- `harness_core.terminal_observation` owns schema version, hard bounds, and
  normalization for every abnormal provider terminal outcome. It records opaque
  session/turn identifiers, terminal status, bounded item/command state
  timeline, final claim state, and sanitized error metadata. It never persists
  raw shell output, prompts, environment values, or assistant text in
  `run.json`.

## Task Breakdown

Tasks execute serially across starter, provider host, and consumer boundaries.

## Task 1: Create Package Workspace And Launcher Boundary

**Purpose:**
- Create two installable distributions and prove launcher failure does not need
  package code.

**Specification Coverage:**
- Package API
- Launcher environment boundary
- Package dependencies and runtime APIs stay separate

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Create: `pyproject.toml`, `uv.lock`
- Create: `packages/harness-core/pyproject.toml`, `packages/harness-core/src/harness_core/__init__.py`, `packages/harness-core/src/harness_core/compatibility.py`
- Create: `packages/harness-core-launcher/pyproject.toml`, `packages/harness-core-launcher/src/harness_core_launcher/__init__.py`, `packages/harness-core-launcher/src/harness_core_launcher/loader.py`
- Create: `packages/harness-core/tests/test_compatibility.py`, `packages/harness-core-launcher/tests/test_loader.py`
- Inspect: `requirements.txt`, `scripts/harness_task.py:_load_policy`

**Dependencies:**
- Approved parent specification.
- No host or consumer source change yet.

**Steps:**
- [ ] Create root `uv` workspace containing only the two package members.
- [ ] Define package names, PEP 440 versions, explicit runtime dependencies, and
  console entrypoints. Keep launcher independent from importing core at module
  import time.
- [ ] Add `harness_core.compatibility` as sole matrix owner. Expose immutable
  package release/API identity and pure admission helpers for request, packet,
  and host APIs.
- [ ] Implement launcher `load_core()` / command boundary. On `ImportError` or
  unloadable core, return typed environment result and perform no consumer-root
  work.
- [ ] Add unit tests for exact matrix values, supported/unsupported integers,
  and typed launcher failure with no filesystem side effect.
- [ ] Generate `uv.lock`. Do not commit `dist/`, virtual environments, or build
  metadata.

**Verification:**
- [ ] `uv lock --check`
- [ ] `uv run --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv run --package harness-core-launcher pytest packages/harness-core-launcher/tests -q`
- Expected: both distributions build/import; launcher reports typed environment
  failure when core import is intentionally unavailable.

**Exit Criteria:**
- Two distributions have one workspace/lockfile. Core matrix and launcher
  boundary have focused automated proof.

## Task 2: Move Harness Semantics Into Core Package

**Purpose:**
- Make package source sole executable owner of packet, plan, validation,
  lifecycle, and controller behavior.

**Specification Coverage:**
- One executable core
- Symmetric entrypoints
- Plan scope derivation
- Core identity evidence
- Packet continuation compatibility

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Move into `packages/harness-core/src/harness_core/`: logic from `scripts/harness_task.py`, `scripts/plan_coordination.py`, `scripts/planning_artifact_schema.py`, `scripts/validate_harness_config.py`
- Create: `packages/harness-core/src/harness_core/api.py`, `packages/harness-core/src/harness_core/cli.py`, `packages/harness-core/src/harness_core/config.py`, `packages/harness-core/src/harness_core/coordination.py`
- Move/adapt: `tests/test_harness_task.py`, `tests/test_plan_coordination.py`, `tests/test_validate_harness_config.py` into package tests
- Inspect: `scripts/harness_task.py:resolve_managed_packet`, `scripts/harness_task.py:run_managed`, `scripts/harness_task.py:apply_controller_decision`, `scripts/plan_coordination.py:load_plan_coordination`

**Dependencies:**
- Task 1 complete.

**Steps:**
- [ ] Move existing logic with `git mv` where possible. Preserve public behavior
  before adding package imports; do not copy implementations into new modules.
- [ ] Define package public API equivalent to `run_managed(repo_root, request,
  adapter, run_id=None)` plus direct validation, coordination status, handoff,
  controller decision, verification, and packet inspection operations.
- [ ] Add package admission before request resolution: validate
  `harness_core.request_api` against `SUPPORTED_REQUEST_APIS`; validate adapter
  `host_api` against `SUPPORTED_HOST_APIS`; record exact compatibility evidence.
- [ ] Add immutable packet `core_identity` fields for package release, request
  API, packet API, and host API. Keep `allowed_paths` explicit and retain
  plan-task derivation; never infer authorization from planned writes.
- [ ] Enforce resume: only `planned` packets with packet API in
  `SUPPORTED_PACKET_READ_APIS` and existing plan digest/base constraints may
  continue. Unversioned/unreadable packets block without mutation; controller
  successor path remains existing source of retry truth.
- [ ] Add package CLI operations. Generic managed execution remains unavailable
  without a provider adapter.
- [ ] Add focused regression tests for direct/host-equivalent packet
  normalization, every protocol failure, packet identity, plan-linked empty
  planned writes, stale-plan rejection, and unreadable old-packet continuation.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv run --package harness-core python -m harness_core.cli validate --repo-root <temporary-consumer-root>`
- Expected: package owns all semantic tests; compatible request creates packet
  with identity; every admission failure leaves no run/workspace artifact.

**Exit Criteria:**
- Package has executable semantic ownership. No package module dynamically loads
  consumer Python core files.

## Task 3: Replace Consumer Core Copies With Delegating Shims

**Purpose:**
- Make new starter kits package consumers, not core forks. Preserve temporary
  script entrypoints only as non-executable delegators.

**Specification Coverage:**
- Consumer data ownership
- Legacy scripts are one-way migration shims only
- Explicit compatibility admission
- Reduced release management

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml`, `repo_config/starter-kit-manifest.json`
- Modify: `scripts/harness_task.py`, `scripts/plan_coordination.py`, `scripts/planning_artifact_schema.py`, `scripts/validate_harness_config.py`
- Modify: `scripts/validate_repo_contracts.py`, `tests/test_starter_kit_generation.py`, `tests/test_validate_repo_contracts.py`
- Modify: `README.md`, `docs/operating_system/procedures/managed-execution-adapter-contract.md`, `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`, `.agents/skills/skill-subagent-driven-development/SKILL.md`, `.agents/skills/skill-verification-before-completion/SKILL.md`
- Verify generated: `AGENTS.md`, `generated_agents/codex/AGENTS.md`, `generated_agents/codex/skills/skill-subagent-driven-development/SKILL.md`

**Dependencies:**
- Task 2 complete.

**Steps:**
- [ ] Add `harness_core.request_api: 3` to starter policy and extend package
  validation to reject missing, malformed, or unsupported value before packet
  creation.
- [ ] Replace legacy script bodies with direct imports/delegation to launcher or
  core public API. Preserve supported command/function signatures during bridge;
  do not retain parsers, resolver logic, policy validation, or lifecycle code.
- [ ] Update kit manifest required/copy paths and starter-kit tests. New kits may
  ship explicit shims during migration but must not ship independent core source
  or core implementation tests.
- [ ] Update repository contract validation to identify copied core semantics as
  forbidden and shim-only scripts as valid.
- [ ] Update canonical human guidance from script-owned core to launcher/package
  commands, package availability failure, request API policy, host API,
  unreadable historical packets, and ordered preflight. Never edit generated
  AGENTS/skill outputs directly.
- [ ] Run `python scripts/sync_agent_adapters.py`, then update generated output
  through normal sync. Do not deploy runtime files until source and generated
  drift checks pass.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py -q`
- [ ] `python scripts/build_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/validate_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/sync_agent_adapters.py --check`
- Expected: generated kit contains policy/data/shims only; copied core cannot
  execute; canonical and generated guidance agree.

**Exit Criteria:**
- Starter and generated kits consume package semantics through shims/launcher.
  No current starter path remains an independent core owner.

## Task 4: Bind Codex Host To Package And Ordered Admission

**Purpose:**
- Remove host target-script loading. Prove host uses launcher/core package and
  checks policy protocol before App Server connectivity.

**Specification Coverage:**
- Host adapter boundary
- Deterministic admission order
- Package dependencies and runtime APIs stay separate
- Symmetric entrypoints

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\pyproject.toml`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\uv.lock`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\cli.py:_load_core`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\cli.py:main`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:RUNTIME_PROVIDER`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.identity`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_cli.py`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_runtime_dependencies.py`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_live_single_work_lane.py`

**Dependencies:**
- Tasks 1 and 2 complete.
- Immutable Git tags for both distributions available from canonical starter
  remote. If absent, block here. Do not use `../project-OS-starter` path source.

**Steps:**
- [ ] Add PEP 440 dependencies for `harness-core` and
  `harness-core-launcher`. Configure `tool.uv.sources` to immutable starter Git
  tags/subdirectories, then regenerate `uv.lock`.
- [ ] Delete dynamic `<harness-root>/scripts/harness_task.py` loader. Route all
  host core loading through launcher library.
- [ ] Add static `host_api: 2` to adapter identity without App Server contact.
  Host constructs adapter and lets core perform request/host admission before
  `_preflight()` opens WebSocket.
- [ ] Make `preflight` accept consumer root when it claims consumer admission.
  Keep capability-only output explicitly host-static; it must not claim policy
  validation.
- [ ] Update CLI tests: missing core returns launcher environment result;
  malformed/unsupported request API and unsupported host API preempt connection;
  supported policy then reaches existing App Server preflight result.
- [ ] Replace copied-core live fixture with generated consumer/shim fixture plus
  installed tagged package. Assert host evidence and packet core identity agree.

**Verification:**
- [ ] `uv lock --check` in `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- [ ] `uv run pytest tests/test_cli.py tests/test_runtime_dependencies.py -q` in `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- [ ] With App Server running: `CODEX_HARNESS_LIVE=1 CODEX_HARNESS_ROOT=<migrated-starter-root> uv run pytest tests/test_live_single_work_lane.py -q` in `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: no consumer executable core import; first failure follows launcher,
  protocol, then host-runtime order; host run records matching core identity.

**Exit Criteria:**
- Host consumes one tagged package release through launcher and advertises static
  host API `2`. App Server connectivity cannot mask a core protocol failure.

## Task 4A: Preserve Terminal Observation Across Every Managed Lane

**Purpose:**
- Make every abnormal terminal managed outcome diagnosable without retrying a
  packet or retaining provider transcript state.

**Specification Coverage:**
- One executable core
- Provider-neutral host adapter boundary
- Symmetric lane evidence and controller recovery
- Sensitive evidence minimization

**Required Skills:**
- `skill-systematic-debugging`
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Create: `packages/harness-core/src/harness_core/terminal_observation.py`,
  `packages/harness-core/tests/test_terminal_observation.py`
- Modify: `packages/harness-core/src/harness_core/api.py`,
  `packages/harness-core/src/harness_core/compatibility.py`, and moved
  `harness_task` terminal normalization/dispatch-failure symbols
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py:InterruptedTurnError`, `AppServerClient._complete_turn`, `AppServerClient._interrupt_and_await_terminal`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:PacketTurnTimeoutError`, `CodexAdapter._complete_lane_turn`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_app_server.py`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py`, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_live_single_work_lane.py`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`

**Dependencies:**
- Tasks 1, 2, and 4 complete.

**Steps:**
- [ ] Preserve package API continuity first: keep the released
  `timeout_observation` import as a thin delegating compatibility adapter with
  no independent schema. Add the new core API, run package tests, release
  immutable `harness-core-v0.1.4`, then update host `pyproject.toml` and
  `uv.lock` to that tag before host imports the new API. Do not use an
  untagged Git revision or source-path fallback.
- [ ] Start RED tests from observed terminal failures: completed shell commands
  followed by timeout, an active shell command at interruption, an assistant
  message without a valid final claim, terminal interrupt confirmation, and a
  provider `turn/completed` event with `status: failed` plus structured error.
- [ ] Define `terminal_observation` version `1` in `harness-core`. Its one
  normalizer owns allowed `kind` values, schema, cardinality/size bounds,
  packet lane and budget checks, and stable serialization into
  `attempt.evidence.terminal_observation`. Preserve prior
  `attempt.evidence.timeout` as historical read-only evidence only.
- [ ] Require only provider-neutral fields: `kind`, `lane_id`, opaque runtime
  `session_id`/`turn_id`, source, packet timeout budget when relevant, elapsed
  time, terminal and interrupt status, bounded ordered item state, bounded
  command state, final-claim state, and sanitized provider error metadata. Use
  exact schema from parent spec: `error` is null or sorted bounded field names
  plus optional code/message SHA-256 hashes and byte lengths. Session/turn and
  terminal status may be null only before provider allocation. Record hashes,
  lengths, type, exit code, and state; never raw command output, prompts,
  environment values, or assistant text.
- [ ] Make `AppServerClient` construct this observation while events arrive.
  One shared abnormal-outcome mapper accepts provider terminal events, approval
  requests, transport exceptions, and host timeout interrupts. It maps
  `timeout`, `provider_failure`, `approval_required`, and `protocol_failure`
  for every lane. Track started and completed item IDs so timeout distinguishes
  active shell command from completed command exploration. Carry claim parse
  state before transport cleanup.
- [ ] Keep Codex threads `ephemeral`. Do not make durable provider transcripts
  a recovery dependency; the bounded observation is required before exception
  propagation and survives adapter cleanup.
- [ ] Make host terminal exceptions forward raw bounded observation to core.
  Delete duplicated timeout-field allowlists or host-only shaping. Core records
  valid observations; malformed or over-bound provider evidence becomes typed
  invalid terminal evidence and cannot unlock retry/acceptance. Only
  `kind: timeout` can follow timeout escalation policy.
- [ ] Apply same contract to every provider-backed work, check, and read-only
  validator turn. Host-only integration has no provider turn and keeps existing
  phase-specific failure evidence. Provider conformance must reject a host that
  advertises a managed topology but cannot supply valid terminal observation
  for its provider-backed operations.
- [ ] Update managed-execution guidance: terminal timeout means block or use
  immutable escalation only; provider failure remains `dispatch_failed` until
  controller decision. Inspect `attempt.evidence.terminal_observation` before
  any successor. Local output never substitutes for host observation.

**Verification:**
- [ ] Package tests prove normalization accepts bounded valid evidence and
  rejects wrong lane, wrong budget, malformed IDs, raw sensitive fields, and
  over-bound timelines. Prove exact `error` shape, null runtime IDs before
  allocation, provider `failed` as `provider_failure`, approval request as
  `approval_required`, and protocol exception as `protocol_failure`.
- [ ] Host fake-App-Server tests prove each RED terminal shape reaches
  `run.json` with correct active/completed state and no raw output/text.
- [ ] Parameterized host tests cover writer, sequential work, parallel work,
  checks, and read-only validator turns through shared terminal path. Prove
  host-only integration keeps phase-specific failure evidence; no lane-specific
  terminal serializer is permitted.
- [ ] `uv run --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv run pytest tests/test_app_server.py tests/test_adapter.py tests/test_cli.py -q` in `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- [ ] Use fake App Server protocol fixtures to force timeout, provider failure,
  approval, and protocol failure. Verify each reaches `run.json` with distinct
  normalized kind, no raw text, and no writer claim or acceptance. With App
  Server running, run ordinary managed success proof only; if it fails, capture
  its bounded observation without requiring live failure injection.
- Expected: abnormal turns are diagnosable from immutable run evidence even
  when provider threads are ephemeral; no automatic retry or acceptance occurs.

**Exit Criteria:**
- Every admitted managed lane emits the same core-owned, bounded terminal
  observation. Timeout, active-command, completed-work, final-claim, and
  provider-failure classes stay distinct without transcript recovery.

## Task 5: Migrate Supported Consumer And Historical Runs

**Purpose:**
- Prove package-only consumer behavior against real managed execution and safe
  recovery from pre-package run records.

**Specification Coverage:**
- Consumer compatibility declaration
- Core identity evidence
- Mixed-version and continuation boundaries
- One core identity across entrypoints

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-subagent-driven-development` only for packet-authorized managed lanes

**Files And Symbols:**
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\repo_config\harness.yaml`
- Modify/remove only after bridge proof: `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\scripts\harness_task.py`, `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\scripts\plan_coordination.py`, `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\scripts\planning_artifact_schema.py`, `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\scripts\validate_harness_config.py`
- Add/modify focused consumer regression tests under `C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT\tests`
- Inspect: existing `.harness/runs/*/run.json` only as immutable evidence; do not
  rewrite historical records.

**Dependencies:**
- Tasks 3, 4, and 4A complete.
- Tagged package release installed in consumer/host environments.

**Steps:**
- [ ] Add consumer request API policy and replace copied core scripts with
  package shims. Keep consumer-specific routes, roles, skills, rules, plans,
  requests, and `.harness` state unchanged.
- [ ] Run package configuration validation and package direct CLI status against
  consumer root. Confirm stale copied implementation is not loaded.
- [ ] Create a fresh representative managed packet for each admitted topology:
  `single_work_lane`, `sequential_work_lanes`, and `parallel_work_lanes`. Use
  existing host evidence, isolated workspace, tool binding, check, and read-only
  validator requirements; do not waive proof.
- [ ] Create fixture/copy of unversioned planned run. Confirm continuation blocks
  without changing packet/run evidence, then controller creates successor from
  original request/plan fields.
- [ ] Record external repository commit IDs in execution handoff, not this plan
  frontmatter or `.harness` state of a different repository.

**Verification:**
- [ ] `uv run python -m harness_core.cli validate --repo-root C:\Users\HOANG PHI LONG DANG\repos\JOB-PROJECT`
- [ ] Focused consumer harness regression tests for policy, direct package CLI,
  host run, and unreadable historical packet.
- [ ] Fresh managed evidence for all three topology modes with matching packet,
  host, check, and validator identities.
- Expected: consumer has no executable core fork; old packet stays immutable;
  fresh package packet completes existing managed lifecycle.

**Exit Criteria:**
- At least one real consumer proves package migration, all admitted topologies,
  and historical-run recovery. No product source changes are needed for this task.

## Task 6: Retire Legacy Core Distribution Surfaces

**Purpose:**
- Remove bridge-only scripts/tests from starter-kit required output after every
  supported consumer has package-only proof.

**Specification Coverage:**
- Consumer no longer owns executable core
- Legacy scripts are one-way migration shims only
- Reduced release management

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/starter-kit-manifest.json`, `scripts/validate_repo_contracts.py`, `tests/test_starter_kit_generation.py`, `tests/test_validate_repo_contracts.py`
- Delete when Task 5 proof covers every supported consumer: `scripts/harness_task.py`, `scripts/plan_coordination.py`, `scripts/planning_artifact_schema.py`, `scripts/validate_harness_config.py`
- Delete/move: legacy harness-script tests now superseded by package test suite
- Modify: `README.md`, `docs/operating_system/procedures/managed-execution-adapter-contract.md`, canonical AGENTS/skill guidance from Task 3

**Dependencies:**
- Task 5 complete for every supported consumer.
- Explicit maintainer confirmation that no supported consumer still invokes shim
  commands. If confirmation is absent, keep shims and mark this task blocked.

**Steps:**
- [ ] Remove legacy scripts and their direct test copies from starter-kit
  manifest/required paths. Keep package installation and launcher commands in
  guidance.
- [ ] Delete canonical bridge shims only after manifest and consumer proofs
  establish they are unused. Do not add another compatibility copy.
- [ ] Update repository contract validator to require package source/tests and
  forbid legacy core paths in generated kits.
- [ ] Rebuild/validate kit and regenerate agent adapters after canonical guidance
  changes.

**Verification:**
- [ ] `python scripts/build_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/validate_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/validate_repo_contracts.py`
- Expected: kit carries policy, plans, rules, skills, and package-use guidance;
  it contains neither independent core nor obsolete bridge scripts.

**Exit Criteria:**
- Package is sole executable core in starter and supported consumer environments.

## Task 7: Prove Release, Kit, Host, And Runtime Drift

**Purpose:**
- Produce final source, package, host, consumer, kit, and generated-guidance
  evidence before completion review.

**Specification Coverage:**
- All completion criteria and acceptance criteria in parent specification.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: package workspace, starter kit manifest/output, generated agent
  surfaces, `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`, and migrated
  consumer root.

**Dependencies:**
- Tasks 1 through 6 and Task 4A complete.

**Steps:**
- [ ] Build wheels from immutable release tag and verify package metadata/version
  against packet `core_identity`.
- [ ] Run direct launcher/package failure matrix: missing core, malformed request
  API, unsupported request API, unsupported host API, unreadable packet, and
  host runtime unavailable.
- [ ] Compare equal direct and host packet resolution. Only provider transport
  evidence may differ.
- [ ] Run starter kit build/validation, repository contracts, adapter sync, and
  deployed agent runtime drift checks when canonical guidance changed.
- [ ] Run fresh live provider proof. Validator must be read-only and inspect the
  final workspace used by checks; controller acceptance must cite host evidence.
- [ ] Compare forced fake-protocol timeout, provider failure, approval, and
  protocol-failure observations through direct core normalization and provider
  host mapping; only opaque provider locator values may differ. Run live
  provider success separately; do not require unsupported failure injection.

**Verification:**
- [ ] `uv lock --check`
- [ ] `uv run --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv run --package harness-core-launcher pytest packages/harness-core-launcher/tests -q`
- [ ] `python scripts/build_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/validate_starter_kit.py --output-root <temporary-output-root>`
- [ ] `python scripts/validate_repo_contracts.py`
- [ ] `python scripts/sync_agent_adapters.py --check`
- [ ] `python scripts/validate_agent_runtime_drift.py`
- [ ] `uv lock --check` and focused/full host tests in `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- [ ] `git diff --check` in both repositories
- Expected: all checks pass; no copied core remains; fresh host/validator
  evidence uses one package identity.

**Exit Criteria:**
- `skill-verification-before-completion` can return verified with current,
  cross-repository evidence. No package fallback, unversioned-packet resume, or
  host-specific core behavior remains.

## Verification

- Run each task's focused proof before advancing.
- Run Task 7 only after package tags, host migration, and consumer migration
  evidence exist.
- Treat unavailable package release, host, or live App Server as a recorded
  blocker; do not replace required cross-repository proof with local success.

## Completion Criteria

The plan is ready for completion verification when:

1. PEP 440 package requirements/locks and integer protocol matrix have distinct,
   tested owners
2. launcher emits typed environment failure without package or consumer fallback
3. package owns all executable harness semantics and packet identity
4. host imports package through launcher and applies deterministic admission order
5. starter kit and migrated consumer contain no executable core fork
6. old packets remain immutable and unreadable continuation creates a successor
7. direct, host, all three topologies, checks, and read-only validator produce
   fresh matching package identity evidence
8. every admitted lane records one bounded, core-normalized terminal observation
   for forced timeout and provider failure, without raw sensitive output or
   transcript recovery
9. final verification runs all listed package, kit, host, consumer, generated,
   runtime-drift, lock, and diff checks
