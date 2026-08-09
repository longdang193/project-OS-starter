---
artifact_type: spec
status: active
layer: change
template_id: detailed-specification
title: Unified Attempt Terminalization SSOT
date: 2026-08-09
owners:
  - harness-core
  - codex-harness-host
---

# Unified Attempt Terminalization SSOT

## Goal and Problem

### Problem

- current behavior: core records post-dispatch outcomes through separate failure, terminal-failure, verification, and stranded-recovery paths. Host cancels a lane by cancelling a Python future and launches provider subprocesses without an attempt-wide Windows containment boundary.
- affected users, systems, or maintainers: `harness-core`, `codex-harness-host`, controller, operators, managed run readers, recovery tooling, and Windows hosts.
- evidence: core has multiple state writers around `_record_failure`, `_record_terminal_failure`, and `recover_stranded_run`; host currently uses `Future.cancel()` and `asyncio.create_subprocess_exec` for lane lifecycle.
- consequence of no change: terminal evidence can diverge from run state, a stale or failed host can leave unprovable process state, recovery can race execution, and Windows descendants can outlive managed work.

### Goal

- desired outcome: core owns every durable attempt ending through one `terminalize_attempt(evidence)` operation. Host owns provider process lifecycle and bounded observations only.
- observable success: every post-dispatch attempt has either one immutable terminal record with released lease, or explicit nonterminal `orphaned` state with durable recovery-blocked evidence. Host never writes `run.json`.

## Required Outcomes

### Outcome: Single core terminalization boundary

- affected actor or system: controller and `harness-core`.
- required result: controller invokes only `terminalize_attempt(evidence)` for terminal state mutation. Core validates, derives outcome and decisions, transitions state, releases lease, and writes `run.json` once.
- success condition: no direct post-dispatch call path writes `attempt.outcome`, terminal evidence, lease release, or terminal state outside core terminalization.

### Outcome: Bounded leased execution

- affected actor or system: core and host.
- required result: core creates one immutable, non-renewable execution lease immediately before `planned` becomes `running`. Packet contains exact `execution_lease_seconds` resolved from versioned host duration limits, topology schedule, checks, core verification, and cleanup grace.
- success condition: host cannot begin work after lease deadline; stale evidence cannot terminalize later attempt; every terminal record retains released lease identity.

### Outcome: Proven process stop

- affected actor or system: Windows host and recovery controller.
- required result: host owns one Job Object handle per lease, assigns every provider root before execution, waits for contained process stop on timeout or cancellation, and emits bounded stop proof. On host crash, last handle closure kills contained processes; stateless observer proves recorded host and provider process identities absent. Observer never reopens job.
- success condition: cancellation or timeout cannot terminalize from future cancellation, elapsed time, PID-only guess, or unbounded tree walk.

### Outcome: Safe crash and orphan handling

- affected actor or system: controller, host observer, and core.
- required result: expired lease with absence proof terminalizes block-only. Expired lease with live or unverified provider process becomes durable `orphaned` with `terminalization.status: recovery_blocked`; it does not terminalize, resume, retry, or abandon.
- success condition: no successor is created while process stop remains unproved; completed cleanup can later terminalize same orphaned attempt with new valid host evidence.

### Outcome: Compatibility without synthetic history

