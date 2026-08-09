---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: harness-claim-repair-ssot
parent_spec: docs/superpowers/specs/2026-08-08-harness-claim-repair-ssot.md
targets:
  - agents/roles.yaml
  - repo_config/harness.yaml
  - packages/harness-core
  - ../codex-harness-host
  - docs/operating_system/procedures
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - AGENTS.md
  - README.md
  - uv.lock
---

# Harness Claim Repair SSOT Plan

## Goal

Deliver typed claim contracts, core-owned claim observations, and one
same-thread read-only repair before controller successor handling. Move current
API 5 requests to packet API 7 / host API 6 / provider contract 6. Preserve
packet API 6 runtime support through released host 0.1.4 and never use a fresh
repair context.

## Implementation Outcomes

### Typed V7 Packet Contract

`agents/roles.yaml` contains one `claim_fields` type catalog. Policy schema V6
contains generic `claim_repair` settings plus one dedicated
`claim_repair_failed` friction follow-up. Core resolves those facts into packet
API 7 lane claim schemas without field-name type branches.

### Core-Owned Repair Lifecycle

Core classifies `claim_observation/v1`, admits only completed same-thread
agent lanes, performs at most one repair under finalization reserve, and records
safe repair evidence. Valid repair continues same attempt. Failed repair emits
`claim_invalid` plus `claim_repair_failed`; ineligible paths never dispatch
repair.

### Host API 6 Exact-Thread Repair

Codex host API 6 advertises and enforces `claim_repair_same_thread`. It parses
completion into typed observation, continues exact original thread with a
read-only no-tool turn, and cannot create a fresh repair thread. Host 0.1.5
pins released `harness-core` 0.1.19.

### Aligned Guidance and Consumers

Canonical adapter, consumer, and generated agent guidance describe V7 repair,
V6 compatibility, preserved `writer_completion_missing`, and new recurring
repair-failure diagnosis. Generated `AGENTS.md` derives from canonical template.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current workspace for `project-OS-starter`; checked-out sibling `../codex-harness-host` only after core release gate
- Commit policy: no commits during implementation. Core tag `harness-core-v0.1.19` and host tag `codex-harness-host-v0.1.5` need separate explicit Git/release authorization.
- Parallel ownership: none; policy schema, compatibility matrix, core lifecycle, host adapter, and consumer pins share contract.
- Sequential fallback: complete core contract and direct proof, obtain core release approval, implement host, obtain host release approval, then update consumer guidance and generated adapter surfaces.

## Task Breakdown

### Task 1: Define typed catalog and V7 compatibility

**Purpose:**
- Make policy and role-file data sole source for claim type, repair count,
  same-thread capability, friction route, and API compatibility.

**Specification Coverage:**
- Packet-derived typed claim contract, one repair budget, explicit V7/V6
  compatibility, preserved `writer_completion_missing`, and SSOT invariants.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `agents/roles.yaml`
- Modify: `repo_config/harness.yaml`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:ROLE_FIELDS`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:FRICTION_POLICY_FIELDS`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:COMPATIBILITY_PROFILES`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:CURRENT_PACKET_API`
- Modify: `packages/harness-core/pyproject.toml:[project]`
- Modify: `uv.lock`
- Modify: `packages/harness-core/tests/test_config_validation.py`
- Modify: `packages/harness-core/tests/test_compatibility.py`
- Modify: `packages/harness-core/tests/test_cli.py`
- Verify: `scripts/validate_harness_config.py`

**Dependencies:**
- Active parent spec `docs/superpowers/specs/2026-08-08-harness-claim-repair-ssot.md`.

**Steps:**
- [ ] Add failing config tests for top-level `claim_fields`, exact V1 types,
  role references, required-field type definitions, constraint targets, generic
  `claim_repair`, and `claim_repair_failed` follow-up route.
- [ ] Add `claim_fields` catalog with `nonempty_string`, `string_list`, and
  `friction_list`; keep role result kinds, required field names, and allowed
  values in existing role entries.
