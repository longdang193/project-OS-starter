---
artifact_type: plan
status: proposed
layer: change
template_id: implementation-plan
spec_ref: docs/superpowers/specs/2026-08-09-unified-attempt-terminalization-ssot.md
---

# Unified Attempt Terminalization SSOT Implementation Plan

## Goal

Implement approved unified attempt terminalization. Core becomes sole durable writer for leases, terminal records, outcomes, run state, and `run.json`. Host produces bounded lane observations and Windows containment proof only. New packets require compatible core and host capabilities; active legacy attempts drain before cutover.

## Implementation Outcomes

### Core-owned terminal transaction

`harness-core` exposes `terminalize_attempt(evidence)` and related nonterminal cancellation/orphan helpers. New attempts get deterministic immutable lease, revisioned run record, canonical evidence digest, and one terminal record. Existing terminal records remain readable without rewrite.

### Host lifecycle proof

`codex-harness-host` produces v2 lane observations, finite duration capability, cancellation stop proof, and Windows Job Object containment. Host never writes core run state or aggregates controller outcomes.

### Safe rollout and maintained guidance

Migration preflight blocks active legacy attempts. Core/host compatibility, canonical adapter guidance, consumer setup, root agent template, generated routing, package pins, and tests agree.

## Execution Approach

- Mode: `sequential_work_lanes`
- Required skills: `skill-test-driven-development`, `skill-code-standards`, `skill-backend-verification`, `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: clean worktree for this repository and clean separate worktree for `../codex-harness-host`; existing host worktree has unrelated uncommitted edits and must not receive this work.
- Commit policy: no commits, tags, publishes, or lockfile release changes without separate explicit authorization.
- Parallel ownership: none. Core schema and packet contract precede host changes; host capability precedes new-packet admission.
- Sequential fallback: if local cross-package installation blocks host tests, stop after core proof. Do not repoint committed host dependency to an unreleased branch; use temporary local test override only outside committed files.

## Task Breakdown

### Task 1: Define v2 observations, duration model, and packet lease

**Purpose:**
- Add pure core contracts before lifecycle mutation: sanitized host observation v2, deterministic lease-duration model, policy validation, and immutable packet fields.

**Specification Coverage:**
- Ownership and trusted boundary; execution lease; host terminal observations; atomicity and idempotency; finite packet-resolved lease decision.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/terminal_observation.py:normalize_terminal_observation`
- Create: `packages/harness-core/src/harness_core/execution_lease.py`
- Modify: `packages/harness-core/src/harness_core/managed.py:_resolve_execution_budget`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:_validate_execution_budgets`
- Modify: `packages/harness-core/src/harness_core/api.py:__all__`
- Modify: `repo_config/harness.yaml`
- Modify: `packages/harness-core/tests/test_terminal_observation.py`
- Create: `packages/harness-core/tests/test_execution_lease.py`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `packages/harness-core/tests/test_config_validation.py`

**Dependencies:**
- Approved specification active.
- Clean core worktree.

**Steps:**
- [ ] Add failing tests for `host_terminal_observation/v2`: exact fields, opaque IDs, lane binding, lease binding, sanitized error metadata, containment proof, raw-value rejection, and current v1 reader preservation.
- [ ] Add `execution_lease.py` with one stdlib-only duration resolver. Define versioned host duration limits and deterministic topology scheduling: lane bound by dependency wave and writer limit; add bounded checks, core verification, and cleanup grace.
- [ ] Extend policy schema and `repo_config/harness.yaml` with finite duration-model fields, `execution_lease_seconds`, and capability version. Reject zero, negative, unknown, or unbounded components during policy validation and packet resolution.
- [ ] Project resolved duration model ID, lease duration, host terminal-observation capability, and v2 artifact metadata into new immutable packet. Preserve legacy packet readers without synthetic lease fields.
- [ ] Export new pure normalizers and lease resolver through `harness_core.api`; do not add ambient generic CLI control command.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminal_observation.py packages/harness-core/tests/test_execution_lease.py packages/harness-core/tests/test_config_validation.py -q`
- [ ] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- Expected: v2 observation accepts only bounded safe host data; duration is reproducible for sequential and parallel fixtures; invalid duration/capability blocks before packet creation.

**Exit Criteria:**
- New packet contains exact finite lease inputs and v2 host contract metadata. Pure schema and policy tests pass without changing run state.

### Task 2: Centralize core terminalization, cancellation, orphan, and migration state

