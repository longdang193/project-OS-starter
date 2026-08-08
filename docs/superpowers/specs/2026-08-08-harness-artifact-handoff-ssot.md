---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: harness-artifact-handoff-ssot
targets:
  - repo_config/harness.yaml
  - packages/harness-core
  - ../codex-harness-host
  - scripts/render_harness_routing.py
  - docs/operating_system/procedures
---

# Harness Artifact Handoff SSOT

## Goal and Problem

### Problem

- current behavior or opportunity: request API 4 accepts caller-selected
  `readonly_artifacts`; retained writer traces and route-local artifact rules
  have separate ownership. Recurring friction diagnosis selects source artifacts
  through a separate helper. No policy-owned catalog, deterministic profile
  resolver, or exact handoff audit exists.
- affected users, systems, or maintainers: controller, `harness-core`, Codex
  provider host, read-only managed agents, policy authors, and starter-kit
  consumers.
- evidence: `repo_config/harness.yaml` retains only
  `sanitized_command_trace` and configures `harness_diagnosis` with
  `readonly_artifacts`. Core resolves caller-provided source run and attempt
  triples in `packages/harness-core/src/harness_core/managed.py`. Friction
  selection separately gathers terminal source attempts. Host rehashes and
  materializes packet descriptors.
- consequence of no change: controller and route code retain competing source
  selection paths. Arbitrary artifact references remain admitted. Later
  successor requests cannot prove which bounded context core selected.

### Goal

- desired outcome: policy version 5 defines one initial catalog and two
  route-owned handoff profiles. Request API 5 accepts a direct predecessor and
  profile, never individual artifact IDs. Core resolves bounded context and
  records immutable packet proof plus run audit. Existing recurring-friction
  follow-up uses same resolver through a core-owned source set.
- observable success: a valid read-only packet contains only catalog-valid,
  hash-verified descriptors selected from an exact source. Invalid identity,
  profile, required evidence, schema, hash, or bounds blocks before workspace
  preparation and provider dispatch.

## Required Outcomes

### Outcome: Catalog-owned V1 artifact contract

- affected actor or system: policy authors, core, host, and starter-kit users.
- required result: `repo_config/harness.yaml` version 5 owns catalog kinds,
  schema IDs, retention, limits, profiles, required kinds, optional kinds, and
  deterministic kind priority.
- success condition: V1 permits only `terminal_observation` with schema
  `terminal_observation/v1` and `sanitized_command_trace` with schema
  `sanitized_command_trace/v1`. Core rejects every unlisted kind, free-form
  schema, duplicate catalog entry, and oversized descriptor.

### Outcome: Exact source and deterministic selection

- affected actor or system: controller and `harness-core`.
- required result: an external handoff request names exactly one terminal
  predecessor run ID and attempt ID plus an optional route-allowed profile.
  Core selects required kinds before optional kinds, then profile kind priority.
- success condition: required evidence cannot be crowded out by optional
  evidence. No controller request names artifact IDs, paths, content, or
  arbitrary ancestor runs.

### Outcome: One resolver preserves friction diagnosis

- affected actor or system: `friction-report`, `harness_diagnosis`, and core.
- required result: recurring-friction follow-up supplies its existing bounded
  terminal source set only to the core resolver. Thresholds, fingerprinting,
  and controller-free read-only diagnosis remain unchanged.
- success condition: direct and friction sources share catalog validation,
  profile bounds, selection ordering, descriptor construction, packet proof,
  and rejection behavior.

### Outcome: Read-only materialization and compatibility

- affected actor or system: Codex provider host and historical runs.
- required result: imports remain limited to read-only packet authority. Host
  validates and materializes selected descriptors outside writable workspace
  access, and exposes only artifact metadata and read path to packet prompt.
- success condition: request API 5 resolves packet API 6 for host API 5 and
  provider contract 5. Packet APIs 3, 4, and 5 remain readable under existing
  compatibility rules. New API 6 packets never dispatch against an API 4 host.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