- [ ] Move policy to schema V6. Add `claim_repair.max_repairs_per_lane: 1`,
  exact subcode set, and required capability
  `claim_repair_same_thread: enforced`. Retain finalization reserve and map
  `claim_repair_failed` to `harness_diagnosis` without changing
  `writer_completion_missing` mapping.
- [ ] Extend policy validation so unknown types, missing field definitions,
  unsupported subcodes, missing capability, and invalid repair bounds fail
  before packet resolution.
- [ ] Replace active API 5 compatibility profile with `claim_repair`:
  request API 5, packet API 7, host API 6, provider contract 6. Retain
  `artifact_handoff_legacy` packet API 6 / host API 5 / provider contract 5
  profile with no request aliases.
- [ ] Bump core package release to `0.1.19`, regenerate `uv.lock`, and update
  exact compatibility/public identity assertions.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_compatibility.py packages/harness-core/tests/test_cli.py -q`
- [ ] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- [ ] `uv lock --check`
- Expected: only typed catalog-valid policy resolves; API 5 selects packet 7;
  packet 6 remains dispatchable through host API 5 profile.

**Exit Criteria:**
- Canonical policy and role catalog validate. Compatibility matrix makes no
  caller-selected repair, fresh fallback, or field-name type branch possible.

### Task 2: Implement core observation and repair lifecycle

**Purpose:**
- Replace direct host claim collection with typed observation, core validation,
  same-thread repair admission, durable evidence, and one failure friction event.

**Specification Coverage:**
- `claim_observation/v1`, all managed claim-producing lanes, exact admission
  predicate, same-attempt success, `claim_invalid` failure, and no-repair paths.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_load_roles`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_validate_managed_claim`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_lane_claim`
- Modify: `packages/harness-core/src/harness_core/managed.py:_execute_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:_record_failure`
- Modify: `packages/harness-core/src/harness_core/managed.py:friction_report`
- Modify: `packages/harness-core/tests/test_managed.py`
- Verify: `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Task 1 complete and V7 compatibility/profile tests passing.

**Steps:**
- [ ] Add parameterized failing tests for every `claim_observation/v1` state and
  every field type across implement, investigate, review, validate, and improve
  lanes. Cover valid initial claims, each unusable subcode, valid repair, invalid
  repair, repeat-repair rejection, and preserved packet/attempt identity.
- [ ] Load typed catalog with roles, validate role references and constraints,
  and project typed `claim_schema` plus resolved repair contract into V7 agent
  lanes. Keep packet V6 reader and legacy claim behavior intact.
- [ ] Define one safe observation normalizer. Accept only exact lane/thread
  identity, `missing`, `non_json`, `json_non_object`, or object candidate;
  retain digest/length rather than raw completion content.
- [ ] Reorder agent-lane collection so core records final lane evidence before
  repair admission. Replace direct `collect_claim` handling with observation
  validation for work and validator lanes through one helper.
- [ ] Admit repair only for V7 agent lanes with provider-completed terminal
  evidence, final workspace evidence, unused per-lane count, remaining reserve,
  and host capability. Call one host repair method, revalidate through same
  helper, and continue current attempt on success.
- [ ] Record `attempt.evidence.claim_repair` with observation classification,
  admission, repair count, safe prompt digest, finalization identity, repeated
  validation, and no raw text. On executed repair failure, emit exactly one
  `claim_repair_failed` friction event before terminal `claim_invalid`.
- [ ] Preserve original timeout, interruption, artifact, workspace, provider,
  policy/API, and authority-violation outcomes. Capability or thread absence
  records no-repair `claim_invalid` without host repair call.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_managed.py -q`
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_managed.py -k 'claim or finalization or friction or timeout' -q`
- Expected: valid repair stays attempt 1; failed repair offers controller
  lifecycle only after one repair; excluded paths and missing capability make
  zero repair calls; no raw completion appears in `run.json` fixtures.

**Exit Criteria:**
- Core owns all claim classification and lifecycle decisions. Direct backend
  tests prove success, failure, final evidence, idempotency, and friction route.

### Task 3: Release core API 7 for host consumption

**Purpose:**
- Publish verified `harness-core` 0.1.19 so host can consume packet API 7 and
  provider contract 6 through pinned dependency truth.

**Specification Coverage:**
- Explicit V7/V6 compatibility, immutable historical packets, and no ambient
  local-core substitution for provider host.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-finishing-a-development-branch`

