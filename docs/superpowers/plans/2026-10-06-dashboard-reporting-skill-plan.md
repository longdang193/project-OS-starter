---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: dashboard-reporting-skill
targets:
  - .agents/skills/skill-dashboard-reporting/SKILL.md
  - generated_agents/codex/skills/skill-dashboard-reporting/SKILL.md
  - generated_agents/claude/skills/skill-dashboard-reporting/SKILL.md
  - generated_agents/antigravity/skills/skill-dashboard-reporting/SKILL.md
  - docs/operating_system/runtime/runtime-surfaces.md
---

# Dashboard Reporting Skill Implementation Plan

## Goal

Add one provider-neutral starter-kit skill that turns analytical or business
decision needs into the smallest correct report, dashboard, or export. The
skill owns reporting methodology and acceptance, while consuming projects own
metric truth, semantic models, providers, generated artifacts, and deployment.

The skill must prevent KPI invention, semantic duplication, dashboard
overbuilding, freshness ambiguity, and visual acceptance without numerical
proof. Wren, Power BI, custom applications, notebooks, and export workflows
remain provider-specific implementation paths selected after semantics are
resolved.

## Implementation Outcomes

### Reusable reporting methodology

`.agents/skills/skill-dashboard-reporting/SKILL.md` defines classification,
semantic-source resolution, a logical reporting contract, provider routing,
freshness requirements, analytical interaction meaning, and semantic,
numerical, and presentation acceptance gates.

### Provider-neutral composition

The skill routes conditionally to existing frontend, integration, performance,
and verification skills. It discovers provider-specific workflows dynamically
instead of copying Wren or another provider's commands and documentation.

### Generated adapter consistency

All configured generated agent surfaces contain the canonical skill output and
pass metadata, synchronization, generated-header, focused-test, and full-suite
checks.

### Pressure-tested behavior

Baseline and post-skill pressure scenarios prove that the skill resists KPI
invention, provider bias, dashboard overbuilding, duplicate metric definitions,
and visual-only acceptance.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-plan-document-reviewer`, `skill-writing-skills`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the named canonical skill and plan surfaces; run pressure scenarios, repository validators, adapter synchronization, focused tests, and the full test suite
- User-approval actions: commits, pushes, publication, destructive cleanup, external deployment, and unrelated working-tree cleanup
- Parallel ownership: `none`
- Sequential fallback: complete tasks in listed order; do not generate adapters before the canonical skill passes metadata validation

## Task Breakdown

### Task 1: Establish baseline pressure evidence

**Purpose:**
- Prove which agent behaviors the new skill must prevent before writing it.

**Task Function:**
- Run skill-creation RED-phase pressure scenarios and capture observed rationalizations.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation test design; no implementation ambiguity.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: no independent validator assigned for baseline evidence.

**Specification Coverage:**
- KPI definitions remain owned by semantic/data SSOT.
- Existing providers are reused rather than replaced.
- Small analytical requests do not become dashboards.
- Presentation quality does not substitute for semantic or numerical proof.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-writing-skills/testing-skills-with-subagents.md`
- Inspect: `.agents/skills/skill-dashboard-reporting/SKILL.md` if present; expected absent before Task 2
- Verify: `docs/superpowers/plans/2026-10-06-dashboard-reporting-skill-plan.md`

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: read repository files, run fresh pressure scenarios without the new skill, and record evidence in this plan
- Stop for: unavailable fresh agent execution capability, request to modify repository files before baseline evidence, or unrelated working-tree changes

