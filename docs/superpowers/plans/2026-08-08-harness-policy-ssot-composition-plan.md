---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: harness-policy-ssot-composition
parent_spec: docs/superpowers/specs/2026-08-08-harness-policy-ssot-composition.md
targets:
  - repo_config/harness.yaml
  - packages/harness-core
  - ../codex-harness-host
  - scripts/render_harness_routing.py
  - docs/operating_system
  - generated_exports/project-OS-starter-kit
---

# Harness Policy SSOT Composition Plan

## Goal

Replace copied route runtime settings with one-hop policy profiles. Core
resolves one complete immutable packet. Controller and host enforce verification
and bounded context. Generated guidance and starter-kit output derive from
canonical policy.

## Implementation Outcomes

### V4 Route Intent Resolves Once

`repo_config/harness.yaml` version `4` declares authorities, toolsets, and
verification profiles. Routes select exactly one of each plus explicit
delegation. `harness-core` resolves route intent and safe defaults into a
complete packet without route-level capability, tool, check, or provider copies.

### Runtime Proof Matches Route Authority

Read-only packets prove `workspace_unchanged` against packet base. Write
packets run selected controller checks. Bounded work context and retained
artifacts reject oversized input before provider dispatch or evidence storage.
Host renders one invocation context projection per turn and runs only
packet-declared tools and controller checks.

### Derived Surfaces Stay Disposable

Routing guidance, generated agent adapters, and starter-kit output regenerate
from canonical policy and canonical guidance. No generated surface becomes a
second policy owner.

## Execution Approach

- Mode: `sequential_work_lanes`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current workspace for `project-OS-starter`; current checked-out sibling `../codex-harness-host` for host changes
- Commit policy: no commits during execution
- Parallel ownership: none; `packages/harness-core/src/harness_core/managed.py` and packet contract changes are shared dependencies
- Sequential fallback: complete packet grammar first, runtime enforcement second, canonical policy and generated guidance third, then cross-contract proof

## Task Breakdown

### Task 1: Resolve V4 route intent and canonical policy

**Purpose:**
- Accept only V4 one-hop route composition. Resolve selected profiles and safe
  defaults into self-contained packet authority.

**Specification Coverage:**
- Policy grammar, explicit security authority, one-hop route composition,
  compatibility boundary, no unsupported fallback, and complete-packet
  invariants.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/config_validation.py:ROUTE_FIELDS`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:CONTEXT_LIMIT_FIELDS`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:load_yaml`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:validate`
- Modify: `packages/harness-core/src/harness_core/managed.py:_load_policy`
- Modify: `packages/harness-core/src/harness_core/managed.py:_route_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_task`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/tests/test_config_validation.py:write_harness_root`
- Modify: `packages/harness-core/tests/test_config_validation.py`
- Modify: `packages/harness-core/tests/test_managed.py:test_resolve_task_returns_route_packet`
- Modify: `packages/harness-core/tests/test_managed.py:test_route_packet_selects_owned_skill_set`
- Modify: `repo_config/harness.yaml`
- Verify unchanged API values: `packages/harness-core/src/harness_core/compatibility.py:SUPPORTED_REQUEST_APIS`
- Verify: `packages/harness-core/tests/test_compatibility.py:test_protocol_matrix_is_exact`

**Dependencies:**
- Approved spec `docs/superpowers/specs/2026-08-08-harness-policy-ssot-composition.md`.
- Preserve current packet and host API matrix. Policy grammar migration alone
  does not change packet field names or host binding contract.

**Steps:**
- [ ] Make `load_yaml` reject duplicate YAML mapping keys before schema
  validation so duplicate profile or route names cannot collapse silently.
- [ ] Replace V3 route-field validation with V4 top-level `authorities`,
  `toolsets`, and `verification_profiles`; require exactly one named profile
  selection per route.
- [ ] Restrict `defaults` to `source_workspace`, runtime provider, retry
  policy, execution budget profile, and empty approval gates. Reject defaults
  that grant write, delegation, approval bypass, or verification bypass.
- [ ] Remove validation and resolver support for `capabilities.sets`,
  route-level `capabilities`, `tools`, `workspace`, `checks`, retry and budget
  copies, provider copies, static state graph, topology `review_required`, and
  tool `fallback`.
- [ ] Resolve one authority, toolset, and verification profile into packet
  values while retaining selected profile names and rejecting missing, unknown,
  duplicate, deep-merge, or authority/tool-access widening cases before packet
  creation.
- [ ] Keep `harness.delegate` explicit in its selected authority and require a
  separately selected bounded delegation profile. Keep route-local nonempty
  approval gates visible in packet output.
- [ ] Migrate `repo_config/harness.yaml` in this task so root-level packet tests
  never load a V3 policy through V4-only core. Set `version: 4`; define
  read-only, read-only-delegation, and workspace-write authorities; define
  shell/Serena/ast-grep and shell/Semble toolsets; and define read-only
  `workspace_unchanged` and write `diff` verification profiles.
- [ ] Add `artifact_max_bytes` to canonical context limits. Move workspace
  source, runtime provider, retry policy, execution budget, and empty approval
  gates to defaults. Replace route copies with profile selections; retain
  template, role, rules, skills, execution modes, delegation selection, and
  explicit protected-policy gates.
- [ ] Delete unused capability sets, tool fallback declarations, static state
  graph, and topology `review_required` from canonical policy. Do not add
  inheritance, aliases, or deep merge behavior.
- [ ] Add table-driven policy and packet tests for every V4 route class,
  invalid one-hop references, forbidden deleted fields, unsafe defaults, and
  stable request/packet/host compatibility values.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_config_validation.py packages/harness-core/tests/test_managed.py packages/harness-core/tests/test_compatibility.py -q`