**Files And Symbols:**
- Verify: `packages/harness-core/pyproject.toml:[project]`
- Verify: `packages/harness-core/src/harness_core/compatibility.py:COMPATIBILITY_PROFILES`
- Verify: `packages/harness-core/tests`
- Verify: `uv.lock`

**Dependencies:**
- Task 2 complete.
- Explicit authorization to commit, tag, and publish `harness-core-v0.1.19`.

**Steps:**
- [ ] Run fresh package, direct lifecycle, config, compatibility, and root
  contract verification against exact reviewed sources.
- [ ] Reconcile package version, lockfile, compatibility profile, policy schema,
  and test evidence. Stop on failed or stale proof.
- [ ] After explicit authorization only, commit approved core changes, create
  tag `harness-core-v0.1.19`, publish through established release workflow, and
  confirm immutable tag resolves from clean checkout.

**Verification:**
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv build --package harness-core`
- [ ] `uv lock --check`
- Expected: package build and full core suite pass; published tag exposes API 7
  with packet V6 legacy reader/dispatcher still available.

**Exit Criteria:**
- Core release exists and is independently installable. Without release
  authorization or successful published-tag proof, pause here; do not change
  host dependency source.

### Task 4: Implement host API 6 same-thread repair

**Purpose:**
- Add host capability, typed completion observation, and one exact-thread
  read-only repair turn using released core 0.1.19.

**Specification Coverage:**
- `claim_observation/v1`, exact original thread, no fresh repair context,
  read-only no-tool authority, host API 6/provider contract 6, and packet V6
  legacy preservation through prior host release.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `../codex-harness-host/pyproject.toml:[project]`
- Modify: `../codex-harness-host/uv.lock`
- Modify: `../codex-harness-host/src/codex_harness_host/claims.py:parse_claim`
- Modify: `../codex-harness-host/src/codex_harness_host/app_server.py:AppServerClient.complete_turn`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:RUNTIME_PROVIDER`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.capabilities`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.collect_claim`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter._finalize_interrupted_lane`
- Modify: `../codex-harness-host/src/codex_harness_host/cli.py`
- Modify: `../codex-harness-host/tests/test_adapter.py`
- Modify: `../codex-harness-host/tests/test_app_server.py`
- Modify: `../codex-harness-host/tests/test_cli.py`
- Verify: `../codex-harness-host/tests`

**Dependencies:**
- Task 3 published `harness-core-v0.1.19`.
- Host dependency pin and lock resolve that exact tag.

**Steps:**
- [ ] Add failing protocol tests proving a continuation sends a new `turn/start`
  on stored original `threadId`, never sends `thread/start`, uses read-only
  sandbox, supplies no dynamic tools, and preserves packet-selected agent
  identity and finalization reserve.
- [ ] Change claim parser from exception-only JSON parsing to
  `claim_observation/v1`: `missing`, `non_json`, `json_non_object`, or
  `object` with parsed candidate. Retain only digest/byte length for unusable
  content.
- [ ] Extend dispatch handle and lane evidence with original thread identity and
  terminal completion state. Expose host API method for core to request one
  repair candidate from exact handle/thread.
- [ ] Implement repair prompt from lane typed schema and safe core fields. Use
  `AppServerClient` continuation on original thread with read-only no-tool
  authority. Reject unavailable thread continuation, attempted tool use,
  command use, write access, or a second repair invocation.
- [ ] Keep interrupted-timeout finalizer behavior on legacy packet path. Packet
  V7 incomplete timeout remains core no-repair; it must not re-enter old fresh
  finalizer as claim repair.
- [ ] Advertise `claim_repair_same_thread: enforced`, return host API 6 and
  provider contract 6, pin `harness-core-v0.1.19`, bump host release to
  `0.1.5`, and regenerate host lockfile.

**Verification:**
- [ ] From `../codex-harness-host`: `uv run --locked pytest tests/test_app_server.py tests/test_adapter.py tests/test_cli.py -q`
- [ ] From `../codex-harness-host`: `uv lock --check`
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests/test_managed.py -q`
- Expected: protocol fake records original-thread continuation only; malformed
  text never reaches prompt; one repair has no commands/tools/writes; capability
  absence causes zero host repair calls.

