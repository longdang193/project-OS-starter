---
artifact_type: plan
template_id: implementation-plan
status: completed
layer: change
name: harness-invocation-delegation-protocol
spec_ref: docs/superpowers/specs/2026-08-07-harness-invocation-delegation-protocol.md
targets:
  - packages/harness-core
  - packages/harness-core-launcher
  - repo_config/harness.yaml
  - agents/roles.yaml
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/pyproject.toml
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/uv.lock
---

# Harness Invocation and Delegation Protocol Implementation Plan

## Goal

Implement packet API 4 / host API 3 delegation. One execution-node graph. One
agent-invocation packet contract. One capability, budget, context, compatibility,
and provider-conformance owner.

## Implementation Outcomes

### Core protocol

`harness-core` owns compatibility matrix, run-record migration, execution-node
state, immutable invocation packets, child admission, idempotency, reservations,
and controller-only decision transitions.

### Policy authority

`repo_config/harness.yaml` owns semantic capabilities, context limits,
delegation profiles, and write authority. `agents/roles.yaml` owns template
eligibility and claimed-result schemas only.

### Provider symmetry

Codex host API 3 reuses typed adapter effects for workspace, bindings, agent
dispatch, collection, cancellation, integration, and checks. `harness.delegate`
is dynamic packet-selected tool. Ambient child spawning remains absent or typed
failure with conformance proof.

### Evidence and recovery

Run-record API 2 preserves execution-node observations, immutable packet digests,
reservation ledger, parent/child links, and controller decisions. Packet API 3
stays read-only through host API 3; no host-3 legacy dispatch or packet rewrite.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: two explicit repository workspaces. Each managed packet or test run uses one repository root only; no packet spans core and host roots.
- Commit policy: no commits during execution; separate explicit authorization required.
- Parallel ownership: none. `managed.py`, policy, role registry, and host contract share protocol boundary.
- Sequential fallback: complete core contract/tests, policy, execution-node/delegation state, package release boundary, host bridge, then cross-repository conformance.

## Task Breakdown

### Task 1: Define core protocol matrix and run migration

**Purpose:**
- Make packet API, host API, request API, and run-record API one core-owned relational contract.

**Specification Coverage:**
- Compatibility decision and migration boundary.
- Packet API 3 read-only host-3 recovery; packet API 4 host-3 dispatch.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/compatibility.py`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py:run_managed`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core-launcher/src/harness_core_launcher/loader.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/compatibility.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/__init__.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_compatibility.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_managed.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core-launcher/tests/test_loader.py`

**Dependencies:**
- Approved specification.

**Steps:**
- [ ] Add one compatibility-profile table. Derive admission, packet read, dispatch, and feature checks from it.
- [ ] Add run-record API 2 writer and API 1 reader. Preserve packet/run identity and historical evidence bytes.
- [ ] Return typed error for host-3 packet-3 dispatch; retain host-3 packet-3 inspection.
- [ ] Export compatibility matrix/query types through public core API. Keep launcher package-absence result typed and unchanged.
- [ ] Add focused regression cases before implementation for each matrix row and run migration path.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_managed.py -k "compatibility or packet_api or run"`
- [ ] `uv run --package harness-core-launcher pytest packages/harness-core-launcher/tests/test_loader.py`
- Expected: API 4/host 3 dispatches; API 4/host 2 and API 3/host 3 dispatch block; API 3 remains readable.

**Exit Criteria:**
- No independent compatibility constants or host-local legacy fallback decide protocol behavior.

### Task 2: Centralize policy authority and role schema

**Purpose:**
- Move effect authority from roles into semantic capability/workspace policy.

**Specification Coverage:**
- Semantic-capability decision.
- Context-table and delegation-profile ownership.

**Required Skills:**
- `skill-central-config-layer`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/repo_config/harness.yaml`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/agents/roles.yaml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/repo_config/harness.yaml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/agents/roles.yaml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_config_validation.py`