- affected actor or system: operators and migration tooling.
- required result: existing terminal runs remain readable unchanged. An active unleased historical attempt remains isolated from new dispatch and may close only through signed operator cleanup evidence passed to `terminalize_attempt(evidence)`.
- success condition: migration never invents lease, rewrites packet hashes, forces a running legacy attempt into new protocol, or retains a direct legacy terminal writer.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
| --- | --- | --- | --- | --- |
| Who writes run state now? | Core uses separate failure and terminal-recovery writers; `_write_run` atomically replaces JSON but has no terminal transaction abstraction. | `packages/harness-core/src/harness_core/managed.py` | high | Centralize post-dispatch terminal mutation. |
| What host cancellation proof exists? | `cancel_lane` only calls `Future.cancel()`. | `codex-harness-host@ae9d1d4:src/codex_harness_host/adapter.py` | high | Cancellation must wait for Job Object stop proof. |
| Is terminal evidence already sanitized? | Current terminal observation bounds opaque IDs, item and command states, final claim state, and hashes. | `packages/harness-core/src/harness_core/terminal_observation.py` | high | Reuse sanitized subrecords; do not copy raw transcripts. |
| Does current recovery bind runtime ownership? | Current recovery matches run and attempt but has no execution lease. | `packages/harness-core/src/harness_core/managed.py` | high | New recovery requires exact expired lease and process-absence evidence. |
| Can current host bound one lane? | Host may retry lane work and run a separate read-only finalizer. | `codex-harness-host@ae9d1d4:src/codex_harness_host/adapter.py` | high | Packet lease duration must derive from declared finite host duration model. |

### Prototype and Validation Evidence

- prototype reference: `Not created: backend contract; Windows containment spike is implementation verification, not product prototype`.
- validated scenarios and states: source trace confirmed split core terminal writers, unleased recovery, lane-only future cancellation, bounded terminal observation, and host finalization path.
- findings incorporated into approved behavior: one core terminal mutation; core-built terminal record; exact lease bound; sole Job Object handle; no named-job reaper; durable orphan state; active-legacy drain gate.
- rejected alternatives: host writes `run.json`; controller chooses terminal outcome; host observer opens a job after kill-on-close; PID-tree cleanup; implicit timeout retry; synthetic leases; local absolute source paths.

### Scope

- included behavior: terminal observation ingestion, core terminal record, lease, cancellation request binding, state transitions, Windows containment, crash recovery, orphan state, idempotency, migration, tests, and canonical guidance.
- affected boundaries: core managed API and schemas, host adapter lifecycle, provider subprocess client, host capability contract, policy state map, tests, canonical adapter docs, generated agent guidance.
- admissible cases: normal completion, verification failure after normal provider completion, provider failure, timeout, cancellation, host crash with absence proof, unresolved orphan, leased stranded recovery, and operator-attested cleanup for an unleased historical attempt.
- compatibility expectation: old terminal records remain immutable and readable; no active legacy attempt crosses protocol versions.

### Non-Goals

- changing routing, packet selection, task planning, controller acceptance policy, provider transport protocol, arbitrary retry policy, cross-controller scheduler, or product-work recovery;
- giving core permission to kill a host-owned process;
- adding transcript, prompt, environment, command-output, or raw provider-error retention;
- making unproved orphan process cleanup appear terminal or retryable.

### Requirements and Behavioral Contract

#### Requirement: Ownership and trusted boundary

- trigger or actor: controller supplies evidence envelope or a signed controller-authorization outcome envelope to core.
- preconditions: controller and host adapter run in one trusted local execution boundary. Host-observation provenance is semantic validation, not cryptographic authentication. Legacy cleanup uses a separate external attester boundary.
- required behavior: host produces immutable `host_terminal_observation/v2` records. Core reads persisted core verification evidence and builds `attempt_terminal_evidence/v2`, then records `attempt_outcome/v2`. Evidence callers cannot supply derived outcome ID/digest, target state, evidence digest, or terminal ID. Outcome callers bind one persisted outcome and requested terminal decision through signed `controller_authorization/v1`. Current trusted public records live only in `~/.codex/harness-authorities.toml`; it contains active or revoked public keys, opaque principals, and roles, never private signing material. External private keys remain outside controller, host, agent, packet, run, and repository boundaries.
- output or state change: core stores host-observation digests plus core-evidence references, or normalized signed legacy-cleanup evidence, in one terminal record; every new final state also stores one `attempt_terminal_receipt/v3`.
- failure behavior: unsupported source, malformed record, mismatched identity, raw actor or approval flag, unknown issuer, revoked issuer, unsupported signature algorithm, expired authorization, or public configuration containing private-key fields rejects without mutation.
- observable acceptance: host code has no run-path writer; terminal outcome and receipt derive solely inside core; agent-visible configuration cannot mint cleanup or controller authority.

