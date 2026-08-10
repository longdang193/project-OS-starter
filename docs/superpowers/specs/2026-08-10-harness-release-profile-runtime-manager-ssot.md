---
artifact_type: spec
template_id: detailed-specification
status: active
layer: change
name: harness-release-profile-runtime-manager-ssot
targets:
  - packages/harness-core
  - packages/harness-core-launcher
  - C:/Users/HOANG PHI LONG DANG/repos/codex-harness-host
  - C:/Users/HOANG PHI LONG DANG/repos/project-OS-starter-kit
  - docs/operating_system/procedures/harness-core-consumer-setup.md
---

# Harness Release Profile and Runtime Manager SSOT

## Goal and Problem

### Problem

- Routine harness releases require manual alignment of core compatibility,
  host lock provenance, host command paths, consumer provider-contract fields,
  generated guidance, and local PATH state.
- Current locked source-host invocation proves correct runtime, but each
  consumer and operator repeats release-specific `uv` commands. A bare PATH
  host can resolve stale code.
- Consumer policy currently owns request API and route intent, but also copies
  provider `contract_version`, a runtime compatibility fact owned by core.
- Consequence: routine implementation updates receive broad manual matrix and
  deployment work; incompatible pairs can be configured, then rejected only at
  admission.

### Goal

Deliver one low-management runtime path with one owner per fact:

- core owns protocol compatibility profiles and their canonical digest;
- existing `harness-core-launcher` owns stable local bootstrap and active
  runtime-pointer selection;
- host owns immutable release assembly, provider lifecycle, capability report,
  preflight, and managed dispatch;
- consumer policy keeps route intent and its versioned request API only;
- kit emits one bootstrap command without release pins or host paths.

Observable success:

- controller invokes one stable launcher command for upgrade, rollback,
  doctor, preflight, and managed run;
- managed invocation never resolves bare `codex-harness-host` from PATH;
- a core/host/profile mismatch fails before provider, workspace, packet, or
  `run.json` work;
- compatible implementation-only releases need no consumer policy or kit sync;
- failed activation preserves last verified runtime byte-for-byte.

## Required Outcomes

### Outcome: Core-owned protocol profile

- **Affected actor or system:** harness-core, host, launcher, controller.
- **Required result:** core exposes one `harness_runtime_protocol_profile/v1`
  value for each dispatchable compatibility profile.
- **Success condition:** profile includes `profile_id`, `profile_digest`,
  `request_api`, `packet_api`, `host_api`, `provider_id`,
  `provider_contract`, and sorted required baseline capability IDs. Digest is
  SHA-256 of core's existing canonical UTF-8 JSON serializer over every field
  except `profile_digest`.

### Outcome: Trusted immutable host release profile

- **Affected actor or system:** host release, launcher, local operator.
- **Required result:** every verified staged v1 host runtime contains exactly
  one `harness_runtime_release/v1` document generated from core protocol
  profile and locked source provenance.
- **Success condition:** document contains `release_profile_id`,
  `release_profile_digest`, `protocol_profile`, `host_package_release`,
  `host_commit`, `core_package_release`, and `core_commit`. Its digest uses
  the same core canonical JSON serializer, excluding digest field. It is an
  immutable staged-runtime snapshot, never a second compatibility table or a
  file committed into the host source tree.

### Outcome: Atomic verified runtime activation

- **Affected actor or system:** launcher, local operator, controller.
- **Required result:** launcher stages a trusted host release, verifies it,
  then changes one active pointer atomically.
- **Success condition:** pointer schema `harness_runtime_pointer/v1` at
  `$HOME/.codex/harness/current.json` contains `active_profile_id`,
  `active_profile_digest`, `active_root`, and optional previous profile ID,
  digest, and root. Pointer always names one fully verified profile and one
  rollback target.

### Outcome: Uniform managed invocation

- **Affected actor or system:** launcher, host, core, controller, agent.
- **Required result:** launcher reads active pointer and invokes host from
  `active_root` only. Host preflight, capability evidence, packet, and terminal
  observation carry matching release-profile ID and digest.
- **Success condition:** core validates one shared runtime-profile admission
  before provider launch, workspace materialization, packet creation, or
  `run.json` mutation.

