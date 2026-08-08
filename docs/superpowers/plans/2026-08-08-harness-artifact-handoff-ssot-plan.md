---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: harness-artifact-handoff-ssot
parent_spec: docs/superpowers/specs/2026-08-08-harness-artifact-handoff-ssot.md
targets:
  - repo_config/harness.yaml
  - packages/harness-core
  - ../codex-harness-host
  - scripts/render_harness_routing.py
  - docs/operating_system/procedures
  - generated_exports/project-OS-starter-kit
  - ../project-OS-starter-kit
  - uv.lock
---

# Harness Artifact Handoff SSOT Plan

## Goal

Replace API 4 caller-selected readonly-artifact references with policy-owned V1
catalog profiles. Deliver API 5 request admission, API 6 immutable packet proof,
target attempt audit, shared direct/friction selection, and read-only host
materialization. Preserve historical packet readers and generated consumer
surfaces.

## Implementation Outcomes

### Policy-Owned V1 Catalog

`repo_config/harness.yaml` version 5 defines only normalized terminal
observations and sanitized command traces, plus direct and friction diagnosis
profiles. Routes select profiles; controllers never select descriptors.

### Auditable Deterministic Handoff

Core accepts API 5 exact direct source identity, reserves required selection
capacity, emits API 6 packet proof, and records target attempt audit. Friction
follow-up uses same resolver without changing threshold behavior.

### Matching Provider and Consumer Contract

Codex host API 5 verifies and exposes read-only descriptors. Core and host use
matching release pins. Routing guidance, consumer setup, and starter output
derive from canonical policy and documentation.

## Execution Approach

- Mode: `sequential_work_lanes`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current workspace for `project-OS-starter`; current checked-out sibling `../codex-harness-host` for host changes; declared generated roots `generated_exports/project-OS-starter-kit` and `../project-OS-starter-kit` for Task 4 only
- Commit policy: no commits during implementation tasks. Published core and host releases require separate fresh verification plus explicit authorized branch/release workflow.
- Parallel ownership: none; policy grammar, compatibility values, packet fields, and host contract are shared boundaries
- Sequential fallback: migrate compatibility and policy grammar first, core resolver second, friction/host contract third, then generated surfaces and release proof

## Task Breakdown

### Task 1: Define API 5 policy and compatibility line

**Purpose:**
- Replace route-local `readonly_artifacts` grammar with V1 catalog and handoff
  profile grammar. Add request API 5, packet API 6, host API 5, provider
  contract 5, and core release `0.1.18`.

**Specification Coverage:**
- V1 catalog, explicit source compatibility, API migration, historical readers,
  and read-only-only admission.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:validate`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:READONLY_ARTIFACT_POLICY_FIELDS`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:COMPATIBILITY_PROFILES`
- Modify: `packages/harness-core/src/harness_core/compatibility.py:CURRENT_PACKET_API`
- Modify: `packages/harness-core/pyproject.toml:[project]`
- Modify: `uv.lock`
- Modify: `packages/harness-core/tests/test_config_validation.py:write_harness_root`
- Modify: `packages/harness-core/tests/test_config_validation.py`
- Modify: `packages/harness-core/tests/test_compatibility.py:test_protocol_matrix_is_exact`
- Modify: `packages/harness-core/tests/test_cli.py:test_module_identity_reports_policy_schema`
- Verify: `scripts/validate_harness_config.py --repo-root .`

**Dependencies:**
- Active parent spec
  `docs/superpowers/specs/2026-08-08-harness-artifact-handoff-ssot.md`.

**Steps:**
- [x] Replace `evidence_artifacts.writer_retained_kinds` and route
  `readonly_artifacts` grammar with policy-owned V1 catalog entries and
  `direct_terminal_diagnosis` plus `friction_terminal_diagnosis` profiles.
- [x] Require each profile to declare lineage mode, allowed/required kinds,
  unique kind priority, `base_compatibility`, positive count limit, and positive
  total-byte limit. Set direct profile to `exact_packet_base` and friction
  profile to `same_repository`.
- [x] Restrict profile-bearing routes to read-only authority. Reject V1 catalog
  kinds beyond `terminal_observation` and `sanitized_command_trace`.
- [x] Add compatibility profile mapping request 5 to packet 6, host 5, and
  provider contract 5. Preserve packet API 3, 4, and 5 read profiles.
- [x] Reject every fresh request whose API differs from policy-owned
  `harness_core.request_api`; preserve packet API 3, 4, and 5 readers without
  admitting fresh API 4 requests under policy version 5.
- [x] Set core package version to `0.1.18`; update policy and compatibility
  fixtures to API 5 values.

**Verification:**
- [x] `uv run --locked python -m pytest packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_compatibility.py -q`
- [x] `uv run --locked python scripts/validate_harness_config.py --repo-root .`
- Expected: valid V1 policy resolves; invalid catalog/profile/write-route/API
  fixtures fail before packet creation; fresh API 4 rejects under policy
  version 5; packet APIs 3–5 remain readable.

**Exit Criteria:**
- Policy version 5 and core compatibility expose one validated V1 catalog line.

### Task 2: Implement core resolver, packet proof, audit, and friction source set

**Purpose:**
- Replace public descriptor references with exact API 5 source/profile handoff.
  Resolve deterministic V1 descriptors and target attempt audit. Move recurring
  friction onto same core resolver before core release.

**Specification Coverage:**
- Exact direct predecessor identity, required-first ordering, source/base
  compatibility, bounded descriptors, immutable packet proof, fresh-proof
  boundary, and core-owned friction source-set selection.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_artifact_descriptor`
