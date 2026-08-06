---
artifact_type: plan
template_id: implementation-plan
status: active
layer: change
name: packet-runtime-budget-and-continuation-recovery
parent_spec: docs/superpowers/specs/2026-08-05-uniform-harness-execution-orchestrator.md
targets:
  - repo_config/harness.yaml
  - scripts/harness_task.py
  - scripts/validate_harness_config.py
  - tests/test_harness_task.py
  - tests/test_validate_harness_config.py
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - .agents/skills/skill-systematic-debugging/SKILL.md
  - .agents/skills/skill-improve-harness/SKILL.md
  - repo_config/starter-kit-manifest.json
  - ../codex-harness-host/src/codex_harness_host/app_server.py
  - ../codex-harness-host/src/codex_harness_host/adapter.py
  - ../codex-harness-host/src/codex_harness_host/cli.py
  - ../codex-harness-host/src/codex_harness_host/native_tools.py
  - ../codex-harness-host/tests/test_app_server.py
  - ../codex-harness-host/tests/test_adapter.py
  - ../codex-harness-host/tests/test_cli.py
  - ../codex-harness-host/tests/test_live_single_work_lane.py
related_features:
  - managed-harness
  - runtime-budget
  - continuation-recovery
---

# Packet Runtime Budget And Continuation Recovery Plan

## Goal

Make managed execution recoverable and diagnosable across every admissible
topology. Static harness policy selects bounded runtime behavior; packet freezes
it; provider host enforces it; run evidence explains timeout; controller alone
chooses next action. Existing planned attempts resume by run ID without request
resubmission. A controller escalation creates one fresh packet through the
packet-named profile; it never mutates earlier packet data or treats timeout as
retry.

## Implementation Outcomes

### One Runtime-Budget Contract

`repo_config/harness.yaml` owns named execution-budget profiles, each route's
initial profile, and each profile's permitted timeout decisions plus optional
named escalation target. `scripts/harness_task.py` resolves one profile into
immutable packet `execution_budget`. The resolved object contains profile ID,
positive bounded `turn_timeout_seconds`, timeout-permitted decisions, and only
one policy-named successor profile when escalation is allowed. Packet schema
and policy validation reject missing, malformed, out-of-range, unknown, or
arbitrarily selected values.

### One Provider Consumption Boundary

`../codex-harness-host` receives only packet-resolved budget. Its App Server
turns, lane dispatch, validator, and checks use that same value. It reports a
structured timeout object instead of opaque timeout text. No host CLI timeout
flag, provider fallback, or hidden hard-coded runtime budget remains. This
packet contract requires provider contract version 2; a version-1 host fails
identity validation before dispatch.

### One Continuation Contract

Provider `run` accepts exactly one of `--request` or `--run-id`. Request starts
a new run; run ID resumes an existing planned attempt with `request=None`.
Core remains the sole owner of run-state validation, successor creation, and
controller decisions.

### Operational Guidance And Fresh Deployment

Managed-execution guidance tells controllers to inspect timeout evidence before
any decision, to resume a planned attempt by ID, and to escalate or block
terminal timeouts rather than retrying or minting another request. Provider deployment guidance uses
a refreshed rebuild command so unchanged package versions cannot leave stale
global CLI behavior installed.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-systematic-debugging`, `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-subagent-driven-development`, `skill-verification-before-completion`
- Isolation: starter core and host adapter change serially in their owning repositories; no product repository source changes during contract work.
- Commit policy: commit each repository only after its focused and full proof passes; deploy host only after its commit is pushed.
- Parallel ownership: none. Starter packet schema and host adapter interface are shared boundaries.
- Sequential fallback: keep the current 300-second policy until packet budget, host enforcement, and timeout evidence pass together. Do not dispatch a new product successor while either side is mixed-version.

## Task Breakdown

### Task 1: Define And Validate Static Runtime Budget

**Purpose:**
- Add one canonical execution-budget policy shape without copying timeout values
  into roles, skills, provider CLI, or route-specific runners.

**Specification Coverage:**
- Immutable execution budget.
- Timeout evidence and controller recovery.
- Static policy SSOT.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml`
- Modify: `scripts/harness_task.py` packet resolution and policy validation
- Modify: `scripts/validate_harness_config.py`
- Modify: `tests/test_harness_task.py`
- Modify: `tests/test_validate_harness_config.py`