### Outcome: Thin consumer policy and kit guidance

- **Affected actor or system:** consumer repository and starter kit.
- **Required result:** current consumer policy retains
  `harness_core.request_api`, runtime provider ID, route, authority, toolset,
  verification, and scheduling policy. It does not select host API, packet API,
  provider contract, host source path, package pin, or release profile.
- **Success condition:** compatible runtime releases do not require consumer
  policy edit or kit sync. Kit sync occurs only for its own generated-surface or
  consumer-policy schema change.

## Design Analysis

### Current State and Evidence

| Question | Evidence | Source | Confidence | Specification implication |
| --- | --- | --- | --- | --- |
| Who owns protocol compatibility? | Core has one compatibility matrix and dispatch admission helper. | `packages/harness-core/src/harness_core/compatibility.py` | high | Export profile normalization from core; do not recreate it. |
| What currently proves locked host runtime? | Deployment script invokes host through locked project, checks non-editable core provenance, capabilities, and preflight. | `scripts/deploy_harness_core_to_host.ps1` | high | Reuse locked host source as v1 trust channel. |
| Is PATH safe for managed host dispatch? | Canonical guidance prohibits bare host command because it can resolve stale user tool code. | `docs/operating_system/templates/agents/root-AGENTS.template.md` | high | Launcher pointer is sole host executable selector. |
| Who owns request API? | Canonical routing guidance and policy assign request API to consumer `harness.yaml`. | `repo_config/harness.yaml`; root agent template | high | Preserve request API ownership and versioned request boundary. |
| Does a bootstrap package already exist? | `harness-core-launcher` returns typed environment evidence when core cannot load. | `packages/harness-core-launcher/src/harness_core_launcher/loader.py` | high | Extend existing bootstrap; add no package or daemon. |

### Prototype and Validation Evidence

- **Prototype reference:** Not applicable: backend protocol and local runtime
  selection have no graphical prototype.
- **Validated scenario:** policy provider contract `6` with packet API `8` and
  live host API/contract `7`.
- **Finding:** initial core admission rejects
  `harness_core_packet_dispatch_incompatible` before packet work.
- **Incorporated behavior:** static historical-policy shape remains readable;
  runtime compatibility is enforced once at first admission.
- **Rejected alternatives:** bare PATH host fallback, consumer-specific release
  pins, host-owned copy of core compatibility matrix, new bootstrap package,
  custom signature registry, and automatic upgrade during dispatch.

### Scope

- **Included behavior:** profile serialization and admission; release snapshot
  generation; launcher pointer activation and rollback; active-root invocation;
  host evidence binding; provider-contract policy migration; kit/guidance
  generation; release conformance tests.
- **Affected boundaries:** core compatibility, launcher CLI, host CLI and
  capability/preflight/run evidence, consumer policy parser, starter-kit
  canonical inputs, generated agent guidance, local user runtime directory.
- **Admissible cases:** no active profile; first install; same-profile replay;
  verified upgrade; failed stage; failed preflight; activation contention;
  rollback; stale PATH executable; core/host/profile mismatch; legacy consumer
  contract field; current and historical packets.
- **Compatibility expectation:** packet and `run.json` remain immutable;
  historical packet readers remain supported under existing compatibility rules;
  no new runtime manager changes terminalization or provider process ownership.

### Non-Goals

- Package-index distribution, remote runtime download, or automatic update.
- Provider endpoint, launcher command, credential, authority, or attester
  configuration changes.
- Request API removal, unversioned request transport, or consumer routing
  redesign.
- Historical run evidence rewrite, packet backfill, or direct process action.
- New scheduler, daemon, registry service, or additional installable package.

### Requirements and Behavioral Contract

#### Requirement: V1 trust channel

- **Trigger or actor:** launcher `upgrade` receives a local host source root.
- **Preconditions:** source root is clean and detached or checked out at a full
  Git commit; `uv.lock` declares an immutable non-editable core source; source
  commit and lock provenance are readable. Launcher does not implement a
  second canonical JSON validator.