|---|---|---|---|---|
| Which kinds exist now? | Policy retains `sanitized_command_trace`; terminal observation is core evidence. | `repo_config/harness.yaml`; `packages/harness-core/src/harness_core/managed.py` | high | Restrict V1 catalog to these two structured kinds. |
| How are artifacts selected now? | Request accepts one `{kind, source_run_id, source_attempt_id}` per artifact. | `packages/harness-core/src/harness_core/managed.py:_resolve_readonly_artifacts` | high | Replace public artifact references with one direct source plus profile. |
| Can plan lineage identify one source? | Coordination tracks task dependencies and latest task run, not predecessor attempt identity. | `packages/harness-core/src/harness_core/coordination.py`; `packages/harness-core/src/harness_core/managed.py:coordination_status` | high | External request owns exact predecessor run and attempt fields. |
| Does friction need several source runs? | Existing helper enumerates current candidate events in newest-first order. | `packages/harness-core/src/harness_core/managed.py:_friction_readonly_artifact_requests` | high | Keep internal friction source-set derivation; route it through shared resolver. |
| Can write-capable packets import? | Core rejects readonly artifacts when packet access is not `read_only`. | `packages/harness-core/src/harness_core/managed.py:_resolve_readonly_artifacts` | high | V1 handoff stays read-only. |
| Does host verify descriptor bytes? | Host reserializes, hashes, writes, and reports each descriptor. | `../codex-harness-host/src/codex_harness_host/adapter.py:_materialize_readonly_artifacts` | high | Preserve descriptor representation; add API 6 conformance proof. |
| What compatibility line exists? | Request API 4 resolves packet API 5 for host API 4 and provider contract 4. | `packages/harness-core/src/harness_core/compatibility.py` | high | Add explicit API 5/6/5/5 line; preserve historical readers. |

### Prototype and Validation Evidence

- prototype reference or `Not applicable: source and focused core/host tests
  prove current artifact resolution and materialization.`
- validated scenarios and states: terminal source run, retained trace byte
  limit, required diagnostic evidence, friction candidate enumeration, descriptor
  hash verification, and read-only artifact packet admission.
- findings incorporated into approved behavior: exact predecessor identity,
  V1-only schemas, required-first selection, no write-capable imports, and one
  resolver for direct and friction sources.
- rejected alternatives: controller-selected IDs; arbitrary source runs;
  recursive ancestor scans; imported evidence as acceptance proof; catalog kinds
  for claims, checks, reviews, research, diagnostics, or raw shell output;
  retaining request API 4 while removing its artifact-ID capability.

### Scope

- included behavior: policy version 5 catalog and profile grammar; request API
  5 direct handoff contract; internal friction source-set adapter; packet API 6
  proof; `run.json` audit; host API 5 conformance; generated routing and
  consumer setup documentation.
- affected boundaries: canonical policy, core config validation and resolver,
  run lifecycle, friction follow-up, packet compatibility, provider host,
  generated harness routing, and starter-kit output.
- admissible cases: no handoff; one direct terminal predecessor; one route
  default or caller-requested allowed profile; bounded recurring-friction source
  set; valid optional trace; missing optional trace; invalid or unavailable
  required terminal observation.
- compatibility expectation: existing packets remain readable. Fresh packets
  use only request API 5 and packet API 6 after policy migration.

### Non-Goals

- importing artifacts into write-capable packets;
- transitive re-export of imported descriptors or ancestor traversal;
- V1 support for claims, check results, validator results, research, reviews,
  diagnostic traces, source facts, or arbitrary JSON;
- changing friction thresholds, windows, fingerprints, follow-up routing, retry,
  delegation, skills, tool binding, workspace resume, or controller decisions;
- accepting imported artifacts for `diff`, check, validator, direct-boundary,
  or final-state acceptance criteria.

### Requirements and Behavioral Contract

#### Requirement: V1 catalog and profile grammar

