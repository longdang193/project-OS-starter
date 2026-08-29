---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: pact-schemathesis-capability-integration
targets:
  - .agents/skills/skill-backend-verification/SKILL.md
  - docs/operating_system/rules/backend-verification-rule.md
  - docs/operating_system/tooling/frontend-backend-integration-tools.md
  - .agents/skills/skill-full-stack-integration/SKILL.md
  - tests/test_runtime_tool_resolution_contract.py
---

# Pact and Schemathesis Capability Integration

## Goal

Add provider-neutral routing for schema-driven API evidence and consumer-driven
compatibility evidence. Preserve canonical contract ownership, direct backend
proof, optional runtime resolution, unchanged Starter dependencies, and
generated adapter ownership. Pact and Schemathesis remain runtime methods, not
Starter dependencies, registries, skills, or source-of-truth artifacts.

## Implementation Outcomes

### Provider-neutral evidence routing

Backend verification recognizes `schema-driven API evidence` for HTTP/API
boundaries with a machine-readable contract and material behavior change. Full
integration guidance recognizes `consumer-driven compatibility evidence` for
independently evolving consumer/provider boundaries across frontend, mobile,
CLI, service, and messaging consumers.

### Preserved evidence and ownership boundaries

Canonical transport or event contracts remain authoritative. Schema-driven
evidence supplements direct backend proof and cannot prove durable state, side
effects, authorization, dependency semantics, rollback, retry, idempotency, or
traceability. Consumer-driven evidence is scoped to tested interactions and
consumer/provider revisions; it cannot prove complete provider correctness.

### Synchronized runtime surfaces