#### Requirement: `terminalize_attempt(evidence)`

- trigger or actor: controller after required host observations are available, after verified external operator cleanup evidence is available, or after external controller authorization is available for pending outcome.
- preconditions: evidence form accepts one source: leased host observations, leased recovery observation, or unleased historical `legacy_cleanup_attestation/v1`. Outcome form requires `awaiting_decision`, exact persisted outcome ID/digest, one requested terminal decision, and signed authority.
- required behavior: core locks run, normalizes evidence, loads persisted lane and verification evidence, computes core-owned classification, and records outcome. A one-decision terminal outcome policy auto-finalizes. A multi-decision outcome requires exact signed controller authority. Legacy evidence can produce only block-only outcome. No caller supplies target state, evidence digest, terminal ID, or automatic decision.
- output or state change: output contains `terminalization.status` of `applied`, `finalized`, `replayed`, or `recovery_blocked`, plus current `terminal_id` and `run_revision` when terminalized. Finalization writes receipt, decision/history, state transition, and revision in the same run-lock transaction.
- failure behavior: a different valid record after terminalization returns conflict; invalid evidence or authority leaves byte-identical run record. Receipt replay never revalidates changed policy or registry.
- observable acceptance: post-dispatch error, success, timeout, cancellation, recovery, and controller terminal decisions all invoke this operation rather than separate terminal writers.

#### Requirement: Execution lease

- trigger or actor: core immediately before first host provider dispatch.
- preconditions: packet passed admission and contains host capability duration model matching packet contract.
- required behavior: core writes one `execution_lease` with UUID, epoch, packet SHA-256, host instance ID, issued time, expiry, and duration model ID. `execution_lease_seconds` equals core's deterministic topology schedule using immutable packet lanes and declared finite host bounds, plus bounded checks, core verification, and cleanup grace.
- output or state change: attempt records active lease; host receives exact lease values with packet.
- failure behavior: capability mismatch, nonpositive or unbounded duration component, or dispatch after expiry rejects before provider process launch.
- observable acceptance: fixture with maximum retries, finalization, serialized lanes, checks, and cleanup reaches terminalization before expiry; evidence observed after expiry cannot win over valid recovery or terminal record.

#### Requirement: Host terminal observations

- trigger or actor: host observes normal provider completion, provider failure, timeout interrupt, cancellation stop, or post-crash absence.
- preconditions: host owns provider lifecycle for exact active lease.
- required behavior: each `host_terminal_observation/v2` contains observation ID, run and attempt IDs, packet SHA-256, lease ID and epoch, host instance ID, lane ID, source, bounded timing, opaque provider IDs, sanitized item and command states, final claim state, error hashes and lengths, process containment state, and stop proof.
- output or state change: core persists only normalized observation or digest; core builds attempt-level aggregate from packet lanes and existing node evidence.
- failure behavior: missing lane, wrong lease, incomplete containment, raw sensitive values, or invalid bounded data rejects.
- observable acceptance: parallel and sequential lanes produce independent observations; core derives one attempt terminal record without a new host attempt-aggregation API.

#### Requirement: Normal completion and core verification

- trigger or actor: every dispatched provider lane reported completed and core checks finished.
- preconditions: host containment reports zero active provider processes; core has persisted criteria and check evidence.
- required behavior: core terminalizes `completed` after reading its own verification references. Proven criteria produce existing accept-or-block outcome; failed criteria produce existing verification failure policy.
- output or state change: attempt becomes terminal and run moves to `awaiting_decision`.
- failure behavior: missing required lane observation or verification reference rejects terminalization.
- observable acceptance: normal provider success cannot bypass verification, and verification failure does not require fabricated host failure evidence.

#### Requirement: Provider failure and timeout