**Implementation Steps:**
1. Define named execution-budget profiles with positive bounded timeout,
   permitted timeout decisions, and optional one-way escalation target. Bind
   every route to one initial profile. Keep only default and one escalation
   profile unless real route evidence requires more.
   Bump `codex_app_server` policy contract version from 1 to 2 because this
   packet schema gains required behavior.
2. Resolve a normalized `execution_budget` into every managed packet before
   workspace preparation. Continuation reuses its stored packet exactly;
   controller escalation resolves a new packet only through current packet's
   named successor profile.
3. Reject missing, unsafe, non-integer, zero, over-limit, and unpermitted
   timeout-decision values, unknown profiles, cycles, and arbitrary successor
   profile selection before packet creation.
4. Add direct tests proving every topology resolves same object shape and prior
   attempt packet stays unchanged after controller retry or escalation. Prove
   timeout allows no retry, permitted escalation selects only named profile,
   and terminal profile permits only block. Prove version-1 adapter identity
   blocks before workspace preparation or dispatch.

**Exit Criteria:**
- One validated policy owner resolves one immutable packet budget.
- No role, tool, or CLI surface owns a competing timeout default.

### Task 2: Preserve Timeout Evidence In Core Lifecycle

**Purpose:**
- Make provider timeout distinct from generic dispatch failure without coupling
  harness core to Codex implementation types.

**Specification Coverage:**
- Timeout evidence and controller recovery.
- Reproducible run authority.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/harness_task.py` managed adapter-error normalization and
  `_record_failure()` path
- Modify: `tests/test_harness_task.py`

**Implementation Steps:**
1. Define provider-neutral optional exception evidence contract: host errors
   may expose a validated mapping; core copies only recognized bounded timeout
   fields and ignores malformed or provider-specific extras.
2. Record `dispatch_timeout` separately from generic `dispatch_failed`, with
   packet budget, elapsed seconds, terminal status, event summary, last tool
   call, and completed-command count.
3. Keep controller as sole decision writer. Timeout outcome permits only packet
   policy decisions: `block`, plus `escalate` only when packet names a valid
   successor budget profile. `retry` is rejected. Escalation creates one new
   planned packet through that profile; core injects the named successor profile
   during packet resolution and rejects any decision-supplied budget profile.
   It never mutates prior packet.
4. Add deterministic core tests for complete timeout evidence, malformed host
   evidence, terminal interruption absence, continuation of planned attempt,
   duplicate request rejection, and unchanged prior packet.

**Exit Criteria:**
- One `run.json` answers why timeout occurred and what controller may do.
- Core imports no Codex host class or provider-specific exception.

### Task 3: Enforce Packet Budget And Report Timeout In Codex Host

**Purpose:**
- Consume starter packet contract uniformly for all Codex host operations.

**Specification Coverage:**
- Provider-neutral managed execution.
- Immutable execution budget.
- New-run and continuation symmetry.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `../codex-harness-host/src/codex_harness_host/app_server.py`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py`
- Modify: `../codex-harness-host/src/codex_harness_host/cli.py`
- Modify: `../codex-harness-host/src/codex_harness_host/native_tools.py`
- Modify: `../codex-harness-host/tests/test_app_server.py`
- Modify: `../codex-harness-host/tests/test_adapter.py`
- Modify: `../codex-harness-host/tests/test_cli.py`
- Modify: `../codex-harness-host/tests/test_live_single_work_lane.py`

**Implementation Steps:**
1. Pass immutable packet budget into every App Server operation that creates a
   turn and every packet-selected command/check binding. Retain only short
   connection/interrupt safety ceilings outside execution budget, label them
   non-execution transport limits, and ensure they cannot extend a packet turn.
   Remove static execution-timeout ownership from host dispatch path.
   Bump `RUNTIME_PROVIDER.contract_version` to 2 so a stale host cannot claim
   conformance to budget packets.
2. Convert terminal `TurnTimeout` data into normalized provider-neutral timeout
   evidence. Preserve command and event summaries within bounded output limits.
3. Keep `--request` and `--run-id` mutually exclusive. Test new-run,
   continuation, invalid mixed input, stale run state, and exact core call
   arguments. Test reported v2 identity and fail-closed mismatch against a
   v1 packet/provider expectation.
