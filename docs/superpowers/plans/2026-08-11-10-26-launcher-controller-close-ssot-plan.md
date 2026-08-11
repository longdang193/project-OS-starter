---
artifact_type: plan
template_id: implementation-plan
status: completed
layer: change
name: launcher-personal-controller-close-ssot-plan
parent_spec: docs/superpowers/specs/2026-08-11-personal-local-controller-close-ssot.md
targets:
  - packages/harness-core/src/harness_core/authority.py
  - packages/harness-core/src/harness_core/managed.py
  - packages/harness-core/tests/test_terminal_authority.py
  - packages/harness-core/tests/test_terminalization.py
  - packages/harness-core/tests/test_managed.py
  - packages/harness-core/tests/test_cli.py
  - packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py
  - packages/harness-core-launcher/src/harness_core_launcher/cli.py
  - packages/harness-core-launcher/tests/test_runtime_manager.py
  - packages/harness-core-launcher/tests/test_loader.py
  - docs/operating_system/rules/multi-agent-orchestration-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/procedures/harness-core-consumer-setup.md
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
  - AGENTS.md
  - generated_agents
  - C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit
---

# Launcher Personal Controller Close SSOT Plan

## Goal

Implement approved personal local controller mode with one setup command and one
routine close command. Reuse current Ed25519 registry, authorization, outcome,
receipt, run lock, active runtime profile, and detached signer path. Add no
broker, daemon, remote service, new schema, or generic controller framework.

## Implementation Outcomes

### One conventional personal authority

Core owns fixed personal key path, deterministic public identity, idempotent
initialization, and safe key-first partial recovery. No signer-selection config,
environment file, copied issuer value, or custom ACL manager is added.

### One core close transaction

Core resolves personal authority, binds current outcome, signs existing
`controller_authorization/v1` in memory, and invokes shared finalization under
one run lock. Same decision and reason replay stored receipt before signer or
registry lookup; conflicting close rejects.

### One launcher core-control helper without boundary regression

Launcher routes `controller-init`, `close`, and existing provider-free
terminalization through active-profile core module invocation. Launcher
`decision` remains host-bound so retry and escalation retain adapter admission
and current provider preflight.

### One canonical personal-use contract

Canonical rules and procedures state same-user authority trade-off, personal-only
scope, setup/close commands, detached compatibility, and production exclusion.
Existing generation and starter-kit sync scripts propagate guidance.

### Release-ready proof without release side effects

Focused core, launcher, generated-surface, starter-kit, and repository contract
checks pass. Implementation ends release-ready; commit, tag, push, package
release, runtime activation, and historical-run disposition remain separately
authorized actions.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-executing-plans`, `skill-central-config-layer`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `isolated worktree for project-OS-starter`
- Commit policy: `external authorization`; no commit, tag, push, release, runtime upgrade, or historical-run disposition during execution
- Parallel ownership: none; authority, terminalization, launcher transport, and generated guidance share contracts
- Sequential fallback: core authority setup, core close transaction, launcher boundary, canonical guidance, final verification

## Task Breakdown

### Task 1: Add fixed personal controller initialization

**Purpose:**
- Create or validate one personal controller without manual identity or path configuration.

**Specification Coverage:**
- One-time personal controller setup.
- Fixed personal authority identity.
- Bounded partial setup recovery.
- Convention over signer configuration.

**Required Skills:**
- `skill-central-config-layer`
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/authority.py:authority_registry_path`
- Inspect: `packages/harness-core/src/harness_core/authority.py:load_private_ed25519_key`
- Add: `packages/harness-core/src/harness_core/authority.py:personal_controller_key_path`
- Add: `packages/harness-core/src/harness_core/authority.py:initialize_personal_controller`
- Add: `packages/harness-core/src/harness_core/authority.py:resolve_personal_controller`
- Modify: `packages/harness-core/src/harness_core/managed.py:main`
- Modify: `packages/harness-core/tests/test_terminal_authority.py`
- Modify: `packages/harness-core/tests/test_cli.py`

**Dependencies:**
- Approved parent specification active.
- Existing registry parser, canonical JSON, fingerprint, PEM loader, signer, and atomic-write patterns remain authoritative.