- trigger or actor: host receives provider terminal failure or reaches packet timeout.
- preconditions: host has contained provider process scope and emits terminal or interrupt observation.
- required behavior: core derives `dispatch_failed`, `dispatch_timeout`, or existing `writer_completion_missing` from sanitized observation and packet lane type. Timeout decisions remain immutable packet policy; writer completion missing remains block-only.
- output or state change: attempt becomes terminal, lease releases, run moves to `awaiting_decision`.
- failure behavior: timeout without stop proof, terminal confirmation state, or valid budget binding rejects.
- observable acceptance: timeout never silently retries or resumes; provider failure never selects successor without controller decision.

#### Requirement: Cancellation

- trigger or actor: authorized controller requests cancellation of active leased attempt.
- preconditions: run is active and has no terminal record.
- required behavior: core records idempotent `cancellation_request` with UUID, actor, reason hash and length, request time, and lease binding. Host receives request, terminates lease Job Object, waits for empty process list, and echoes request ID in `host_cancellation` observation.
- output or state change: only echoed stop-proof observation terminalizes `cancelled`; run moves to `awaiting_decision` with packet-defined block-only default.
- failure behavior: repeated request returns same request ID; future cancellation, transport loss, or process-stop uncertainty leaves attempt active or orphaned, never cancelled.
- observable acceptance: cancellation evidence with unknown request ID rejects.

#### Requirement: Windows process containment

- trigger or actor: host dispatches first provider root process for lease.
- preconditions: Windows platform; host has permission to create and configure Job Object.
- required behavior: host creates one unnamed Job Object per lease and retains sole handle. It launches each provider root suspended, assigns root to job, configures kill-on-close, then resumes. Timeout and cancellation terminate job and await empty job process list before evidence. Host records root PID with process creation identity, job identity, termination action, and final count.
- output or state change: bounded containment proof attaches to host observation.
- failure behavior: Job Object create, assignment, configuration, wait, or identity check failure rejects dispatch or terminalization before declaring stop. No PID-tree, process-group, `taskkill`, or named-job reaper fallback.
- observable acceptance: crash of process holding sole job handle ends descendant sentinel; stateless observer confirms recorded host and root process identities are absent without opening job.

#### Requirement: Host crash, stranded recovery, and orphan state

- trigger or actor: lease expires without terminal record.
- preconditions: evidence names exact run, attempt, packet, lease, and original host process identity.
- required behavior: stateless host observer reports process-absence proof only; it never opens or controls prior Job Object. Core locks run and, if host and recorded root processes are absent, terminalizes `host_crash` or `stranded_recovery` block-only. If process remains live or proof is incomplete, same operation records `recovery_blocked` evidence, marks run `orphaned`, and keeps lease identity with `recovery_blocked` state.
- output or state change: absence proof creates immutable terminal record. Incomplete proof creates durable nonterminal orphan record; resume, retry, successor, acceptance, waiver, and legacy abandonment are disallowed.
- failure behavior: recovery before expiry, mismatched lease, terminal attempt, or ordinary active work rejects without mutation.
- observable acceptance: after external cleanup, fresh absence proof may terminalize orphaned attempt; no execution restarts while orphaned.

#### Requirement: Operator-attested legacy cleanup

