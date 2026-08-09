---
artifact_type: plan
status: completed
layer: change
template_id: implementation-plan
title: Terminalization Authority and Receipt SSOT Plan
date: 2026-08-09
spec_ref: docs/superpowers/specs/2026-08-09-terminalization-authority-receipt-ssot.md
owners:
  - harness-core
---

# Terminalization Authority and Receipt SSOT Plan

## Execution Status

Core release `harness-core-v0.1.22` and `codex-harness-host` consumer-runtime
handoff are complete. Host provenance pins the immutable release tag.

## Goal

Deliver core-owned, auditable terminal finalization. `attempt.outcome` becomes v2 decision SSOT; `terminalize_attempt` becomes sole final-state writer; block-only outcomes auto-finalize; ambiguous outcomes require signed authority; one user-local authority registry replaces active old attester configuration.

## Implementation Outcomes

### Outcome v2 and receipt v3

`run.json` records outcome ID, digest, deadline, policy snapshot, final authority, and terminal receipt atomically. Existing v2 terminal records remain readable and unchanged.

### Policy and authority boundary

Policy schema `9` configures generic one-decision auto-finalization, bounded pending outcome lifetime, controller roles, and same-key pairing rule. Core validates current public authority registry with existing Ed25519 dependency; host source stays unchanged.

### Operator and consumer compatibility

CLI accepts canonical terminalization envelopes, rejects `--auto-block`, keeps one translation-only legacy-evidence wrapper for readable packet API `8` attempts, and offers explicit registry migration. The wrapper can be removed only in a separate compatibility change that drops packet API `8` read support after a migration audit confirms no unleased packet-8 legacy attempts remain. Canonical docs and generated agent surfaces describe one core terminalization path.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `external authorization`
- Parallel ownership: none; `managed.py`, policy, schemas, and terminal tests share contracts.
- Sequential fallback: complete authority/config contract, then core state transition, then CLI/docs, then full proof.

## Task Breakdown

### Task 1: Add policy and public authority boundary

**Purpose:**
- Create one validated current authority registry and policy schema `9` without changing host lifecycle.

**Specification Coverage:**
- Signed controller authority and one public registry.
- One registry with explicit cutover.
- Policy auto-finalization matrix.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/legacy_cleanup.py:115`
- Inspect: `packages/harness-core/src/harness_core/config_validation.py:497`
- Inspect: `packages/harness-core/src/harness_core/compatibility.py:59`
- Modify: `packages/harness-core/src/harness_core/authority.py` (new)
- Modify: `packages/harness-core/src/harness_core/legacy_cleanup.py:173`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:561`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:61`
- Modify: `packages/harness-core/src/harness_core/api.py:1`
- Modify: `repo_config/harness.yaml:1`
- Add: `packages/harness-core/tests/test_terminal_authority.py`
- Modify: `packages/harness-core/tests/test_config_validation.py`
- Modify: `packages/harness-core/tests/test_legacy_cleanup.py`

**Dependencies:**
- Approved detailed specification.
- No host source change.

**Steps:**
- [x] Write direct failure-first tests for malformed registry, private fields, duplicate key IDs, wrong roles, revoked keys, key fingerprint, authority time bounds, issuer pairing, migration collision, no-old-registry fallback, and shared canonical signed-document bytes.
- [x] Add strict `harness-authorities.toml` parser, canonical digest, key fingerprint, role/status validation, exact-field controller-authorization normalizer, detached Ed25519 verifier, and target-safe registry migration helper.
- [x] Make `authority.py` sole owner for signed-document canonical JSON, base64url encoding/decoding, Ed25519 key validation, signatures, and key fingerprints. Rewire legacy cleanup to consume those primitives; retain legacy attestation schema and exact process-identity validation.
- [x] Add `terminalization` policy fields: `auto_finalize_single_terminal_outcome`, `pending_outcome_ttl_seconds`, controller authorization roles, clock/bounds, and same-key evidence/approval default denial. Advance policy schema constant and validation from `8` to `9`; keep packet API `8`, run API `2`, host API `7`.
- [x] Route new legacy cleanup signing and validation through current authority registry. Keep finalized historical replay free of registry lookup; reject all new-validation fallback to old registry.
- [x] Add deterministic migration from `harness-attesters.toml` to target registry. Refuse conflicting target without explicit overwrite, atomically replace only validated target, and return opaque count/digest.

**Verification:**
- [x] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminal_authority.py packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_legacy_cleanup.py -q`
- Expected: valid registry/authority and migration pass; every malformed or untrusted path rejects without replacing configuration or mutating run state.

**Exit Criteria:**
- Current policy validates at schema `9`; one public authority registry and controller-authorization verifier exist; legacy cleanup retains bounded signed proof semantics.

### Task 2: Unify outcome recording and terminal finalization

**Purpose:**
- Make outcome v2 the universal decision subject and receipt v3 the only final-state authority.

