---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: required-skill-sets-allowed-facets
parent_spec: docs/superpowers/specs/2026-08-08-required-skill-sets-allowed-facets.md
targets:
  - repo_config/harness.yaml
  - packages/harness-core/src/harness_core/config_validation.py
  - packages/harness-core/src/harness_core/managed.py
  - packages/harness-core/tests
  - scripts/render_harness_routing.py
  - docs/operating_system/tooling/harness-routing.generated.md
  - ../codex-harness-host/tests/test_adapter.py
---

# Required Skill Sets And Operating Profiles Plan

## Goal

Make `repo_config/harness.yaml` sole owner of reusable skill composition and
safe operating envelopes. Core resolves deterministic immutable packet data.
Controller selects only route-allowed facets and profiles. Same-provider timeout
escalation preserves prior trusted binding.

## Implementation Outcomes

### Policy-Owned Skill Selection

`repo_config/harness.yaml` defines reusable `skill_sets`. Composed routes name
required and allowed set IDs. Core accepts only recorded allowed selections and
stores deterministic `skill_sets` provenance plus resolved `skills` in packets.
Legacy direct-skill routes remain valid.

### Profile-Bounded Operating Autonomy

`repo_config/harness.yaml` defines complete inheritable `operating_profiles`.
Composed routes declare default and allowed profiles plus directed timeout
edges. Core rejects raw authority, tool, runtime, template, budget, and check
selection. Same-provider timeout successors inherit immutable runtime binding.

### Derived Guidance And Consumer Proof

Generated routing guidance renders catalog references and resolved baseline
without copying policy. Host consumes unchanged `skills` from both legacy and
composed packets. Starter-kit output distributes canonical policy only.

## Execution Approach

- Mode: `sequential_work_lanes`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: current `project-OS-starter` workspace; sibling `../codex-harness-host` only for focused consumer regression proof
- Commit policy: no commits during execution
- Parallel ownership: none; policy grammar and immutable packet contract share `packages/harness-core/src/harness_core/managed.py`
- Sequential fallback: validate grammar first, resolve packet skills second, resolve profiles and successors third, migrate canonical policy and guidance fourth, then run cross-contract proof

## Task Breakdown

### Task 1: Validate catalog and composed-route grammar

**Purpose:**
- Add one policy grammar for reusable skill sets and complete operating profiles.
- Preserve current direct-skill, direct-profile route shape as legacy behavior.

**Specification Coverage:**
- Skill-Set Catalog
- Required And Allowed Route Sets
- Operating-Profile Catalog And Route Range
- legacy compatibility, policy SSOT, inheritance-cycle rejection, and no implicit authority expansion

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/config_validation.py:POLICY_FIELDS`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:ROUTE_FIELDS`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:ROUTE_OPTIONAL_FIELDS`
- Add: `packages/harness-core/src/harness_core/config_validation.py:resolve_operating_profile`
- Modify: `packages/harness-core/src/harness_core/config_validation.py:validate`
- Add validation helpers in `packages/harness-core/src/harness_core/config_validation.py` for `skill_sets`, composed-route shape, and directed escalation edges
- Modify: `packages/harness-core/tests/test_config_validation.py:write_harness_root`
- Modify: `packages/harness-core/tests/test_config_validation.py:test_v4_policy_profiles_validate`
- Add focused cases in `packages/harness-core/tests/test_config_validation.py`

**Dependencies:**
- Approved parent spec exists at `docs/superpowers/specs/2026-08-08-required-skill-sets-allowed-facets.md`.
- Current `repo_config/harness.yaml` stays unchanged until Task 4.

**Steps:**
- [ ] Define `skill_sets` entries as `{skills, selection_guidance}`. Require non-empty unique IDs, non-empty ordered unique skill lists, known skill names, and non-empty guidance.
- [ ] Define `resolve_operating_profile` as pure shared policy resolution for `extends`, `template`, `authority`, `toolset`, `verification_profile`, `runtime_provider`, and `execution_budget_profile`. Let child-declared fields override one parent; reject missing parents, cycles, unrecognized fields, incomplete results, and unknown referenced policy objects.
- [ ] Support two disjoint route forms. Legacy routes retain `skills`, `template`, `authority`, `toolset`, and `verification_profile`. Composed routes use `required_skill_sets`, `allowed_skill_sets`, `default_operating_profile`, `allowed_operating_profiles`, and optional `escalation_transitions`; reject mixed direct and composed fields.
- [ ] Represent each composed timeout edge as `{from, on, to}`. Require unique `{from, on}` pairs, `on: dispatch_timeout`, route-allowed endpoints, and a destination permitted by source budget timeout policy. Require default profile in route allowance and every allowed profile to resolve policy default runtime provider.
- [ ] Add red-first validation tests for empty or unknown catalog IDs, duplicate skills or set IDs, overlapping required and allowed set IDs, profile cycles, incomplete inheritance, route-disallowed or cross-provider profiles, and invalid timeout edges. Keep current valid legacy fixture green.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_config_validation.py -q`
- Expected: valid legacy and composed fixture policies pass; each malformed catalog, profile, or route returns deterministic validation errors.