- Replace: `packages/harness-core/src/harness_core/managed.py:_resolve_readonly_artifacts`
- Add: `packages/harness-core/src/harness_core/managed.py:_resolve_artifact_handoff`
- Add: `packages/harness-core/src/harness_core/managed.py:_select_handoff_artifacts`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_append_attempt`
- Modify: `packages/harness-core/src/harness_core/managed.py:_friction_readonly_artifact_requests`
- Modify: `packages/harness-core/src/harness_core/managed.py:friction_report`
- Modify: `packages/harness-core/tests/test_managed.py:test_harness_diagnosis_packet_resolves_declared_readonly_artifacts`
- Add tests: `packages/harness-core/tests/test_managed.py`
- Verify: `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Task 1 complete.

**Steps:**
- [x] Define API 5 `artifact_handoff` admission as exact
  `source_run_id`, `source_attempt_id`, and optional route-allowed `profile`.
  Absence yields no descriptors; reject API 5 `readonly_artifacts` input.
- [x] Validate source terminal state, attempt identity, V1 producer/schema,
  JSON bytes, SHA-256, per-artifact limit, source/base compatibility, and
  duplicate source/descriptor identity.
- [x] Select one compatible descriptor per required kind before optional kinds.
  Rank optional kinds by profile priority and use fixed direct-source order.
- [x] Preserve descriptor shape. Add packet `artifact_handoff` proof and target
  attempt `artifact_handoff_audit` with source, profile, selected metadata,
  optional rejections, count, bytes, and SHA-256 over canonical JSON of ordered
  sources, selected descriptor metadata, and rejection metadata.
- [x] Keep imported descriptors out of acceptance criteria and prevent
  descriptor re-export or ancestor traversal.
- [x] Derive friction source pairs from qualifying events in newest
  `occurred_at`, then `event_id`, order. Reuse selector internally and expose
  only `friction_terminal_diagnosis` profile context to controllers.

**Verification:**
- [x] `uv run --locked python -m pytest packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_compatibility.py -q`
- Expected: exact direct source resolves reproducibly; malformed source/profile,
  API 4 artifact IDs, hash/size/schema failures, and missing required terminal
  observation reject before workspace preparation; optional trace cannot starve
  terminal observation.

**Exit Criteria:**
- API 6 packet proof and target audit identify one valid direct source and one
  deterministic V1 selection. Friction emits profile-only follow-up context
  after shared source-set validation.

### External Release Gate 1: Publish verified core release

**Purpose:**
- Publish immutable `harness-core-v0.1.18` after Tasks 1–2 pass, before host
  lock resolution.

**Owner And Preconditions:**
- `skill-verification-before-completion` produces fresh core verification.
- Authorized branch/release workflow commits, tags, and publishes the core
  release. Do not infer authorization from this plan.

**Exit Criteria:**
- Published `harness-core-v0.1.18` resolves from its immutable tag and matches
  verified Task 1–2 source.

### Task 3: Upgrade host through API 6 contract

**Purpose:**
- Upgrade host API and prove selected artifact root is readable but not writable
  by read-only tools.

**Specification Coverage:**
- Host byte verification, read-only materialization, provider compatibility,
  and API-skew rejection.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:RUNTIME_PROVIDER`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter.host_api`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:_materialize_readonly_artifacts`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:_prompt`
- Modify: `../codex-harness-host/tests/test_adapter.py:test_prepare_workspace_materializes_packet_readonly_artifacts`
- Modify: `../codex-harness-host/pyproject.toml:[project]`
- Modify: `../codex-harness-host/uv.lock`
- Verify: `../codex-harness-host/tests/test_adapter.py`

**Dependencies:**
- Task 2 complete.
- External Release Gate 1 complete.

**Steps:**
- [ ] Advance host provider contract and host API to 5. Retain API 6 descriptor
  shape and require packet proof plus descriptor hash/byte checks.
- [ ] Add host conformance test using read-only packet tool binding to prove
  materialized evidence path cannot be written; retain metadata-only prompt
  projection and exact read path instruction.
- [ ] Set host package version to `0.1.4`, pin `harness-core` to
  `harness-core-v0.1.18`, regenerate `uv.lock`, then run host capabilities and
  preflight from `../codex-harness-host`.