- trigger or actor: policy validation and packet resolution.
- preconditions: policy version is 5 and route authority is `read_only`.
- required behavior: policy declares a unique catalog entry for each V1 kind
  with fixed schema ID, producer owner, retention rule, and byte limit.
  Profiles declare `lineage_mode`, `allowed_kinds`, `required_kinds`, ordered
  `kind_priority`, `base_compatibility`, `count_limit`, and `total_byte_limit`.
  `direct_terminal_diagnosis` requires `exact_packet_base`.
  `friction_terminal_diagnosis` requires `same_repository`. A route declares
  its allowed profile names and optional default profile.
- output or state change: packet carries resolved profile policy and V1
  descriptor limits. Generated routing guidance names routes with a handoff
  profile only when configured.
- failure behavior: duplicate, unknown, unstructured, write-route, negative,
  zero, oversized, or inconsistent catalog/profile values block before packet
  creation.
- observable acceptance: valid policy admits exact V1 profiles; malformed
  profile fixtures and `readonly_artifacts` on request API 5 reject.

#### Requirement: External direct predecessor handoff

- trigger or actor: controller submits request API 5 with `artifact_handoff`.
- preconditions: request route permits direct predecessor profile; source run
  is terminal; source attempt exists; source base and packet base meet selected
  compatibility relation.
- required behavior: `artifact_handoff` contains exactly
  `source_run_id`, `source_attempt_id`, and optional `profile`. Absence means
  no imported context. Present handoff resolves requested profile or route
  default. Controller cannot name artifact IDs, paths, contents, source lists,
  or ancestor runs.
- output or state change: core records exact source identity, resolved profile,
  rejected optional evidence, selected descriptor metadata, and deterministic
  digest in target attempt `artifact_handoff_audit`.
- failure behavior: missing source identity, unknown profile, no default,
  nonterminal source run, unavailable attempt, incompatible base, or absent
  required kind blocks before workspace preparation.
- observable acceptance: direct handoff accepts one exact eligible source and
  rejects all malformed or unallowed handoff requests with typed core errors.

#### Requirement: Required-first deterministic resolver

- trigger or actor: core resolves a direct or internal friction source set.
- preconditions: source identity and selected profile are valid.
- required behavior: core validates kind schema, producer, finalization, JSON
  serialization, SHA-256, per-artifact size, source compatibility, and profile
  limits. It selects one compatible artifact for every required kind before
  optional artifacts. It then selects optional artifacts by `kind_priority` and
  stable source order. Direct source order is its one declared attempt; friction
  source order is newest `occurred_at`, then `event_id`, both descending.
- output or state change: packet gets existing readonly descriptors plus
  immutable `artifact_handoff` proof containing profile, lineage mode, selected
  count, total bytes, and selection digest. Digest is SHA-256 of canonical JSON
  containing version, profile, lineage mode, ordered source pairs, ordered
  descriptor metadata, and optional rejection metadata.
- failure behavior: invalid optional evidence is excluded and audited. A
  missing required kind, incompatible required descriptor, duplicate source,
  duplicate selected descriptor, or exceeded required selection bound rejects
  handoff before dispatch.
- observable acceptance: optional trace cannot consume terminal-observation
  capacity; same eligible source set always yields same descriptor order and
  digest.

#### Requirement: Core-owned friction source set

- trigger or actor: `friction-report` prepares its existing
  `harness_diagnosis` follow-up.
- preconditions: current candidate meets existing distinct-run threshold and
  route selects `friction_terminal_diagnosis` profile.
- required behavior: core derives terminal source attempts only from candidate
  event records. It passes that bounded set to the shared resolver. Controller
  receives profile-level follow-up context, never artifact IDs.
- output or state change: target packet and audit identify the friction
  fingerprint and selected source run/attempt pairs.
- failure behavior: missing required terminal observation blocks the diagnostic
  follow-up with typed evidence. Friction policy values and event records remain
  unchanged.
- observable acceptance: recurring candidate produces same diagnostic profile
  and selected evidence order as current event order, without a second resolver.

#### Requirement: API 5/6/5/5 compatibility and host materialization