- **Required behavior:** launcher creates a detached Git worktree at a unique
  `$HOME/.codex/harness/staging/<id>/host`, then runs `uv sync --locked` there.
  Staged host invokes core profile builder and writes release profile from core
  protocol profile, staged host package release, staged `HEAD`, and installed
  core provenance.
  Launcher verifies profile, identity, capabilities, and bounded preflight,
  then atomically renames stage to
  `$HOME/.codex/harness/profiles/<release_profile_digest>/` before activation.
- **Output or state change:** verified immutable profile directory and staged
  pointer candidate only.
- **Failure behavior:** missing, dirty, malformed, unknown-field, digest,
  commit, lock, identity, capability, or preflight failure rejects profile and
  leaves current pointer unchanged. Generated malformed or conflicting profile
  rejects before pointer activation; failure removes only unreferenced staging
  directory.
- **Observable acceptance:** one rejected profile cannot become active or
  dispatch work.

#### Requirement: Pointer transaction and idempotency

- **Trigger or actor:** verified `upgrade` or `rollback`.
- **Preconditions:** launcher acquires exclusive local activation lock at
  `$HOME/.codex/harness/activation.lock`.
- **Required behavior:** launcher writes pointer candidate to same-directory
  temporary file, flushes it, and atomically replaces `current.json`. It never
  mutates verified profile directories. Same active digest returns success
  without staging or pointer rewrite. `rollback` swaps active and previous
  pointer entries only when previous directory still verifies.
- **Output or state change:** pointer stores current and immediately previous
  verified profile. After successful replacement launcher may remove only
  profile directories not named by either pointer entry.
- **Failure behavior:** lock contention returns
  `harness_runtime_profile_activation_busy`; crash or write failure leaves old
  pointer valid and temporary files ignored; missing previous profile returns
  `harness_runtime_profile_rollback_unavailable`.
- **Observable acceptance:** activation is replay-safe and crash-safe; current
  plus previous profile are always retained.

#### Requirement: Active-profile invocation and admission

- **Trigger or actor:** launcher `doctor`, `preflight`, or managed run.
- **Preconditions:** `current.json` exists and target directory verifies.
- **Required behavior:** launcher invokes only exact host project in pointer.
  It never searches PATH for host. Host reads staged release profile and
  emits release-profile ID/digest in identity, capabilities, preflight, and
  terminal evidence. Core resolves policy request API as today, derives active
  provider contract from core protocol profile, then validates exact profile,
  host API, host contract, and required capabilities through shared admission.
- **Output or state change:** packet stores verified release-profile snapshot;
  `run.json` receives it only through immutable packet and host/core evidence.
- **Failure behavior:** absent pointer returns
  `harness_runtime_profile_unavailable`; invalid local data returns
  `harness_runtime_profile_invalid`; untrusted source or provenance mismatch
  returns `harness_runtime_profile_untrusted`; core/host disagreement returns
  `harness_runtime_profile_mismatch`; preflight failure returns
  `harness_runtime_profile_preflight_failed`. All reject before packet work.
- **Observable acceptance:** stale PATH host cannot affect managed result;
  every dispatchable packet and host evidence agree on profile digest.

#### Requirement: Consumer policy migration

- **Trigger or actor:** core loads active consumer policy.
- **Preconditions:** policy uses current or legacy supported schema.
- **Required behavior:** policy continues to own request API and route intent.
  Core ignores legacy provider `contract_version` for current profile
  resolution, reports one migration diagnostic, and derives provider contract
  solely from core protocol profile. New consumer policy schema omits
  `contract_version`; its presence is invalid only in that new schema.
- **Output or state change:** packet profile contract comes from core, never
  policy. Existing policy bytes are not automatically rewritten.
- **Failure behavior:** an unknown provider, unsupported policy request API, or
  incompatible active profile still rejects at initial admission. Historical
  packets retain their own immutable provider-contract evidence.
- **Observable acceptance:** unchanged legacy policy dispatches with core-owned
  contract; new generated policy cannot copy runtime compatibility values.

#### Requirement: Release and kit classification

