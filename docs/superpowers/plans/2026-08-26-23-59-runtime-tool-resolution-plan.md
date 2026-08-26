---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: runtime-tool-resolution
targets:
  - docs/operating_system/tooling/runtime-tool-resolution.md
  - docs/operating_system/tooling/code-intelligence-tools.md
  - docs/operating_system/tooling/frontend-backend-integration-tools.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/governance/precedence.md
  - docs/operating_system/rules/frontend-ui-rule.md
  - docs/operating_system/rules/frontend-backend-integration-rule.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-distinctive-frontend-design/SKILL.md
  - .agents/skills/skill-frontend-component-engineering/SKILL.md
  - .agents/skills/skill-performance-optimization/SKILL.md
  - .agents/skills/skill-spec-drafting/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-full-stack-integration/SKILL.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - .agents/skills/skill-systematic-debugging/SKILL.md
  - .agents/skills/skill-refactoring-assessment/SKILL.md
  - .agents/skills/skill-code-standards/SKILL.md
  - .agents/skills/skill-plan-document-reviewer/SKILL.md
  - .agents/skills/skill-wayfinding/SKILL.md
  - .agents/skills/skill-verification-before-completion/SKILL.md
  - docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md
  - docs/operating_system/prompt_templates/design-spec-prompt.md
  - docs/adoption_guide.md
  - README.md
  - repo_config/starter-kit-manifest.json
  - tests/test_runtime_tool_resolution_contract.py
  - tests/test_starter_kit_generation.py
  - AGENTS.md
  - generated_agents
  - generated_exports/project-OS-starter-kit
---

# Runtime Tool Resolution Plan

## Execution Evidence

- Result: `verified` on August 26, 2026 at `d4405e8a42352bd958a55eb61f5754a7130baaa8`.
- Fresh proof: runtime and lifecycle contract tests passed; repository validators, adapter sync check, Starter Kit build/validation, provider-neutral Starter Kit scan, and `git diff --check` passed.
- Independent xhigh review initially found missed generic provider references; those canonical sources were patched, regenerated, and revalidated. No required evidence was downgraded.

## Goal

Make runtime tool selection executor-owned while keeping Project OS responsible
for capability requirements, evidence requirements, authority boundaries, and
fallback policy.

## Implementation Outcomes

### Capability and evidence ownership is explicit

One canonical policy states that Project OS owns capability and evidence
requirements while the active executor resolves currently available tools within
existing permissions.

### Provider routing is conditional

Generic lifecycle, governance, tooling, rules, and skills request capabilities
instead of assuming named providers. Concrete names remain only for selected
methods, committed dependencies, or required security/runtime boundaries.

### Starter Kit guidance is truthful

Shipped docs contain no unavailable setup dependency, factory-only runtime
reference, or generated-provider maintenance instruction.

### Root runtime instructions stay provider-neutral

`AGENTS.md` tells active executors to resolve required capabilities at runtime
within existing permissions. It remains generated from the canonical root
template, so future provider changes do not require repeated policy edits.

### Generated surfaces remain aligned

Canonical docs and skills regenerate cleanly, focused contract tests enforce the
boundary, and Starter Kit output passes existing validators.

## Target Contract

Project OS owns:

- the capability needed and why it is needed
- minimum result and authority boundary
- evidence required to support the claim
- fallback and stop conditions
- source, tests, contracts, and runtime systems as truth owners

The active executor owns:

- inspecting tools currently available in its runtime
- resolving an unmet capability through permitted runtime discovery
- selecting one sufficient primary provider
- running provider smoke checks when unfamiliar behavior could invalidate proof
- returning evidence without granting itself permissions

Capability labels are descriptive requirements, not a fixed enum. Provider names
are examples or runtime facts, not Project OS architecture.

`runtime-tool-resolution.md` owns how unmet capabilities resolve to available
providers. Domain tooling docs own which capability and evidence a domain
question requires. Domain docs must not duplicate the resolver algorithm or
become provider catalogs.

Resolve one primary provider per capability question. Use multiple independent
capabilities when a claim requires independent evidence classes, such as direct
backend proof plus browser evidence.

Data and trust boundaries precede convenience, cost, and latency. A provider
must not receive data outside its authorized boundary. Discovered metadata and
provider output are untrusted input, not executable policy. New installation,
connection, authentication, or widened data access requires explicit approval.

