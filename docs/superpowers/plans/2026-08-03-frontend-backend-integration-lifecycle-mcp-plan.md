---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: frontend-backend-integration-lifecycle-mcp
parent_spec: none
targets:
  - docs/operating_system
  - .agents/skills
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - tests/test_validate_template_required_sections.py
---

# Frontend-Backend Integration Lifecycle And MCP Implementation Plan

## Goal

Add a lightweight draft-spec-to-prototype-to-final-spec lifecycle, make UI intent and integration ownership unambiguous, require direct backend test/state/trace proof whether or not a frontend exists, deliver cross-boundary work through traceable vertical slices, and install Context7 and Specmatic MCP support with stage-specific guidance that preserves source, contracts, tests, and runtime evidence as truth.

## Implementation Outcomes

### Draft And Final Specifications Share One Lifecycle

One specification file begins with `template_id: draft-specification` and `status: proposed`, guides prototype discovery, then is materialized in place as `template_id: detailed-specification` and `status: active` after approval. Git history preserves draft state; no parallel permanent draft artifact or new planning artifact type is introduced.

### UI Intent Has One Owner At Every Stage

Draft specs own exploratory UI intent, prototypes provide validation evidence, finalized specs own approved UI behavior, canonical design-system sources own durable visual primitives, and `*.integration.md` sidecars own only temporary contract-to-UI mapping, unresolved mismatches, and required evidence.

### Integration Work Uses Vertical Capability Slices

Plans divide frontend/backend features by complete user capability rather than frontend and backend phases. Subagent-driven execution is selected only for approved, separable sequential tasks with settled behavior and explicit per-task commit authorization; UI and contract tasks carry required rendered, accessibility, and conformance evidence.

### Backend Verification Works Without A Frontend

Every material backend behavior change has direct boundary proof, important business and failure-path proof, final state or side-effect assertions, and fresh automated test output. Contract, real-dependency, trace, and browser evidence are selected by applicability. Frontend or consumer verification extends backend proof; it never substitutes for it.

### Context7 And Specmatic Are Available And Bounded

Codex can access Context7 for current version-specific library documentation and Specmatic for canonical OpenAPI inspection, mocks, examples, and contract conformance. Neither MCP becomes an architecture, contract, source, test, or runtime owner; absence of either tool falls back to pinned documentation, existing contract tooling, source, and tests.

### Canonical And Generated Surfaces Stay Synchronized

Rules, skills, templates, prompt wording, setup procedures, generated adapters, and starter-kit output agree. Focused tests prove both draft and detailed templates can target `docs/superpowers/specs/*.md` through explicit `template_id` selection.

### Rule And Skill Routing Is Explicit And Resolvable

Agents receive concise triggers from root instructions and planning dispatch, hard invariants from always-applied rules, and detailed methods from one appropriate skill. A canonical integration routing matrix owns stage-to-rule-to-skill handoffs. Repository validation rejects active references to missing skill identifiers or canonical rule paths, preventing stale targets such as the current nonexistent `skill-parallel-execution`.

## Execution Approach

- Mode: `subagent-ready`
- Required skills: `skill-executing-plans`, `skill-subagent-driven-development`, `skill-writing-skills`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: current workspace; optional worktree only if unrelated changes appear before execution
- Commit policy: per-task commits require explicit user authorization before `skill-subagent-driven-development`; without authorization use `skill-executing-plans` inline sequentially
- Parallel ownership: none; rules, skills, root instructions, generated adapters, and starter-kit output are shared sequential surfaces
- Sequential fallback: execute Tasks 1-7 in order with one executor, focused verification after each task, then final verification

## Task Breakdown

### Task 1: Install And Document Integration MCP Servers

**Purpose:**
- Make Context7 and Specmatic available in Codex through private machine configuration and add one reusable setup, smoke-test, fallback, and removal procedure to the starter repository.

**Specification Coverage:**
- Context7 and Specmatic are installed without repository credentials or machine-specific committed paths.
- Current machine uses remote Context7 and Docker-backed Specmatic because Docker is available and Java is not installed.
- MCP availability is proven with temporary evidence that leaves no repository artifact.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `%USERPROFILE%\.codex\config.toml` existing `[mcp_servers.*]` patterns
- Modify: `%USERPROFILE%\.codex\config.toml`
- Add: `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md`
- Modify: `README.md` MCP orientation section
- Verify: Codex MCP tool inventory after restart