**Exit Criteria:**
- Policy validation accepts only explicit legacy or composed route contracts. Every composed profile resolves one complete safe envelope before packet work begins.

### Task 2: Resolve immutable skill-set selections

**Purpose:**
- Resolve required and controller-selected allowed skill sets into deterministic packet metadata and existing `skills` input.

**Specification Coverage:**
- Controller Selection
- Plan-Linked Requests
- Packet And Host Boundary
- Required-Only Resolution, Allowed Facet Selection, Invalid Selection Rejection, and legacy packet compatibility

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_normalize_managed_request`
- Add: `packages/harness-core/src/harness_core/managed.py:_normalize_skill_set_selections`
- Add: `packages/harness-core/src/harness_core/managed.py:_resolve_skill_sets`
- Modify: `packages/harness-core/src/harness_core/managed.py:_route_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_task`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/tests/test_managed.py:test_resolve_task_returns_route_packet`
- Modify: `packages/harness-core/tests/test_managed.py:test_route_packet_selects_owned_skill_set`
- Add focused resolver and `run_managed` admission cases in `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Task 1 policy grammar and tests pass.

**Steps:**
- [ ] Normalize optional request `skill_set_selections` as ordered `{id, reason}` objects. Require unique allowed IDs and non-empty reasons. Reject malformed, duplicate, unknown, and disallowed selections before packet creation.
- [ ] Resolve composed route skills in this fixed order: required set IDs, selected allowed set IDs, then first-occurrence skill de-duplication. Keep legacy `route["skills"]` output unchanged.
- [ ] Store packet audit metadata as `skill_sets.required`, `skill_sets.selected`, and `skill_sets.resolved`; retain `skills` as exact resolved names for host and agent consumption.
- [ ] Persist normalized skill selection provenance in immutable packet and run attempt data. Preserve existing plan digest behavior. Do not add `packet_digest` or change request, packet, host, or provider API versions.
- [ ] Keep plan-linked selection request-owned while `_normalize_managed_request` continues deriving plan mode, base ref, allowed paths, and planned write paths from plan coordination.
- [ ] Prove valid and invalid selection paths through `resolve_managed_packet` and `run_managed`. Assert rejected selections create no packet, workspace, or run directory.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_managed.py -k "route_packet or skill_set or plan_bound or run_managed" -q`
- Expected: required-only packet excludes backend proof; valid backend selection appears once with reason and immutable provenance; invalid selection has no managed-run side effects; legacy packet output stays stable.

**Exit Criteria:**
- Packet skill provenance is immutable, replayable, and policy-derived. User prose and host code cannot add skills.

### Task 3: Resolve profiles and inherit timeout binding

**Purpose:**
- Replace raw operating controls with one resolved profile. Repair timeout successor resolution without caller-supplied provider binding.

**Specification Coverage:**
- Bounded Operating Autonomy
- Operating-Profile Catalog And Route Range
- Successor Runtime-Binding Inheritance
- Profile-Governed Timeout Escalation and Runtime And Profile Rejection

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `packages/harness-core/src/harness_core/managed.py:_resolve_execution_budget`
- Add: `packages/harness-core/src/harness_core/managed.py:_normalize_operating_profile_selection`
- Import: `packages/harness-core/src/harness_core/config_validation.py:resolve_operating_profile`
- Modify: `packages/harness-core/src/harness_core/managed.py:_route_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_resolve_runtime_provider`
- Modify: `packages/harness-core/src/harness_core/managed.py:resolve_managed_packet`
- Modify: `packages/harness-core/src/harness_core/managed.py:_successor_request`
- Modify: `packages/harness-core/src/harness_core/managed.py:apply_controller_decision`
- Modify: `packages/harness-core/tests/test_managed.py:test_api5_packet_requires_immutable_provider_runtime_binding`
- Modify: `packages/harness-core/tests/test_managed.py:test_timeout_escalation_uses_packet_named_budget_profile`
- Add focused profile selection and successor binding cases in `packages/harness-core/tests/test_managed.py`

**Dependencies:**
- Tasks 1 and 2 pass.
- Existing packet API 5 runtime-binding validation remains source of binding validity.