- trigger or actor: external operator confirms cleanup of an historical active attempt without `execution_lease`; controller submits that signed evidence to `terminalize_attempt(evidence)`.
- preconditions: attempt is current-policy terminalizable, unleased, has no terminal record, outcome, decision, claim, node observation, or persisted evidence, and immutable packet lacks current terminal-observation contract. New packet APIs never select this path.
- required behavior: evidence contains only `attempt_id` and `legacy_cleanup_attestation`. Unsigned attestation uses `schema_id: legacy_cleanup_attestation/v1` and exact fields: `attestation_id`, `run_id`, `attempt_id`, `packet_sha256`, `issuer_key_id`, `absence_observed_at`, `issued_at`, `expires_at`, `cleanup_scope`, `discovery_method`, `root_process_identity`, `process_identities`, `scope_complete`, `reason_sha256`, and `reason_length`. Transport adds one base64url `attestation_signature`. Core verifies Ed25519 signature over UTF-8 sorted compact JSON bytes of unsigned payload. Opaque identifiers use ASCII letters, digits, `.`, `_`, and `-`; SHA-256 values are lowercase hexadecimal; unsupported fields reject.
- required behavior: `cleanup_scope` is exactly `operator_discovered_provider_tree` or `operator_attested_no_provider_process`. Current public authority registry maps `issuer_key_id` to one opaque principal, roles, Ed25519 public key fingerprint, and `active` or `revoked` state. `harness-core migrate-harness-authorities` performs explicit conversion from retired `harness-attesters.toml`; current validation never falls back to it. Rotation adds new active issuer before old issuer becomes revoked. New evidence from revoked issuer rejects; exact evidence already recorded may replay from stored digest without re-evaluating current issuer status. Current repository policy defines enabled flag, historical packet maximum API, allowed cleanup scopes and discovery methods, attestation age, lifetime, clock skew, total payload bytes, identifier bytes, creation-ID bytes, reason length, process-identity count, and allowed attester roles. No repository policy, packet, run record, request, or agent workspace contains private signing material.
- required behavior: for `operator_discovered_provider_tree`, `root_process_identity` and every `process_identities` member contain positive `pid`, bounded `creation_id`, and `state: absent`; root appears exactly once in nonempty list. For `operator_attested_no_provider_process`, `root_process_identity` is `null`, `process_identities` is empty, and discovery method is `windows_no_process_observation/v1`. In both scopes, `scope_complete` is exactly `true`. Duplicate `{pid, creation_id}` pairs, PID-only entries, live or unverified states, or scope-shape mismatch reject. Core records signed operator-discovered scope or signed no-process assertion, never historic host or lease proof.
- required behavior: core evaluates one current UTC time. `absence_observed_at <= issued_at < expires_at`; absence age, attestation lifetime, future skew, and total age must satisfy policy. Legacy terminal record remains `attempt_terminal_evidence/v2` with `source_kind: legacy_cleanup`, `lease_id: null`, `lease_epoch: null`, and normalized `legacy_cleanup` audit. Pre-existing v2 record without `source_kind` remains leased and requires string lease ID plus positive lease epoch. Readers accept both shapes. Core derives `legacy_cleanup_attested`, records block-only `attempt_outcome/v2`, then policy auto-finalizes `attempt_terminal_receipt/v3` and `blocked` in one transaction.
- required behavior: controller invokes `harness-core terminalize-attempt --run-id <run-id> --input <envelope.json>`. Temporary `--evidence <path>` translates only readable packet API 8 legacy evidence; `--auto-block` is rejected. Re-entry after terminalization or block is idempotent: matching stored digest returns `replayed`; already blocked result returns success without a second decision. External operator creates signed input through `harness-core sign-legacy-cleanup`; private-key file must be outside repository and agent workspace. This policy-owned automatic block requires no second human approval.
- output or state change: immutable audit holds attester ID, issuer key ID, signed evidence digest, reason hash and length, timestamps, discovery method, scope shape, identity set, and historical packet identity. `run.json` changes atomically through core only.
- failure behavior: leased, current-schema, terminal with different digest, claimed, observed, evidenced, outcome-bearing, decided, unknown issuer, revoked issuer for new evidence, invalid signature, malformed canonical bytes, stale or future timestamp, scope-shape mismatch, or mismatched identity rejects without mutation. Core computes candidate legacy digest before terminal-state rejection; same signed canonical evidence replays from `awaiting_decision` or final `blocked` state, while different evidence after terminalization rejects.
- observable acceptance: cleanup never creates successor, resume, replay, waiver, acceptance, fabricated lease, host process action, or modified packet history. `abandon_legacy_attempt` returns `legacy_abandonment_retired` without mutation.

#### Requirement: Atomicity and idempotency

