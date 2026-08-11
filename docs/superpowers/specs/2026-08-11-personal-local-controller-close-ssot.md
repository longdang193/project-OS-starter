---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: personal-local-controller-close-ssot
targets:
  - packages/harness-core
  - packages/harness-core-launcher
  - docs/operating_system/rules/multi-agent-orchestration-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/procedures/harness-core-consumer-setup.md
  - docs/operating_system/procedures/managed-execution-adapter-contract.md
---

# Personal Local Controller Close SSOT

## Goal and Problem

### Problem

- current behavior or opportunity: personal harness operation requires issuer selection, rationale file, detached authorization file, outcome envelope construction, and a second terminalization command.
- affected users, systems, or maintainers: single local operator, `harness-core`, and `harness-core-launcher`.
- evidence: current terminalization verifies signed `controller_authorization/v1`, but routine closure remains file-oriented and launcher terminalization uses the active profile's `harness-core` console script.
- consequence of no change: routine probe closure costs more operator effort than personal-use risk warrants, encouraging stale pending runs and manual mistakes.

### Goal

- desired outcome: one explicit personal-controller setup command and one launcher close command perform local signed terminalization without manual authorization or envelope files.
- observable success: after one-time setup, `harness-core-launcher close` finalizes or replays an eligible outcome with existing authority and receipt contracts, while retry and escalation remain host-bound.

## Required Outcomes

### Outcome: One-time personal controller setup

- affected actor or system: local operator and core authority layer.
- required result: `harness-core-launcher controller-init` creates or validates one Ed25519 key at `~/.codex/harness-controller/controller-ed25519.pem` and one matching active `controller_approver` entry in `~/.codex/harness-authorities.toml`.
- success condition: repeated valid setup is idempotent; mismatch, revocation, ambiguity, unsafe repository placement, or conflicting partial state blocks without overwriting trusted material.

### Outcome: One-command signed close

- affected actor or system: launcher and core terminalization.
- required result: `harness-core-launcher close --harness-root <root> --run-id <id> --decision <accept|block|waive> --reason <text>` resolves personal key, binds current outcome, signs `controller_authorization/v1` in memory, and finalizes under run lock.
- success condition: no temporary rationale, authorization, or terminalization envelope file exists; `run.json` stores only normalized public authority and existing receipt data.

### Outcome: Preserved runtime boundaries

- affected actor or system: launcher, host, core, and provider runtime.
- required result: provider-free controller initialization and terminal close invoke active-profile core directly; launcher `decision` continues through host so executable retry and escalation receive current admission and preflight.
- success condition: close starts no provider session or host command, while successor decisions still require host adapter evidence.

### Outcome: Minimal compatibility change