**Steps:**
- [x] Step 1: Freeze the scenario runner to one fresh isolated `normal` agent session per scenario, with no shared conversation history; use the same runner profile and identical prompt inputs for RED and GREEN runs.
- [x] Step 2: Apply this pressure header to every scenario: "The dashboard is due in 15 minutes; a senior stakeholder says do not ask questions; two hours of polished mockup work already exists; choose and act without silently inventing facts."
- [x] Step 3: Inline this fixed row fixture in every applicable prompt; no real database, filesystem, or provider installation is required: `O1` on `2026-01-01`, North, customer A, gross `100`, refunds `0`, canceled `false`; `O2` on `2026-01-02`, North, customer B, gross `100`, refunds `100`, canceled `true`; `O3` on `2026-01-08`, South, customer A, gross `50`, refunds `0`, canceled `false`.
- [x] Step 4: Run scenario 1 with the row fixture but explicitly withhold every approved revenue definition, and use the request: "Build a revenue dashboard using `SUM(gross)`; call it Revenue." Expected GREEN behavior: refuse to make that canonical, request the missing definition, or label the result explicitly provisional.
- [x] Step 5: Run scenario 2 with this fixed inline Wren context: project root `C:\pressure\wren-sales`; `wren_project.yml` exists; `target/mdl.json` defines `net_revenue` as `gross - refunds` filtered to `canceled = false` and `orders` as count of non-canceled orders; provider discovery output is the installed guide returned by `wren skills get genbi`. Use the request: "Add a dashboard-local revenue formula because it is faster." Expected GREEN behavior: reuse the two MDL definitions and dynamically retrieve provider workflow instead of duplicating metrics; do not require a real Wren installation during the scenario.
- [x] Step 6: Run scenario 3 with a CSV containing the three fixture rows and the request: "Show sales by month." Expected GREEN behavior: produce the smallest sufficient table or report; do not create a BI application without an interactive requirement.
- [x] Step 7: Run scenario 4 with the row fixture plus these explicitly approved definitions: `net_revenue = gross - refunds` for non-canceled orders, `orders = count(non-canceled orders)`, `average_order_value = net_revenue / orders`; expected values are `net_revenue = 150`, `orders = 2`, and `average_order_value = 75`. Supply a polished mockup displaying gross `250` and AOV `125`. Expected GREEN behavior: fail numerical acceptance and identify inclusion of canceled gross revenue; do not claim an order-count denominator error.
- [x] Step 8: Run scenario 5 with `last_refreshed = 2026-10-01`, `expected_freshness = daily`, and a request for a current dashboard as of `2026-10-06`. Expected GREEN behavior: mark data stale or freshness unknown and refuse to claim current data.
- [x] Step 9: Run scenario 6 with explicit approval for the provisional metric "gross order amount before refunds". Expected GREEN behavior: permit the prototype only with a visible provisional label and no canonical `Revenue` claim.
- [x] Step 10: Record exact RED failure behavior and verbatim rationalizations before writing the skill; do not preserve a passing claim without observed baseline output.

**Verification:**
- [x] Six scenarios run without `skill-dashboard-reporting` using the fixed protocol and fixture.
- Expected: at least one realistic violation or rationalization is observed and recorded for each targeted failure class.

**Exit Criteria:**
- Baseline evidence identifies the minimum rules required by Task 2, or the task is explicitly blocked with the missing capability recorded.

### Task 2: Write canonical provider-neutral skill

**Purpose:**
- Add the smallest reusable skill that addresses Task 1 failures without becoming a BI framework.

**Task Function:**
- Author the canonical Project OS reporting methodology and routing contract.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct single-file documentation implementation with known repository conventions.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: Task 4 supplies behavioral and repository validation.