**Specification Coverage:**
- One outcome SSOT.
- One finalization operation and receipt.
- Bounded policy autonomy.
- Outcome expiry, idempotency, and atomicity.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/managed.py:2101`
- Inspect: `packages/harness-core/src/harness_core/managed.py:2309`
- Inspect: `packages/harness-core/src/harness_core/managed.py:2775`
- Inspect: `packages/harness-core/src/harness_core/managed.py:3487`
- Inspect: `packages/harness-core/src/harness_core/managed.py:4365`
- Modify: `packages/harness-core/src/harness_core/managed.py:_set_outcome`
- Modify: `packages/harness-core/src/harness_core/managed.py:terminalize_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:apply_controller_decision`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_failure`
- Modify: `packages/harness-core/src/harness_core/managed.py:_terminalize_collected_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:recover_stranded_run`
- Modify: `packages/harness-core/tests/test_terminalization.py`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `packages/harness-core/tests/test_legacy_cleanup.py`

**Dependencies:**
- Task 1 complete.
- Current tests establish existing reason and allowed-decision semantics.

**Steps:**
- [x] Write regression tests before behavior changes. Cover all outcome sources, auto-finalize only single block, ambiguous outcome pending, exact signed accept/block/waive, expiry, post-expiry block flag, invalid authority, conflicting finalization, replay after registry/policy change, injected write failure, and concurrent finalizers.
- [x] Add one shared outcome recorder. It computes exact outcome v2 ID/digest, immutable deadline, policy snapshot, and bounded outcome history. Replace direct unversioned `_set_outcome` persistence across terminal, verification, pre-dispatch, child, recovery, and dispatch-failure paths.
- [x] Add one internal finalization helper called under existing run lock. It validates outcome form, policy-auto eligibility, authority where required, expiry rules, receipt digest/ID, and writes receipt v3, decision/history, state transition, and revision together.
- [x] Refactor `terminalize_attempt` evidence form to normalize existing source union, record/reuse canonical outcome, then invoke same helper only for exact one-terminal-decision policy outcome. Add outcome form for external controller authorization.
- [x] Refactor terminal `accept`, `block`, and `waive` in `apply_controller_decision` into a transport shim to outcome-form terminalization. Preserve retry, escalation, and request-approval behavior unchanged.
- [x] Refactor recovery, collected observations, retry exhaustion, and every direct terminal transition to use finalization helper. Keep `orphaned` nonterminal and preserve no-replay recovery behavior.

**Verification:**
- [x] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_legacy_cleanup.py -q`
- Expected: every new terminal state has one v3 receipt; rejected calls leave `run.json` byte-identical; existing retry/escalation behavior remains nonterminal.

**Exit Criteria:**
- No direct final `accept`, `block`, or `waive` writer remains outside shared finalizer; all decision sources have outcome v2 proof; automatic legacy block uses one write.

### Task 3: Expose canonical CLI and migration behavior

**Purpose:**
- Replace split auto-block transport with one envelope command and explicit user-local registry migration.

**Specification Coverage:**
- CLI, API, and documentation compatibility.
- One registry cutover.
- Terminal receipt replay and historical-read behavior.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `packages/harness-core/src/harness_core/managed.py:4442`
- Inspect: `packages/harness-core/src/harness_core/cli.py:1`
- Modify: `packages/harness-core/src/harness_core/managed.py:main`
- Modify: `packages/harness-core/src/harness_core/api.py:1`
- Modify: `packages/harness-core/src/harness_core/cli.py:1`
- Modify: `packages/harness-core/tests/test_legacy_cleanup.py:246`
- Modify: `packages/harness-core/tests/test_terminalization.py`
- Modify: `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Tasks 1 and 2 complete.

**Steps:**
- [x] Add failing CLI tests for canonical envelope, legacy wrapper, rejected auto-block, rejected raw actor, controller authorization issuance/signing, migration dry-run/collision, terminal decision shim, JSON result, and exit code.
- [x] Add `terminalize-attempt --run-id <id> --input <terminalization-envelope.json>` as canonical transport. Parse exact evidence/outcome form before core call.
- [x] Reject `--auto-block`. Keep `--evidence` only as a translation-only wrapper for readable packet-8 legacy cleanup evidence; reject any nonlegacy payload or mixed command fields. Remove it only with a separate compatibility change that drops packet-8 read support after a recorded migration audit finds no unleased packet-8 legacy attempts.
- [x] Add external-only `sign-controller-authorization`. It derives exact current run, attempt, packet, and outcome bindings from an `awaiting_decision` run; accepts issuer ID, terminal decision, rationale file, bounded expiry, and private-key file; writes signed JSON only outside repository and run storage. It never terminalizes or edits `run.json`. Verify signer key/role against public registry before output and return only opaque authorization digest and ID.
- [x] Add `migrate-harness-authorities` CLI command backed only by Task 1 migration helper. It performs no run mutation and never reads private key material.
- [x] Route terminal kinds from generic `decision` command through core terminalization envelope. Keep generic nonterminal routing, result shapes, and error exit semantics intact.
- [x] Update exported API symbols and runtime identity output. Do not advance packet API, run API, host API, or host terminal-observation contract.