- Expected: valid V4 fixtures resolve complete packets; invalid profile and
  deleted-field fixtures fail before packet creation; compatibility matrix stays
  unchanged.

**Exit Criteria:**
- Core packet resolution has one V4 authority path. No route-level copied
  capabilities, tools, checks, fallback, workspace, retry, budget, or provider
  values remain accepted.

### Task 2: Enforce context bounds and controller verification

**Purpose:**
- Make every declared context/evidence limit and verification profile enforceable
  through core and host boundaries.

**Specification Coverage:**
- Controller-owned verification, symmetric read/write behavior, bounded packet
  and evidence context, no hidden tool fallback, active invocation-context
  ownership, and lifecycle acceptance invariants.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_task`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_collect_changes`
- Modify: `packages/harness-core/src/harness_core/managed.py:_assert_workspace_readonly_artifacts`
- Modify: `packages/harness-core/src/harness_core/managed.py:_verify_managed`
- Modify: `packages/harness-core/src/harness_core/managed.py:_normalize_retained_artifacts`
- Modify: `packages/harness-core/tests/test_managed.py`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.run_checks`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter.dispatch_lane`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter._complete_lane_turn`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\adapter.py:CodexAdapter._prompt`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py:FakeClient.complete_turn`
- Modify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_adapter.py`
- Verify transport unchanged: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\src\codex_harness_host\app_server.py:AppServerClient.complete_turn`
- Verify: `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host\tests\test_app_server.py`

**Dependencies:**
- Task 1 complete. V4 resolver exposes resolved verification policy and packet
  profile provenance.
- `docs/superpowers/specs/2026-08-07-harness-invocation-delegation-protocol.md`
  remains owner of `work_context` schema, digest, artifact/base identity,
  invocation-local projection, and run-wide delegation budget.

**Steps:**
- [ ] Add `artifact_max_bytes` to V4 context limits. Enforce UTF-8 objective
  bytes, total serialized fact bytes, fact count, outcome summary bytes,
  artifact count, and per-artifact bytes before packet dispatch.
- [ ] Preserve `work_context` facts, artifact references, base-commit identity,
  and digest. Reject missing, unsafe, mismatched, duplicate, or oversized
  content; never truncate semantic input or persisted evidence.
- [ ] Require retained command traces and readonly artifact descriptors to meet
  both their existing sanitizer limits and `artifact_max_bytes`. Persist digest
  and byte length only after validation.
- [ ] Evaluate V4 verification profiles in `_verify_managed`: run named checks
  through host `run_checks`; evaluate `workspace_unchanged` through final
  change collection against packet base; record one evidence-backed check node;
  block absent, malformed, conflicting, or failed evidence.
- [ ] Keep worker capabilities free of `checks.run`. A write route receives
  controller check evidence; a read-only route fails on every final workspace
  change, including changes that pass `git diff --check`.
- [ ] Change `CodexAdapter._prompt` to render one serialized
  `packet["work_context"]` projection. Remove both duplicate
  `packet["user_request"]` prompt renderings. Keep readonly-artifact access
  from materialized packet evidence and keep `AppServerClient.complete_turn`
  transport shape unchanged.
- [ ] Add direct core and host tests: boundary-sized input succeeds; each
  overflow rejects before adapter invocation; readonly mutation blocks;
  configured write check executes once with binding evidence; unavailable or
  unselected tool fails without fallback; prompt contains one context
  projection and no parent transcript duplicate.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_managed.py -q`