**Purpose:**
- Replace post-dispatch terminal writers with one lock-protected core transaction and preserve nonterminal orphan safety.

**Specification Coverage:**
- `terminalize_attempt(evidence)`; normal completion; provider failure; timeout; cancellation; host crash; stranded recovery; orphan state; legacy abandonment; atomicity; idempotency; migration gate.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_write_run`
- Modify: `packages/harness-core/src/harness_core/managed.py:_append_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:_transition`
- Modify: `packages/harness-core/src/harness_core/managed.py:_normalize_terminal_evidence`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_failure`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_terminal_failure`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_dispatch_exception`
- Modify: `packages/harness-core/src/harness_core/managed.py:_cancel_active_lanes`
- Modify: `packages/harness-core/src/harness_core/managed.py:_execute_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:recover_stranded_run`
- Modify: `packages/harness-core/src/harness_core/managed.py:run_managed`
- Modify: `packages/harness-core/src/harness_core/managed.py:apply_controller_decision`
- Modify: `packages/harness-core/src/harness_core/api.py:__all__`
- Modify: `packages/harness-core/tests/test_managed.py`
- Create: `packages/harness-core/tests/test_terminalization.py`
- Modify: `packages/harness-core/tests/test_cli.py`

**Dependencies:**
- Task 1 complete.
- Exact v2 observation and lease contracts frozen by tests.