**Dependencies:**
- Task 1 complete.

**Steps:**
- [ ] Add policy-owned capability catalog/sets, context-limit table, delegation profiles, and child verification mode.
- [ ] Add role-schema v2 without `writes`. For request APIs 2/3 only, normalize accepted role-schema v1 `writes` into immutable legacy packet capability at admission; API 4 rejects v1 role authority and resolves effects only from policy/workspace.
- [ ] Reject unknown profiles, invalid limits, unsafe capability/workspace intersections, and invalid verification modes before host I/O.
- [ ] Add focused policy and role regression proof for former writable/read-only role cases.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_managed.py -k "role or capability or delegation or context"`
- Expected: API 4 role schema cannot widen effects; API 2/3 legacy role input converts once at admission without changing historical packets.

**Exit Criteria:**
- `agents/roles.yaml` v2 has no capability or write grant. Legacy v1 conversion is isolated to compatibility admission and never becomes API 4 authority.

### Task 3: Normalize execution-node graph without fake agent turns

**Purpose:**
- Preserve shared scheduling/evidence behavior while keeping deterministic host effects distinct from provider invocations.

**Specification Coverage:**
- Execution-node decision and one lifecycle outcome.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py:_execute_attempt`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Tasks 1–2 complete.

**Steps:**
- [ ] Introduce normalized execution-node records and node kinds: `agent`, `integration`, `check`.
- [ ] Reuse `dispatch_lane`/claim/evidence only for `agent`; reuse `materialize_final_state` and `run_checks` for deterministic nodes.
- [ ] Store packet only on agent nodes. Normalize deterministic observations without synthetic role, prompt, claim, or packet.
- [ ] Preserve single, sequential, and parallel dependency, timeout, cancellation, evidence, and controller-decision behavior.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests/test_managed.py -k "single_work_lane or sequential_work_lanes or parallel_work_lanes or integration or checks or validator"`
- Expected: graph records every node; integration/check path never reaches provider dispatch or claim collection.

**Exit Criteria:**
- Existing work modes retain current behavior through one execution-node scheduler.

### Task 4: Implement core-mediated delegation state and accounting

**Purpose:**
- Add controlled child admission, idempotency, parent wait/resume, cancellation, and reservation semantics.

**Specification Coverage:**
- Controlled `harness.delegate` requirement.
- Child-profile, provisional-proof, lifecycle-recovery decisions.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py:run_managed`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py:apply_controller_decision`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/api.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/managed.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/src/harness_core/api.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_managed.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests/test_timeout_observation.py`

**Dependencies:**
- Tasks 1–3 complete.