**Verification:**
- [x] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_legacy_cleanup.py packages/harness-core/tests/test_managed.py -q`
- Expected: one terminal CLI path reaches core finalizer; no CLI path writes terminal state without receipt/authority validation.

**Exit Criteria:**
- Canonical CLI and API use one terminalization operation; migration is explicit and safe; old auto-block mutation is unavailable.

### Task 4: Align release metadata and canonical guidance

**Purpose:**
- Ship coherent core contract, policy, architecture docs, and generated agent guidance without changing host lifecycle ownership.

**Specification Coverage:**
- Compatibility, migration, and risk.
- Amend authority portion of terminalization architecture.
- Generated-source consistency.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/pyproject.toml:7`
- Modify: `uv.lock:163`
- Modify: `docs/superpowers/specs/2026-08-09-unified-attempt-terminalization-ssot.md:96`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md:13`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md:400`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md:25`
- Generated: `AGENTS.md:1`
- Generated: `generated_agents/**`
- Generated: `generated_exports/project-OS-starter-kit/**`
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `scripts/sync_starter_kit.py`
- Post-release consumer handoff: `../codex-harness-host/pyproject.toml`
- Post-release consumer handoff: `../codex-harness-host/uv.lock`

**Dependencies:**
- Tasks 1 through 3 complete and focused tests passing.

**Steps:**
- [x] Bump `harness-core` patch release and refresh lock metadata after behavior and tests stabilize. Do not change packet, run, host, or provider contract versions.
- [x] Amend older terminalization specification only where it currently describes v2 terminal evidence, legacy attester registry, or `--auto-block`; link authority/receipt behavior to approved SSOT spec without duplicating lifecycle rules.
- [x] Update canonical root agent template: outcome v2 is decision subject, terminalize envelope is sole final mutation, policy auto is one-decision only, registry path/cutover is current, controller authorization is external, and auto-block is forbidden.
- [x] Regenerate derived agent adapters from canonical template, then sync starter-kit outputs only after canonical source changes.
- [x] Update both canonical consumer procedures: one registry, external controller signer, canonical input envelope, packet-8 wrapper lifetime, and retired `--auto-block`. Regenerate derived agent adapters and starter-kit outputs only from their canonical sources.
- [x] Split local core proof from post-release host handoff. Local completion proves package behavior before release. After separate Git/release authorization creates the bumped `harness-core-v<version>` tag, host owner updates `../codex-harness-host/pyproject.toml` and `../codex-harness-host/uv.lock` to that immutable tag, commits host provenance separately, then runs locked identity, capabilities, and preflight. Host source remains unchanged unless this proof exposes incompatibility.

**Verification:**
- [x] `uv lock`
- [x] `uv run --locked python scripts/sync_agent_adapters.py`
- [x] `uv run --locked python scripts/sync_agent_adapters.py --check`
- [x] `uv run --locked python scripts/sync_starter_kit.py`
- [x] `uv run --locked python scripts/validate_repo_contracts.py`
- Expected: lock, generated adapters, starter kit, and canonical docs agree; no generated file is hand-edited. Post-release host pin update is outside this workspace and requires separate authorization.

**Exit Criteria:**
- Core release metadata and all canonical/generated guidance describe one terminal authority path. Local core completion does not claim host alignment; host handoff requires released immutable tag, separate host pin commit, and runtime proof.

## Verification

### Focused Backend Proof

- [x] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_terminal_authority.py packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_terminalization.py packages/harness-core/tests/test_legacy_cleanup.py packages/harness-core/tests/test_managed.py -q`
- Expected: outcome source matrix, policy auto, authority validation, expiry, replay, concurrency, migration, CLI, and historical readers pass.

### Full Repository Proof

- [x] `uv run --locked pytest packages/harness-core/tests -q`
- [x] `uv run --locked python scripts/validate_template_required_sections.py`
- [x] `uv run --locked python scripts/validate_repo_contracts.py`
- [x] `git diff --check`
- Expected: no core regression, template violation, repository-contract drift, or whitespace error.

### Consumer Runtime Proof

- [x] After separate core tag publication and host pin/lock commit, run in `../codex-harness-host`: `uv sync --locked`
- [x] In `../codex-harness-host`: `uv run --locked harness-core --identity`
- [x] In `../codex-harness-host`: `uv run --locked codex-harness-host capabilities`
- [x] In `../codex-harness-host`: `uv run --locked codex-harness-host preflight`
- Expected: released core reports policy schema `9`, packet API `8`; host reports existing API/contract `7` and ready preflight. No host `run.json` or lifecycle change is required. This is post-release handoff proof, not local core completion proof.

## Completion Criteria

1. all outcome writers use v2 identity, digest, deadline, and policy snapshot
2. all new final states use one v3 receipt written atomically by core
3. one-decision terminal outcomes auto-finalize; all discretionary final decisions require exact signed authority
4. current validation reads one authority registry with deterministic migration and no old fallback
5. legacy cleanup preserves signed exact-identity requirements and loses only split auto-block transport
6. historical records remain unchanged and report computed missing provenance
7. packet API `8`, run API `2`, host API `7`, and host lifecycle ownership remain stable
8. focused, full, generated-surface, and consumer-runtime proof pass before release handoff