**Steps:**
- [ ] Add failing direct API tests for `terminalize_attempt`, `request_attempt_cancellation`, and migration preflight. Cover success, verification failure, provider failure, timeout, writer completion missing, cancellation, host-crash absence proof, stranded recovery, legacy abandonment, malformed evidence, stale lease, duplicate replay, and conflicting replay.
- [ ] Introduce per-run lock plus monotonic `run_revision`; make `_write_run` retain same-directory temporary replace behavior while terminal transaction writes lease, evidence, outcome, state history, and revision together.
- [ ] Add attempt fields for immutable lease, host-observation digest references, terminal record, cancellation request, and recovery-blocked evidence. Add active nonterminal `orphaned` state and prohibit dispatch, retry, resume, acceptance, waiver, and legacy abandonment there.
- [ ] Implement core-owned canonical evidence ordering, compact sorted JSON digest, and derived terminal ID. Core must load persisted lane/verification evidence; input cannot select outcome, decision, target state, digest, or terminal ID.
- [ ] Replace `_record_failure`, `_record_terminal_failure`, dispatch exception handling, verification completion, and `recover_stranded_run` terminal writes with adapters into `terminalize_attempt`. Keep legacy reader compatibility only; do not leave new-packet alternate writer path.
- [ ] Implement idempotent cancellation request record. Bind host cancellation observation to request ID and require stop proof before terminal `cancelled` result.
- [ ] Implement expired-lease observer handling. Absence proof creates block-only terminal record. Live or unverified process records `recovery_blocked`, transitions to `orphaned`, and remains nonterminal until fresh cleanup evidence arrives.
- [ ] Implement migration preflight scanning active historical unleased attempts. Block v2 packet admission while any remain; allow audited direct block only through explicit legacy abandonment.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_cli.py -q`
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- Expected: direct core boundary proves final `run.json` state, outcome, lease release, idempotency, atomic-write failure preservation, and no successor while orphaned.

**Exit Criteria:**
- Every new-packet post-dispatch path reaches one core terminal transaction. Core tests prove important success, failure, state, duplicate-delivery, and migration behavior.

### Task 3: Produce host v2 observations and Windows containment proof

**Purpose:**
- Make host enforce finite lease time, emit v2 lane observations, bind cancellation, and contain provider descendants with sole-handle Windows Job Object.

**Specification Coverage:**
- Host terminal observations; provider failure and timeout; cancellation; Windows process containment; crash observation; finite packet lease; no host run-state writes.

**Required Skills:**
- `skill-test-driven-development`
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.capabilities`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.identity`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.dispatch_lane`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.collect_lane_evidence`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.cancel_lane`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter._complete_lane_turn`
- Modify: `../codex-harness-host/src/codex_harness_host/app_server.py:StdioAppServerClient._connect`
- Modify: `../codex-harness-host/src/codex_harness_host/app_server.py:StdioAppServerClient._close_connection`
- Create: `../codex-harness-host/src/codex_harness_host/windows_job.py`
- Modify: `../codex-harness-host/src/codex_harness_host/cli.py:main`
- Modify: `../codex-harness-host/tests/test_adapter.py`
- Modify: `../codex-harness-host/tests/test_app_server.py`
- Create: `../codex-harness-host/tests/test_windows_job_containment.py`
- Modify: `../codex-harness-host/tests/test_live_single_work_lane.py`

**Dependencies:**
- Task 1 packet schema and capability names complete.
- Task 2 core APIs and v2 reader available in local test environment.
- Clean dedicated host worktree; no edits to existing dirty host worktree.

**Steps:**
- [ ] Add host capability and identity fields for v2 terminal observations and finite duration model. Make core/host mismatch fail before new packet dispatch.
- [ ] Replace lane-only terminal payload construction with v2 host observation builder. Preserve opaque provider IDs and sanitized current item, command, final-claim, error, and retained-artifact behavior.
- [ ] Bind host dispatch to packet lease deadline. Include retry, finalizer, interrupt settlement, and stop wait within declared duration model. Reject dispatch when remaining lease cannot cover required host step.
- [ ] Add cancellation request handling: cancel active host work, terminate containment, wait for zero active processes, then return observation echoing core cancellation request ID. `Future.cancel()` may aid local scheduling but cannot be stop proof.
- [ ] Add stdlib `ctypes` Windows Job Object wrapper. Create unnamed job, configure kill-on-close, launch provider root suspended, assign before resume, terminate on timeout/cancel, enumerate active process count, and record PID plus creation identity. Do not add `pywin32` or other dependency.
- [ ] Keep one sole job handle in host dispatch process. On host crash, do not reopen job from observer; observer only reports absence using recorded host/root process identities. Reject unavailable Windows APIs before provider execution.
- [ ] Keep non-Windows behavior explicit: capability reports containment unavailable and core refuses new Windows-containment packets rather than emulating with PID trees or `taskkill`.

**Verification:**
- [ ] From `../codex-harness-host`: `uv run --locked pytest tests/test_adapter.py tests/test_app_server.py tests/test_live_single_work_lane.py -q`
- [ ] From `../codex-harness-host` on Windows: `uv run --locked pytest tests/test_windows_job_containment.py -q`
- Expected: host emits only bounded v2 observations; cancellation waits for stop proof; failed Job Object setup starts no provider process; descendant sentinel exits on timeout, cancellation, and host-handle crash.

**Exit Criteria:**
- Host lifecycle proof matches core v2 contract. Windows containment uses one native Job Object path with no prohibited fallback.

### Task 4: Prove core-host compatibility and controlled migration

**Purpose:**
- Exercise new behavior through host CLI and core managed boundary, then prepare release-compatible package changes without publishing.

**Specification Coverage:**
- Core/host capability pairing; active legacy drain gate; rollback reader compatibility; direct backend contract and representative trace proof.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `packages/harness-core/pyproject.toml:[project]`
- Modify: `packages/harness-core/src/harness_core/compatibility.py`
- Modify: `packages/harness-core/tests/test_compatibility.py`
- Modify: `scripts/deploy_harness_core_to_host.ps1`
- Modify: `tests/test_deploy_harness_core_to_host.py`
- Modify: `../codex-harness-host/pyproject.toml:[project]`
- Modify: `../codex-harness-host/uv.lock`
- Modify: `../codex-harness-host/tests/test_runtime_dependencies.py`
- Verify: `../codex-harness-host/src/codex_harness_host/cli.py:main`

**Dependencies:**
- Tasks 1 through 3 complete with focused suites passing.
- Migration preflight behavior complete.
- Explicit authorization required before changing release tags, publishing packages, or committing package-version changes.

**Steps:**
- [ ] Add compatibility version and capability assertions for v2 observation, duration model, lease, and Windows containment. Preserve readers for historical terminal records.
- [ ] Extend deployment script and tests to install or stage exact locally built core package for host integration proof without committing temporary dependency overrides.
- [ ] Add host CLI integration fixtures for normal completion, provider failure, timeout, cancellation, host crash absence proof, orphan block, and legacy migration preflight. Capture run ID, attempt ID, lease ID, terminal ID, and final state as representative trace evidence.
- [ ] Verify rollback rule: core reader understands v2 record before any v2 packet admission; host capability absence causes no new packet/lease side effect.
- [ ] Update package versions, host core pin, and locks only when a separate release authorization exists. Otherwise leave release metadata unchanged and record release as handoff gate.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_compatibility.py tests/test_deploy_harness_core_to_host.py -q`
- [ ] From `../codex-harness-host`: `uv run --locked pytest tests/test_runtime_dependencies.py tests/test_live_single_work_lane.py -q`
- [ ] From `../codex-harness-host`: `uv run --locked codex-harness-host capabilities`
- Expected: compatible local package pair proves all terminal paths through host-to-core boundary; incompatible capability blocks before packet creation; release mutation remains paused without authorization.