- **Trigger or actor:** release pipeline classifies source change.
- **Required behavior:** unchanged protocol profile, launcher external
  behavior, host external behavior, and consumer schema is
  implementation-only. Changed profile data or manager/host evidence contract
  is profile release. Changed consumer schema or kit canonical generated input
  is consumer-schema release.
- **Failure behavior:** release claiming a lower tier despite changed profile,
  manager, host evidence, or consumer schema is rejected by conformance check.
- **Observable acceptance:** compatible implementation releases require no kit
  sync; consumer-schema release triggers generated-output validation.

### Constraints and Alternatives

- **constraint:** v1 release source must use existing Git and `uv` locked-source
  mechanics. No network or package index is trusted by this specification.
- **alternative:** sign a separate profile with custom authority registry.
  - benefit: future remote distribution.
  - trade-off: new key, revocation, and operator management.
  - reason rejected: source commit plus clean detached worktree and lock are
    sufficient for local v1 and reuse current tooling.
- **alternative:** host CLI alone owns bootstrap and pointer.
  - benefit: fewer packages named in guidance.
  - trade-off: no stable non-host entrypoint exists when host is missing or
    stale.
  - reason rejected: existing launcher already owns typed environment bootstrap.
- **alternative:** move request API into runtime profile.
  - benefit: fewer consumer policy values.
  - trade-off: breaks existing consumer/core versioned interface and requires
    new intent schema.
  - reason rejected: not needed to remove runtime release drift.

## Design Decisions

### Decision: One profile chain, separate fact owners

- **context:** one editable manifest cannot own both core protocol semantics and
  host release provenance without creating cross-repository duplicate sources
  or self-referential Git commit data.
- **selected approach:** core owns canonical protocol profile. Host release
  stages immutable resolved snapshot plus provenance. Launcher owns only active
  pointer. Packets and evidence retain immutable snapshots.
- **rationale:** each fact has one editable owner; downstream copies are bound
  evidence checked against upstream owner.
- **alternatives considered:** policy-owned contract, host-owned compatibility
  table, central registry service, and duplicated kit release file.
- **accepted trade-offs:** v1 needs local clean source checkout for upgrade.
- **affected owners and boundaries:** core, host, launcher, consumer policy,
  starter kit, user-local runtime directory.

### Decision: Existing launcher is stable runtime manager

- **context:** consumers need stable invocation even when host path or PATH
  tool is stale.
- **selected approach:** extend `harness-core-launcher`; no new package or
  daemon. It reads pointer and invokes host from verified active root. Host
  remains sole provider lifecycle and evidence producer.
- **rationale:** reuses installed bootstrap package and preserves core/host
  boundary.
- **alternatives considered:** bare host CLI, per-consumer wrapper, new runtime
  package.
- **accepted trade-offs:** launcher gains local filesystem and subprocess work,
  bounded to pointer and verified profile roots.
- **affected owners and boundaries:** launcher controls selection; host controls
  execution; core controls admission.

### Decision: Current plus previous verified profile retention

- **context:** rollback must not require rediscovery or re-download, while
  unbounded profile retention creates local cleanup work.
- **selected approach:** pointer retains exactly active and previous verified
  profile. Activation removes all other profile directories only after atomic
  pointer commit.
- **rationale:** one-step rollback covers failed release while bounding disk and
  administration.
- **alternatives considered:** no rollback, arbitrary retention config, and
  unlimited history.
- **accepted trade-offs:** older releases require explicit restage from trusted
  source root.
- **affected owners and boundaries:** launcher cleanup only; no agent cleanup.

### Decision: Legacy provider-contract field is non-authoritative

- **context:** existing consumers contain provider contract version but current
  core profile owns compatibility.
- **selected approach:** legacy schemas read and diagnose field without using
  it for current profile resolution. New schema forbids field. No automatic repo
  mutation occurs.
- **rationale:** migration is safe across many consumers without repeated
  manual updates and does not preserve a competing runtime source.
- **alternatives considered:** immediate rejection and forever-authoritative
  legacy field.
- **accepted trade-offs:** old policy text can contain inert migration metadata
  until consumer adopts new schema.
- **affected owners and boundaries:** core policy normalization, kit canonical
  policy, consumer validation, packet resolver.

### Compatibility, Migration, and Risk