**Steps:**
- [ ] Add fixed key path and deterministic key/principal derivation from fingerprint.
- [ ] Add initialization that creates missing key, atomically persists PEM, and creates or extends one validated registry without overwriting identities.
- [ ] Recover only existing-key/missing-entry state; block registry-only, revoked, conflicting, duplicate, malformed, repository-local, or ambiguous state.
- [ ] Add core `controller-init` CLI returning only status, key ID, fingerprint, and registry digest.
- [ ] Add direct tests for first setup, idempotent replay, partial recovery, blocked states, private-output absence, and byte-identical failed files.

**Verification:**
- [ ] `uv run --locked pytest -q tests/test_terminal_authority.py tests/test_cli.py` from `packages/harness-core`
- Expected: valid setup configures or replays one identity; rejected setup does not overwrite key or registry.

**Exit Criteria:**
- Personal authority needs no config file, environment variable, issuer argument, fingerprint argument, or private-key argument after setup.

### Task 2: Add core personal close transaction

**Purpose:**
- Finalize eligible personal runs with one signed in-memory core operation.

**Specification Coverage:**
- One-command signed close.
- Atomic personal close.
- Deterministic replay.
- Existing finalizer and schemas remain authoritative.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/managed.py:terminalize_attempt`
- Inspect: `packages/harness-core/src/harness_core/managed.py:_finalize_outcome`
- Inspect: `packages/harness-core/src/harness_core/managed.py:sign_controller_authorization`
- Add: `packages/harness-core/src/harness_core/managed.py:close_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:main`
- Modify: `packages/harness-core/tests/test_terminalization.py`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `packages/harness-core/tests/test_cli.py`

**Dependencies:**
- Task 1 complete.
- Existing detached signer and canonical envelope behavior remain unchanged.

**Steps:**
- [ ] Extract or reuse one lock-held finalization branch shared by detached and personal authorization paths.
- [ ] Add replay check before signer and registry access using stored outcome, decision, issuer, reason SHA-256, and reason length.
- [ ] Add `close-attempt --run-id --decision --reason` that validates current outcome, resolves personal authority, signs existing authorization schema in memory, normalizes it, and finalizes under one run lock.
- [ ] Preserve accept criteria, waiver, block, expiry, role, same-key, policy, receipt, state, and detached-envelope behavior.
- [ ] Add tests for accept/block/waive, expiry, signer failures, replay after trust change, conflicting replay, concurrent close, write failure, and zero host/provider calls.

**Verification:**
- [ ] `uv run --locked pytest -q tests/test_terminalization.py tests/test_managed.py tests/test_cli.py` from `packages/harness-core`
- Expected: first close finalizes atomically; exact duplicate replays; every failure leaves run bytes unchanged.

**Exit Criteria:**
- Core exposes one personal close operation adapting into existing signed terminalization rather than writing a second terminal state path.

### Task 3: Add launcher personal controller commands

**Purpose:**
- Provide stable one-command setup and closure through active runtime without changing provider decision routing.

**Specification Coverage:**
- Preserved runtime boundaries.
- Launcher command ownership.
- Structured subprocess errors.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py:_result_json`
- Inspect: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py:RuntimeManager.terminalize_attempt`
- Inspect: `packages/harness-core-launcher/src/harness_core_launcher/cli.py:main`
- Add: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py:RuntimeManager.invoke_active_core`
- Add: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py:RuntimeManager.controller_init`
- Add: `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py:RuntimeManager.close_attempt`
- Modify: `packages/harness-core-launcher/src/harness_core_launcher/cli.py:main`
- Modify: `packages/harness-core-launcher/tests/test_runtime_manager.py`
- Modify: `packages/harness-core-launcher/tests/test_loader.py`

**Dependencies:**
- Tasks 1 and 2 complete.
- Active-profile verification and host invocation remain unchanged.

**Steps:**
- [ ] Add active-core helper invoking `uv --project <active-host-root> run --locked python -m harness_core.managed` with control-plane timeout and sanitized runtime environment.
- [ ] Parse stdout only on zero exit and stderr only on nonzero exit; reject absent, malformed, non-object, or conflicting dual-JSON output with generic structured launcher failure.
- [ ] Route `terminalize-attempt`, `controller-init`, and `close` through active-core helper.
- [ ] Keep launcher `decision`, `run`, `capabilities`, and `preflight` on existing host invocation path.
- [ ] Add tests for exact argv, structured success/failure, malformed output, conflicting streams, no-host close, and host-bound retry/escalate decision.

**Verification:**
- [ ] `uv run --locked pytest -q tests/test_runtime_manager.py tests/test_loader.py` from `packages/harness-core-launcher`
- Expected: personal commands use core module; executable decisions still use host; every result has deterministic structured handling.

**Exit Criteria:**
- Launcher offers `controller-init` and `close` without console-shim or decision-admission regression.

### Task 4: Synchronize personal-use guidance

**Purpose:**
- Make canonical and generated instructions match approved personal trust model and commands.

**Specification Coverage:**
- Explicit personal local authority mode.
- Minimal compatibility change.
- Personal-use security boundary and non-goals.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `docs/operating_system/rules/multi-agent-orchestration-rule.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Generate: `AGENTS.md`
- Generate: `generated_agents`
- Generate: `C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit`