**Steps:**
- [ ] Add typed core `delegate(request) -> DelegationResult` boundary and immutable child packet derivation.
- [ ] Export `delegate` and typed result/error contract through `harness_core.api`; host imports this public boundary only.
- [ ] Validate role, capability, path, workspace, depth, count, concurrency, timeout, and result schema intersection before child workspace/provider turn.
- [ ] Add run-owned idempotency mapping and atomic reservation/release ledger.
- [ ] Add attempt-scoped delegation coordinator shared by parent callback and scheduler. Serialize run mutation/persistence, dispatch child through same attempt context, and never call `run_managed()` recursively from dynamic-tool callback.
- [ ] Implement `waiting_for_child` and controller-boundary transitions for child terminal, timeout, cancellation, and decision-required outcomes.
- [ ] Apply selected child verification mode. Keep every child outcome provisional until final validator/controller acceptance.
- [ ] Add direct success/failure/idempotency/cancellation/timeout/decision regression tests first.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_timeout_observation.py -k "delegate or child or reservation or idempotency or cancellation or timeout or concurrent"`
- Expected: duplicate request creates one child; denied request creates no workspace/turn; reservation releases once; controller alone decides successor.

**Exit Criteria:**
- Delegation works only through core admission and synchronized attempt state. No prompt, host-local policy, or recursive `run_managed()` controls child authority.

### Task 5: Stage package release and host dependency boundary

**Purpose:**
- Make host development and released installation consume same tested core API.

**Specification Coverage:**
- Provider-neutral package boundary and compatibility rollout.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/pyproject.toml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/uv.lock`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/pyproject.toml`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/uv.lock`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_runtime_dependencies.py`

**Dependencies:**
- Tasks 1–4 complete.

**Steps:**
- [ ] Bump `harness-core` package version after API-4 tests pass; build package artifact and record release candidate version.
- [ ] For local host proof, run `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run --with-editable C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core pytest tests/test_runtime_dependencies.py`. Do not alter committed host source to an untagged local path.
- [ ] After explicit release authorization, create immutable core tag, update host `tool.uv.sources.harness-core` to that tag, regenerate host `uv.lock`, and prove installed package version/API identity.
- [ ] Preserve host API 2 compatibility until host API 3 conformance and consumer API 4 rollout are proven.

**Verification:**
- [ ] `uv build packages/harness-core`
- [ ] `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run --with-editable C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core pytest tests/test_runtime_dependencies.py`
- [ ] `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run pytest tests/test_runtime_dependencies.py`
- Expected: local host proof imports intended editable core; committed host lock resolves only immutable released core tag.

**Exit Criteria:**
- Host never executes new protocol against silently stale `harness-core-v0.1.4` dependency.

### Task 6: Add host API 3 delegate bridge and conformance

**Purpose:**
- Expose packet-selected `harness.delegate` through Codex App Server while keeping host effect-only.

**Specification Coverage:**
- Host API 3 typed effect protocol.
- Ambient native delegation proof and provider symmetry.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py:CodexHarnessAdapter`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py:AppServerClient`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/src/codex_harness_host/app_server.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_live_delegation.py`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_adapter.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_app_server.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_live_single_work_lane.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests/test_live_delegation.py`

**Dependencies:**
- Task 5 complete.
- Codex App Server dynamic-tool protocol confirmed against installed supported version.

**Steps:**
- [ ] Upgrade adapter advertisement to host API 3 only after core API-4 conformance contract exists.
- [ ] Reuse existing adapter method surface. Pass delegate bridge only for `AgentInvocation` packets with `harness.delegate` capability.
- [ ] Register dynamic `harness.delegate` tool with structured request/result schema; block parent turn until bounded child outcome.
- [ ] Invoke core attempt-scoped coordinator through bridge. Keep parent dynamic-tool response on its connection; run child provider turn through child handle/connection without recursive top-level run.
- [ ] Prove platform native child-spawn capability absent/unexposed. When observable native spawn occurs, produce typed enforcement evidence and cancel parent.
- [ ] Record workspace/binding/model/tool/cancellation evidence without host-selected route, authority, or controller decision.
- [ ] Add fixture and live controlled App Server proof for permitted delegation, denied delegation, ambient absence, cancellation, and final read-only validator.

**Verification:**
- [ ] `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run pytest tests/test_adapter.py tests/test_app_server.py tests/test_live_single_work_lane.py tests/test_live_delegation.py`
- Expected: API-3 conformance passes; dynamic delegation has core-derived outcome; validator stays read-only; no ambient spawn path exists.

**Exit Criteria:**
- Codex host passes shared provider conformance with no core provider branch and no model/tool fallback.

### Task 7: Align canonical docs, generated surfaces, and starter kit

**Purpose:**
- Keep instructions, skills, adapter contract, runtime deployment, and kit output aligned with API 4/host 3 protocol.

**Specification Coverage:**
- Generated-source consistency and completion criteria.

**Required Skills:**
- `skill-writing-skills`
- `skill-central-config-layer`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/AGENTS.md`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/docs/operating_system/templates/agents/root-AGENTS.template.md`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/.agents/skills/skill-subagent-driven-development/SKILL.md`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/.agents/skills/skill-improve-harness/SKILL.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/.agents/rules/multi-agent-orchestration-rule.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/.agents/skills/skill-improve-harness/SKILL.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/repo_config/starter-kit-manifest.json`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/tests/test_starter_kit_generation.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/scripts/sync_agent_adapters.py`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/tests/test_starter_kit_generation.py`

**Dependencies:**
- Tasks 1–6 complete.

**Steps:**
- [ ] Update canonical guidance with execution-node versus agent-invocation distinction, core-only delegation, provisional child proof, host-3 legacy read-only recovery, and packet-selected delegate tool.
- [ ] Remove obsolete wording implying every lane/check receives an agent packet or role.
- [ ] Sync generated agent adapters and deploy local Codex runtime only after canonical sources are correct.
- [ ] Update starter-kit manifest/generation expectations for changed canonical assets.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --check`
- [ ] `python scripts/deploy_agent_runtime.py --target codex --force`
- [ ] `python scripts/validate_agent_runtime_drift.py`
- [ ] `python -m pytest tests/test_starter_kit_generation.py`
- Expected: generated outputs derive from canonical sources; local deploy drift absent; kit does not carry obsolete contract wording.