4. Test `single_work_lane`, `sequential_work_lanes`, and
   `parallel_work_lanes` with same packet budget; prove writer, integration,
   validator, native command bindings, and checks cannot substitute a different
   execution value. Keep preflight transport timeout outside this assertion.
5. Add deterministic timeout/terminal-interrupt test and one opt-in live App
   Server continuation proof using a disposable harness fixture.

**Exit Criteria:**
- Host accepts no execution-timeout setting outside immutable packet data.
- Timeout error arrives in core with validated evidence and no product change.

### Task 4: Align Controller And Deployment Guidance

**Purpose:**
- Teach repeatable recovery without making natural-language guidance policy
  authority.

**Specification Coverage:**
- New-run and continuation symmetry.
- Timeout evidence and controller recovery.

**Required Skills:**
- `skill-writing-skills`
- `skill-subagent-driven-development`
- `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `.agents/skills/skill-systematic-debugging/SKILL.md`
- Modify: `.agents/skills/skill-improve-harness/SKILL.md`
- Modify: `../codex-harness-host/README.md` or
  `../codex-harness-host/docs/feasibility-report.md`

**Implementation Steps:**
1. Document request versus run-ID invocation and prohibit reusing a terminal
   packet or resubmitting an existing request.
2. Document timeout triage: no tool call means prompt/context stall; productive
   progress means policy-approved budget or smaller task decision; hung command
   means tool/command repair.
3. Document controller `escalate`/`block` boundary. Retry is allowed only when
   packet retry policy explicitly permits a non-timeout outcome and creates a
   new planned attempt. A timeout never permits retry.
4. Document canonical host refresh command:
   `uv tool install --force --reinstall --refresh .`.
5. Sync generated agent surfaces only from canonical starter sources.

**Exit Criteria:**
- Guidance routes every timeout through evidence and controller decision.
- Guidance contains no copied timeout values or provider-specific policy.

### Task 5: Prove Cross-Repository Conformance And Distribute Starter

**Purpose:**
- Prevent starter/host drift before a real product successor runs.

**Specification Coverage:**
- Provider-neutral managed execution.
- Bounded runtime and actionable timeout recovery.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`
- `skill-subagent-driven-development`

**Files And Symbols:**
- Modify only if proof exposes defect: starter or host files named by Tasks 1–4
- Run: `scripts/build_starter_kit.py`
- Run: `scripts/sync_local_starter_kit_repo.ps1`
- Run: `scripts/validate_agent_runtime_drift.py`

**Implementation Steps:**
1. Run starter policy, packet, continuation, and planning validations.
2. Run host unit suite, lock check, and live disposable harness proof.
3. Install host with refreshed rebuild command; prove global CLI exposes both
   `--request` and `--run-id`, then preflight App Server.
4. Build starter kit, sync local kit, and validate runtime drift.
5. Only then create a separately approved product successor from a smaller
   Git-tracked task slice. Do not create another retry from prior terminal
   packet.

**Exit Criteria:**
- Starter and host agree on one packet budget and continuation contract.
- Installed runtime and generated kit match committed canonical sources.

## Verification

- `uv run pytest tests/test_harness_task.py tests/test_validate_harness_config.py -q`
- `uv run python scripts/validate_harness_config.py`
- `uv run python scripts/validate_planning_lifecycle.py`
- `uv run pytest` in `../codex-harness-host`
- `uv lock --check` in `../codex-harness-host`
- Direct host timeout-evidence regression and opt-in live planned-attempt
  continuation proof with `CODEX_HARNESS_LIVE=1`
- `python scripts/build_starter_kit.py`
- `pwsh -NoProfile -File .\scripts\sync_local_starter_kit_repo.ps1`
- `python scripts/validate_agent_runtime_drift.py`
- `git diff --check` in both repositories

## Completion Criteria

1. Every managed packet has one immutable, validated execution budget.
2. Every lane topology and provider operation consumes the packet budget.
3. Timeouts produce actionable normalized evidence and no automatic retry.
4. New runs and planned continuations share one mutually exclusive provider CLI
   boundary.
5. Guidance, generated surfaces, starter kit, and installed host match their
   canonical sources.
6. A real product successor is not dispatched until all contract proof passes.