**Dependencies:**
- Docker Desktop running for Specmatic
- Network access to `https://mcp.context7.com/mcp` and official Specmatic container registry
- Existing MCP configuration preserved, including tool allowlists and environment sections

**Steps:**
- [ ] Add remote Context7 configuration using `[mcp_servers.context7]` with `url = "https://mcp.context7.com/mcp"`.
- [ ] Add Docker-backed Specmatic configuration using `docker run --rm -i -v .:/usr/src/app specmatic/specmatic mcp server`, with a 120-second startup timeout. Document that `.` must resolve to the active project workspace; clients that launch from another directory must use a private absolute path.
- [ ] Keep credentials, API keys, tokens, local caches, and generated MCP state outside repository files.
- [ ] Document Windows Codex setup, Docker prerequisite, optional vendor authentication boundary, restart requirement, tool-specific smoke tests, source-first fallback, and removal steps.
- [ ] Restart Codex so both servers register.
- [ ] Smoke Context7 by resolving one installed library and retrieving version-relevant documentation.
- [ ] Smoke Specmatic against a temporary minimal OpenAPI file under `.tmp-tests/mcp-smoke/`, confirm discovery and validation, then remove temporary files.

**Verification:**
- [ ] `docker info`
- Expected: Docker daemon responds successfully.
- [ ] Codex tool inventory contains Context7 documentation tools and Specmatic specification tools after restart.
- Expected: both servers initialize without exposing credentials or committing local configuration.
- [ ] `git status --short`
- Expected: only intended repository documentation changes appear; no `.codex`, MCP cache, temporary OpenAPI file, or credential file appears.

**Exit Criteria:**
- Context7 and Specmatic complete one clean temporary smoke test each, setup documentation is reproducible, and no private runtime state enters Git.

### Task 2: Establish Integration Ownership And Tool Routing

**Purpose:**
- Create one hard-invariant rule and one operational tooling guide defining artifact ownership, MCP boundaries, handoffs, and source-first fallbacks across integration lifecycle.

**Specification Coverage:**
- Brief, draft spec, prototype, final spec, canonical contract, plan, sidecar, code, tests, and runtime evidence have non-overlapping ownership.
- Backend task-local verification remains required when no frontend, browser flow, or integration sidecar exists.
- Context7 answers library-documentation questions; Specmatic answers canonical contract, mock, example, and conformance questions.
- Existing Serena, GitNexus, DeepWiki, Playwright, and Chrome DevTools responsibilities remain unchanged and non-duplicated.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Add: `docs/operating_system/rules/frontend-backend-integration-rule.md`
- Add: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Modify: `docs/operating_system/README.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` integration routing summary
- Verify: `docs/operating_system/governance/repo-governance.md` ownership boundaries

**Dependencies:**
- Task 1 setup contract and verified server capabilities

**Steps:**
- [ ] Define hard invariants: one specification owner, one transport-contract owner, prototypes as evidence rather than truth, sidecars as temporary mapping/evidence, vertical slices, and source/test/runtime precedence.
- [ ] Define Context7 routing: use only for current version-specific external library documentation when local pinned source or maintained docs do not answer question; record library/version context; treat output as advisory.
- [ ] Define Specmatic routing: use only when canonical OpenAPI exists or is deliberately established; reference rather than copy schemas; use mocks and conformance checks as contract evidence rather than replacements for backend/frontend tests.
- [ ] Define backend evidence profiles: direct boundary, business/failure, state/side-effect, and fresh automated proof are required; contract, real dependency, trace, performance, and browser proof are conditional on changed behavior and approved claims.
- [ ] Define trace verification as reconstruction of one representative operation using existing logs, trace/correlation IDs, job/message IDs, dependency records, or test instrumentation; do not require new observability infrastructure for every backend change.
- [ ] Keep Grafana, Postman, database, and GitHub MCPs as optional target-project profiles with active consumers; do not add them to default Codex setup in Task 1.
- [ ] Define handoffs to Serena/GitNexus for code impact, Playwright for repeatable browser behavior, Chrome DevTools for diagnosis, and native tests/CI for durable enforcement.
- [ ] Add one canonical routing matrix with columns for trigger, owning rule or invariant source, primary method skill, conditional supporting skill/tool, required evidence, and next handoff. Map problem exploration, draft/final specification, backend verification, frontend/backend integration, UI component work, approved-plan execution, subagent execution, debugging, and final verification.
- [ ] Route each trigger to one primary method skill. Name supporting skills only at real boundary crossings so agents do not load overlapping methods or rediscover ownership.
- [ ] Make each new method-backed rule name its primary skill, and make each corresponding skill name the applicable canonical rule path in its boundaries or conditional references. Do not force every rule to name a skill, and do not duplicate rule invariants inside skills.
- [ ] Keep root instructions and planning dispatch as concise trigger surfaces that link to canonical methods; do not copy full skill processes or tooling tables into them.
- [ ] Use conditional references for optional rules and tooling guides. Do not add unconditional `required_reads` merely to make bidirectional links; always-applied rules and exact skill descriptions already provide discovery context.
- [ ] State MCP unavailability never blocks safe source-first work and never causes duplicate contracts or documentation layers.
- [ ] Add concise links from operating-system index; keep detailed guidance out of root README and generated root instructions.