- trigger or actor: new policy resolves fresh packet or host dispatches packet.
- preconditions: policy requests core API 5 and provider host advertises host
  API 5 with contract version 5.
- required behavior: compatibility profile maps request API 5 to packet API 6,
  host API 5, and provider contract 5. Packet API 6 descriptor structure stays
  `{kind, source_run_id, source_attempt_id, sha256, byte_length, content}`.
  Host verifies byte length and SHA-256, materializes only packet descriptors,
  and executes handoff routes with read-only packet tools.
- output or state change: source run stays immutable; successor attempt carries
  packet proof and audit; host reports exact materialized descriptors and root.
- failure behavior: API skew, descriptor shape/hash conflict, unmaterialized
  artifact, unexpected artifact, or attempted mutation through read-only tools
  blocks dispatch. Historical packet APIs 3, 4, and 5 remain readable but do
  not gain handoff fields.
- observable acceptance: matching API 5 host dispatches API 6 packet; API 4
  host rejects it before workspace or provider work; host conformance proves
  imported evidence cannot be written by a read-only packet tool.

### Constraints and Alternatives

- constraint: catalog content can cross run and agent boundaries. V1 must use
  only structured, bounded, preexisting sanitized or normalized evidence.
- alternative: admit generic JSON evidence.
  - benefit: faster catalog expansion.
  - trade-off: secret leakage and unprovable producer semantics.
  - reason accepted or rejected: rejected. New kinds need successor
    specification with schema, producer, sanitization, and proof.
- alternative: retain request API 4 with optional handoff fields.
  - benefit: avoids protocol release.
  - trade-off: keeps public arbitrary artifact references valid.
  - reason accepted or rejected: rejected. Request API 5 removes controller
    artifact-ID selection cleanly.
- alternative: permit imports in write-capable packets.
  - benefit: broader continuation context.
  - trade-off: changes sandbox and authority boundary.
  - reason accepted or rejected: rejected for V1. Read-only diagnosis proves
    catalog behavior without widening write access.

## Design Decisions

### Decision: Narrow catalog, shared resolver

- context: current terminal observation and retained trace already have owned
  producers and bounded formats; other proposed kinds do not.
- selected approach: one catalog grammar admits two V1 kinds. One core resolver
  accepts either a public direct source or core-created friction source set.
- rationale: preserves current friction diagnosis while deleting public
  controller artifact selection and avoiding duplicated selection code.
- alternatives considered: generic artifact registry; route-specific resolver;
  direct source only with reduced friction evidence.
- accepted trade-offs: V1 defers broader evidence reuse and write-capable
  handoffs.
- affected owners and boundaries: policy owns allowed kinds/profiles; core owns
  resolver/audit; host owns byte verification/materialization.

### Decision: Explicit source and required-first bounds

- context: plan lineage has no exact predecessor attempt and optional evidence
  could otherwise consume profile capacity.
- selected approach: public request owns one exact source run/attempt. Resolver
  reserves bounded capacity for each required kind before optional ranking.
- rationale: creates one reproducible lineage identity and prevents false
  rejection when required evidence exists.
- alternatives considered: infer latest dependency run; choose optional first;
  let controller select descriptor IDs.
- accepted trade-offs: callers must provide exact source identity; no arbitrary
  multi-source public handoff.
- affected owners and boundaries: request API, core resolver, attempt audit,
  and friction internal adapter.

### Decision: New API line with historical readers

- context: API 4 exposes caller-selected descriptor references. Removing that
  capability changes request semantics and packet proof.
- selected approach: policy schema 5, request API 5, packet API 6, host API 5,
  provider contract 5, core release `0.1.18`, and host release `0.1.4`.
- rationale: protocol identity makes unsupported old caller behavior fail before
  packet creation while preserving old packets as historical evidence.
- alternatives considered: silent API 4 field removal; optional API 5 fields
  under packet API 5.
- accepted trade-offs: coordinated core and host upgrade plus new published core
  tag `harness-core-v0.1.18`.