- Expected: context and retained-evidence overflow produce typed pre-dispatch
  failures; read-only workspace changes block acceptance; write checks supply
  controller evidence.
- [ ] `uv run pytest tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: host binds only packet tools, runs packet checks read-only, and
  renders one bounded work-context prompt without transport API changes.

**Exit Criteria:**
- Core and host prove same authority model: workers act through packet tools,
  controller owns verification, and every packet/evidence context value stays
  within declared limits.

### Task 3: Regenerate guidance from canonical V4 policy

**Purpose:**
- Regenerate policy-derived human guidance from canonical V4 policy and
  canonical agent sources.

**Specification Coverage:**
- V4 policy grammar, safe defaults, authority/tool/verification symmetry,
  controller-owned checks, generated-source consistency, and private runtime
  transport boundary.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/render_harness_routing.py:render`
- Modify: `tests/test_render_harness_routing.py:test_rendered_routing_matches_policy`
- Modify: `tests/test_render_harness_routing.py:test_check_reports_stale_output`
- Modify: `docs/operating_system/rules/multi-agent-orchestration-rule.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Generate: `docs/operating_system/tooling/harness-routing.generated.md`
- Generate: `AGENTS.md`
- Generate: `generated_agents/**`
- Verify generated-source ownership: `scripts/sync_agent_adapters.py`

**Dependencies:**
- Task 1 complete. Canonical V4 policy must be accepted by core validator.
- Task 2 complete. Policy profile names must map to enforced runtime behavior.

**Steps:**
- [ ] Change routing renderer table to show selected authority, toolset, and
  verification profile names. Do not reproduce core profile resolution in the
  renderer. Regenerate routing guidance with
  `\.venv\Scripts\python.exe scripts\render_harness_routing.py`.
- [ ] Update canonical orchestration and root-agent guidance to state that
  routes select profiles, only core/host run checks, read-only paths prove no
  change, and host transport stays in trusted user configuration. Run
  `\.venv\Scripts\python.exe scripts\sync_agent_adapters.py` rather than
  editing generated adapters.

**Verification:**
- [ ] `\.venv\Scripts\python.exe scripts\validate_harness_config.py --repo-root .`
- Expected: canonical V4 policy validates without unsupported keys or copied
  route runtime fields.
- [ ] `\.venv\Scripts\python.exe -m pytest tests/test_render_harness_routing.py -q`
- Expected: renderer reads V4 profile selections and stale generated output is
  detected.
- [ ] `\.venv\Scripts\python.exe scripts\render_harness_routing.py --check`
- Expected: generated routing guidance has no drift.
- [ ] `\.venv\Scripts\python.exe scripts\validate_agent_runtime_drift.py`
- Expected: generated agent adapters match canonical templates and rules.

**Exit Criteria:**
- Canonical policy is V4 intent only. Generated routing and agent surfaces have
  no independent route authority, check, or transport definition.

### Task 4: Prove generated distribution and release contract

**Purpose:**
- Rebuild starter-kit output and run final cross-contract evidence without
  mutating unrelated workspace work.

**Specification Coverage:**
- Historical compatibility readability, generated policy synchronization,
  host/core contract stability, starter-kit distribution, and final validation
  claims.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `repo_config/starter-kit-manifest.json:copyPaths`
- Verify: `scripts/build_starter_kit.py:main`
- Verify: `scripts/validate_starter_kit.py:validate_starter_kit`
- Verify: `tests/test_starter_kit_generation.py:test_production_manifest_includes_harness_and_excludes_run_state`
- Verify: `packages/harness-core/tests/test_compatibility.py:test_packet_dispatch_uses_matrix_without_host_fallback`
- Verify: `packages/harness-core/tests/test_managed.py:test_legacy_packet_derives_write_capability_without_role_writes`
- Verify: `packages/harness-core/tests/test_managed.py:test_run_managed_resumes_v3_packet_with_host2_when_policy_api4`
- Verify generated output: `generated_exports/project-OS-starter-kit/repo_config/harness.yaml`

**Dependencies:**
- Tasks 1 through 3 complete.
- Keep `repo_config/starter-kit-manifest.json` unchanged unless validation
  proves it no longer distributes canonical `repo_config/harness.yaml`; it
  already owns that copy rule.

**Steps:**
- [ ] Run full V4 core test set covering policy validation, packet resolution,
  lifecycle verification, retained artifacts, timeout/friction behavior, and
  compatibility readers.
- [ ] Run focused host tests from sibling repository after core tests pass.
  Treat provider test failure as host-contract failure; do not change packet or
  host API versions to bypass it.
- [ ] Build disposable starter-kit output from manifest. Validate output copies
  V4 `harness.yaml`, omits private runtime material, and contains no stale
  fallback, capability-set, route-level check, state graph, or review flag.
- [ ] Run repository contract validation, planning artifact validation, and
  whitespace diff validation. Keep unrelated modified and untracked files
  untouched.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests -q`
- Expected: policy-to-packet, direct verification, context failure, terminal
  evidence, coordination, CLI, and compatibility tests pass.
- [ ] `uv run pytest tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: host adapter and App Server transport tests pass with unchanged
  packet/host compatibility versions.
- [ ] `\.venv\Scripts\python.exe -m pytest tests/test_render_harness_routing.py tests/test_starter_kit_generation.py -q`
- Expected: rendered policy and starter-kit distribution tests pass.
- [ ] `\.venv\Scripts\python.exe scripts\build_starter_kit.py --repo-root .`
- Expected: `generated_exports/project-OS-starter-kit` rebuilds from manifest.
- [ ] `\.venv\Scripts\python.exe scripts\validate_starter_kit.py --repo-root .`
- Expected: starter-kit output validates and contains canonical V4 policy.
- [ ] `\.venv\Scripts\python.exe scripts\validate_repo_contracts.py`
- Expected: repository contract checks pass.
- [ ] `\.venv\Scripts\python.exe scripts\validate_planning_lifecycle.py`
- Expected: specification and implementation plan metadata and parent link pass.
- [ ] `git diff --check`
- Expected: no whitespace errors in touched files.

**Exit Criteria:**
- Fresh evidence proves V4 route intent, bounded context, controller-owned
  verification, unchanged packet/host compatibility, generated-surface sync,
  and valid starter-kit output. Final status remains `proposed` until
  `skill-verification-before-completion` reconciles executed evidence.

## Verification

- Core: policy parser, route-to-packet snapshots, invalid-reference failures,
  read-only mutation rejection, write-check evidence, context/evidence bounds,
  and compatibility readers.
- Host: one work-context prompt rendering, packet-only tool bindings,
  controller-owned checks, readonly workspace behavior, and unchanged transport
  signature.
- Generated surfaces: V4 policy validator, routing renderer drift check, agent
  adapter drift check, starter-kit build and validation.
- Final: repository contract command, planning lifecycle command, and
  `git diff --check`.

## Completion Criteria

1. Every current route resolves one authority, one toolset, one verification
   profile, and one delegation profile.
2. Defaults never grant write, delegation, approval bypass, external side
   effect, or verification bypass.
3. Read-only routes reject any final workspace change; write routes record
   configured controller check evidence; workers do not gain `checks.run`.
4. Objective, fact, outcome, artifact, readonly-evidence, and retained-trace
   boundaries reject overflow before dispatch or persistence.
5. Provider packet and host compatibility values remain unchanged; historical
   packet and run readers pass their existing fixtures.
6. Routing guidance, generated agent adapters, and starter-kit policy regenerate
   from canonical sources with zero drift.
7. `skill-verification-before-completion` receives all Task 4 evidence before
   marking this plan completed.