- trigger or actor: every accepted terminalization or recovery-blocked observation.
- preconditions: per-run exclusive lock acquired.
- required behavior: core normalizes input, orders host observations by lane ID, observed time, and observation ID, serializes with existing sorted compact JSON convention, and computes SHA-256 `evidence_digest`. Core derives `terminal_id` from version, run ID, attempt ID, lease identity when present, and digest. Core increments `run_revision`, writes temp JSON in target directory, flushes file contents, atomically replaces `run.json`, then releases lock.
- output or state change: one complete new run record contains terminal or orphan transition, evidence, outcome when terminal, and lease state together.
- failure behavior: same digest replays without changing bytes or history; different digest after terminal rejects; write failure preserves prior complete record; stale temporary files are ignored.
- observable acceptance: concurrent processes produce one applied result and replay or rejection for all others.

### Constraints and Alternatives

- constraint: no new host process may write core run state.
- alternative: host serializes and writes `run.json`.
  - benefit: fewer controller calls.
  - trade-off: duplicates core transition and policy authority.
  - reason rejected: violates SSOT and makes recovery host-dependent.
- constraint: Windows descendants need deterministic containment.
- alternative: PID-tree, process group, or `taskkill` cleanup.
  - benefit: less native interop.
  - trade-off: does not prove descendant ownership or stop.
  - reason rejected: cannot satisfy timeout, cancellation, and crash invariants.
- constraint: crash recovery must not require unavailable host Job Object handle.
- alternative: named job reopened by reaper.
  - benefit: reaper control after host crash.
   - trade-off: conflicts with sole-handle kill-on-close model.
   - reason rejected: observer proves absence; it never reopens old containment.
- constraint: legacy cleanup must authenticate an external operator without giving controller or agents capability to mint evidence.
- alternative: shared HMAC secret in controller trusted configuration.
  - benefit: stdlib-only verification.
  - trade-off: verifier can mint attestations when agent access or process isolation is incomplete.
  - reason rejected: Ed25519 public-key verification keeps controller configuration non-secret and leaves signing capability outside harness execution.

## Design Decisions

### Decision: Core builds terminal record from host observations

- context: host lifecycle observations and core verification evidence have different authorities.
- selected approach: host returns lane-level `host_terminal_observation/v2`; controller transports them; core loads its own persisted evidence and builds canonical `attempt_terminal_evidence/v2`.
- rationale: preserves host-only lifecycle ownership without requiring host attempt aggregation or letting controller assert policy.
- alternatives considered: signed host envelope, host aggregate record, controller-composed terminal record.
- accepted trade-offs: trusted local controller boundary remains explicit; cryptographic attestation is out of scope.
- affected owners and boundaries: host adapter produces observations; core owns aggregate, classification, and persistence.

### Decision: One terminal mutation; explicit orphan result

- context: terminalization needs one durable state mutation, but unproved live process cannot become terminal.
- selected approach: `terminalize_attempt` is sole terminal mutation and can return nonterminal `recovery_blocked` while recording `orphaned` state.
- rationale: preserves safety and durable visibility without a hidden recovery-claim API.
- alternatives considered: persistent recovery claim before probe; direct block with live process; no durable orphan state.
- accepted trade-offs: orphan needs external cleanup before final terminalization.
- affected owners and boundaries: core owns lock and orphan transition; host observer only reports proof.

### Decision: Finite packet-resolved lease

- context: lease expiration must never race valid bounded work.
- selected approach: core resolves immutable `execution_lease_seconds` using versioned finite host duration limits and packet topology before dispatch; no renewal.
- rationale: preserves packet-owned budget and avoids heartbeat protocol.
- alternatives considered: unbounded lease, arbitrary controller extension, renewable heartbeat lease.
- accepted trade-offs: host duration model changes require capability version bump and packet admission update.
- affected owners and boundaries: core resolves and persists duration; host enforces deadline.

### Decision: Sole-handle Windows Job Object