- affected owners and boundaries: compatibility matrix, package metadata, host
  source pin, consumer setup, and deployment preflight.

### Compatibility, Migration, and Risk

- old behavior: request API 4 receives caller-provided descriptor references;
  route-local `readonly_artifacts` owns kind rules; friction has its own source
  selector.
- new behavior: request API 5 receives only exact source plus profile; policy
  owns catalog/profiles; shared resolver produces packet descriptors and audit.
- compatibility boundary: packet APIs 3, 4, and 5 remain readable. Fresh policy
  version 5 creates API 6 packets only with host API 5/provider contract 5.
- migration or backfill: update canonical policy, core compatibility, core
  package version, host pin/lock, host contract, generated routing, and consumer
  setup. Historical `run.json` files receive no backfill.
- rollout and rollback: publish `harness-core-v0.1.18`, update host lock and
  release `codex-harness-host` 0.1.4, run host preflight, then admit new packets.
  Rollback restores matching policy/core/host release line; API 6 terminal runs
  remain preserved and never resume under API 4 host.
- deprecation or consumer impact: API 4 callers must create API 5 successor
  requests. API 5 rejects `readonly_artifacts` at public admission.
- risk:
  - source/audit mismatch. mitigation: packet-to-run audit digest and direct
    resolver tests.
  - required evidence starvation. mitigation: required-first reservation tests.
  - host mismatch. mitigation: typed compatibility admission and host API 5
    conformance tests.
  - sensitive evidence expansion. mitigation: V1 fixed schemas only.

## Invariants and Edge Cases

### Invariants

- `repo_config/harness.yaml` is sole catalog and profile policy owner.
- V1 descriptors originate only from exact terminal source attempts and use
  fixed kind/schema/producer contracts.
- External request owns exact direct source identity, never artifact identity.
- Core owns source validation, selection, descriptor hashing, audit, and
  rejection codes.
- Required kinds reserve selection capacity before optional kinds.
- Imported artifacts are context only; fresh successor proof remains mandatory.
- API 6 imports exist only in read-only packet authority and host materializes
  only descriptors contained in immutable packet.
- Historical run files and packets remain immutable.

### Edge Cases

- empty or minimal input: missing `artifact_handoff` produces fresh packet with
  no descriptors or audit selection.
- normal and large input: profile count and total-byte bounds reject overflow
  before workspace preparation.
- duplicate, missing, malformed, or unsupported data: duplicate source pairs,
  duplicate descriptors, unknown kind/schema/profile, malformed hash, and
  absent attempt reject.
- retry, cancellation, timeout, partial failure, or concurrency: terminal
  blocked and unvalidated source runs remain eligible only for valid V1 kinds;
  retry creates fresh API 5 request and packet; no source run is modified.
- migration or mixed-version state: APIs 3–5 remain readable; API 6 dispatch
  requires matching API 5 host and provider contract 5.
- generated-source consistency: routing guidance and starter output regenerate
  only from canonical policy and tracked docs.
- security or accessibility boundary: raw HTTP, unbounded command output,
  workspace trees, provider handles, agent threads, incomplete claims, secrets,
  and ambient files are never catalog artifacts. UI is not applicable.

## Validation Plan

### Backend Verification Claims

- direct boundary: table-driven policy/config validation and
  `resolve_managed_packet` tests cover catalog/profile and API 5 admission.
- important success and failure behavior: exact direct source, internal friction
  source set, required-first ordering, optional exclusion, missing required
  artifact, unsupported profile, bad hash, oversized payload, and API skew.
- final state or side effects: immutable packet descriptor/proof matches
  target-attempt audit; no source `run.json` mutation occurs.
- rollback, retry, duplicate, or idempotency behavior: duplicate request
  identity and unsupported compatibility fail before dispatch; historical packet
  readers remain stable; retry creates fresh packet/audit.
- canonical contract and conformance proof: core compatibility matrix and host
  API 5 adapter tests prove identical packet descriptor contract.