**Verification:**
- [ ] `uv run --locked python -m pytest packages/harness-core/tests/test_managed.py -q`
- [ ] `uv run --locked --project ../codex-harness-host python -m pytest tests/test_adapter.py -q`
- [ ] `uv run --locked --project ../codex-harness-host codex-harness-host capabilities`
- [ ] `uv run --locked --project ../codex-harness-host codex-harness-host preflight`
- Expected: friction follow-up selects profile-level context in stable event
  order; host API 5 accepts API 6 descriptor contract; API 4 host rejects API
  6 before workspace work; read-only write probe fails.

**Exit Criteria:**
- Direct and friction handoff use one resolver; matching host source proves
  read-only artifact materialization and API 6 admission.

### Task 4: Regenerate consumer surfaces and prove release line

**Purpose:**
- Update canonical guidance and packages, regenerate derived output, and run
  full repository proof for API 5/6/5/5 release line.

**Specification Coverage:**
- Generated-source consistency, consumer migration, starter-kit distribution,
  deployment provenance, and final validation.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `scripts/render_harness_routing.py:render`
- Modify: `tests/test_render_harness_routing.py:test_rendered_routing_matches_policy`
- Regenerate: `docs/operating_system/tooling/harness-routing.generated.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/procedures/managed-execution-adapter-contract.md`
- Verify: `repo_config/starter-kit-manifest.json`
- Regenerate: `generated_exports/project-OS-starter-kit`
- Regenerate: `../project-OS-starter-kit`

**Dependencies:**
- Task 3 complete.

**Steps:**
- [ ] Render configured route handoff profile/default information from
  `repo_config/harness.yaml`; do not duplicate catalog policy in generated
  guidance.
- [ ] Update consumer setup and adapter contract with policy 5, request 5,
  packet 6, host 5, provider contract 5, core `0.1.18`, and host `0.1.4`.
- [ ] Regenerate routing guidance, then synchronize both starter-kit outputs
  from canonical sources.
- [ ] Run deployment provenance check after host lock update so installed host
  loads tagged core, not editable source.
- [ ] Reconcile task evidence against parent specification before completion
  verification; do not mark plan completed in this task.

**Verification:**
- [ ] `uv run --locked python -m pytest tests/test_render_harness_routing.py tests/test_deploy_harness_core_to_host.py -q`
- [ ] `uv run --locked python scripts/render_harness_routing.py --check`
- [ ] `uv run --locked python scripts/sync_starter_kit.py`
- [ ] `pwsh -NoProfile -File .\scripts\deploy_harness_core_to_host.ps1`
- [ ] `uv run --locked python scripts/validate_repo_contracts.py`
- Expected: generated guidance and both starter-kit outputs match canonical
  sources; host proves locked tagged core; repository contract passes.

**Exit Criteria:**
- Consumer-visible API guidance, generated artifacts, and locked host runtime
  all match API 5/6/5/5 contract.

### External Release Gate 2: Publish verified host release

**Purpose:**
- Publish `codex-harness-host` `0.1.4` after Tasks 3–4 and final verification.

**Owner And Preconditions:**
- `skill-verification-before-completion` produces fresh final verification.
- Authorized branch/release workflow commits, tags, and publishes the host
  release. Do not infer authorization from this plan.

**Exit Criteria:**
- Released host `0.1.4` matches verified API 5/provider contract 5 source and
  its lockfile pin.

## Verification

- Core: policy schema, compatibility readers, direct handoff admission,
  fresh API 5-only admission, required-first selection, audit digest, source
  immutability, missing/error paths, and friction source-set order.
- Host: API 5 capability, API 6 descriptor byte/hash checks, metadata prompt
  projection, read-only evidence materialization, and API-skew block.
- Distribution: published core tag, host pin and lock, routing renderer, starter
  output synchronization, deployment provenance, and generated drift checks.
- Final: `uv run --locked python scripts/validate_repo_contracts.py`,
  `uv run --locked python scripts/validate_template_required_sections.py`,
  `uv run --locked python scripts/validate_planning_lifecycle.py`, and
  `git diff --check`.

## Completion Criteria

1. V1 catalog admits only terminal observation and sanitized command trace under
   policy version 5.
2. API 5 public requests name exact direct source identity and never artifact
   IDs, paths, contents, or arbitrary source lists.
3. Core reserves required descriptor capacity, preserves optional exclusion
   audit, and produces matching API 6 proof plus target attempt audit.
4. Existing recurring friction follow-up uses shared resolver without changing
   thresholds, fingerprints, route, or source event ordering.
5. Policy version 5 admits only fresh API 5 requests; API 6 packets dispatch
   only with host API 5/provider contract 5; historical packet readers remain
   valid.
6. Read-only packet tools cannot mutate materialized artifact context.
7. Core and host release pins, routing guidance, consumer procedure, and both
   starter-kit outputs match canonical sources.
8. `skill-verification-before-completion` receives fresh Task 4 evidence before
   External Release Gate 2 and plan status changes from `proposed`.