- context: host crash must terminate contained provider descendants without a reaper reopening stale containment.
- selected approach: dispatching host owns sole unnamed job handle; crash closes last handle and kills contained process scope. Stateless observer only verifies absence from recorded process identities.
- rationale: smallest Windows-native containment model satisfying timeout, cancellation, and host-crash safety.
- alternatives considered: persistent supervisor, named reaper job, PID-tree cleanup, process groups.
- accepted trade-offs: no automated control of uncontained orphan; containment breach remains blocking incident.
- affected owners and boundaries: host owns job lifecycle; core never owns or terminates job.

### Decision: Signed operator cleanup for active legacy attempts

- context: historical attempts have no lease identity and cannot safely join v2 protocol, but permanent release blocking leaves externally cleaned runs stranded.
- selected approach: active legacy attempts remain unreadable for dispatch or resume and can close only through signed operator cleanup evidence inside the existing terminalization boundary. Valid evidence gets automatic policy-owned block decision; no per-attempt human controller approval follows signature verification.
- rationale: avoids synthetic leases, direct legacy writes, shared signing secret, and permanent administrative drain gate.
- alternatives considered: v1/v2 active compatibility bridge; direct operator abandonment; shared HMAC secret; automatic abandonment; run rewrite.
- accepted trade-offs: external operator must retain complete pre-cleanup provider-tree discovery and signing authority; harness cannot repair legacy containment.
- affected owners and boundaries: external attester signs; controller holds public attester configuration and invokes core; core verifies and persists; host has no legacy cleanup responsibility.

### Compatibility, Migration, and Risk

- old behavior: v1 terminal observation and unleased stranded recovery; host future cancellation and child-only subprocess kill.
- new behavior: v2 host observations, core-built terminal record, packet lease, Job Object stop proof, orphaned state, and signed operator cleanup for active unleased historical attempts.
- compatibility boundary: historical terminal records read unchanged. New behavior applies only to packets admitted after both core and host capability deployment.
- migration or backfill:
  1. Add core reader, state schema, run lock, duration model, terminalization operation, and migration preflight.
  2. Stop new dispatch or resume for every active historical unleased attempt; preserve its immutable packet and current evidence.
  3. Configure public attester records outside repository and prove private signing material remains outside harness processes.
  4. Release compatible core and host capability.
  5. Admit new leased packets only when core/host capability versions match; legacy cleanup remains isolated to historical attempts.
  6. Close active historical attempts only through signed cleanup evidence, then remove retired abandonment adapter after retained historical-reader period.
- rollout and rollback: rollback before v2 packet admission is safe after preserving old terminal records. After v2 admission, rollback requires core reader capable of v2 records; do not downgrade to writer lacking v2 reader.
- deprecation or consumer impact: generated guidance and consumer setup must state v2 core/host pairing; no legacy host dispatch for new packets.
- risk:
  - Windows Job Object assignment unavailable.
  - mitigation: reject dispatch before provider work; keep packet planned for controller block or supported host.
  - active legacy attempt at deployment.
  - mitigation: isolate from dispatch and resume; preserve proof until signed operator cleanup passes core validation.
  - containment breach leaves live orphan.
  - mitigation: durable `orphaned` state, no successor, external incident cleanup, then fresh absence observation.

## Invariants and Edge Cases

- Core is sole writer of packet, lease, terminal record, outcome, decisions, run state, and `run.json`.
- Host owns provider launch, interrupt, wait, Job Object lifecycle, and sanitized observation production. Host cannot choose terminal classification.
- One attempt has at most one terminal record. No later evidence can alter a terminal attempt.
- Lease is immutable and retained after release. Exact run, attempt, packet SHA-256, lease ID, epoch, and host identity must match.
- Terminal attempt guarantees no known active provider process. `orphaned` is explicitly nonterminal and blocks all continuation.
- Normal completion requires all dispatched lanes terminal plus core verification references; host success alone is insufficient.
- Timeout and cancellation require bounded containment stop proof. Future cancellation, controller interruption, or elapsed budget alone is insufficient.
- Timeout remains policy-owned escalation or block; `writer_completion_missing` remains block-only.
- Provider error and command evidence remain opaque hashes, lengths, statuses, and bounded IDs. Never persist raw sensitive material.
- Same normalized evidence digest replays. Different digest cannot supersede terminal or orphan record without allowed cleanup transition.
- Legacy cleanup requires no lease, exact signed audit, fresh absence observation, and complete operator-discovered provider-tree scope. Leased attempt legacy cleanup is always rejected.
- Pre-dispatch admission failure creates no lease or host terminal observation.
- Windows Job Object setup failure creates no provider side effect. Process groups, PID-tree traversal, and named-job reaper fallback are forbidden.