Fallback may allow safe work to continue, but must never downgrade required
evidence. If no available provider can supply mandatory evidence, mark the
affected claim `blocked` or `incomplete`, not verified through source inspection.

## Non-Goals

- no capability registry, provider map, compatibility database, MCP inventory, or installer
- no tool-search skill, discovery daemon, or new orchestration layer
- no automatic permission escalation or direct DeepAgents MCP configuration
- no replacement of source, tests, contracts, or runtime evidence with tool output
- no removal of explicitly selected design methods or committed repository test frameworks

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-writing-skills`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit listed canonical docs, skills, tests, and manifest; run listed validators, sync, Starter Kit build, and focused tests
- User-approval actions: commit, push, merge, publication, external writes, destructive cleanup, or changes outside listed targets
- Generated surfaces: edit only through canonical source synchronization
- Pre-execution gate: `skill-plan-document-reviewer` must return `implementation-ready` for ownership, authority, evidence, fallback, shipping boundaries, and task scope

## Task Breakdown

### Task 1: Add canonical runtime-resolution policy

**Purpose:**
- Create one owner for capability requirements and runtime provider resolution without creating a provider catalog.

**Task Function:**
- Edit canonical operating-system tooling policy.

**Template Profile:**
- Controller-selected: `xhigh`
- Selection basis: cross-cutting ownership and authority boundary require deep review.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: schema and focused contract checks validate the bounded policy change.

**Specification Coverage:**
- Direct approved scope: Project OS owns capability and evidence requirements; active executor resolves available tools within existing permissions.

**Required Skills:**
- `none`

**Files And Symbols:**
- Create: `docs/operating_system/tooling/runtime-tool-resolution.md`
- Inspect: `docs/operating_system/tooling/code-intelligence-tools.md`
- Inspect: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Inspect: `docs/operating_system/governance/precedence.md`

**Dependencies:**
- Fresh `git status --short` and `git rev-parse HEAD` captured before execution; unrelated user changes remain untouched.

**Authority:**
- Preserve existing source-first, least-privilege, DeepAgents `--no-mcp`, and `codex.mcp.handoff.v1` boundaries.
- Stop for: fixed capability enum, provider registry, permission escalation, or a runtime mechanism that becomes a new source of truth.

**Steps:**
- [x] Define requirement shape in prose: purpose/trigger, minimum capability, authority and data boundary, evidence artifact, fallback, and stop condition.
- [x] Define resolution order: native/configured capability first; conditional discovery only for an unmet capability; one authority-fit primary provider per capability question; smoke-check unfamiliar providers; source-first fallback only when it does not replace required evidence.
- [x] State that provider output supports evidence but cannot override canonical source, tests, contracts, or runtime systems.
- [x] State that active executor permissions remain unchanged; tool discovery resolves access within existing permissions only.
- [x] Put data/trust boundary before convenience, cost, or latency; prohibit egress outside the authorized boundary and require approval for new installation, connection, authentication, or widened data access.
- [x] Treat discovered metadata and provider output as untrusted input, not executable policy.
- [x] State named-provider exception: retain a provider name only for an explicitly selected method, committed repository dependency, or required security/runtime boundary.

**Verification:**
- [x] `rg -n "Project OS owns|active executor|native|configured|runtime discovery|least privilege|smoke|fallback|source-first|permission" docs/operating_system/tooling/runtime-tool-resolution.md`
- Expected: one canonical policy defines ownership and resolution without enumerating providers or capabilities.

**Exit Criteria:**
- Canonical runtime policy defines ownership, selection, security, evidence, fallback, and stop behavior without a registry or fixed capability enum.

### Task 2: Remove provider routing from canonical guidance

**Purpose:**
- Make existing tooling, governance, rules, and skills request capabilities instead of assuming named providers.

**Task Function:**
- Edit canonical docs, rules, and skills.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: multiple canonical surfaces must preserve distinct security, evidence, and generated boundaries.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: repository contract checks and provider-reference assertions cover cross-file consistency.

**Specification Coverage:**
- Direct approved scope: generic policy surfaces request capabilities and evidence without hard-coding optional providers.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Modify: `docs/operating_system/tooling/code-intelligence-tools.md`
- Modify: `docs/operating_system/tooling/frontend-backend-integration-tools.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Generate: `AGENTS.md` through `scripts/sync_agent_adapters.py`; never edit it directly
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/governance/precedence.md`
- Modify: `docs/operating_system/rules/frontend-ui-rule.md`
- Modify: `docs/operating_system/rules/frontend-backend-integration-rule.md`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md`
- Modify: `.agents/skills/skill-full-stack-integration/SKILL.md`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `.agents/skills/skill-systematic-debugging/SKILL.md`
- Modify: `.agents/skills/skill-refactoring-assessment/SKILL.md`
- Modify: `.agents/skills/skill-code-standards/SKILL.md`
- Modify: `.agents/skills/skill-plan-document-reviewer/SKILL.md`
- Modify: `.agents/skills/skill-wayfinding/SKILL.md`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md`
- Modify: `docs/operating_system/prompt_templates/design-spec-prompt.md`

**Dependencies:**
- Task 1 complete.
- Run a canonical provider-reference inventory before editing; freeze active generic routing files in this task's target list.

**Authority:**
- Preserve explicit `impeccable` selection, committed Playwright Test or equivalent repository test suites, Codex MCP ownership, and DeepAgents handoff rules.
- Preserve concrete names where they describe a selected method, committed dependency, or security boundary.
- Stop for: replacing direct backend proof with browser/provider output, weakening accessibility evidence, or changing skill IDs/frontmatter contracts beyond required read cleanup.

**Steps:**
- [x] Reduce `code-intelligence-tools.md` to code-intelligence capability and evidence guidance; link to `runtime-tool-resolution.md`; keep native source inspection and source/test authority.
- [x] Replace provider-specific routing rows in frontend/backend tooling with frontend/backend capability triggers and evidence needs; link runtime selection to the resolver without duplicating its algorithm.
- [x] Replace provider catalog paragraphs in root template and governance with a short capability-resolution rule and canonical policy reference; never edit generated `AGENTS.md` directly.
- [x] Replace named browser, design, and external-documentation defaults in frontend rules with capability requirements; retain explicit method and repository-owned test exceptions.
- [x] Remove mandatory `required_reads` for `code-intelligence-tools.md` from brainstorming, spec drafting, writing plans, full-stack integration, plan review, and wayfinding; use conditional reads when task scope requires tooling policy.
- [x] Update planning, execution, debugging, refactoring, code-standards, specification, and full-stack routing to request capability/evidence needs, then resolve them through the runtime policy.
- [x] Update verification language to require fresh evidence by claim, not a specific provider.
- [x] Update `design-spec-prompt.md` to request current-state evidence by capability, not a named provider.

**Verification:**
- [x] `rg -n "Serena|GitNexus|DeepWiki|Context7|browser\.test|impeccable|Playwright Test|code-intelligence-tools" docs/operating_system .agents/skills`
- Expected: remaining provider names have an explicit selected-method, committed-dependency, or security-boundary reason; no lifecycle or generic skill requires a provider by name.

**Exit Criteria:**
- All active generic provider-routing references found by inventory are either converted to capability requests or explicitly preserved under the named-provider exception.

### Task 3: Make shipped guidance truthful

**Purpose:**
- Prevent Starter Kit consumers from receiving setup or references that depend on factory-only runtime state.

**Task Function:**
- Edit Starter Kit publication inputs and adoption guidance.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: publication boundary and shipped-reference correctness are material risks.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: manifest and Starter Kit validators provide deterministic proof.

**Specification Coverage:**
- Direct approved scope: Starter Kit contains truthful provider-neutral guidance and excludes source-only setup machinery.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md`
- Inspect: `scripts/get_gitnexus_freshness.ps1`
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `docs/adoption_guide.md`
- Modify: `README.md`
- Verify: `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md`
- Verify: `tests/test_deploy_agent_runtime.py` and its active freshness-helper consumer