**Dependencies:**
- Tasks 1 through 3 complete with settled command names and result shapes.

**Steps:**
- [ ] Document same-user authority trade-off and personal-only scope.
- [ ] Document one-time `controller-init`, routine `close`, advanced detached compatibility, and production/shared-machine exclusion.
- [ ] Preserve host-bound retry/escalate rules and launcher-only managed provider invocation.
- [ ] Run `python scripts/sync_agent_adapters.py --all-platforms`, then `uv run --locked python scripts/sync_starter_kit.py`.
- [ ] Search generated guidance for stale external-only claims, routine manual-envelope instructions, bare host commands, and private material.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `uv run --locked python scripts/validate_starter_kit.py`
- Expected: canonical and generated guidance agree; no private key, copied identity value, or production-security claim is published.

**Exit Criteria:**
- Personal setup and close are documented once at canonical owners and derived everywhere through existing generators.

### Task 5: Verify and prepare release handoff

**Purpose:**
- Produce fresh release-ready proof without Git, package, runtime, or historical-run disposition.

**Specification Coverage:**
- Release-ready proof without release side effects.
- All backend verification claims and acceptance criteria.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `packages/harness-core`
- Verify: `packages/harness-core-launcher`
- Verify: `scripts/validate_repo_contracts.py`
- Inspect: `packages/harness-core/pyproject.toml`
- Inspect: `packages/harness-core-launcher/pyproject.toml`
- Inspect: `C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host/pyproject.toml`

**Dependencies:**
- Tasks 1 through 4 complete.
- No release authorization is implied by implementation completion.

**Steps:**
- [ ] Run focused core and launcher suites, generated checks, starter-kit validation, root contract validation, and whitespace checks.
- [ ] Confirm host source is unchanged and record release impact: core and launcher releases are required; host consumer pin/lock release is required only to stage released packages into new runtime profile.
- [ ] Confirm active runtime and historical runs `16`, `17`, and `19` remain unchanged.
- [ ] Stop with release-ready handoff listing verified commands, changed files, package impact, and separate release order: core, launcher, host consumer pin, launcher upgrade, doctor/capabilities/preflight, isolated close proof, then historical dispositions.

**Verification:**
- [ ] `uv run --locked pytest -q tests/test_terminal_authority.py tests/test_terminalization.py tests/test_managed.py tests/test_cli.py` from `packages/harness-core`
- [ ] `uv run --locked pytest -q tests/test_runtime_manager.py tests/test_loader.py` from `packages/harness-core-launcher`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `uv run --locked python scripts/validate_repo_contracts.py --fast`
- [ ] `git diff --check`
- Expected: all checks pass; no package release, runtime pointer, host source, or historical run changed.

**Exit Criteria:**
- Implementation is verified and release-ready; release and live closure await explicit separate authorization.

## Verification

- `uv run --locked pytest -q tests/test_terminal_authority.py tests/test_terminalization.py tests/test_managed.py tests/test_cli.py` from `packages/harness-core`
- `uv run --locked pytest -q tests/test_runtime_manager.py tests/test_loader.py` from `packages/harness-core-launcher`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `uv run --locked python scripts/validate_repo_contracts.py --fast`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. one fixed personal authority initializes and resolves without copied configuration
2. one core close transaction signs existing authorization schema and reuses existing finalizer
3. exact duplicate close replays before signer lookup and conflicting close rejects
4. launcher personal commands use active core while retry/escalate decision remains host-bound
5. structured core subprocess results have deterministic stream ownership
6. detached signing, current schemas, historical evidence, and runtime protocol remain compatible
7. canonical and generated guidance state personal-only trust trade-off and contain no private material
8. focused and repository-wide verification passes without release or live-run mutation

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified`. Commit, tag, push, package release, runtime upgrade, isolated
released-profile smoke proof, and historical-run disposition require separate
explicit authorization.