**Verification:**
- [ ] `rg -n "skill-brainstorming|skill-spec-drafting|skill-backend-verification|skill-full-stack-integration|skill-frontend-component-engineering|skill-executing-plans|skill-subagent-driven-development|skill-systematic-debugging|skill-verification-before-completion" docs/operating_system/tooling/frontend-backend-integration-tools.md docs/operating_system/templates/agents/root-AGENTS.template.md`
- Expected: routing matrix names every lifecycle owner once and root instructions contain only concise activation guidance.
- [ ] `rg -n "Context7|Specmatic|backend verification|direct boundary|draft spec|prototype|integration.*sidecar|vertical slice" docs/operating_system/rules docs/operating_system/tooling docs/operating_system/README.md`
- Expected: one canonical rule owns invariants, one tooling guide owns operational routing, and index text only links to owners.
- [ ] Review new files against `docs/operating_system/governance/repo-governance.md`.
- Expected: no duplicated planning process, transport schema, UI checklist, or client setup instructions across ownership layers.

**Exit Criteria:**
- Integration ownership and MCP routing have one canonical source each, with explicit tool handoffs and fallbacks.

### Task 3: Add Backend Test, Trace, And Verification Method

**Purpose:**
- Add one backend-independent rule and one task-local verification skill that prove backend behavior directly before optional frontend or consumer integration.

**Specification Coverage:**
- Direct backend proof is required for API routes, workers, queue consumers, scheduled tasks, webhooks, commands, and services whether or not a frontend exists.
- Evidence is claim-based rather than an eight-layer mandatory checklist.
- One representative operation is reconstructable through existing observability or test instrumentation without forcing Grafana, OpenTelemetry, or logging at every layer.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Add: `docs/operating_system/rules/backend-verification-rule.md`
- Add: `.agents/skills/skill-backend-verification/SKILL.md`
- Modify: `.agents/skills/skill-code-standards/SKILL.md`
- Modify: `.agents/skills/skill-test-driven-development/SKILL.md` Integration section
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md` evidence map and related skills
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` Backend Work routing
- Verify: `.agents/skills/skill-systematic-debugging/SKILL.md` remains failure diagnosis owner

**Dependencies:**
- Task 2 ownership and tool-routing contracts

**Steps:**
- [ ] Define hard invariants: frontend output is never backend proof; important failed operations leave consistent state; direct boundary, state, failure, and automated evidence are required for material backend behavior changes.
- [ ] Define applicability profiles instead of mandatory test layers: unit proof for isolated rules, contract proof when a canonical contract exists, real-dependency proof when behavior depends on it, browser E2E when a frontend exists, and performance proof only for explicit performance claims.
- [ ] Create `skill-backend-verification` with sequence: define claims, test boundary directly, verify business/failure behavior, verify state/rollback/idempotency, verify contract and real dependencies when applicable, reconstruct one representative operation, then hand evidence to consumer integration and final verification.
- [ ] Make backend rule refer agents to `skill-backend-verification`; make backend skill link conditionally to integration tooling and explicitly hand failures to `skill-systematic-debugging`, implementation loops to `skill-test-driven-development`, consumer integration to `skill-full-stack-integration`, and final claims to `skill-verification-before-completion`.
- [ ] Add concise root trigger: use `skill-backend-verification` whenever material backend behavior changes, whether or not a frontend exists.
- [ ] Keep `skill-test-driven-development` as implementation-loop owner, `skill-systematic-debugging` as root-cause owner, and `skill-verification-before-completion` as final completion owner.
- [ ] Add a backend-only evidence row to final verification and a separate frontend/backend integration row that requires backend evidence plus browser/client proof.
- [ ] State MCP tools may inspect or invoke supporting systems, but native test-runner output and committed assertions remain proof.

