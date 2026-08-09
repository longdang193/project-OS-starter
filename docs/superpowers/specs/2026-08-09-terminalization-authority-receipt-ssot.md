---
artifact_type: spec
status: active
layer: change
template_id: detailed-specification
title: Terminalization Authority and Receipt SSOT
date: 2026-08-09
owners:
  - harness-core
---

# Terminalization Authority and Receipt SSOT

## Goal and Problem

### Problem

- current behavior or opportunity: `harness-core` records terminal evidence in `terminalize_attempt`, then records `accept`, `block`, or `waive` through a separate `apply_controller_decision` write. Core-only failures also create `awaiting_decision` without terminal evidence. Neither path persists decision authority, authenticated approver identity, approval reference, or trust snapshot.
- affected users, systems, or maintainers: controllers, external cleanup operators, agents, audit reviewers, `harness-core`, and every managed attempt reaching a final run state.
- evidence: `terminalize_attempt` writes `attempt_terminal_evidence/v2` and `apply_controller_decision` only persists caller-supplied decision plus timestamp. Approval-gate, unavailable-mode, plan-binding, child, dispatch, verification, and terminal-evidence paths converge on `attempt.outcome` before final decision.
- consequence of no change: terminal records cannot prove who or what authorized final state; `--auto-block` uses two run writes; authority only on terminal-evidence paths would create a parallel pending system and exclude valid core-only outcomes.

### Goal

- desired outcome: `attempt.outcome` is single decision subject for every `awaiting_decision` attempt. One core terminalization operation finalizes any eligible outcome with policy-derived or externally authorized disposition and writes one atomic receipt.
- observable success: every new final `accepted`, `blocked`, or `unvalidated` state has `attempt_terminal_receipt/v3` bound to immutable outcome digest, evidence references, decision, authority mode, policy digest, and applicable trust snapshot. Historical records remain byte-identical and report missing provenance.

## Required Outcomes

### Outcome: One outcome SSOT

- affected actor or system: core outcome producers, controllers, and audit readers.
- required result: every newly written `attempt.outcome` uses `attempt_outcome/v2` with `outcome_id`, `outcome_digest`, `recorded_at`, `valid_until`, reason, allowed decisions, evidence references, bounded detail, and policy digest. Core computes identity from run ID, attempt ID, packet digest, and normalized outcome fields.
- success condition: terminal evidence, verification, provider failure, timeout, cancellation, host crash, orphan and stranded recovery, pre-dispatch/core outcomes, child failure, and signed legacy cleanup all use this one outcome shape before final decision.

### Outcome: One finalization operation and receipt

- affected actor or system: controller API, CLI, run state, and audit tooling.
- required result: `terminalize_attempt(root, run_id, envelope)` is sole core mutation for `accept`, `block`, and `waive`. It writes `attempt_terminal_receipt/v3` and final state in one run-lock transaction. `apply_controller_decision` retains only nonterminal `retry`, `escalate`, and `request_approval`; terminal kinds delegate to `terminalize_attempt`.
- success condition: no CLI, recovery helper, or internal outcome path writes a terminal decision or final run state directly.

### Outcome: Bounded policy autonomy

- affected actor or system: agents, controllers, and policy owners.
- required result: policy auto-finalizes only when outcome has exactly one allowed decision and it is terminal. Core derives decision; caller never submits it. Multi-decision outcomes require external controller authorization for `accept`, `block`, or `waive`.
- success condition: block-only conditions such as legacy cleanup, cancellation, writer-completion-missing, host crash, and stranded recovery finalize atomically. Ambiguous outcomes cannot auto-accept, auto-waive, or skip retry/escalation choices.

### Outcome: Signed controller authority and one public registry

- affected actor or system: external approvers, core verifier, and local trusted configuration.
- required result: `controller_authorization/v1` is Ed25519-signed and exact-field. It binds run ID, attempt ID, packet digest, outcome ID, outcome digest, requested decision, authorization ID, issuer key ID, issued time, expiry, reason SHA-256 and length, and signature. `~/.codex/harness-authorities.toml` is sole active public-key registry for current validation.
- success condition: core derives principal from active registry entry; it rejects raw actor flags, unknown/revoked keys, wrong roles, stale or future authority, mismatched binding, unsupported decisions, and same-key evidence-plus-approval unless policy permits pairing.