**Dependencies:**
- Task 2 complete.

**Authority:**
- Keep Starter Kit consume-only and omit source-only setup machinery instead of shipping an unexecutable recipe.
- Stop for: adding factory scripts, credentials, provider inventories, or generated runtime state to the Starter Kit.

**Steps:**
- [x] Add `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md` to `omitPaths`; keep Context7-specific setup out of generic Starter Kit output rather than rewriting it into a second policy.
- [x] Remove generic adoption guidance that assumes Serena, Semble, AST-Grep, GitNexus, or another named provider; point consumers to source-first work and conditional runtime resolution.
- [x] Update `README.md` to remove its direct link to omitted Context7 setup and point to provider-neutral runtime-resolution guidance.
- [x] Remove generic policy references to `scripts/get_gitnexus_freshness.ps1`; retain the script and its deployment-runtime tests because they have an active source-only consumer.
- [x] Verify new `runtime-tool-resolution.md` ships through existing `docs/operating_system` copy behavior without adding a second copy path.

**Verification:**
- [x] `py -3 scripts/validate_repo_config.py`
- [x] `rg -n "Context7 MCP Setup|get_gitnexus_freshness|Serena|GitNexus|DeepWiki|Context7" docs/adoption_guide.md repo_config/starter-kit-manifest.json docs/operating_system -g '*.md' -g '*.json'`
- [x] Assert `docs/operating_system/procedures/frontend-backend-integration-mcp-setup.md` is absent from built Starter Kit output and `scripts/get_gitnexus_freshness.ps1` remains available only to its active source-only consumer.
- Expected: shipped policy has no unavailable setup dependency; Context7 setup is omitted, while active deployment freshness support remains intact.

