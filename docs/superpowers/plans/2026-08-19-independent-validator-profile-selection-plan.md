---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: independent-validator-profile-selection
targets:
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - docs/operating_system/templates/implementation-plan-template.md
  - agents/xhigh.toml
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-deepagents-executing-plans/SKILL.md
  - .agents/skills/skill-subagent-driven-development/SKILL.md
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/runtime-adapter-procedure.md
  - tests/test_native_personal_local_workflow.py
  - AGENTS.md
  - generated_agents/codex/AGENTS.md
  - generated_agents/claude/CLAUDE.md
  - generated_agents/antigravity/GEMINI.md
  - generated_agents/codex/agents/xhigh.toml
  - generated_agents/codex/skills/skill-writing-plans/SKILL.md
  - generated_agents/claude/skills/skill-writing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-writing-plans/SKILL.md
  - generated_agents/codex/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/claude/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/antigravity/skills/skill-deepagents-executing-plans/SKILL.md
  - generated_agents/codex/skills/skill-subagent-driven-development/SKILL.md
  - generated_agents/claude/skills/skill-subagent-driven-development/SKILL.md
  - generated_agents/antigravity/skills/skill-subagent-driven-development/SKILL.md
---

# Independent Validator Profile Selection Plan

## Goal

Separate profile capability ordering from validator selection throughout Starter governance. Preserve `xhigh > high > normal > low` as capability metadata while selecting executor and validator profiles independently from their bounded task contracts, including permission for a validator to use a lower, equal, or higher profile than its executor.

## Decisions

- Capability order remains `xhigh > high > normal > low`; this order describes relative profile capacity only.
- Executor and validator profiles are selected independently using the lowest profile that can reliably complete each bounded contract.
- Validation method and evidence matter more than validator rank. A lower-profile validator is valid when its validation contract is bounded and within that profile's capability.
- `xhigh` remains available for execution. No policy reserves it for validation or prohibits it when separate validation exists.
- `docs/operating_system/templates/agents/root-AGENTS.template.md` remains canonical for root guidance; `AGENTS.md` is regenerated, never edited directly.
- `agents/xhigh.toml` remains canonical for the tracked `xhigh` role description; generated role outputs are regenerated through the existing adapter sync.
- Root guidance and `agents/xhigh.toml` keep audience-specific profile summaries under their existing owners; this change aligns meaning without introducing a new shared textual source.
- No compatibility shim or second policy path is added. All affected guidance moves to one invariant: validator capability must meet the validation task, not exceed executor capability.

## Implementation Outcomes

### Canonical policy and plan contract

Root agent guidance, implementation-plan template, and `xhigh` role definition state the independent-selection rule without weakening capability ordering. Plan task metadata records an optional controller-selected validator and validation basis, without a fixed rank mapping or an `xhigh` executor ban.

### Symmetric execution guidance

Planning and execution skills plus runtime and worktree procedures use the same profile-selection model. Fixed `low` to `normal`, `normal` to `high`, and `high` to `xhigh` reviewer mappings disappear. `Profile Pairing` becomes `Validator Profile Selection` where applicable.

### Regression proof and generated alignment

Focused tests prove capability order remains documented, independent executor-validator selection is documented, lower-profile validation is allowed, and stale rank-based wording is absent from governed surfaces. Adapter regeneration updates generated outputs, and focused plus full validation passes without unrelated changes.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Executor: `codex`
- Required skills: `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Parallel ownership: `none`; policy wording, consumers, generated outputs, and tests overlap semantically.
- Sequential fallback: update regression expectations and canonical sources, align direct consumers, regenerate adapters, then run focused and broad verification.

## Task Ledger

| Task | Description | Status | Depends On |
|---|---|---|---|
| 1 | Define independent-selection contract and regression expectations | completed | none |
| 2 | Align skills, runtime guidance, and procedures | completed | Task 1 |
| 3 | Regenerate adapters and verify repository consistency | completed | Tasks 1-2 |

## Task Breakdown

### Task 1: Define independent-selection contract and regression expectations

**Status:** pending

**Profile:**
- Executor: `normal`
- Selection basis: bounded governance, template, role-description, and Python-test edits with exact wording requirements.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently review SSOT ownership, invariant precision, and regression coverage under policy active when execution begins.

**Specification Coverage:**
- Preserve profile capability ordering without using it as validator assignment rule.
- Permit lower, equal, or higher validator profiles when validation contract fits.
- Remove `xhigh` executor prohibition and validation-only implication.
- Simplify implementation-plan validator metadata to controller selection plus validation basis.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `tests/test_native_personal_local_workflow.py:test_profile_hierarchy_and_validator_rule_are_documented`; rename it to describe capability order and independent validator selection.
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md` section `## Subagent Routing`.
- Modify: `docs/operating_system/templates/implementation-plan-template.md` profile guidance and `**Validator Profile (optional):**` example.
- Modify: `agents/xhigh.toml` role description only.
- Preserve: `AGENTS.md` and `generated_agents/codex/agents/xhigh.toml` until Task 3 regeneration.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: edit named canonical sources and focused test; rename only named test function; run focused pytest.
- Stop for: conflict with more specific scoped `AGENTS.md`, discovery that another canonical policy owner controls these statements, or required schema change outside named targets.