- affected actor or system: existing operators, historical runs, and external signers.
- required result: detached `sign-controller-authorization` and `terminalize-attempt --input` remain supported; current authorization, outcome, receipt, packet, run, host, and provider schemas remain unchanged.
- success condition: old runs remain byte-identical until explicitly closed, and external/offline signing remains usable without personal mode.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| What owns final state? | Core validates authority and atomically writes receipt, decision, state history, and run record. | `packages/harness-core/src/harness_core/managed.py` | high | Reuse existing finalizer; add no parallel terminal writer. |
| What proves authorization? | `controller_authorization/v1` binds exact run, attempt, packet, outcome, decision, issuer, time, and rationale digest. | `packages/harness-core/src/harness_core/authority.py` | high | Keep schema and normalization unchanged. |
| Why must retry remain host-bound? | Core successor preparation requires injected adapter for current host admission and provider preflight. | `packages/harness-core/src/harness_core/managed.py` | high | Do not route generic launcher `decision` through core-only invocation. |
| What runtime selector exists? | Launcher verifies active profile and invokes its locked host project. | `packages/harness-core-launcher/src/harness_core_launcher/runtime_manager.py` | high | Reuse active profile; add no daemon or broker. |
| What is actual trust model? | Harness is personal and runs under one local user account. | approved user direction, 2026-08-11 | high | Local invocation authority is accepted trade-off, not external separation. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: <reason>`: Not applicable: existing Ed25519, registry, terminalization, launcher profile, and CLI mechanisms cover required behavior.
- validated scenarios and states: external signing and terminalization, exact authority validation, atomic receipt creation, active-profile invocation, structured nonzero host output, and retry runtime-binding symmetry.
- findings incorporated into approved behavior: keep executable decisions host-bound; replay before fresh authorization; make subprocess JSON stream ownership deterministic.
- rejected alternatives: signer broker, daemon, hardware token, Windows Hello, remote controller, multiple signer profiles, automatic rotation, and new terminalization schema.

### Scope

- included behavior: fixed personal key path, idempotent setup, in-memory signed close, deterministic replay, active-profile core invocation, structured errors, guidance updates, and detached compatibility.
- affected boundaries: core authority resolution, core terminalization CLI, launcher invocation, user-local authority files, generated agent guidance, and operator procedures.
- admissible cases: first/repeated setup, key-first partial setup, missing or malformed key, missing registry, unknown/revoked/ambiguous match, accept/block/waive, expiry, replay, conflicting replay, malformed subprocess output, and incompatible active profile.
- compatibility expectation: no host API, provider contract, request API, packet API, run API, outcome schema, authorization schema, or receipt schema change.

### Non-Goals

- production multi-user security
- remote or background controller service
- interactive OS approval, hardware-backed keys, or credential-vault integration
- multiple personal controllers or rotation workflow
- automatic selection of ambiguous terminal decisions
- provider dispatch, retry, escalation, or successor creation through core-only invocation
- release, runtime activation, or historical-run disposition during implementation

### Requirements and Behavioral Contract

#### Requirement: Fixed personal authority identity

- trigger or actor: local operator runs `controller-init`.
- preconditions: active launcher profile is trusted; repository root is not used for private material.
- required behavior: core uses fixed key path, derives fingerprint, and uses key ID `personal-local-<first-16-fingerprint-hex>` with principal `personal-local-controller` and role `controller_approver`.
- output or state change: private PEM and public registry entry are written atomically per file; output contains only status, key ID, fingerprint, and registry digest.
- failure behavior: no existing private key or registry entry is overwritten; mismatched, revoked, duplicate, or ambiguous identity blocks.
- observable acceptance: valid repeated setup returns `configured` or `replayed` with identical public identity.

#### Requirement: Recover bounded partial setup

- trigger or actor: setup reruns after interruption.
- preconditions: private key exists at fixed path but matching registry entry is absent.
- required behavior: setup derives public identity from existing key and adds only its deterministic registry entry after validating registry.
- output or state change: registry gains one matching active entry; private key remains byte-identical.
- failure behavior: registry entry without private key, matching revoked entry, conflicting key ID, or multiple matching entries blocks without replacement.
- observable acceptance: key-first interruption recovers; unsafe ambiguity never self-heals.

#### Requirement: Atomic personal close

- trigger or actor: caller runs launcher `close` with run, terminal decision, and non-empty reason.
- preconditions: run has current outcome allowing requested decision; no receipt exists; personal authority resolves uniquely and actively.
- required behavior: under one run lock, core validates policy and reason bounds, binds current run/attempt/packet/outcome, signs authorization in memory, normalizes it through existing verifier, and invokes existing finalizer.
- output or state change: one existing `attempt_terminal_receipt/v3` and final state are persisted atomically.
- failure behavior: signer, trust, policy, outcome, decision, expiry, or write failure leaves `run.json` byte-identical.
- observable acceptance: command returns structured finalized or blocked result; host/provider methods are never called.

#### Requirement: Deterministic replay

- trigger or actor: identical close command repeats after finalization.
- preconditions: existing receipt matches outcome, decision, issuer, reason SHA-256, and reason length.
- required behavior: core returns stored terminal ID without loading key, rereading registry, signing, or writing run state.
- output or state change: structured `replayed` result; run bytes unchanged.
- failure behavior: different decision, reason, outcome, or authority identity returns `attempt_already_finalized`.
- observable acceptance: replay survives later key removal, registry revocation, and policy change.

#### Requirement: Launcher command ownership

- trigger or actor: launcher receives `controller-init`, `close`, `terminalize-attempt`, or `decision`.
- preconditions: active runtime profile verifies.
- required behavior: provider-free core commands use one `invoke_active_core` helper with `uv --project <active-host-root> run --locked python -m harness_core.managed`; `decision` continues through existing host invocation.
- output or state change: zero-exit core JSON comes from stdout; nonzero core JSON comes from stderr.
- failure behavior: invalid authoritative-stream JSON returns generic structured launcher failure; conflicting dual-JSON output is rejected.
- observable acceptance: retry/escalate reach host adapter; close never reaches host.

### Constraints and Alternatives

- constraint: personal mode delegates controller authority to any process running as same local user that can invoke launcher and read personal key.
- constraint: user-profile filesystem protection is accepted; no custom ACL manager is added.
- alternative: external signer broker.
  - benefit: stronger caller/approver separation.
  - trade-off: service lifecycle, protocol, setup, and recovery maintenance.
  - reason accepted or rejected: rejected for personal-use scope.
- alternative: fixed key without public registry.
  - benefit: one fewer file.
  - trade-off: removes current trust, revocation, role, and audit SSOT.
  - reason accepted or rejected: rejected.
- alternative: core-only generic `decision` invocation.
  - benefit: one launcher subprocess helper for every command.
  - trade-off: bypasses host adapter required by retry and escalation.
  - reason accepted or rejected: rejected.

## Design Decisions

### Decision: Explicit personal local authority mode

- context: one local operator wants minimal management rather than production-grade separation.
- selected approach: core may load one fixed personal private key and sign terminal authorization only through explicit setup and close commands.
- rationale: reuses existing cryptography, registry, authorization, finalizer, launcher profile, and receipt contracts with no new service or schema.
- alternatives considered: detached-only signing, external broker, OS credential integration, unattended background controller.
- accepted trade-offs: same-user processes can exercise controller authority; mode is unsuitable for production or shared machines.
- affected owners and boundaries: private key remains user-local; registry remains public trust SSOT; core owns validation/signing/finalization; launcher owns stable invocation.

### Decision: Convention over signer configuration

- context: signer-selection file adds another SSOT and setup step.
- selected approach: use one fixed private key path and derive registry identity from fingerprint.
- rationale: removes copied issuer, principal, fingerprint, and path configuration.
- alternatives considered: `harness-controller.toml`, environment variables, CLI key path on every close.
- accepted trade-offs: one personal key only; rotation requires separate approved work.
- affected owners and boundaries: key path convention belongs to core authority module; public identity belongs to registry.

### Decision: Existing finalizer and schemas remain authoritative

- context: convenience must not create a second terminal state machine.
- selected approach: personal close creates existing authorization object in memory and calls shared lock-held finalization branch.
- rationale: preserves policy, expiry, acceptance criteria, receipt, state, and audit behavior.
- alternatives considered: unsigned local flag, raw actor field, direct final-state write.
- accepted trade-offs: personal close remains subject to current terminalization restrictions.
- affected owners and boundaries: `terminalize_attempt` remains compatibility authority; personal close adapts into it.

### Compatibility, Migration, and Risk

- old behavior: external/offline signer produces detached authorization and caller submits envelope.
- new behavior: optional personal commands initialize one local authority and create equivalent signed authorization in memory.
- compatibility boundary: detached commands and historical evidence remain supported; current schemas and APIs remain unchanged.
- migration or backfill: no automatic migration of environment scripts, private keys, runs, or historical authority. Existing valid fixed-path key may be registered by setup.
- rollout and rollback: release core and launcher through existing profile procedure; retain detached path as rollback. Removing personal key disables convenience mode without changing runs.
- deprecation or consumer impact: manual detached flow becomes advanced compatibility guidance, not removed behavior.
- risk:
  - same-user agent or process can close runs.
  - mitigation: explicit personal-only documentation, fixed user-local key, registry validation, exact outcome binding, and auditable receipt.
  - partial setup can leave one file written.
  - mitigation: recover only key-first state; block registry-only or conflicting state.

## Invariants and Edge Cases

### Invariants

- `run.json` remains sole mutable run-state SSOT.
- every attempt packet, claim, terminal observation, and prior receipt remains immutable.
- one core finalizer remains sole writer for `accept`, `block`, and `waive`.
- one public authority registry remains trust SSOT.
- private key bytes never enter repository, packet, request, run record, logs, structured output, or generated guidance.
- personal close never invokes host or provider work.
- retry and escalation always use host adapter admission and current runtime binding.
- failed setup or close does not partially mutate run state.

### Edge Cases

- empty or minimal input: missing decision, empty reason, missing run, or missing outcome blocks.
- normal and large input: reason uses existing byte limits and stores only digest and length.
- duplicate, missing, malformed, or unsupported data: malformed key/registry, duplicate match, unsupported decision, or invalid JSON blocks with stable structured error.
- retry, cancellation, timeout, partial failure, or concurrency: run lock serializes close; conflicting concurrent close produces one receipt and one replay/conflict result; setup recovers only safe key-first interruption.
- migration or mixed-version state: old runtime lacks commands and reports structured unavailable behavior; old runs remain readable and closable after profile upgrade.
- generated-source consistency: canonical root agent template changes regenerate adapter surfaces and starter-kit output through existing scripts.
- security boundary: personal mode grants same-user invocation authority and makes no production-security claim.

## Validation Plan

### Backend Verification Claims

- direct boundary: call core personal setup and close APIs against temporary home, registry, key, and run fixtures.
- important success and failure behavior: prove first setup, replayed setup, partial recovery, mismatch/revocation/ambiguity, accept/block/waive, expired outcome rules, signer failure, and forbidden decision.
- final state or side effects: assert exact key/registry contents, one receipt, final state, decision history, no provider calls, and byte-identical failed run/config paths.
- rollback, retry, duplicate, or idempotency behavior: prove same close replays after trust changes; conflicting close rejects; executable decision still requires host adapter.
- canonical contract and conformance proof: current authorization/outcome/receipt schemas and runtime protocol profile remain unchanged.
- real dependencies requiring proof: temporary filesystem, Ed25519 key generation/loading, public registry, subprocess result streams, run lock, and atomic writes.
- representative-operation trace mechanism: launcher close through active profile produces one core receipt with no host invocation captured by test runner.
- performance claim and threshold, or `Not applicable: <reason>`: Not applicable: no performance claim.

### Acceptance Criterion: Personal setup needs no manual identity values

- setup or precondition: temporary user home with no controller key or authority registry.
- action: run launcher `controller-init` twice.
- expected result: first call configures one key/entry; second replays same identity; no issuer, principal, fingerprint, path, or public-key input is required.
- failure condition: output contains private material, second call changes files, or conflicting state is overwritten.
- proof method: focused core and launcher CLI tests.
- expected evidence: structured configured/replayed results and byte comparisons.

### Acceptance Criterion: Routine close is one provider-free command

- setup or precondition: configured personal controller and awaiting eligible outcome.
- action: run launcher close with decision and reason, then repeat exact command.
- expected result: first call finalizes; second replays same terminal ID; no temporary files or host/provider calls occur.
- failure condition: authorization file is required, receipt differs, host starts, or run changes on replay.
- proof method: direct core test plus captured launcher subprocess test.
- expected evidence: one receipt, identical run bytes after replay, and core-only argv.

### Acceptance Criterion: Successor decisions preserve runtime admission

- setup or precondition: retryable or escalatable outcome and active profile.
- action: submit launcher `decision` for retry or escalation.
- expected result: launcher invokes host; host supplies adapter; core prepares successor from current profile.
- failure condition: launcher invokes core-only decision, prior runtime binding is cloned, or packet exists after incompatible preflight.
- proof method: launcher argv tests and existing managed retry symmetry tests.
- expected evidence: captured host command and fresh successor binding assertions.

## Completion Criteria

Specification is complete when:

1. personal-use trust model and accepted same-user authority trade-off are explicit
2. setup, close, replay, failure, compatibility, and launcher ownership contracts are unambiguous
3. existing registry, authorization, finalizer, receipt, and runtime profile remain SSOT
4. broker, daemon, remote, multi-signer, rotation, and production-security work remain excluded
5. every required outcome maps to direct backend and launcher proof
6. implementation sequencing remains in linked implementation plan