**Exit Criteria:**
- Starter Kit manifest explicitly omits provider-specific setup, adoption and README guidance are truthful, and active source-only deployment support is not deleted as dead code.

### Task 4: Add contract coverage and regenerate outputs

**Purpose:**
- Detect provider coupling, ownership drift, invalid required reads, and Starter Kit leakage.

**Task Function:**
- Add focused contract assertions and run canonical generators.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded test and generation work follows established repository patterns.

**Validator Profile:**
- Controller-selected: `normal`
- Selection basis: generated drift and Starter Kit validators are direct evidence.

**Specification Coverage:**
- Direct approved scope: structural contract proof, generated projections, root `AGENTS.md`, and Starter Kit output enforce the runtime-resolution boundary.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Create: `tests/test_runtime_tool_resolution_contract.py`
- Modify: `tests/test_starter_kit_generation.py` only if current fixtures need the new omit rule
- Generate: `generated_agents/`
- Generate: `generated_exports/project-OS-starter-kit/`
- Generate: `AGENTS.md`
- Verify: `scripts/sync_agent_adapters.py`, `scripts/validate_repo_contracts.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`

**Dependencies:**
- Tasks 1 through 3 complete.

**Steps:**
- [x] Add focused structural assertions for one canonical runtime-resolution owner, Project OS versus executor ownership, evidence authority, native/configured-first ordering, conditional discovery, no fixed provider registry, and no evidence downgrade when fallback is used.
- [x] Add assertions that mandatory `required_reads` do not force `code-intelligence-tools.md` for generic planning or review skills.
- [x] Add assertions for data/trust-boundary language, approval before widened access, preserved DeepAgents `--no-mcp`, `codex.mcp.handoff.v1`, explicit design-method exceptions, repository-owned test-framework exceptions, and manifest omission of Context7 setup.
- [x] Keep vendor-name scans as one-time migration evidence only; do not encode a durable provider blacklist in `tests/test_runtime_tool_resolution_contract.py`.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Confirm sync updates `AGENTS.md` from `docs/operating_system/templates/agents/root-AGENTS.template.md`.
- [x] Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Run `py -3 scripts/build_starter_kit.py`.
- [x] Run `py -3 scripts/validate_starter_kit.py`.
- [x] Inspect generated and Starter Kit diffs; reject manual generated edits, provider inventories, credentials, runtime state, or omitted canonical policy.