**Verification:**
- [ ] `rg -n "frontend.*never.*backend proof|direct boundary|state|rollback|representative operation|skill-backend-verification" docs/operating_system/rules/backend-verification-rule.md .agents/skills/skill-backend-verification .agents/skills/skill-code-standards .agents/skills/skill-test-driven-development .agents/skills/skill-verification-before-completion`
- Expected: backend task-local method, debugging, TDD, full-stack integration, and final verification retain distinct owners.
- [ ] Review required versus conditional evidence in new rule and skill.
- Expected: no universal requirement for all eight test levels, Grafana, OpenTelemetry, correlation-ID framework, or browser flow.

**Exit Criteria:**
- Backend changes have one reusable direct-verification method independent of frontend availability, with proportional state, failure, contract, dependency, and trace evidence.

### Task 4: Add Draft-Spec Promotion And Prototype Validation Flow

**Purpose:**
- Add lightweight draft specification template and update planning/specification methods so one mutable spec guides prototyping and is materialized in place after validation.

**Specification Coverage:**
- Draft template captures goal, scope, user flow, business rules, UI intent, known states, assumptions, open questions, prototype reference, and validation findings.
- Detailed specification records approved behavior, prototype reference, state transitions, validation/error requirements, acceptance criteria, observability intent, and approved deferrals.
- Detailed specification selects applicable backend boundary, state, failure, dependency, contract, and trace claims without prescribing redundant test layers.
- No new planning artifact type, schema field, lifecycle generator, or duplicate draft file is introduced.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Add: `docs/operating_system/templates/draft-specification-template.md`
- Modify: `docs/operating_system/templates/detailed-specification-template.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Modify: `tests/test_validate_template_required_sections.py`
- Verify: `scripts/validate_template_required_sections.py:_select_rule`

**Dependencies:**
- Task 2 artifact ownership and tool-routing rule
- Task 3 backend verification contract

**Steps:**
- [ ] Add `draft-specification` metadata targeting `docs/superpowers/specs/*.md`, requiring lightweight exploration sections and `artifact_type: spec`, `status: proposed`, `layer: change`.
- [ ] Define promotion as in-place transformation from draft template to detailed template after prototype approval; preserve history through Git rather than second permanent artifact.
- [ ] Add draft and materialize modes to `skill-spec-drafting`, including return-to-prototype behavior when validation disproves assumptions.
- [ ] Route `skill-brainstorming` to draft spec when prototype work needs stable behavioral guidance, while retaining direct approved scope for local design-clear work.
- [ ] Extend planning dispatch with concise method routing: backend proof uses `skill-backend-verification`; matching frontend/backend contract work uses `skill-full-stack-integration`; failures return to `skill-systematic-debugging`; final completion uses `skill-verification-before-completion`.
- [ ] Link brainstorming and specification skills to the integration tooling guide only when external library, contract, prototype, or backend-verification evidence is material; avoid mandatory reads for ordinary planning work.
- [ ] Add Context7 as optional evidence for external framework constraints and Specmatic as optional contract-feasibility evidence without letting either tool own specification decisions.
- [ ] Update detailed template guidance for approved user flow, UI behavior/state transitions, prototype reference, contract requirements, observability intent, and unresolved approved deferrals.
- [ ] Add backend verification intent covering direct boundary, expected state or side effects, important failure behavior, contract applicability, real dependencies, and representative-operation traceability.
- [ ] Update prompt wording to support draft creation and final materialization instead of jumping directly to frozen detailed specification.
- [ ] Add validator tests proving two spec templates can share one target glob and documents select correct rule through `template_id`.
- [ ] Expand shipped-template/schema coverage so both draft and detailed spec templates satisfy required frontmatter.

**Verification:**
- [ ] `python -m pytest tests/test_validate_template_required_sections.py -q`
- Expected: existing template tests and new shared-glob draft/detailed selection tests pass.
- [ ] `python scripts/validate_template_required_sections.py`
- Expected: existing planning artifacts remain valid and detailed-spec grandfathering behavior does not change.
- [ ] `python scripts/validate_planning_lifecycle.py`
- Expected: draft specs remain normal `spec` artifacts with allowed `proposed` status; no planning schema change is required.

**Exit Criteria:**
- Repository validates lightweight draft spec and later same path as detailed approved spec without duplicated lifecycle data.

### Task 5: Refine UI Intent And Full-Stack Sidecar Boundaries

**Purpose:**
- Align frontend rule and implementation skills with new specification lifecycle, remove duplicate UI-intent ownership, and make installed UI guidance platform-safe.

**Specification Coverage:**
- Final spec owns approved user-visible behavior; design-system sources own durable visual primitives; component engineering owns runtime state implementation.
- Integration sidecar owns contract-to-UI mapping, unresolved mismatches, and acceptance evidence only.
- `ui-ux-pro-max` is used only when target platform matches declared scope and never creates second design-system SSOT without explicit approval.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/rules/frontend-ui-rule.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` Front-End Work section
- Modify: `.agents/skills/skill-distinctive-frontend-design/SKILL.md`
- Modify: `.agents/skills/skill-frontend-component-engineering/SKILL.md`
- Modify: `.agents/skills/skill-full-stack-integration/SKILL.md`
- Modify: `.agents/skills/skill-code-standards/SKILL.md`
- Verify: no active `*.integration.md` sidecars require migration

**Dependencies:**
- Task 3 backend verification method exists
- Task 4 draft/final spec ownership exists

**Steps:**
- [ ] Replace "temporary UI intent" sidecar ownership with "temporary contract-to-UI mapping, unresolved mismatch, and acceptance evidence" everywhere active guidance uses old phrase.
- [ ] Update sidecar example to reference final spec and canonical contract, map contract outcomes to named UI states, list unresolved mismatches, and avoid copied request/response schemas.
- [ ] Require component engineering to consume approved UI behavior and state transitions rather than invent product behavior during implementation.
- [ ] Keep aesthetic direction in `skill-distinctive-frontend-design`; treat prototypes and rendered comparisons as evidence feeding specification approval.
- [ ] Gate `ui-ux-pro-max` by declared target platform and existing project design-system ownership; prohibit automatic persistence of `design-system/MASTER.md` or page overrides when canonical design system already exists.
- [ ] Add Context7 only for version-specific UI framework or accessibility-library documentation; keep Playwright and Chrome DevTools routing unchanged.
- [ ] Add Specmatic to full-stack integration only when canonical OpenAPI exists, using it for mock/conformance evidence before and after real backend integration.
- [ ] Require `skill-full-stack-integration` to invoke `skill-backend-verification` for direct backend, state, failure, dependency, contract, and representative-operation evidence before accepting browser/client proof.
- [ ] Make frontend/backend integration rule refer agents to `skill-full-stack-integration` for cross-boundary method and `skill-backend-verification` for backend proof; make frontend UI rule refer to full-stack skill only when contract or route work exists.
- [ ] Give `skill-full-stack-integration` one conditional tooling-guide reference and explicit handoffs to backend verification, frontend component engineering, Playwright/DevTools evidence, and final verification without copying those methods.
- [ ] Keep `skill-frontend-component-engineering` focused on state ownership and `skill-distinctive-frontend-design` focused on aesthetic direction; each links to frontend UI rule and full-stack skill only at real boundary crossings.
- [ ] Preserve accessibility, responsive, theme, long-content, state, and committed-regression requirements in canonical frontend rule.

**Verification:**
- [ ] `rg -n "temporary UI intent" AGENTS.md docs .agents generated_agents --glob '!docs/superpowers/plans/**'`
- Expected: no active canonical or generated guidance retains obsolete sidecar ownership after synchronization.
- [ ] `rg -n "Context7|Specmatic|ui-ux-pro-max|Playwright MCP|Chrome DevTools MCP|skill-backend-verification" docs/operating_system/rules/frontend-ui-rule.md .agents/skills/skill-distinctive-frontend-design .agents/skills/skill-frontend-component-engineering .agents/skills/skill-full-stack-integration`
- Expected: tools have distinct questions, platform-safe activation, and source-first fallback.

**Exit Criteria:**
- UI behavior, visual direction, component state, contract mapping, and runtime evidence each have one explicit owner.

### Task 6: Make Plans And Subagent Execution Vertical-Slice Aware

**Purpose:**
- Ensure implementation plans and subagent reviews preserve vertical capability slices, settled behavior, commit authorization, direct backend proof, and task-specific UI/contract evidence.

**Specification Coverage:**
- Frontend/backend work is not decomposed into isolated frontend and backend phases.
- Backend-only tasks select direct boundary, state, failure, dependency, contract, and trace evidence without requiring a frontend sidecar.
- `subagent-ready` means approved plan, separable sequential tasks, same-session coordination, and explicit per-task commit authorization.
- Context7 and Specmatic are named only when task-local questions require them.

**Required Skills:**
- `skill-writing-skills`
- `skill-subagent-driven-development`

**Files And Symbols:**
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `docs/operating_system/templates/implementation-plan-template.md` Execution Approach and task guidance
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`
- Modify: `.agents/skills/skill-subagent-driven-development/implementer-prompt.md`
- Modify: `.agents/skills/skill-subagent-driven-development/task-reviewer-prompt.md`
- Modify: `.agents/skills/skill-dispatching-parallel-agents/SKILL.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `.agents/skills/skill-refactoring-assessment/SKILL.md`
- Modify: `.agents/skills/skill-using-superpowers/references/codex-tools.md`
- Modify: `.agents/skills/skill-using-superpowers/references/gemini-tools.md`
- Modify: `scripts/validate_agent_metadata_schema.py`
- Modify: `tests/test_validate_agent_metadata_schema.py`
- Verify: `.agents/skills/skill-executing-plans/SKILL.md` remains general execution owner

**Dependencies:**
- Task 2 tool-routing contracts
- Task 3 backend verification method
- Task 4 final-spec handoff
- Task 5 sidecar and evidence boundaries

**Steps:**
- [ ] Require backend and frontend/backend plans to define smallest valuable capability as task boundary, ordered as contract when applicable, backend implementation, direct backend test, state/failure verification, real dependency proof when material, consumer/frontend integration when present, representative trace, and final verification.
- [ ] Add `Commit policy` to plan Execution Approach because subagent-driven execution consumes that decision; keep it body metadata rather than frontmatter.
- [ ] Tighten `subagent-ready` selection to match `skill-subagent-driven-development` preconditions and name `skill-executing-plans` as fallback without commit authorization.
- [ ] Require backend task plans to name applicable direct boundary, final state or side effects, important failures, rollback/idempotency behavior, real dependencies, contract evidence, and representative-operation trace mechanism.
- [ ] Require frontend integration tasks additionally to name final spec, prototype reference when material, canonical contract owner, integration sidecar, browser flow, and sidecar removal condition.
- [ ] Require implementer reports to include applicable backend test/state/failure/trace evidence; material UI tasks add rendered viewport/theme/accessibility/state evidence; Specmatic tasks add contract discovery, validation, mock, or conformance evidence named by plan.
- [ ] Require task reviewers to reject frontend-only proof for backend claims and treat missing required backend, browser, or contract evidence as spec-compliance findings without rerunning broad suites or expanding task scope.
- [ ] Preserve fresh implementer, task review, fix/re-review, final broad review, and final verification sequence.
- [ ] Resolve every canonical `skill-parallel-execution` reference by expanding `skill-dispatching-parallel-agents` to own approved disjoint concurrent lanes as well as investigation fan-out, then update executing, planning, refactoring, subagent, and `skill-using-superpowers` tool-reference guidance to reference the existing owner.
- [ ] Extend agent metadata validation to reject unresolved backticked `skill-*` identifiers and backticked `docs/operating_system/rules/*.md` paths across all canonical skill Markdown, rules, root template, and planning dispatch; keep intentionally invalid examples from masquerading as active routing references.
- [ ] Add focused tests showing valid skill/rule references pass, one missing skill target fails with exact file and identifier, and one missing rule path fails with exact file and path.
- [ ] Keep subagent skill dependent on plan `Required Skills`; do not hardcode every backend, frontend, contract, or tooling skill into every implementer brief.

**Verification:**
- [ ] `rg -n "vertical capability|Commit policy|skill-backend-verification|direct backend|state.*failure|representative trace|Context7|Specmatic|browser evidence|contract evidence" .agents/skills/skill-writing-plans docs/operating_system/templates/implementation-plan-template.md .agents/skills/skill-subagent-driven-development`
- Expected: plan, implementer, and reviewer contracts agree without repeating full MCP or frontend rules.
- [ ] `python -m pytest tests/test_validate_agent_metadata_schema.py -q`
- Expected: canonical routing references resolve; missing `skill-*` identifiers and canonical rule paths are rejected with actionable locations.
- [ ] `rg -n "skill-parallel-execution" .agents/skills docs/operating_system --glob '!docs/superpowers/plans/**'`
- Expected: no canonical entrypoint, prompt, or tool-reference file retains nonexistent `skill-parallel-execution`; concurrent lanes route through `skill-dispatching-parallel-agents`.
- [ ] Review `skill-subagent-driven-development` against `skill-executing-plans`.
- Expected: subagent skill remains specialized execution method, not design, specification, planning, or verification owner.

**Exit Criteria:**
- Approved backend and vertical-slice plans can execute through subagents without rediscovering backend claims, UI behavior, contract ownership, tool routing, or evidence requirements.

### Task 7: Regenerate, Validate, And Rebuild Distributed Surfaces

**Purpose:**
- Synchronize all generated runtime adapters and starter-kit output, then prove repository contracts and MCP guidance remain coherent.

**Specification Coverage:**
- Canonical sources remain editable owners; generated rules, root instructions, provider skills, and starter-kit export contain synchronized results.
- No machine configuration, credential, temporary contract, private MCP state, or stale ownership phrase enters distributed output.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `repo_config/starter-kit-manifest.json` so distributed skills retain referenced tooling guides
- Generate: `AGENTS.md`
- Generate: `.agents/rules/*.md`
- Generate: `generated_agents/codex/**`
- Generate: `generated_agents/claude/**`
- Generate: `generated_agents/antigravity/**`
- Generate: `generated_exports/project-OS-starter-kit/**`
- Verify: `repo_config/starter-kit-manifest.json`

**Dependencies:**
- Tasks 1-6 complete and focused checks passing

**Steps:**
- [ ] Run adapter synchronization for every platform from canonical rules, skills, and root template.
- [ ] Remove obsolete starter-kit omission for `docs/operating_system/tooling`; distributed skills already reference that directory. Rebuild output and rely on directory ownership for new files rather than redundant explicit entries.
- [ ] Run focused template, adapter, metadata, starter-kit, and repository-contract tests.
- [ ] Run stale-reference searches for obsolete sidecar wording, duplicate draft artifacts, unsupported universal `ui-ux-pro-max` routing, copied schema guidance, frontend-only backend proof, and mandatory observability infrastructure.
- [ ] Run routing-reference validation and inspect root/rule/skill handoffs for missing, circular, or duplicated ownership.
- [ ] Inspect `git diff --check`, generated headers, and working-tree status.
- [ ] Re-run Context7 and Specmatic temporary smoke tests after final configuration and documentation settle.

**Verification:**
- [ ] `python scripts/sync_agent_adapters.py --all-platforms`
- [ ] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `python scripts/build_starter_kit.py`
- [ ] `python scripts/validate_starter_kit.py`
- [ ] `python scripts/validate_agent_runtime_drift.py`
- [ ] `python scripts/validate_repo_contracts.py`
- [ ] `python -m pytest tests/test_validate_agent_metadata_schema.py tests/test_validate_template_required_sections.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- [ ] `git diff --check`
- Expected: every command exits successfully; generated and starter-kit surfaces match canonical sources.
- [ ] `rg -n "temporary UI intent|design-system/MASTER.md.*must|Context7.*(source of truth|authoritative)|Specmatic.*(contract owner|source of truth)|frontend-only proof is sufficient|Grafana.*required|OpenTelemetry.*required" AGENTS.md docs .agents generated_agents generated_exports --glob '!docs/superpowers/plans/**'`
- Expected: no stale or ownership-violating active guidance remains.
- [ ] Run routing resolver from `scripts/validate_agent_metadata_schema.py` through `python scripts/validate_agent_metadata_schema.py`.
- Expected: every active skill reference resolves; every required read and explicit rule/skill path exists.
- [ ] `git status --short`
- Expected: only intended canonical files, generated outputs, tests, and this plan are changed; no `%USERPROFILE%\.codex` content or `.tmp-tests/mcp-smoke` artifact is tracked.

**Exit Criteria:**
- Canonical, generated, distributed, runtime, and test evidence agree with approved specification lifecycle, backend verification method, integration flow, and MCP boundaries.

## Verification

### Execution Status

- Repository implementation, generated adapters, deployed Codex runtime, and starter-kit rebuild are complete.
- Context7 direct MCP initialization returned HTTP 200 and protocol metadata.
- Specmatic `v2.51.1` MCP server started, discovered temporary OpenAPI 3.0.3 contract, and validated one external example; temporary files were removed.
- Focused tests, full `68`-test suite, repository contracts, adapter checks, starter-kit validation, runtime drift, metadata resolver, template validators, and `git diff --check` pass.
- Fresh Codex MCP evidence passed: Context7 resolved `/python/cpython` and retrieved current `tomllib` documentation; Specmatic listed active mock servers successfully.
- External MCP verification complete. Plan status is `completed`.

- `python scripts/validate_planning_lifecycle.py`
- `python scripts/validate_template_required_sections.py`
- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_starter_kit.py`
- `python -m pytest tests/test_validate_agent_metadata_schema.py tests/test_validate_template_required_sections.py tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py -q`
- `git diff --check`
- Context7 smoke: resolve one pinned library and retrieve version-relevant documentation after Codex restart.
- Specmatic smoke: discover and validate one temporary minimal OpenAPI contract, then confirm temporary files are removed.
- Backend verification inspection: direct backend proof exists independently of frontend proof; required and conditional evidence remain distinct.
- Routing inspection: root instructions and planning dispatch provide concise triggers, rules point to method skills, skills hand off to adjacent owners, and all active `skill-*` references resolve.
- Ownership inspection: one draft/final spec path, one canonical transport contract, sidecar limited to mapping/evidence, and no duplicated UI or MCP guidance.

## Completion Criteria

The plan is ready for completion verification when:

1. Context7 and Specmatic initialize in Codex and pass clean temporary smoke tests without committed credentials or machine state.
2. Draft and detailed specifications share one validated artifact lifecycle and target path.
3. Prototype evidence can refine draft before same specification becomes approved implementation truth.
4. Material backend behavior changes have direct boundary, business/failure, state or side-effect, and fresh automated proof whether or not a frontend exists.
5. Contract, real-dependency, trace, performance, and browser evidence are selected by applicability; no universal Grafana, OpenTelemetry, correlation-ID framework, database MCP, or eight-layer test requirement exists.
6. UI intent, visual direction, component state, transport contract, integration mapping, backend verification, and runtime evidence each have one canonical owner.
7. Context7 and Specmatic have precise stage-specific activation, handoff, evidence, and fallback guidance.
8. Backend and frontend/backend plans use complete capability slices and subagent execution honors settled behavior, commit authorization, direct backend proof, and required UI/contract evidence.
9. Canonical rules, skills, templates, prompts, generated adapters, tests, README guidance, and starter-kit output are synchronized.
10. Root instructions, planning dispatch, rules, and skills use one canonical stage-to-rule-to-skill routing matrix; all active skill identifiers and canonical rule paths resolve, and no nonexistent `skill-parallel-execution` link remains.
11. Every required focused and final verification command passes with no stale wording, generated drift, temporary MCP artifact, secret, or unrecorded scope deviation.

The plan may be marked `completed` only when `skill-verification-before-completion`:

1. runs fresh final verification
2. confirms completion criteria against repository evidence
3. finds no unresolved required task, failed required check, stale status, or unrecorded scope deviation
4. returns `verified` and updates plan status

A checked box records progress; it is not proof by itself.