Canonical rule and skill edits regenerate the tracked Codex, Claude, and
Antigravity surfaces. Focused semantic tests, adapter drift checks, repository
contract validation, and diff checks prove alignment without adding provider
packages or changing runtime-resolution architecture.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-backend-verification`, `skill-full-stack-integration`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit named canonical documentation, extend the named test, regenerate tracked adapter outputs, run declared local validation commands
- User-approval actions: provider installation, provider authentication, broker or external-service writes, commit, push, publication, discard, cleanup of unrelated files, or destructive recovery
- Parallel ownership: none
- Sequential fallback: execute tasks in listed order; stop on canonical ownership conflict, generated-surface drift outside named outputs, or unavailable mandatory validation

## Task Breakdown

### Task 1: Define Schema-Driven Backend Evidence

**Purpose:**
- Add precise, supplemental schema-driven API evidence semantics without weakening direct backend verification.

**Task Function:**
- Backend verification contract maintenance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, source-first documentation change with existing ownership and evidence rules.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused semantic tests and repository contract validation follow in later tasks.

**Specification Coverage:**
- HTTP/API plus machine-readable contract plus material behavior change triggers optional schema-driven API evidence.
- Provider output supplements, never replaces, direct backend boundary, failure, state, dependency, authorization, rollback/idempotency, and trace proof.
- Evidence records canonical schema reference, operation scope, invocation, result, artifact path when produced, and coverage limits.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `.agents/skills/skill-backend-verification/SKILL.md:Core Method and Evidence Output`
- Modify: `docs/operating_system/rules/backend-verification-rule.md:backend evidence bullets`
- Verify: `docs/operating_system/tooling/runtime-tool-resolution.md:Requirement Contract, Resolution Order, Evidence Authority, Security Boundary, Fallback`

**Dependencies:**
- Current backend rule and skill remain canonical.
- Runtime resolution remains provider-neutral and forbids implicit installation, connection, authentication, or data egress.

**Authority:**
- Preauthorized local actions: edit the two named canonical files only.
- Stop for: a request to make schema-driven evidence a complete backend gate, add a provider-specific requirement, or change runtime permissions.

**Steps:**
- [x] Add the conditional schema-driven API evidence trigger to the backend skill's contract-proof method.
- [x] Add evidence fields and explicit coverage limits to the backend skill's evidence output.
- [x] Add one backend-rule sentence preserving direct proof requirements.

**Verification:**
- [x] Inspect changed sections against `docs/operating_system/rules/backend-verification-rule.md` and `docs/operating_system/tooling/runtime-tool-resolution.md`.
- Expected: schema-driven evidence is supplemental, provider-neutral, and bounded by existing backend proof requirements.

**Exit Criteria:**
- Backend skill and rule express the trigger, evidence fields, and non-substitution limits without naming Pact or Schemathesis as required methods.

### Task 2: Define General Consumer Compatibility Routing

**Purpose:**
- Add a general consumer/provider capability contract and keep frontend integration as a specialization rather than its owner.

**Task Function:**
- Cross-boundary integration routing maintenance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing integration tooling document owns triggers, mapping, and evidence; existing frontend skill needs only a narrow hook.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: semantic routing assertions follow in Task 3.

**Specification Coverage:**
- Independently evolving consumer/provider boundaries with material compatibility risk trigger `consumer-driven compatibility evidence`.
- Evidence includes consumer identity and tested revision/version/build when available or required, provider identity and tested revision/version/build when available or required, canonical transport/event contract owner/reference, consumer expectation owner/reference, verified interaction scope, invocation and result, freshness, artifact or broker reference when applicable, fallback disposition, and known limits.
- General routing covers frontend, mobile, CLI, service, and messaging consumers.
- Frontend consumers invoke the generic capability through `skill-full-stack-integration` only after direct backend proof.
- Missing mandatory capability evidence is `blocked` or `incomplete`, never verified through source inspection alone.

**Required Skills:**
- `skill-full-stack-integration`

**Files And Symbols:**
- Modify: `docs/operating_system/tooling/frontend-backend-integration-tools.md:Artifact Ownership, Routing Matrix, Contract Evidence Capabilities`
- Modify: `.agents/skills/skill-full-stack-integration/SKILL.md:Core Method and Sidecar Contract`
- Verify: `docs/operating_system/rules/frontend-backend-integration-rule.md:ownership and direct-proof bullets`

**Dependencies:**
- Task 1 complete.
- Existing canonical transport/event contract ownership remains unchanged.

**Authority:**
- Preauthorized local actions: edit the two named canonical files and inspect the named frontend-backend rule.
- Stop for: generic Pact ownership in the frontend-only skill, a new contract/schema owner, a new sidecar artifact type, or provider-specific installation instructions.

**Steps:**
- [x] Add the general consumer/provider compatibility routing row and capability evidence contract to the integration tooling document.
- [x] Replace frontend-skill ownership wording with a frontend-only invocation of the generic capability after backend proof.
- [x] Use `existing canonical transport/event contract` wording so HTTP, messaging, and equivalent contract forms remain supported.

**Verification:**
- [x] Inspect the routing row, capability section, frontend skill method, and existing frontend-backend rule together.
- Expected: non-frontend consumers do not require `skill-full-stack-integration`; canonical contracts remain authoritative; frontend evidence never replaces backend proof.

**Exit Criteria:**
- Generic compatibility routing lives in the integration tooling owner, with a narrow frontend hook and complete evidence/fallback limits.

### Task 3: Add Semantic Routing Regression Tests

**Purpose:**
- Protect capability ownership and evidence semantics without making optional provider names part of long-lived governance tests.

**Task Function:**
- Documentation contract regression testing.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one focused existing test file already validates runtime-resolution ownership and provider neutrality.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the test file provides direct executable proof for the new semantic assertions.

**Specification Coverage:**
- Schema-driven API evidence is supplemental and cannot satisfy state, side-effect, dependency, authorization, rollback/idempotency, or trace proof.
- Consumer-driven compatibility evidence is general, not frontend-owned, and does not own canonical transport/event contracts.
- Frontend specialization delegates to the generic compatibility capability.
- Both capabilities route through runtime resolution.
- Generic guidance remains provider-neutral and `requirements.txt` remains unchanged by plan constraint, not provider-specific test assertions.

**Required Skills:**
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `tests/test_runtime_tool_resolution_contract.py:semantic capability routing tests`
- Verify: `.agents/skills/skill-backend-verification/SKILL.md`
- Verify: `.agents/skills/skill-full-stack-integration/SKILL.md`
- Verify: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Verify: `requirements.txt`

**Dependencies:**
- Tasks 1 and 2 complete.

**Authority:**
- Preauthorized local actions: add focused assertions to the named test file and run its focused test command.
- Stop for: a need to change validator implementation, introduce a provider registry, or assert named optional providers as architecture.

**Steps:**
- [x] Add normalized-content assertions for both capability labels, ownership, routing, and evidence limits.
- [x] Assert runtime-resolution references and provider-neutral wording remain present.
- [x] Run the focused test file and inspect `requirements.txt` for unplanned dependency changes.

**Verification:**
- [x] `py -3 -m pytest -q tests/test_runtime_tool_resolution_contract.py`
- Expected: all focused runtime-policy and capability-routing tests pass.

**Exit Criteria:**
- Semantic tests fail if either capability becomes a source owner, a complete proof substitute, a frontend-only route, or an implicit provider requirement.

### Task 4: Regenerate Tracked Agent Surfaces

**Purpose:**
- Synchronize canonical rule and skill changes into all maintained adapter outputs without hand-editing generated files.

**Task Function:**
- Generated-surface synchronization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository generator owns fan-out.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: generator check and runtime drift validation provide direct output proof.

**Specification Coverage:**
- Canonical skill edits fan out to `generated_agents/codex/skills/`, `generated_agents/claude/skills/`, and `generated_agents/antigravity/skills/`.
- Canonical backend rule edits fan out to `.agents/rules/backend-verification-rule.md`.
- Generated outputs retain ownership headers and contain no unrelated changes.

**Required Skills:**
- `none`

**Files And Symbols:**
- Modify through generator: `generated_agents/codex/skills/skill-backend-verification/SKILL.md`
- Modify through generator: `generated_agents/codex/skills/skill-full-stack-integration/SKILL.md`
- Modify through generator: `generated_agents/claude/skills/skill-backend-verification/SKILL.md`
- Modify through generator: `generated_agents/claude/skills/skill-full-stack-integration/SKILL.md`
- Modify through generator: `generated_agents/antigravity/skills/skill-backend-verification/SKILL.md`
- Modify through generator: `generated_agents/antigravity/skills/skill-full-stack-integration/SKILL.md`
- Modify through generator: `.agents/rules/backend-verification-rule.md`
- Verify: `adapters/codex/mapping.yaml`, `adapters/claude/mapping.yaml`, `adapters/gemini/mapping.yaml`

**Dependencies:**
- Tasks 1–3 complete.
- Canonical sources contain the complete intended change.

**Authority:**
- Preauthorized local actions: run adapter synchronization and generated-output checks.
- Stop for: generated changes outside named fan-out, missing generated headers, or drift caused by unrelated workspace state.

**Steps:**
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Confirm generated copies contain the canonical capability wording and remain provider-neutral.
- [x] Run `py -3 scripts/sync_agent_adapters.py --check --all-platforms`.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- Expected: adapter check succeeds with no drift.

**Exit Criteria:**
- All generated rule and skill surfaces match canonical sources; no generated file was edited directly.

### Task 5: Run Final Repository Verification

**Purpose:**
- Reconcile documentation, tests, generated outputs, dependencies, and preserved workspace state before implementation handoff.

**Task Function:**
- Final plan verification and scope reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final repository acceptance requires lead-controller judgment over generated and preserved workspace state.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final commands cover repository contracts, runtime drift, and patch hygiene.

**Specification Coverage:**
- Optional Pact and Schemathesis methods remain target-project runtime choices.
- No Starter dependency, provider registry, new skill, evidence schema, broker, or persistent repository map is added.
- Existing untracked `.playwright-mcp/` and `db/` paths remain untouched.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `requirements.txt`
- Verify: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Verify: all canonical and generated files named in Tasks 1–4
- Verify: `git status --short` and `git diff --check`

**Dependencies:**
- Tasks 1–4 complete.
- No external provider installation, authentication, broker write, or deployment action is required for this plan.

**Authority:**
- Preauthorized local actions: run repository validators, focused tests, drift checks, and read-only diff/status inspection.
- Stop for: failed required validation, unplanned dependency or generated-surface changes, or evidence that unrelated untracked paths were modified.

**Steps:**
- [x] Run repository contract validation and all-platform runtime drift validation.
- [x] Inspect the final diff for canonical-before-generated ownership and unchanged dependency/runtime policy boundaries.
- [x] Record deviations, substitutions, blockers, or `none` for the execution handoff.

**Verification:**
- [x] `py -3 scripts/validate_agent_runtime_drift.py --skip-deploy-check --all-platforms`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`
- [x] `git diff --check`
- Expected: runtime drift, repository contracts, and diff hygiene pass; final diff contains only approved canonical, test, and generated outputs.