- real dependencies requiring proof: published `harness-core-v0.1.18` host pin,
  regenerated `uv.lock`, host capabilities, and transport preflight.
- representative-operation trace mechanism: packet, target attempt audit, host
  materialization evidence, and friction follow-up result trace exact source to
  selected descriptors.
- performance claim and threshold: Not applicable. Existing count and byte
  limits bound resolver work; no throughput target is claimed.

### Acceptance Criterion: Direct handoff resolves one bounded source

- setup or precondition: API 5 read-only route allows
  `direct_terminal_diagnosis`; source run is terminal with normalized terminal
  observation and optional retained trace.
- action: resolve packet with exact run/attempt and profile.
- expected result: packet descriptors and target audit contain terminal
  observation first, optional trace second, matching hash/byte evidence, profile,
  source identity, and digest.
- failure condition: caller-selected artifact ID, unknown profile, source
  mismatch, missing required terminal observation, or incompatible base admits.
- proof method: direct resolver/run-record tests.
- expected evidence: packet and `run.json` audit assertions plus automated
  output.

### Acceptance Criterion: Required evidence survives optional pressure

- setup or precondition: profile has required terminal observation, optional
  trace, and bounds allowing only required evidence.
- action: resolve eligible source set containing both kinds.
- expected result: terminal observation is selected; trace is excluded and
  audited without rejection.
- failure condition: optional artifact consumes capacity and causes required-kind
  rejection.
- proof method: boundary-sized selection tests.
- expected evidence: stable ordered descriptor and audit rejection assertions.

### Acceptance Criterion: Friction follow-up shares resolver

- setup or precondition: current friction candidate contains terminal attempts
  from threshold-qualified source runs.
- action: generate follow-up and resolve its diagnosis packet.
- expected result: core passes candidate source set to
  `friction_terminal_diagnosis`, returns profile-level handoff data, and emits
  one audit/descriptor contract.
- failure condition: controller receives artifact IDs or friction source order
  differs from newest event order.
- proof method: friction report and packet-resolution tests.
- expected evidence: follow-up payload, ordered packet descriptors, and audit
  source-pair assertions.

### Acceptance Criterion: Host and compatibility block unsafe dispatch

- setup or precondition: matching and mismatched API 5 host fixtures plus valid
  API 6 packet descriptors.
- action: dispatch matching host, then attempt host API 4 dispatch and write
  through a read-only packet tool.
- expected result: matching host rehashes/materializes descriptors; mismatched
  host rejects before workspace preparation; write attempt fails.
- failure condition: API 4 host begins workspace work, descriptor mismatch
  materializes, or read-only evidence can be mutated.
- proof method: host adapter and compatibility matrix tests.
- expected evidence: host materialization record, typed compatibility failure,
  and failed write probe.

### Acceptance Criterion: Derived consumer surfaces stay synchronized

- setup or precondition: canonical policy and consumer setup procedure reflect
  API 5/6/5/5 line.
- action: render routing guidance and synchronize starter-kit output.
- expected result: generated guidance and starter kit describe handoff profiles
  without becoming a policy owner.
- failure condition: generated drift, stale API values, or copied artifact-ID
  request guidance remains.
- proof method: renderer, starter-kit, and repository-contract validators.
- expected evidence: clean generated drift output and validator results.

## Completion Criteria

Specification is complete when:

1. policy version 5 has one V1 catalog and route-owned direct/friction profiles;
2. request API 5 names exact source identity and never artifact IDs;
3. core shares one resolver, reserves required evidence capacity, and writes
   matching packet proof plus attempt audit;
4. friction follow-up keeps its current thresholds and source ordering through
   that resolver;
5. API 6/host API 5 compatibility, release pins, and host read-only
   materialization are proven;
6. historical packets remain readable and imported evidence cannot satisfy fresh
   successor acceptance;
7. routing guidance, consumer setup, and starter-kit output regenerate from
   canonical sources; and
8. implementation sequencing stays in
   `docs/superpowers/plans/2026-08-08-harness-artifact-handoff-ssot-plan.md`.