**Exit Criteria:**
- Host API 6 and core API 7 contract tests pass together using released core
  dependency. No test permits fresh-thread claim repair.

### Task 5: Release host and synchronize canonical guidance

**Purpose:**
- Publish compatible host, update canonical operational docs and consumer pins,
  then regenerate derived agent and routing guidance.

**Specification Coverage:**
- Host release pairing, preserved timeout diagnosis, repair-failure diagnosis,
  generated-source consistency, and consumer installation compatibility.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-finishing-a-development-branch`

**Files And Symbols:**
- Modify: `../codex-harness-host/pyproject.toml:[project]`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `README.md`
- Generate: `AGENTS.md`
- Generate: `docs/operating_system/tooling/harness-routing.generated.md`
- Modify: `uv.lock`
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `scripts/render_harness_routing.py`

**Dependencies:**
- Task 4 complete and host tests passing.
- Explicit authorization to commit, tag, and publish `codex-harness-host-v0.1.5`.

**Steps:**
- [ ] Run fresh host package and core/host integration verification. Reconcile
  host 0.1.5 pin, API 6/provider contract 6, V7 packet behavior, and V6 legacy
  path before release action.
- [ ] After explicit authorization only, commit host changes, publish tag
  `codex-harness-host-v0.1.5`, and confirm clean install resolves core 0.1.19
  plus host 0.1.5.
- [ ] Update canonical adapter contract with `claim_observation/v1`, exact
  thread repair method, no fresh fallback, no-tool enforcement, safe evidence,
  `claim_repair_failed`, and preserved `writer_completion_missing` follow-up.
- [ ] Update consumer setup and root README with released core/host pins and
  compatibility requirements. Update root AGENTS template with same lifecycle
  boundary; do not edit generated `AGENTS.md` directly.
- [ ] Run agent-adapter sync and routing renderer from canonical sources. Review
  generated diffs for no private configuration, secrets, raw completion text,
  or stale API 5/packet 6 current guidance.

**Verification:**
- [ ] From `../codex-harness-host`: `uv run --locked pytest -q`
- [ ] `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- [ ] `uv run --locked python scripts/sync_agent_adapters.py`
- [ ] `uv run --locked python scripts/render_harness_routing.py`
- [ ] `git diff --check`
- Expected: published pins match release tags; generated files match canonical
  sources; managed-execution guidance has one same-thread repair rule.

**Exit Criteria:**
- Host release is available, consumer documents cite matching releases, and
  generated agent/routing surfaces are synchronized from canonical sources.

## Verification

- `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- `uv run --locked --package harness-core pytest packages/harness-core/tests -q`
- From `../codex-harness-host`: `uv run --locked pytest -q`
- `uv run --locked python scripts/sync_agent_adapters.py`
- `uv run --locked python scripts/render_harness_routing.py`
- `uv run --locked python scripts/validate_template_required_sections.py`
- `uv run --locked python scripts/validate_planning_lifecycle.py`
- `uv lock --check`
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. policy schema V6 and role typed catalog resolve packet API 7 without
   field-name type branches
2. core classifies every allowed observation and repairs each eligible agent lane
   once on exact original thread only
3. host API 6 proves continuation is read-only, no-tool, no-write, no-fresh-thread
   and emits safe observation/evidence
4. ineligible, timeout, provider, workspace, artifact, policy/API, and authority
   failures preserve existing behavior with zero repair dispatch
5. `claim_repair_failed` retains recurring diagnosis while
   `writer_completion_missing` keeps current timeout follow-up
6. packet V6 remains usable through released legacy host and packet V7 requires
   released core 0.1.19 plus host 0.1.5
7. canonical docs, generated agent/routing files, package pins, locks, and fresh
   verification evidence agree

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` after fresh proof. Release-tag steps require separate explicit
Git authorization; absent authorization is a documented pause, not completion.