## Validation Plan

### Core boundary and state proof

- Add direct `terminalize_attempt` tests for normal completion, verification failure, provider failure, timeout, `writer_completion_missing`, cancellation, host crash, stranded recovery, orphaned recovery block, cleanup-after-orphan, and signed operator-attested legacy cleanup.
- Test malformed, oversized, raw-sensitive, mismatched run/attempt/packet/lease/host/lane, expired, stale, duplicate, unsigned, invalid-signature, unknown-issuer, revoked-issuer, future-skew, missing-absence-time, incomplete-scope, duplicate-identity, PID-only, no-process scope shape, replay after block, and direct-retired-abandonment evidence.
- Test deterministic evidence digest and terminal ID using sorted compact JSON; same record replays byte-identically and different record rejects.
- Use multi-process tests for run lock, atomic replace failure, concurrent terminalization, concurrent recovery, stale temporary files, and revision monotonicity.
- Assert final `run.json`, lease state, attempt outcome, state history, node status, and decision allowance for every path.

### Host boundary and Windows proof

- Test host cannot write `run.json` and returns only v2 lane observation.
- Test finite duration model includes retry, finalizer, interrupt settlement, sequential/parallel topology, checks, verification, and cleanup grace.
- Test cancellation request ID propagation; repeated cancellation remains idempotent; no terminal cancellation without zero process count.
- On Windows, launch provider parent plus descendant sentinel; prove suspended assignment precedes execution, timeout/cancellation terminate job, and host crash of sole handle kills descendants.
- Test Job Object create, assign, configure, wait, identity, and stop-proof failure rejects before terminal success; prove no PID-tree, process-group, `taskkill`, or named-job reaper fallback.
- Test stateless observer reports only absence from recorded process identities and cannot terminate or open previous job.

### Migration and integration proof

- Test migration preflight detects every active legacy run state, blocks its dispatch and resume, and preserves immutable records without blocking new leased-packet admission.
- Test signed legacy cleanup accepts only eligible unleased historical attempt, terminalizes through core, records block-only outcome plus policy-auto receipt, replays after block, and records no private signing material. Test signed controller authorization, expiry, role, same-key denial, receipt replay after registry change, and retired `--auto-block` rejection.
- Test v1 historical terminal records remain readable without rewrite; v2 reader remains available for rollback after v2 packet admission.
- Run core and host contract suite against released compatible packages; reject host capability or duration-model mismatch before packet creation.
- Update canonical adapter, consumer, runtime, and root-agent template guidance; regenerate derived agent and routing surfaces; inspect no private paths, secrets, or stale lifecycle rules.

## Completion Criteria

1. Every post-dispatch terminal path reaches one core `terminalize_attempt` transaction; no legacy terminal writer remains reachable for new packet API.
2. Each new attempt has exact immutable lease duration, revision, and retained release record; stale or concurrent evidence cannot win.
3. Core-created terminal record joins sanitized host observations with persisted core verification evidence and derives all outcome policy.
4. Windows host proves Job Object containment on normal completion, timeout, cancellation, and host crash; no prohibited fallback exists.
5. Expired live or unverified process becomes durable `orphaned`, blocks continuation, and can terminalize only after fresh absence proof.
6. Active legacy attempts remain isolated from dispatch and resume until signed cleanup terminalizes them; historical terminal evidence remains unchanged.
7. Direct boundary, failure, state, idempotency, migration, host lifecycle, and Windows integration proof pass from fresh automated output.
8. Canonical documentation, generated agent/routing surfaces, core/host compatibility declarations, and package release notes agree.