- **old behavior:** each consumer invokes locked host source manually and pins
  provider contract in policy; bare PATH host is prohibited but can still be
  invoked accidentally outside guidance.
- **new behavior:** launcher owns verified active-root selection; core derives
  current provider contract; host and packet prove same profile digest.
- **compatibility boundary:** existing request API and packets remain unchanged.
  Legacy consumer provider contract is ignored only for current resolution;
  historical packet evidence remains authoritative for historical reads.
- **migration or backfill:** no `run.json` or packet mutation. Host release adds
  no committed profile document. Launcher staging creates release profile and
  initial install creates pointer. Kit emits new schema only for newly generated
  or explicitly migrated consumers.
- **rollout and rollback:** release core protocol/profile support, then host
  profile and launcher, then kit/docs. Activate only after locked stage passes.
  Launcher rollback returns previous verified profile. Revert source releases
  normally; never mutate release profile or past packet.
- **deprecation or consumer impact:** manual locked-host commands remain a
  temporary documented bridge only until launcher manages active profile. Bare
  host command remains prohibited.
- **risk:** local source trust, pointer corruption, stale external launcher,
  host/core mismatch, migration ambiguity, and accidental profile cleanup.
  - **mitigation:** clean full-commit verification, lock provenance, atomic
    pointer, existing launcher bootstrap, shared core admission, explicit
    migration diagnostics, and two-profile retention.

## Invariants and Edge Cases

### Invariants

- Core is only editable owner of protocol compatibility and canonical profile
  digest.
- Host never writes `run.json`; launcher never performs provider lifecycle or
  terminalization.
- Pointer-selected host root is sole managed host executable source.
- Active and previous profile directories are verified and immutable after
  staging.
- Core admission checks same profile data for initial and continuation paths.
- Consumer policy request API stays versioned and policy-owned.
- Provider endpoint, launch command, credentials, authorities, and private keys
  never enter profile, pointer, packet, kit, or diagnostics.
- Historical run, packet, and receipt bytes remain unchanged.

### Edge Cases

- **No active pointer:** return typed unavailable state; do not use PATH or
  create packet.
- **Same profile upgrade:** return idempotent current result; no pointer rewrite
  or profile cleanup.
- **Malformed, oversized, unknown-field, or digest-conflicting generated
  profile:** reject before pointer activation and remove staged directory.
- **Dirty source, changed HEAD, editable core, or lock provenance mismatch:**
  reject as untrusted; retain current pointer.
- **Preflight timeout or failure:** remove staged unreferenced profile; retain
  current and previous profiles.
- **Concurrent activation:** one holder proceeds; other returns typed busy;
  neither dispatches through staged directory.
- **Crash during activation:** old pointer remains valid or new pointer names
  fully verified immutable directory; orphan temporary file is ignored.
- **Stale PATH host:** launcher does not consult it; doctor reports resolved
  active host path only.
- **Host reports mismatched profile, API, contract, or capability:** reject
  before provider or packet work.
- **Legacy policy contract field:** report migration diagnostic; do not treat
  copied value as compatibility authority.
- **New policy schema with legacy field:** static validation rejects.
- **Historical packet without release profile:** preserve read behavior; do not
  fabricate profile or use it to authorize new dispatch.

## Validation Plan

### Backend Verification Claims

- **direct boundary:** test core profile serialization/digest/admission,
  launcher profile validation/activation/rollback/dispatch selection, host
  profile evidence, and consumer policy normalization.
- **important success and failure behavior:** prove first install, matching
  preflight, same-digest replay, mismatch rejection, malformed profile, dirty
  source, lock mismatch, editable core, failed preflight, no pointer, stale
  PATH, contention, rollback, legacy policy, and new-schema rejection.
- **final state or side effects:** assert profile directory content, pointer
  bytes, retained current/previous directories, packet snapshot, host evidence,
  and no `run.json` on every pre-admission failure.
- **rollback, retry, duplicate, or idempotency behavior:** verify identical
  upgrade replay, failed activation pointer preservation, activation crash
  injection before/after replacement, contention result, and rollback swap.