**Exit Criteria:**
- One canonical guidance path describes same protocol as core and host conformance tests.

### Task 8: Run cross-boundary protocol proof and completion review

**Purpose:**
- Prove real package, provider, policy, and generated-runtime behavior before acceptance.

**Specification Coverage:**
- All acceptance criteria and backend verification claims.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/docs/superpowers/specs/2026-08-07-harness-invocation-delegation-protocol.md`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/packages/harness-core/tests`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/tests`
- Verify: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter/scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1–7 complete.
- Local Codex App Server available for live host proof.

**Steps:**
- [ ] Run focused core/package tests, host tests, shared conformance, then live App Server delegation/validator proof.
- [ ] Verify packet API 3 historical read-only recovery and packet API 4 host-3 dispatch separately.
- [ ] Inspect run record, packet digests, reservation ledger, binding evidence, workspace containment, and controller-only decision evidence.
- [ ] Run final repository/kit validators. Record any external App Server failure as environment evidence, never product acceptance.
- [ ] Invoke `skill-verification-before-completion` before marking plan completed.

**Verification:**
- [ ] `uv run --package harness-core pytest packages/harness-core/tests`
- [ ] `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run pytest tests`
- [ ] `uv run --package harness-core python scripts/validate_planning_lifecycle.py`
- [ ] `uv run --package harness-core python scripts/validate_template_required_sections.py`
- [ ] `python scripts/validate_repo_contracts.py --fast`
- Expected: all specification acceptance criteria have fresh direct core/provider evidence, with no unrecorded failure or stale generated output.

**Exit Criteria:**
- Completion review returns `verified`; controller may then accept execution evidence.

## Verification

- `uv run --package harness-core pytest packages/harness-core/tests`
- `uv --directory C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host run pytest tests`
- `uv run --package harness-core python scripts/validate_planning_lifecycle.py`
- `uv run --package harness-core python scripts/validate_template_required_sections.py`
- `python scripts/validate_repo_contracts.py --fast`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. compatibility matrix and run migration have focused regression proof
2. policy alone owns semantic effects, context limits, and delegation profiles
3. graph distinguishes deterministic nodes from provider invocations without lifecycle split
4. child admission, idempotency, budget reservation, cancellation, and decision transitions have direct proof
5. Codex host API 3 passes shared and live applicable conformance proof
6. canonical docs, generated adapters, local runtime, and starter kit remain aligned
7. `skill-verification-before-completion` returns `verified`

## Completion Evidence

Completed August 7, 2026. Fresh proof: core `167 passed`; host `40 passed, 5
live skipped`; prior live App Server delegation `1 passed`; prior live
single-lane proof `4 passed`. Agent sync, runtime drift, starter-kit,
planning/template, repository-contract, and whitespace checks passed.