### Outcome: Deterministic audit and migration

- affected actor or system: run readers, historical runs, release consumers, and reviewers.
- required result: run API remains `2`; receipt schema advances independently to v3. Existing v2 terminal records and decisions remain readable without rewrite. Readers expose computed `audit_provenance: "missing"` when authority snapshot is absent.
- success condition: new receipt replay is idempotent after policy or key changes; no historical approver, trust snapshot, or evidence freshness fact is invented.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| What owns terminal evidence | `terminalize_attempt` normalizes host, recovery, stranded, and legacy cleanup evidence, writes v2 terminal record, sets outcome, and moves to `awaiting_decision`. | `packages/harness-core/src/harness_core/managed.py` | high | Preserve evidence ownership in core; final authority joins outcome. |
| What owns final decision | `apply_controller_decision` reads `attempt.outcome`, stamps `at`, stores decision history, and changes final state. | `packages/harness-core/src/harness_core/managed.py` | high | Route final decisions through one authority-aware operation. |
| Which paths lack terminal evidence | Approval gate, unavailable mode, plan binding, child status, dispatch failure, and verification write outcomes before decisions. | `packages/harness-core/src/harness_core/managed.py` | high | Outcome, not terminal evidence, is universal decision subject. |
| What proof exists for external operators | Legacy cleanup validates Ed25519 public key, issuer state/role, exact subject binding, timestamp bounds, scope, and exact process identities. | `packages/harness-core/src/harness_core/legacy_cleanup.py` | high | Reuse canonical JSON and Ed25519 verification rules. |
| What policy bound exists | Retry policy has approval TTL but outcome lacks immutable deadline. | `repo_config/harness.yaml`; `packages/harness-core/src/harness_core/managed.py` | high | Add terminalization pending-outcome TTL and snapshot it in outcome. |
| What compatibility boundary exists | Packet API is `8`, run API `2`, policy schema `8`, host contract `7`. | `packages/harness-core/src/harness_core/compatibility.py` | high | Keep packet and host API unchanged; advance policy schema only. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: source and runtime audit reproduce defect without UI prototype`.
- validated scenarios and states: signed legacy cleanup was valid at finalization but record omitted authority; post-terminal absence proof was verification-only; source confirms auto-block used two writes.
- findings incorporated into approved behavior: outcome is universal pending record; policy auto requires exact one decision; manual authority binds outcome digest; receipt snapshots validation context.
- rejected alternatives: separate pending-terminalization state, raw actor flags, host authority, PID-only proof, dual active registries, private-key storage, and retroactive audit backfill.

### Scope

- included behavior: policy schema, outcome model, terminalization API, CLI transport, public authority registry, legacy cleanup validation, receipt readers, tests, docs, and generated agent guidance.
- affected boundaries: core owns state and authority validation; host remains provider lifecycle and evidence owner; external operators keep private keys outside repository and agent workspace.
- admissible cases: normal completion, verification failure, provider failure, timeout, cancellation, host crash, orphan recovery, stranded recovery, pre-dispatch/core outcomes, child failure, and signed legacy cleanup.
- compatibility expectation: packet API `8`, host API `7`, host contract `7`, and run API `2` remain. Policy schema becomes `9`; current validation requires authority registry cutover.

### Non-Goals

- host process lifecycle, process containment, host observation schema, or host API changes.
- agent-minted approval, anonymous controller identity, auto-success, auto-waiver, retry/escalation automation, successor creation changes, or historical run rewrite.
- private keys, raw rationale, raw provider errors, or user-local registry values in repository policy, packets, or `run.json`.

### Requirements and Behavioral Contract

#### Requirement: Canonical outcome identity

- trigger or actor: every core path that calls `_set_outcome`.
- preconditions: active attempt has immutable packet and exact subject.
- required behavior: core writes `attempt_outcome/v2`; digest includes subject, normalized reason, ordered allowed decisions, ordered evidence references, bounded detail, policy digest, and deadline. Outcome replacement before finalization appends a distinct history item; no replacement relation is inferred. Replacement after final receipt rejects.
- output or state change: every pending outcome has one ID, digest, recorded time, and deadline.
- failure behavior: malformed reason, unsupported decision, invalid deadline, or inconsistent duplicate digest rejects before run write.
- observable acceptance: every `awaiting_decision` fixture exposes same outcome fields regardless of source.

#### Requirement: `terminalize_attempt(envelope)`

- trigger or actor: controller after core outcome exists, or host/controller after evidence becomes available.
- preconditions: exactly one envelope form is supplied:
  - evidence form: schema ID, attempt ID, and exactly one admissible evidence source; no decision or authorization;
  - outcome form: schema ID, attempt ID, outcome ID, outcome digest, requested terminal decision, and controller authorization; no evidence.
- required behavior: evidence form normalizes evidence, records or reuses outcome, then auto-finalizes only when policy permits. Outcome form verifies current pending outcome and authorization, then finalizes allowed decision.
- output or state change: terminal finalization writes receipt, decision, decision history, transition, and revision in one lock-held write. Non-auto evidence returns `awaiting_decision` without final receipt.
- failure behavior: source mixing, caller-supplied final state/digest, unknown outcome, stale digest, unauthorized decision, invalid signature/time, or final conflict rejects with no partial receipt or transition.
- observable acceptance: legacy cleanup no longer needs `--auto-block`; same operation handles terminal evidence and core-only outcomes.

#### Requirement: Policy auto-finalization matrix

- trigger or actor: core immediately after a newly recorded or replayed outcome.
- preconditions: policy schema `9` defines `terminalization.auto_finalize_single_terminal_outcome`, pending-outcome TTL, controller roles, and same-key pairing rule.
- required behavior: when enabled and `allowed_decisions` contains exactly one value in `{accept, block, waive}`, core derives and finalizes it. Any other list remains pending and needs external authorization for terminal disposition.
- output or state change: policy-auto receipt records `authority.mode: "policy_auto"`, null principal by design, policy digest, outcome digest, and derived decision.
- failure behavior: absent, invalid, ambiguous, or disabled policy rejects auto-finalization and leaves valid outcome pending.
- observable acceptance: legacy cleanup auto-blocks; `verification_passed` with `accept` and `block` stays pending; retryable failure with retry/escalate/block stays pending.

#### Requirement: Outcome expiry and ordering

- trigger or actor: core records non-auto outcome or receives outcome-form envelope.
- preconditions: policy gives positive `pending_outcome_ttl_seconds`; external authority has valid issue and expiry times.
- required behavior: `valid_until` is recorded time plus immutable policy TTL, capped by source evidence expiry. Core finalizes `accept` or `waive` only at or before deadline. It accepts `block` after deadline only with fresh controller authorization and records `outcome_expired: true`. Legacy cleanup is block-only policy-auto and finalizes in evidence transaction before attestation expiry.
- output or state change: receipt records deadline, finalization time, and stale-outcome block flag.
- failure behavior: expired acceptance/waiver, expired authority, future authority beyond skew, or fresh evidence trying to replace expired pending outcome rejects. Caller may safely block or use existing successor policy.
- observable acceptance: old ambiguous outcome cannot accept or waive; legacy attestation cannot wait for later manual finalization; expired block is explicit and fail-closed.

#### Requirement: External controller authorization

- trigger or actor: external approver for multi-decision terminal outcome.
- preconditions: active user-local registry has issuer key with `controller_approver` role and policy permits issuer pairing with evidence issuer.
- required behavior: core validates exact `controller_authorization/v1` fields, canonical Ed25519 signature, registry state/role, byte limit, time bounds, decision/subject binding, and key/registry fingerprints. Same issuer cannot evidence and authorize one outcome unless policy explicitly permits.
- output or state change: receipt stores normalized principal ID, authorization ID/digest, issuer key ID, matching key fingerprint, registry digest, and policy digest; it stores rationale hash and length only.
- failure behavior: raw actor input, unknown/revoked issuer, unsupported algorithm, malformed/oversized record, mismatched identity, invalid time, role failure, same-key failure, or signature failure rejects without mutation.
- observable acceptance: agents transport signed file but cannot construct approval from CLI JSON or environment data.

#### Requirement: One current authority registry and migration

- trigger or actor: core startup, legacy cleanup signing/validation, controller authorization validation, and explicit operator migration.
- preconditions: current registry path is `~/.codex/harness-authorities.toml`; old source may be `~/.codex/harness-attesters.toml`.
- required behavior: current validation reads only new registry. It has schema version and exact records with principal ID, role list, algorithm, public key, key fingerprint, and status. `migrate-harness-authorities` validates old records, atomically writes target only when absent or explicit overwrite is approved, then verifies target before success.
- output or state change: migration reports opaque entry count and digest. Historical receipt replay needs no registry. New legacy cleanup signing/validation uses new registry after cutover.
- failure behavior: missing active registry, invalid source, conflicting target, duplicate key IDs, invalid key, private fields, or target validation failure rejects without replacement.
- observable acceptance: no new validation falls back to old registry; finalized records replay after old file removal.

#### Requirement: Terminal receipt, idempotency, and atomicity

- trigger or actor: policy-auto or valid controller-approved finalization.
- preconditions: current outcome, terminal decision, and authority mode validate under immutable outcome policy snapshot.
- required behavior: receipt digest and terminal ID include subject, outcome digest, decision, authority mode, authorization digest or null, evidence digests, policy digest, and trust snapshot. Core writes `attempt_terminal_receipt/v3`, final decision, decision history, outcome reference, and final transition together.
- output or state change: identical canonical event replays receipt after registry revocation or policy change. Different event after finalization conflicts. Receipt is terminal authority SSOT.
- failure behavior: injected write failure, concurrent different finalization, partial authority, or receipt mismatch leaves no partial final state. Existing v2 records remain immutable.
- observable acceptance: automatic legacy block has one receipt and no intermediate `awaiting_decision` write; concurrent approvals yield one receipt.

#### Requirement: CLI, API, and documentation compatibility

- trigger or actor: core CLI/API consumer.
- preconditions: policy schema and authority registry are valid.
- required behavior: canonical CLI is `terminalize-attempt --run-id <id> --input <terminalization-envelope.json>`. Existing `--evidence` may wrap only exact legacy evidence during packet API `8` support and rejects `--auto-block`. Generic `decision` routes terminal kinds through `terminalize_attempt`; it retains nonterminal routing. `recover-stranded` builds evidence form only.
- output or state change: identity reports policy schema `9`; packet API `8`, run API `2`, host API `7`, and observation contract remain unchanged.
- failure behavior: `--auto-block`, direct legacy abandonment, caller-selected auto decision, private key inside repository, and unsupported CLI combinations reject.
- observable acceptance: host source needs no behavior change; controller has no per-evidence-class terminal command.

### Constraints and Alternatives

- constraint: final disposition must cover core-only outcomes and terminal-evidence outcomes.
- alternative: separate pending-terminalization record.
  - benefit: direct terminal-evidence link.
  - trade-off: duplicates `attempt.outcome`, excludes pre-dispatch outcomes, and creates special authority paths.
  - reason rejected: violates outcome SSOT and symmetry.
- alternative: raw `actor`, `approved_at`, and `reference` flags.
  - benefit: short diff.
  - trade-off: unverified identity and fabricated audit facts.
  - reason rejected: cannot prove authority.
- alternative: old registry plus new fallback.
  - benefit: shorter migration.
  - trade-off: two active trust sources and ambiguous validation.
  - reason rejected: violates one public trust SSOT.
- alternative: host produces approval.
  - benefit: no external authority file.
  - trade-off: expands host beyond lifecycle/evidence ownership.
  - reason rejected: violates core/host boundary.

## Design Decisions

### Decision: `attempt.outcome` is universal finalization subject

- context: existing nonterminal and terminal paths already converge on outcome before controller decision.
- selected approach: enrich outcome to v2 and bind final authority to outcome digest. No separate pending-terminalization record exists.
- rationale: one existing state object covers every admissible decision path with smallest migration.
- alternatives considered: pending evidence receipt; finalization queue.
- accepted trade-offs: outcome writers use one shared helper; tests cover every source.
- affected owners and boundaries: core owns outcome and receipt; host unchanged.

### Decision: One policy-derived autonomous rule

- context: safety stops are often block-only; success and recoverable outcomes require a choice.
- selected approach: auto-finalize only when allowed decisions contains exactly one terminal value and policy enables rule.
- rationale: policy expresses autonomy once; code has no duplicated auto-block lists.
- alternatives considered: per-classification hard-coded blocks; agents choose auto block.
- accepted trade-offs: some safe blocks remain pending when nonterminal choices exist.
- affected owners and boundaries: `repo_config/harness.yaml` owns rule; core enforces it.

### Decision: Signed authority only for ambiguous terminal decisions

- context: discretionary decision needs provenance; block-only policy action does not need a fabricated human identity.
- selected approach: policy-auto receipt has no human principal; multi-decision finalization requires signed controller authority.
- rationale: autonomy stays bounded while discretionary action has real proof.
- alternatives considered: unsigned CLI actor; signature on every terminal call.
- accepted trade-offs: approvers need authority key for acceptance, waiver, or manual block.
- affected owners and boundaries: approver owns private key; core verifies public entry; agents transport only.

### Decision: One registry with explicit cutover

- context: legacy cleanup has user-local public attesters; controller approval adds trusted role.
- selected approach: versioned `harness-authorities.toml` is sole active registry. Migration is explicit, deterministic, atomic, and validated; no new-validation fallback to old file.
- rationale: one reusable public trust boundary reduces ongoing administration.
- alternatives considered: two files; repository keys.
- accepted trade-offs: migration is required before current terminalization validation.
- affected owners and boundaries: user-local registry owns public authorities; repository policy owns allowed roles and pairing.

### Decision: Amend authority portion of terminalization architecture

- context: `docs/superpowers/specs/2026-08-09-unified-attempt-terminalization-ssot.md` owns lease, host evidence, containment, and lifecycle boundary.
- selected approach: this specification owns outcome authority, receipt, and registry behavior; existing specification remains owner for host lifecycle and evidence production.
- rationale: one fact has one owner without rewriting unrelated lifecycle design.
- alternatives considered: rewrite original spec; leave conflicting v2 authority wording.
- accepted trade-offs: implementation updates cross-references and canonical agent guidance.
- affected owners and boundaries: core docs own authority; host docs retain lifecycle boundary.

### Compatibility, Migration, and Risk

- old behavior: outcome is unversioned; terminal record is v2; terminal decision is separate unauthenticated write; legacy cleanup uses old registry and auto-block.
- new behavior: outcome v2 and receipt v3 bind authority; policy schema `9`; new validation uses authority registry; canonical envelope replaces auto-block.
- compatibility boundary: packet API `8`, host API `7`, host contract `7`, and run API `2` remain. Old v2 terminal records report computed missing provenance only.
- migration or backfill: never rewrite historical runs. Registry migration creates user-local target. Active old outcome may block with current authorization but cannot accept or waive until core establishes v2 digest and deadline.
- rollout and rollback: ship v2/v3 readers before requiring new registry; retain legacy evidence wrapper only through packet API `8`; rollback reads old/new records but creates no new v3 receipt.
- deprecation or consumer impact: `--auto-block` rejects; direct abandonment stays retired; terminal `decision` becomes shim; host behavior does not change.
- risk:
  - migration misconfiguration blocks finalization.
    - mitigation: dry-run migration, atomic target write, exact diagnostics, no overwrite by default.
  - authority key compromise approves action.
    - mitigation: status, short expiry, fingerprints, role separation, default same-key denial.
  - outcome writer bypasses helper.
    - mitigation: source-matrix tests and no direct terminal `_transition` outside finalizer.

## Invariants and Edge Cases

### Invariants

- Only core writes run state, outcome identity, terminal receipt, final decision, and terminal state.
- Host only owns provider lifecycle and terminal observation production.
- Every new final decision references one immutable outcome digest.
- Policy-auto decision has exactly one allowed terminal value; caller cannot choose it.
- Controller-approved decision has signed authority bound to subject, outcome, packet, and decision.
- Current validation reads one authority registry; no private material enters repository, packet, run record, or host config.
- Same key cannot evidence and approve one outcome unless policy explicitly grants pairing.
- Final receipt write is atomic, idempotent for identical event, and conflicts for different event.
- Historical authority facts remain absent when not recorded; readers label absence rather than infer it.

### Edge Cases

- empty or minimal input: exact-field envelope and authority records reject empty, missing, null, duplicate, and mixed forms.
- normal and large input: opaque IDs, bytes, rationale hash/length, evidence lists, and registry records enforce policy bounds.
- duplicate, missing, malformed, or unsupported data: same event replays; different evidence, outcome digest, authority, or decision conflicts; malformed input leaves byte-identical state.
- retry, cancellation, timeout, partial failure, or concurrency: retry/escalation stay nonterminal; block-only conditions auto-finalize; concurrent finalizers yield one receipt under run lock.
- migration or mixed-version state: old v2 records remain readable; old active outcomes cannot fabricate provenance; new validation has no old-registry fallback.
- generated-source consistency: canonical agent template changes regenerate root and derived adapters; starter kit sync occurs only when canonical generated surfaces change.
- security boundary: private keys, raw reasons, raw provider failures, PID-only identity, untrusted actor text, and unbounded approvals reject.

## Validation Plan

### Backend Verification Claims

- direct boundary: exercise outcome creation and both envelope forms for every evidence and core-only outcome source.
- important success and failure behavior: prove block-only policy auto, pending ambiguous outcome, signed accept/block/waive, invalid authority, unknown/revoked key, wrong role, same-key denial, stale authority, future skew, expired outcome, and invalid CLI combinations.
- final state or side effects: assert receipt v3, decision/history, outcome ID/digest/deadline, state history, revision, and no host run write.
- rollback, retry, duplicate, or idempotency behavior: inject validation/write failures; assert byte-identical rejection; replay identical receipt after registry revoke/policy change; reject conflicting finalization; preserve nonterminal retry/escalation.
- canonical contract and conformance proof: validate policy schema `9`, authority registry schema, exact envelope/authorization fields, v2/v3 readers, CLI transport, and API exports.
- real dependencies requiring proof: temporary user-local registry, Ed25519 keys, run lock, atomic run write, and CLI file handling.
- representative-operation trace mechanism: CLI legacy cleanup evidence auto-blocks in one receipt; CLI signed authority finalizes verified ambiguous outcome without provider process action.
- performance claim and threshold: Not applicable: no performance behavior changes.

### Acceptance Criterion: Outcome SSOT

- setup or precondition: fixtures for terminal evidence, verification, dispatch failure, approval gate, unavailable mode, plan binding, and child failure.
- action: record each source outcome.
- expected result: every pending outcome is v2 with deterministic ID, digest, deadline, policy snapshot, and unchanged reason/decision semantics.
- failure condition: any source writes unversioned outcome or bypasses shared helper.
- proof method: focused direct tests and run JSON assertions.
- expected evidence: source-to-outcome matrix and no direct terminal decision writer outside finalizer.

### Acceptance Criterion: Authority and policy finalization

- setup or precondition: active registry, valid keys, block-only outcome, and ambiguous outcome.
- action: submit evidence form, then outcome form with valid or invalid authority.
- expected result: block-only finalizes atomically with policy-auto receipt; ambiguous remains pending until valid authority; accept and waive record principal/snapshot.
- failure condition: caller selects automatic decision, missing signature finalizes, or forbidden same issuer signs evidence and approval.
- proof method: direct API and CLI tests using temporary registry.
- expected evidence: one v3 receipt per final state with exact authority fields.

### Acceptance Criterion: Time, replay, and migration safety

- setup or precondition: expired legacy cleanup evidence, expired ambiguous outcome, expired authority, existing v2 terminal record, and changed registry/policy after finalization.
- action: finalize, replay, or attempt conflict.
- expected result: legacy cleanup requires valid evidence in same transaction; expired accept/waive rejects; expired manual block is explicit; same replay succeeds; v2 reader reports missing provenance without write.
- failure condition: stale source accepts, replay revalidates historical key, or migration changes historical bytes.
- proof method: controlled clock, temporary HOME, file-byte comparisons, and CLI JSON assertions.
- expected evidence: bounded timestamp records, deterministic digests, and unchanged historical fixtures.

## Completion Criteria

Specification is complete when:

1. every admissible finalization path uses outcome v2 and one terminalization finalizer
2. policy auto-finalization is generic, conservative, and caller-independent
3. manual finalization has signed authority, exact binding, expiry, role, and same-key rules
4. receipt v3 atomically records authority and validation snapshot
5. new active trust validation has one registry with explicit migration
6. host lifecycle boundary, packet API `8`, host API `7`, and run API `2` remain preserved
7. historical terminal records remain unchanged and observable as provenance-incomplete
8. backend proof covers sources, authority, time, concurrency, replay, migration, and CLI boundary