- **canonical contract and conformance proof:** core compatibility profile,
  release profile, pointer schema, host capability/preflight/terminal evidence,
  consumer-policy schemas, kit generated surfaces, and agent template sync.
- **real dependencies requiring proof:** temporary Git repository/worktree,
  `uv.lock` source pin, staged virtual environment, local activation lock,
  atomic pointer write, and host preflight subprocess.
- **representative-operation trace mechanism:** launcher doctor and managed run
  emit release profile ID/digest through host evidence into packet; compare
  chain against active pointer and core profile.
- **performance claim and threshold:** Not applicable: no performance claim.

### Acceptance Criterion: One compatibility source

- **setup or precondition:** matching and mismatched core protocol profiles,
  host evidence, and policy request API fixtures.
- **action:** admit initial request and planned continuation.
- **expected result:** both paths use one core profile and reject identical
  mismatch conditions before packet/provider work.
- **failure condition:** host, policy, launcher, or continuation contains a
  duplicate compatibility table or admits a mismatch.
- **proof method:** focused direct core API tests and source-to-profile
  conformance tests.
- **expected evidence:** deterministic profile digest and typed rejection.

### Acceptance Criterion: Atomic runtime selection

- **setup or precondition:** temporary clean host source at full commit,
  matching lock, valid release profile, existing active pointer, and controlled
  failed preflight or write fault.
- **action:** install, repeat install, inject failure, contend activation, then
  roll back.
- **expected result:** only verified directories become active; same install is
  idempotent; current pointer survives failure; rollback activates previous;
  profile count is at most two after successful activation.
- **failure condition:** pointer references partial/missing directory, failure
  changes prior pointer, or concurrent caller dispatches staged root.
- **proof method:** temporary filesystem, Git worktree, subprocess fixtures,
  pointer byte assertions, and simulated atomic-replace fault.
- **expected evidence:** pointer/profile directory state and typed outcomes.

### Acceptance Criterion: Managed dispatch profile binding

- **setup or precondition:** active verified profile and a stale host executable
  earlier on PATH.
- **action:** run launcher doctor, capabilities, preflight, and one managed
  read-only probe.
- **expected result:** resolved host path comes from pointer; host/core/packet
  evidence have same release-profile digest; stale PATH executable is unused.
- **failure condition:** ambient host starts, packet lacks profile snapshot, or
  mismatch reaches provider/workspace work.
- **proof method:** stub executable, captured invocation path, direct host/core
  tests, and live bounded provider probe.
- **expected evidence:** path trace, matching profile evidence, and no packet on
  forced mismatch.

### Acceptance Criterion: Consumer and kit migration

- **setup or precondition:** legacy schema policy with provider contract, new
  schema policy without it, and generated starter-kit consumer.
- **action:** validate and resolve both policies; build and validate kit; run
  agent-adapter sync check.
- **expected result:** legacy field generates diagnostic but does not control
  profile; new policy rejects field; generated guidance invokes launcher and
  contains no package pins, host path, host API, packet API, or provider
  contract.
- **failure condition:** consumer policy can override profile, compatible
  implementation release requires kit sync, or generated output is hand-edited.
- **proof method:** policy fixtures, packet assertions, kit build/validation,
  rendered adapter checks, and repository contract validation.
- **expected evidence:** normalized policy, profile-bound packet, and clean
  generated-surface checks.

## Completion Criteria

Specification is complete when:

1. core protocol profile, host release profile, and launcher pointer schemas,
   identities, canonical digests, and typed errors are explicit
2. v1 trusted locked-source channel, native worktree staging, atomic pointer,
   idempotency, contention, cleanup, and rollback semantics are explicit
3. launcher, host, and core ownership preserves existing lifecycle boundaries
   without new package, daemon, trust registry, or dispatch-time upgrade
4. consumer request API remains policy-owned while provider contract is
   core-owned for current resolution
5. legacy policy and historical packet migration preserves evidence without
   backfill or forced immediate consumer update
6. kit owns generated-surface epoch and sync timing; profile contains no kit
   generation metadata
7. validation covers profile, provenance, pointer transaction, PATH isolation,
   admission, host evidence, policy migration, kit surfaces, and bounded live
   managed probe