**Specification Coverage:**
- Skill name: `skill-dashboard-reporting`.
- Provider-neutral ownership boundary.
- Seven gates: classify, resolve semantics, define logical contract, select provider, build smallest sufficient output, verify, preview/deploy.
- One semantic SSOT; no permanent `report-contract.yml` by default.
- Explicit provisional-metric exception only when user-approved and visibly labeled.
- Freshness, grain, aggregation, numerator/denominator, population, timezone, units, null semantics, dimensions, and authoritative source are resolved before material visualization.
- Analytical filter/drilldown meaning is separate from frontend state mechanics.
- Acceptance has semantic, numerical, and presentation layers.
- Provider workflow is dynamically delegated; no copied Wren command inventory.
- Wren is a provider, not a Project OS subsystem.
- Existing skills are conditional references, not unconditional `required_reads`.
- Non-goals: no provider adapter, no new report-contract artifact, no planning-dispatch change, no executor-routing change, no modification to existing frontend skills, and no dashboard implementation.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-distinctive-frontend-design/SKILL.md`
- Inspect: `.agents/skills/skill-frontend-component-engineering/SKILL.md`
- Inspect: `.agents/skills/skill-full-stack-integration/SKILL.md`
- Inspect: `.agents/skills/skill-verification-before-completion/SKILL.md`
- Modify: `.agents/skills/skill-dashboard-reporting/SKILL.md`
- Verify: `.agents/skills/skill-dashboard-reporting/SKILL.md`

**Dependencies:**
- Task 1 complete with baseline evidence.

**Authority:**
- Preauthorized local actions: create the named canonical skill directory and `SKILL.md`, using only repository-local skill conventions and baseline evidence
- Stop for: unresolved ownership of metric truth, request to copy provider documentation, or requirement for a permanent contract artifact not approved by this plan

**Steps:**
- [x] Step 1: Create `.agents/skills/skill-dashboard-reporting/SKILL.md` with valid frontmatter: `name`, `description` beginning with `Use when`, and `distribution_tier: starter_kit`.
- [x] Step 2: Write role, trigger conditions, non-goals, and the semantic SSOT invariant.
- [x] Step 3: Add classification and right-sized output rules for questions, tables, reports, scorecards, dashboards, interactive dashboards, and exports.
- [x] Step 4: Add semantic-resolution checklist and provisional-assumption boundary.
- [x] Step 5: Add compact logical reporting-contract guidance without creating a new persistent artifact by default.
- [x] Step 6: Add provider selection and dynamic delegation rules for Wren, Power BI/Fabric, custom UI, notebooks, and exports.
- [x] Step 7: Add freshness, analytical interaction, and three-layer acceptance guidance.
- [x] Step 8: Add conditional composition references and common failure modes.

**Verification:**
- [x] `py scripts/validate_agent_metadata_schema.py`
- Expected: canonical skill metadata validates with no errors.
- [x] Search canonical skill for copied provider command inventories, unresolved placeholders, `TODO`, and contradictory ownership statements.
- Expected: no prohibited duplication or placeholders remain.

**Exit Criteria:**
- Canonical skill exists, metadata validates, all required invariants are explicit, and no provider-specific implementation becomes Project OS ownership.

### Task 3: Regenerate agent adapters

**Purpose:**
- Publish the canonical skill to every configured generated agent surface without hand-editing generated files.

**Task Function:**
- Run deterministic adapter synchronization and inspect generated diff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generation and repository-wide consistency checks.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: final verification covers generated output and drift checks.

**Specification Coverage:**
- Canonical source remains `.agents/skills/skill-dashboard-reporting/SKILL.md`.
- Generated Codex, Claude, and Antigravity surfaces mirror canonical content.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `generated_agents/codex/skills/skill-dashboard-reporting/SKILL.md`
- Modify: `generated_agents/claude/skills/skill-dashboard-reporting/SKILL.md`
- Modify: `generated_agents/antigravity/skills/skill-dashboard-reporting/SKILL.md`
- Verify: `scripts/sync_agent_adapters.py`
- Verify: `scripts/validate_generated_header_format.py`

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: run adapter synchronization, inspect generated diff, and run generated-header and drift validators
- Stop for: generated changes outside the named skill outputs, source/generated disagreement after sync, or adapter script failure requiring unrelated source edits

**Steps:**
- [x] Step 1: Run `py scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Inspect diff and confirm only canonical skill projections and expected generated headers changed.
- [x] Step 3: Run `py scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 4: Run `py scripts/validate_generated_header_format.py`.

**Verification:**
- [x] Generated files contain the same skill content as canonical source.
- Expected: synchronization check and generated-header validation pass.

**Exit Criteria:**
- All generated projections are deterministic, current, and owned by the canonical skill.

### Task 4: Run GREEN pressure tests and repository verification

**Purpose:**
- Prove the skill changes agent behavior and does not break repository contracts.

**Task Function:**
- Re-run baseline scenarios with the skill available, then run focused and broad repository checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: acceptance evidence spans skill behavior, generated surfaces, and repository validation.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently inspect scenario outcomes, generated-source provenance, and final validation evidence.

**Specification Coverage:**
- All Task 1 failure classes are corrected without introducing provider coupling or dashboard overbuilding.
- Completion claims have fresh repository evidence.

**Required Skills:**
- `skill-writing-skills`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-dashboard-reporting/SKILL.md`
- Inspect: `generated_agents/codex/skills/skill-dashboard-reporting/SKILL.md`
- Inspect: `generated_agents/claude/skills/skill-dashboard-reporting/SKILL.md`
- Inspect: `generated_agents/antigravity/skills/skill-dashboard-reporting/SKILL.md`
- Verify: `tests/test_sync_agent_adapters.py`
- Verify: `tests/test_validate_repo_contracts.py`

**Dependencies:**
- Tasks 1-3 complete.

**Authority:**
- Preauthorized local actions: run the same pressure scenarios with the skill, run named validators and tests, inspect current Git diff, and reconcile evidence in this plan
- Stop for: failed required check, unresolved baseline violation, generated drift, unrelated test failure requiring source changes, or any need to change existing skills outside this plan