**Steps:**
1. Change focused test first so current rank-based wording fails. Expand its positive checked-file set to the root template, implementation-plan template, all three modified skills, runtime surfaces, and both modified procedures; require capability ordering, independent executor-validator selection, and explicit allowance for lower-profile validators in every applicable surface.
2. Replace root template rank coupling with one canonical rule: select executor and validator independently from their respective bounded contracts; validator may be lower, equal, or higher when reliable for validation scope.
3. Change `xhigh` profile description from validation of `high` work to neutral demanding execution or validation language.
4. Update implementation-plan template metadata to use this exact block:
   ```md
   - Controller-selected: `<none>`
   - Selection basis: <validation>
   - Select independently from the executor profile; no profile-rank relationship is required.
   ```
   State that `<none>` is the literal default when no validator is assigned; otherwise replace it with `low`, `normal`, `high`, or `xhigh`.
5. Remove template language requiring higher validator or banning `xhigh` execution while retaining capability order and lowest-reliable-profile selection.
6. Run focused test and confirm failures, if any, point only to consumers intentionally deferred to Task 2 or generated outputs deferred to Task 3.

**Acceptance Criteria:**
- Canonical guidance distinguishes capability order from task fitness.
- Plan template supports no validator, lower-profile validator, peer validator, higher-profile validator, and `xhigh` executor without special cases.
- `agents/xhigh.toml` no longer implies `xhigh` exists to validate `high` work.
- Focused test positively asserts independent selection and lower-profile validator allowance across all Task 2 consumers, not only absence of old wording.
- No generated file is hand-edited.

### Task 2: Align skills, runtime guidance, and procedures

**Status:** pending

**Profile:**
- Executor: `normal`
- Selection basis: bounded cross-document contract alignment with no runtime code changes.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently check semantic symmetry across planning, Codex execution, DeepAgents execution, and runtime procedures.

**Specification Coverage:**
- Replace fixed reviewer-executor mappings in all named direct consumers.
- Keep task function separate from profile selection.
- Preserve lowest-capable-profile and scope-escalation rules.
- Rename misleading pairing terminology where fixed tier coupling is implied.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/skill-writing-plans/SKILL.md` profile-selection and validator metadata guidance.
- Modify: `.agents/skills/skill-deepagents-executing-plans/SKILL.md` section `## Profile Selection` and remove fixed mappings plus `xhigh` executor restriction.
- Modify: `.agents/skills/skill-subagent-driven-development/SKILL.md`; rename `## Profile Pairing` to `## Validator Profile Selection` and replace pairing rules.
- Modify: `docs/operating_system/runtime/runtime-surfaces.md` profile capability guidance.
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md` executor-validator selection guidance.
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md` executor-validator selection guidance.

**Dependencies:**
- Task 1 establishes exact invariant and test vocabulary.

**Authority:**
- Preauthorized local actions: edit named skills and governance documents; preserve unrelated workflow instructions and examples.
- Stop for: consumer wording that encodes distinct safety requirement not covered by validator task fitness, or discovery of additional generated files presented as canonical inputs.

**Steps:**
1. Update plan-writing guidance to record validator profile and selection basis independently from executor profile.
2. Replace DeepAgents fixed tier mapping with independent profile selection for implementation and validation contracts.
3. Replace subagent-driven development pairing language with validator selection language, allowing lower, equal, or higher profiles and `xhigh` execution.
4. Align runtime-surface and both procedure documents to same invariant and terminology.
5. Search governed source files for stale phrases including `validator profile must rank above executor profile`, fixed tier mappings, and the `xhigh` executor prohibition.
6. Run focused workflow test and correct only policy-scope failures.

**Acceptance Criteria:**
- All named consumers state one symmetric independent-selection model.
- No named consumer retains fixed validator mapping or rank requirement.
- No named consumer prohibits `xhigh` execution solely because separate validation exists.
- Profile escalation still occurs when either bounded contract exceeds selected profile.
- Focused workflow test passes before generated synchronization.