**Exit Criteria:**
- Fresh cross-package integration proof covers direct boundary, failures, final state, idempotency, migration, and trace identifiers. No unreleased dependency pin enters committed configuration.

### Task 5: Align canonical documentation and generated guidance

**Purpose:**
- Publish one current lifecycle contract without private paths, stale recovery wording, or generated-surface drift.

**Specification Coverage:**
- Compatibility and migration; trusted boundary; ownership; Windows containment; generated guidance; completion criterion 8.

**Required Skills:**
- `skill-code-standards`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `README.md`
- Modify: `repo_config/harness.yaml`
- Generate: `AGENTS.md`
- Generate: `docs/operating_system/tooling/harness-routing.generated.md`
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `scripts/render_harness_routing.py`
- Verify: `tests/test_render_harness_routing.py`
- Verify: `tests/test_sync_agent_adapters.py`

**Dependencies:**
- Tasks 1 through 4 complete.
- Canonical contract and compatibility versions frozen.

**Steps:**
- [ ] Replace split terminal-writer and unleased stranded-recovery guidance with core terminalization, lease duration, host observations, cancellation request, orphaned state, legacy drain gate, and sole-handle Job Object rules.
- [ ] Document trusted local controller transport boundary accurately. Do not claim cryptographic host attestation or controller-proof impossibility.
- [ ] Document exact migration preflight, no-active-legacy gate, release pairing, rollback reader rule, and external incident path for containment breach.
- [ ] Update canonical root-agent template only; never edit generated `AGENTS.md` as source. Remove local absolute host paths and private machine evidence from all changed documents.
- [ ] Regenerate agent and routing outputs. Review generated diffs for stale packet APIs, secret-bearing provider fields, unsupported reaper language, and private paths.

**Verification:**
- [ ] `uv run --locked python scripts/sync_agent_adapters.py`
- [ ] `uv run --locked python scripts/render_harness_routing.py`
- [ ] `uv run --locked pytest tests/test_sync_agent_adapters.py tests/test_render_harness_routing.py tests/test_validate_template_required_sections.py -q`
- [ ] `git diff --check`
- Expected: canonical and generated guidance agree; no personal paths, secrets, stale lifecycle rules, or generated-source edits remain.

**Exit Criteria:**
- Documentation and generated surfaces describe one current terminalization contract and validate from canonical inputs.

## Verification

- `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminal_observation.py packages/harness-core/tests/test_execution_lease.py packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_compatibility.py -q`
- `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- From `../codex-harness-host`: `uv run --locked pytest tests/test_adapter.py tests/test_app_server.py tests/test_live_single_work_lane.py tests/test_runtime_dependencies.py -q`
- From `../codex-harness-host` on Windows: `uv run --locked pytest tests/test_windows_job_containment.py -q`
- `uv run --locked python scripts/sync_agent_adapters.py`
- `uv run --locked python scripts/render_harness_routing.py`
- `uv run --locked pytest tests/test_sync_agent_adapters.py tests/test_render_harness_routing.py tests/test_validate_template_required_sections.py -q`
- `uv lock --check`
- From `../codex-harness-host`: `uv lock --check`
- `git diff --check`

## Completion Criteria

1. New packets contain core-resolved finite lease duration and v2 host capability binding.
2. Core terminalizes every post-dispatch success and failure through one direct API; host cannot write durable core state.
3. Terminal record atomically joins lease release, canonical evidence digest, outcome, state history, and revision; duplicate evidence replays safely.
4. Cancellation requires persisted request ID and zero-process stop proof.
5. Windows provider descendants are contained by sole-handle Job Object; no PID-tree, process-group, `taskkill`, or named-job reaper fallback exists.
6. Expired unverified process enters durable nonterminal `orphaned` state and blocks continuation until fresh cleanup proof.
7. Migration preflight drains or explicitly closes every active unleased legacy attempt before v2 admission; historical terminal records stay unchanged and readable.
8. Focused core tests, full core suite, host contract suite, Windows containment suite, migration proof, docs/generator checks, lock checks, and whitespace checks pass from fresh commands.

Plan completes only after `skill-verification-before-completion` reports fresh verified evidence. Publishing or committing package releases remains separate explicit authorization.