**Verification:**
- [x] `py -3 -m pytest tests/test_runtime_tool_resolution_contract.py tests/test_starter_kit_generation.py -q`
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py -3 scripts/validate_starter_kit.py`
- Expected: contract tests, generated adapters, and Starter Kit output agree with canonical sources.

**Exit Criteria:**
- Structural tests pass, generated `AGENTS.md` and adapter projections match canonical sources, and Starter Kit output contains required policy without omitted or forbidden runtime assets.

### Task 5: Run final acceptance proof

**Purpose:**
- Prove target ownership and runtime-resolution boundaries at one fresh repository state.

**Task Function:**
- Perform final evidence collection and repository reconciliation.

**Template Profile:**
- Controller-selected: `high`
- Selection basis: final acceptance spans policy, generated surfaces, publication boundaries, and fresh evidence.

**Validator Profile:**
- Controller-selected: `xhigh`
- Selection basis: independent critical review must challenge cross-cutting ownership and fallback claims.

**Specification Coverage:**
- All runtime-resolution outcomes, including security boundary, evidence non-downgrade, provider-neutral generic routing, generated output, and truthful Starter Kit shipping.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all plan targets
- Inspect: `git status --short`, `git rev-parse HEAD`, `git diff --check`, and complete diff
- Verify: `scripts/validate_template_required_sections.py`, `scripts/validate_planning_lifecycle.py`, `scripts/validate_repo_contracts.py`, focused tests, and Starter Kit validators

**Dependencies:**
- Tasks 1 through 4 complete.
- Lifecycle clarification plan may execute before, after, or independently; neither plan partially implements the other.

**Authority:**
- Stop for: failed proof, generated drift, changed files outside approved targets, provider-specific generic routing, broken shipped references, or unresolved source/evidence ownership.

**Steps:**
- [x] Capture fresh `git status --short` and `git rev-parse HEAD`; preserve unrelated changes.
- [x] Run `py -3 scripts/validate_template_required_sections.py --require-template-selection`.
- [x] Run `py -3 scripts/validate_planning_lifecycle.py`.
- [x] Run `py -3 scripts/validate_repo_contracts.py`.
- [x] Run `py -3 -m pytest tests/test_runtime_tool_resolution_contract.py tests/test_validate_template_required_sections.py tests/test_validate_planning_lifecycle.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q`.
- [x] Run `git diff --check`.
- [x] Search generic policy for named-provider routing with `rg -n "must use|default tool|primary tool|Context7|Serena|GitNexus|DeepWiki|browser\.test" README.md docs/operating_system .agents/skills docs/adoption_guide.md -g '*.md'` and classify every remaining match against the named-provider exception.
- [x] Confirm `AGENTS.md` contains capability-resolution guidance and no generic provider default.
- [x] Record `verified`, `incomplete`, or `blocked` from fresh output; do not mark plan completed from checkboxes alone.
- [x] If review causes any canonical edit, return to the affected earlier task, rerun Task 4 generation and validation, then rerun the complete Task 5 proof set.

**Exit Criteria:**
- Project OS states capability and evidence requirements once.
- Active executor resolves available tools at runtime within existing permissions.
- No generic lifecycle, governance, skill, or Starter Kit rule hard-codes optional providers.
- Source, tests, contracts, and runtime systems remain authoritative.
- Generated surfaces and Starter Kit pass validation with no unrecorded scope deviation.

**Exit Criteria:**
- Fresh evidence supports a `verified` result, or records `incomplete`/`blocked` with the exact failed proof and no stale generated output.

## Completion Criteria

1. `runtime-tool-resolution.md` is the sole canonical owner of capability and evidence resolution policy.
2. Existing tooling and skills request capabilities conditionally rather than routing by provider name.
3. Named providers remain only where explicit method, committed dependency, or security/runtime boundary requires them.
4. DeepAgents `--no-mcp`, `codex.mcp.handoff.v1`, direct backend proof, accessibility evidence, and repository-owned test frameworks remain intact.
5. Starter Kit contains truthful guidance and no unavailable setup or factory-only runtime dependency.
6. Focused contract tests, generated checks, repository validators, Starter Kit validation, and `git diff --check` pass.
7. Final verification performed under `skill-verification-before-completion` is recorded as `verified` before optional branch finishing.

## Verification

- `py -3 scripts/validate_template_required_sections.py --require-template-selection`
- `py -3 scripts/validate_planning_lifecycle.py`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 -m pytest tests/test_runtime_tool_resolution_contract.py tests/test_validate_template_required_sections.py tests/test_validate_planning_lifecycle.py tests/test_starter_kit_generation.py tests/test_validate_repo_contracts.py tests/test_sync_agent_adapters.py -q`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_starter_kit.py`
- `git diff --check`