### Task 3: Regenerate adapters and verify repository consistency

**Status:** pending

**Profile:**
- Executor: `normal`
- Selection basis: deterministic generation, repository-wide search, and automated verification.

**Validator Profile (optional):**
- Controller-selected: `high`
- Selection basis: independently validate generated-source provenance, negative stale-policy search, and final test evidence.

**Specification Coverage:**
- Regenerate all adapter outputs from canonical sources.
- Prove no stale rank-coupled policy remains on governed surfaces.
- Prove plan lifecycle, generated headers, sync checks, focused tests, and full suite remain valid.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Generate: `AGENTS.md` from `docs/operating_system/templates/agents/root-AGENTS.template.md`.
- Generate: `generated_agents/codex/AGENTS.md`, `generated_agents/claude/CLAUDE.md`, and `generated_agents/antigravity/GEMINI.md` from synchronized `AGENTS.md`.
- Generate: `generated_agents/codex/agents/xhigh.toml` from `agents/xhigh.toml`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-writing-plans/SKILL.md` from `.agents/skills/skill-writing-plans/SKILL.md`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-deepagents-executing-plans/SKILL.md` from `.agents/skills/skill-deepagents-executing-plans/SKILL.md`.
- Generate: `generated_agents/{codex,claude,antigravity}/skills/skill-subagent-driven-development/SKILL.md` from `.agents/skills/skill-subagent-driven-development/SKILL.md`.
- Verify: all canonical and generated files named in plan frontmatter.

**Dependencies:**
- Tasks 1-2 complete.

**Authority:**
- Preauthorized local actions: run adapter synchronization, focused validators, repository search, and full pytest suite; accept deterministic generated changes from named canonical inputs.
- Stop for: generated drift outside deterministic consequences, unrelated test failure requiring source changes, or adapter sync modifying private or user-local state.

**Steps:**
1. Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
2. Inspect Git diff and confirm generated changes match the explicitly named root-guidance, role, and skill outputs.
3. Run `py -3 scripts/sync_agent_adapters.py --check`.
4. Run repository search across governed Markdown, TOML, and generated agent surfaces for stale rank-coupled wording and fixed mapping variants.
5. Run `py -3 -m pytest -q tests/test_native_personal_local_workflow.py tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py`.
6. Run `py -3 scripts/validate_generated_header_format.py` and `py -3 scripts/validate_planning_lifecycle.py`.
7. Run `py -3 -m pytest -q`.
8. Reconcile plan ledger, verification evidence, deviations, and residual risks before completion claim.

**Acceptance Criteria:**
- Adapter check reports no drift.
- Generated root guidance and `xhigh` role output match canonical sources.
- Search finds no fixed rank requirement, fixed validator mapping, validation-only `xhigh` description, or `xhigh` executor ban in affected governed surfaces.
- Focused tests and validators pass with fresh output.
- Full pytest suite passes, or unrelated pre-existing failures are recorded without changing unrelated code.
- Git diff contains only plan-approved policy, test, and explicitly named generated changes.

## Verification

- [x] `py -3 scripts/sync_agent_adapters.py --check`
- [x] Stale-policy search returns no affected governed matches for higher-rank validator requirements, fixed tier mappings, or `xhigh` executor bans.
- [x] `py -3 -m pytest -q tests/test_native_personal_local_workflow.py tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py`
- [x] `py -3 scripts/validate_generated_header_format.py`
- [x] `py -3 scripts/validate_planning_lifecycle.py`
- [x] `py -3 -m pytest -q`
- [x] Final Git diff matches plan targets plus deterministic generated outputs only.

## Completion Criteria

1. Capability order remains documented as `xhigh > high > normal > low` without implying validator assignment order.
2. Executor and validator profiles are independently selected from their bounded task contracts across all named governance and skill surfaces.
3. Lower, equal, and higher validator profiles are permitted when reliable for validation scope.
4. `xhigh` can serve as executor or validator based on task fitness, with no validation-only wording or separate-validator prohibition.
5. Implementation-plan template records optional validator selection and basis without fixed pairing.
6. Focused regression coverage enforces new invariant and rejects stale rank coupling.
7. Generated surfaces are synchronized from canonical sources and pass drift checks.
8. Fresh focused validators and full test suite provide completion evidence.

## Deviations And Residual Risks

- Local deployment required `--force` because existing user runtime files lacked generated headers; deployment used `--backup`, then passed `--check --force`.