**Steps:**
- [ ] Normalize optional `operating_profile_selection` as `{id, reason}`. Omission selects route default. Accept host-supplied `runtime_provider_id` only when it equals every route-allowed profile provider; reject mismatch and raw `execution_budget_profile`, `authority`, `toolset`, `verification_profile`, `template`, model, tool, rule, check, or binding overrides.
- [ ] Reuse `config_validation.resolve_operating_profile` before `_route_packet` builds authority, tool bindings, checks, agent identity, runtime provider, and execution budget. Require selected profile in route allow-list. Emit provenance with default, selected, resolved, reason, resolved fields, and transition reason; do not add `policy_digest`.
- [ ] Keep legacy direct route resolution on current fields and defaults. Do not require profile metadata when reading historical packets.
- [ ] For `dispatch_timeout`, derive destination only from active packet profile plus route `{from, on, to}` edge. Build successor request internally with destination profile and transition reason; do not accept profile or provider choice from `decision.successor`.
- [ ] Before successor packet resolution, require prior packet binding, resolve destination profile, require same runtime provider, and pass prior immutable binding into `resolve_managed_packet`. Preserve host's per-lane trusted-configuration comparison and its `provider_configuration_changed` failure.
- [ ] Add red-first tests for default and allowed profile resolution, inheritance field provenance, malformed or disallowed profile selection, raw override, mismatched provider request, invalid transition, missing binding, same-provider escalation to `planned`, and changed provider configuration before lane dispatch.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests/test_managed.py -k "operating_profile or timeout_escalation or provider_runtime_binding or successor" -q`
- Expected: profile-selected packets contain one complete envelope; only directed same-provider timeout escalation reaches `planned`; invalid selection, provider mismatch, or configuration drift blocks before product work.

**Exit Criteria:**
- Controller has bounded profile autonomy. Core, not request input, preserves valid same-provider binding across timeout successors.

### Task 4: Migrate local change and regenerate guidance

**Purpose:**
- Migrate one route through reusable catalogs. Render policy-derived guidance. Project core-resolved skills into host lane context without host-side policy resolution.

**Specification Coverage:**
- local-change migration and rollback boundary
- generated-source consistency
- backend proof remains optional for unrelated local changes
- host projects resolved skills only

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `repo_config/harness.yaml:skill_sets`
- Modify: `repo_config/harness.yaml:operating_profiles`
- Modify: `repo_config/harness.yaml:routes.local_change`
- Modify: `scripts/render_harness_routing.py:render`
- Modify: `tests/test_render_harness_routing.py:test_rendered_routing_matches_policy`
- Generate: `docs/operating_system/tooling/harness-routing.generated.md`
- Modify: `../codex-harness-host/src/codex_harness_host/adapter.py:CodexAdapter._prompt`
- Modify: `../codex-harness-host/tests/test_adapter.py:test_prompt_renders_work_context_once`
- Add composed-packet regression in `../codex-harness-host/tests/test_adapter.py`

**Dependencies:**
- Tasks 1 through 3 pass.
- Core Task 2 resolves immutable ordered `packet["skills"]`; host consumes that field without loading policy or resolving facets.

**Steps:**
- [ ] Define `local_change_base` with `skill-code-standards`, `skill-executing-plans`, and `skill-test-driven-development`; define `backend_verification` with `skill-backend-verification`. Give each set controller-facing selection guidance.
- [ ] Define `local_change_standard` with current `normal`, `workspace_write`, `code`, `write`, `codex_app_server`, and `default` budget values. Define `local_change_extended` extending standard and changing only its execution budget to `extended`.
- [ ] Migrate `routes.local_change` to required `local_change_base`, allowed `backend_verification`, default `local_change_standard`, allowed standard and extended profiles, and one `dispatch_timeout` edge from standard to extended. Preserve role, rules, delegation, approval gates, and execution modes.
- [ ] Change routing renderer output to show required and allowed skill-set IDs, resolved required-only baseline skills, default and allowed operating-profile IDs, and existing role data. Read only canonical policy; do not reproduce core resolution logic in renderer.
- [ ] Regenerate `docs/operating_system/tooling/harness-routing.generated.md` with `scripts/render_harness_routing.py`.
- [ ] Extend `CodexAdapter._prompt` task-context payload with ordered `packet["skills"]` and instruction to follow every named repository skill. Preserve legacy fallback only for packets lacking the new audit metadata; never load policy or infer skills in host.
- [ ] Add host adapter regression for legacy and composed packets. Assert prompt includes only packet-resolved ordered skill names, omits `skill_sets` from activation behavior, and keeps existing work-context and transport framing behavior.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest tests/test_render_harness_routing.py -q`
- Expected: renderer exposes catalog and profile policy names; generated routing stays policy-derived.
- [ ] `\.venv\Scripts\python.exe scripts\render_harness_routing.py --check`
- Expected: generated routing file has no drift.
- [ ] `uv run pytest tests/test_adapter.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: host projects only resolved `skills` for legacy and composed packets, ignores audit metadata for activation, and leaves transport framing unchanged.

**Exit Criteria:**
- `local_change` gains optional backend verification through policy selection. Generated and host surfaces create no second skill or profile owner.

### Task 5: Run cross-contract and distribution proof

**Purpose:**
- Verify packet lifecycle, generated docs, starter-kit distribution, and installed host readiness from canonical policy.

**Specification Coverage:**
- Backend Verification Claims
- all acceptance criteria
- generated routing and starter-kit distribution
- API compatibility and no historical-run mutation

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `packages/harness-core/tests/test_config_validation.py`
- Verify: `packages/harness-core/tests/test_managed.py`
- Verify: `packages/harness-core/tests/test_compatibility.py`
- Verify: `tests/test_render_harness_routing.py`
- Verify: `tests/test_starter_kit_generation.py`
- Verify: `scripts/build_starter_kit.py:main`
- Verify: `scripts/validate_starter_kit.py:validate_starter_kit`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `../codex-harness-host/tests/test_adapter.py`

**Dependencies:**
- Tasks 1 through 4 pass.
- Preserve existing terminal run evidence. Never resume or mutate prior blocked runs.

**Steps:**
- [ ] Run full core tests for policy validation, packet resolution, managed lifecycle, successors, and packet compatibility.
- [ ] Run generated-routing and starter-kit tests, then rebuild and validate disposable starter-kit output from manifest.
- [ ] Run host adapter proof plus `capabilities` and `preflight` against trusted user configuration. Treat failed provider configuration as host-environment evidence; do not weaken packet binding checks.
- [ ] Run repository and planning lifecycle validators. Confirm no request, packet, host, or provider API version change.
- [ ] Inspect changed paths and `git diff --check`. Keep unrelated current modifications intact. Handoff downstream `JOB-PROJECT` package pin only after fresh source proof.

**Verification:**
- [ ] `\.venv\Scripts\python.exe -m pytest packages/harness-core/tests -q`
- Expected: policy, resolver, successor, lifecycle, and compatibility suites pass.
- [ ] `\.venv\Scripts\python.exe -m pytest tests/test_render_harness_routing.py tests/test_starter_kit_generation.py -q`
- Expected: policy-derived docs and starter distribution tests pass.
- [ ] `\.venv\Scripts\python.exe scripts\build_starter_kit.py --repo-root .`
- Expected: `generated_exports/project-OS-starter-kit` rebuilds from canonical sources.
- [ ] `\.venv\Scripts\python.exe scripts\validate_starter_kit.py --repo-root .`
- Expected: distributed starter kit contains canonical `repo_config/harness.yaml` and excludes private runtime configuration.
- [ ] `uv run pytest tests/test_adapter.py tests/test_app_server.py -q` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: host consumes packet contract without fallback or transport regression.
- [ ] `uv run codex-harness-host capabilities` and `uv run codex-harness-host preflight` from `C:\Users\HOANG PHI LONG DANG\repos\codex-harness-host`
- Expected: trusted `stdio`, host API `4`, provider contract `4`, and `readiness: ready`.
- [ ] `\.venv\Scripts\python.exe scripts\validate_repo_contracts.py`
- Expected: repository contracts pass.
- [ ] `\.venv\Scripts\python.exe scripts\validate_planning_lifecycle.py`
- Expected: active spec and proposed implementation plan metadata pass.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Fresh proof covers every acceptance criterion. Distribution, host, and core use one packet contract. No blocked run is resumed.

## Verification

- Policy grammar: focused config tests prove catalog, composed-route, profile, and edge validation while legacy direct routes stay valid.
- Packet resolution: focused managed tests prove deterministic required-only and selected-facet skills, immutable provenance, profile envelopes, directed escalation, and binding inheritance.
- Host boundary: focused adapter test proves host task context projects packet-resolved `skills` and keeps audit metadata out of activation behavior.
- Generated output: renderer test and drift check prove routing docs derive from `repo_config/harness.yaml`.
- Distribution: starter-kit build and validation prove canonical policy ships without trusted user provider configuration.
- Final: full core suite, host suite, readiness preflight, repository validators, planning validator, and whitespace check pass.

## Completion Criteria

- `skill_sets` and `operating_profiles` have one canonical policy owner.
- `local_change` resolves base skills without backend proof and adds backend proof only from a recorded allowed selection.
- Packets retain deterministic skill and profile provenance while legacy packets remain consumable.
- Only route-allowed named profiles select authority-bearing behavior.
- Same-provider timeout escalation creates a fresh bound successor; mismatched provider request and binding drift block before lanes.
- Generated routing and starter-kit output have no policy drift.
- No request, packet, host, or provider API version changes.
- `skill-verification-before-completion` records fresh proof before plan status changes from `proposed`.