**Exit Criteria:**
- Plan execution and fresh verification are complete; provider invocation remains deferred to target-project runtime resolution.

## Verification

- `py -3 scripts/validate_agent_runtime_drift.py --skip-deploy-check --all-platforms`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 -m pytest -q tests/test_runtime_tool_resolution_contract.py`
- `py -3 scripts/build_starter_kit.py`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 -m pytest tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q`
- `git diff --check`

Fresh verification: runtime drift passed; repository contracts passed; focused
capability tests passed (`20 passed`); starter-kit validation passed; packaging
tests passed (`13 passed`); diff hygiene passed. Starter output contains the
provider-neutral capability guidance. No Pact or Schemathesis package,
authentication, broker, target-project schema, or project-specific tool config
was added.

## Completion Criteria

The plan is ready for completion verification when:

1. canonical backend and integration guidance defines both capabilities without naming optional providers as architecture
2. direct backend proof remains mandatory and consumer compatibility evidence is scoped to tested interactions and revisions
3. semantic tests protect ownership, evidence limits, routing, and runtime-resolution boundaries
4. generated Codex, Claude, Antigravity, and `.agents/rules` surfaces are synchronized and drift-free
5. `requirements.txt`, runtime-resolution architecture, specification and artifact schemas, provider registry, and GitNexus remain unchanged
6. final validation commands pass and final scope preserves unrelated workspace changes

Fresh final verification completed through `skill-verification-before-completion`.
Plan status is `completed`; branch disposition remains outside this plan.