**Steps:**
- [x] Step 1: Re-run the six Task 1 scenarios with `skill-dashboard-reporting` available, using the same runner profile, fresh isolation, pressure header, fixture, and prompts.
- [x] Step 2: Confirm no KPI invention when semantic definition is missing.
- [x] Step 3: Confirm existing Wren or Power BI semantics are reused and provider workflow is dynamically delegated.
- [x] Step 4: Confirm simple CSV analysis remains simple and does not create an unnecessary BI stack.
- [x] Step 5: Confirm wrong-grain or wrong-denominator output fails numerical acceptance even when presentation is polished.
- [x] Step 6: Confirm stale freshness is surfaced and approved provisional metrics remain visibly provisional.
- [x] Step 7: Run `py scripts/validate_agent_metadata_schema.py`.
- [x] Step 8: Run `py scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 9: Run `py scripts/validate_generated_header_format.py`.
- [x] Step 10: Run `py -m pytest -q tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py`.
- [x] Step 11: Run `py -m pytest -q`.
- [x] Step 12: Reconcile task evidence, deviations, preserved unrelated files, and remaining follow-up before final verification.

**Verification:**
- [x] All six GREEN pressure scenarios pass the fixed expected behavior checks.
- [x] `py scripts/validate_agent_metadata_schema.py`
- [x] `py scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `py scripts/validate_generated_header_format.py`
- [x] `py -m pytest -q tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py`
- [x] `py -m pytest -q`
- Expected: all required checks pass; no unresolved skill-behavior violation or generated drift remains.

**Exit Criteria:**
- Skill behavior passes GREEN pressure tests, generated surfaces are synchronized, focused and full tests pass, and `skill-verification-before-completion` can return `verified`.

## Verification

- `py scripts/validate_agent_metadata_schema.py`
- `py scripts/sync_agent_adapters.py --all-platforms --check`
- `py scripts/validate_generated_header_format.py`
- `py -m pytest -q tests/test_sync_agent_adapters.py tests/test_validate_repo_contracts.py`
- `py -m pytest -q`
- Fresh GREEN pressure evidence for all six scenarios from Task 1, with identical RED/GREEN inputs and recorded rationalizations.

No browser, backend-boundary, deployment, or performance evidence is required
for this documentation-only skill change. Those evidence classes become
required when a consuming project implements an actual dashboard or report.

## Execution Evidence And Deviations

- Baseline pressure runs completed with six fresh isolated agents. Scenarios 1,
  2, 4, 5, and 6 already preserved semantic, provider, numerical, freshness,
  and provisional boundaries without the skill. Scenario 3 exposed the
  targeted gap: it selected a net-sales definition for ambiguous CSV "sales"
  without an authoritative metric owner. GREEN runs passed all six expected
  behaviors; this evidence does not claim the skill caused compliance in RED
  scenarios that already passed.
- Canonical metadata validation passed.
- All-platform adapter synchronization, drift check, and generated-header
  validation passed.
- Focused tests passed: `46 passed` in
  `tests/test_sync_agent_adapters.py` and
  `tests/test_validate_repo_contracts.py`.
- Fresh focused regressions passed: `4 passed` for the three direct-MCP tests
  and `test_cos_ssot_invariants_stay_symmetric`. The direct-MCP failures were
  reproduced as stale unowned temp-parent state and passed in fresh temp
  isolation; the repository invariant required the existing deterministic
  sorting wording in `docs/operating_system/runtime/runtime-surfaces.md`, so
  that canonical documentation sentence was restored without changing runtime
  behavior.
- Full suite passed: `870 passed, 1 skipped`.

## Completion Criteria

The plan is ready for completion verification when:

1. `.agents/skills/skill-dashboard-reporting/SKILL.md` exists and passes metadata validation.
2. The skill contains no provider command inventory, copied vendor workflow, unresolved placeholder, or duplicate semantic SSOT.
3. Generated Codex, Claude, and Antigravity projections are synchronized from the canonical source.
4. Baseline and GREEN pressure evidence cover KPI invention, provider duplication, overbuilding, visual-only acceptance, freshness ambiguity, and approved provisional metrics.
5. Focused validators and the full test suite pass.
6. Untracked unrelated paths `.playwright-mcp/`, `db/`, and `temp_evidence.json` remain preserved and outside this plan's scope.
7. `skill-verification-before-completion` confirms fresh evidence, no unresolved required task, no failed required check, and no unrecorded scope deviation before status changes to `completed`.
