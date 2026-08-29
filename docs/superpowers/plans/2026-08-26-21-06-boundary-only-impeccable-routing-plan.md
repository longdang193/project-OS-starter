---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: boundary-only-impeccable-routing
targets:
  - docs/operating_system/rules/frontend-ui-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - .agents/skills/skill-using-superpowers/SKILL.md
  - .agents/skills/skill-brainstorming/SKILL.md
  - .agents/skills/skill-distinctive-frontend-design/SKILL.md
  - .agents/skills/skill-spec-drafting/SKILL.md
  - .agents/skills/skill-writing-plans/SKILL.md
  - .agents/skills/skill-code-standards/SKILL.md
  - .agents/skills/skill-frontend-component-engineering/SKILL.md
  - docs/operating_system/tooling/frontend-backend-integration-tools.md
  - generated_agents
  - generated_exports/project-OS-starter-kit
---

# Boundary-Only Impeccable Routing

## Goal

Add safe Project OS routing for an explicitly selected Impeccable skill without making Impeccable a starter-owned dependency, creating a second product/design authority, or removing portable frontend fallback skills.

## Implementation Outcomes

### Explicit design-skill precedence

Canonical frontend guidance defines explicit Impeccable selection mechanically: direct user request or an approved specification, plan, or bounded task contract names `impeccable`. Installation, discovery, availability, or generic applicability does not select it. When it is selected, it satisfies its overlapping visual/UX-design scope for that task; otherwise existing frontend skill eligibility and routing behavior remains unchanged.

### Preserved Project OS authority

Canonical and generated agent surfaces preserve Project OS ownership of product intent, approved behavior, design-system sources, component/state ownership, integration contracts, accessibility requirements, measured performance claims, tests, and final verification. Impeccable `shape`, reviews, audits, live output, generated artifacts, persistent product/design/tool state, and hooks receive explicit evidence and authority boundaries.

### Reconciled generated starter

All generated agent surfaces and the starter-kit export match canonical sources, retain the existing metadata validator contract, and contain no stale routing that forces overlapping frontend design skills together.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edits to listed canonical sources, declared repository reads, dirty-path classification, regeneration, validation commands, stale-reference searches, and `git diff --check`
- User-approval actions: push, merge, publication, external writes, destructive recovery, discard, and cleanup outside declared generated outputs
- Parallel ownership: `none`
- Sequential fallback: complete inventory, canonical edits, regeneration, then final validation in order

## Task Breakdown

### Task 1: Inventory canonical routing

**Purpose:**
- Establish exact frontend skill-routing references and lock boundary-only scope before edits.

**Task Function:**
- Repository routing audit

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded source inspection with no delegated implementation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: task-local searches provide sufficient inventory proof.

**Specification Coverage:**
- Preserve existing fallback skills and current external/user-local Impeccable installation.
- Prevent duplicate activation when Impeccable is explicitly selected.
- Exclude vendoring, deletion, version pinning, hooks, metadata exceptions, and command-catalog duplication.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-using-superpowers/SKILL.md:12-103`
- Inspect: `.agents/skills/skill-brainstorming/SKILL.md:22`
- Inspect: `.agents/skills/skill-distinctive-frontend-design/SKILL.md:25-26`
- Inspect: `.agents/skills/skill-spec-drafting/SKILL.md:114-118`
- Inspect: `.agents/skills/skill-writing-plans/SKILL.md:48-52`
- Inspect: `.agents/skills/skill-code-standards/SKILL.md:173-177`
- Inspect: `.agents/skills/skill-frontend-component-engineering/SKILL.md:12`
- Inspect: `docs/operating_system/rules/frontend-ui-rule.md:11-28`
- Inspect: `docs/operating_system/templates/agents/root-AGENTS.template.md:182-188`
- Verify: canonical references excluding `generated_agents` and `generated_exports`

**Dependencies:**
- None

**Authority:**
- Preauthorized local actions: read-only source inspection, dirty-path classification, `git status --short --untracked-files=all`, and `rg` searches.
- Stop for: an unsafe overlap with dirty generator destinations, a request to make Impeccable globally primary, or a distribution decision not covered by this plan.

**Steps:**
- [x] Step 1: Record `git status --short --untracked-files=all`, `git diff --name-only`, and untracked paths; preserve unrelated user changes.
- [x] Step 2: Classify dirty paths under canonical edit targets, `AGENTS.md`, `.agents/rules/**`, `generated_agents/**`, and `generated_exports/project-OS-starter-kit/**`.
- [x] Step 3: Do not run a generator that would overwrite a dirty generator destination unless that path is part of this plan's declared generated result; stop and report the collision.
- [x] Step 4: Search canonical sources for `ui-ux-pro-max`, `skill-distinctive-frontend-design`, and `impeccable`.
- [x] Step 5: Classify each match as existing eligibility, overlapping activation, authority boundary, or non-routing reference.
- [x] Step 6: Confirm no Impeccable version, vendored source, hook, or command catalog will be added.

**Verification:**
- [x] `rg -n "ui-ux-pro-max|skill-distinctive-frontend-design|impeccable" .agents docs README.md scripts tests -g '*.md' -g '*.py' -g '*.yaml' -g '*.json'`
- Expected: every canonical routing occurrence and every dirty generator destination is classified before modification.

**Exit Criteria:**
- Exact canonical routing edits are identified, unrelated references are excluded, and no user change is overwritten.

### Task 2: Apply canonical routing boundaries

**Purpose:**
- Make explicit Impeccable selection exclusive within overlapping visual/UX scope while preserving existing defaults and Project OS ownership.

**Selection Contract:**
- `impeccable` is explicitly selected only when the user directly invokes or requests it, or an approved specification, plan, or current bounded task contract names it as a required skill.
- Installation, discovery, availability, and generic applicability do not select Impeccable.
- When Impeccable is not explicitly selected, preserve existing frontend skill eligibility and routing behavior.

**Task Function:**
- Cross-skill instruction reconciliation

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-owned documentation edits with bounded cross-file consistency risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: generated-source checks and repository validators cover the edited contracts.

**Specification Coverage:**
- Explicit Impeccable selection suppresses duplicate invocation of `ui-ux-pro-max` and `skill-distinctive-frontend-design` for the same decision.
- No explicit Impeccable selection preserves existing frontend skill eligibility and routing behavior.
- Impeccable remains a design method and evidence source, not Project OS authority.
- Persistent `PRODUCT.md`, `DESIGN.md`, or other Impeccable-managed tool state cannot become repository authority without a separate integration decision; this covers commands such as `init` and `document`.
- Hooks remain opt-in integration decisions.
- Impeccable may assist with frontend optimization, but measured performance claims and acceptance evidence remain owned by `skill-performance-optimization`.

**Required Skills:**
- `none`

**Files And Symbols:**
- Modify: `docs/operating_system/rules/frontend-ui-rule.md:11-28`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md:182-188`
- Modify: `.agents/skills/skill-using-superpowers/SKILL.md:96-103`
- Modify: `.agents/skills/skill-brainstorming/SKILL.md:22`
- Modify: `.agents/skills/skill-distinctive-frontend-design/SKILL.md:26`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md:114-118`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md:48-52`
- Modify: `.agents/skills/skill-code-standards/SKILL.md:173-177`
- Modify: `.agents/skills/skill-frontend-component-engineering/SKILL.md:12`
- Modify: `docs/operating_system/tooling/frontend-backend-integration-tools.md:26`
- Verify: all canonical `.agents/skills/**/SKILL.md` references found in Task 1

**Dependencies:**
- Task 1 complete

**Authority:**
- Preauthorized local actions: modify only routing and ownership wording in listed canonical files; preserve unrelated guidance and generated headers.
- Stop for: any need to add external metadata allowances, alter starter distribution, delete existing skills, or change product/design SSOT ownership.

**Steps:**
- [x] Step 1: Replace unconditional frontend routing with explicit-selection precedence and preserve existing frontend skill eligibility and routing when Impeccable is not selected.
- [x] Step 2: Add one centralized authority boundary for design evidence, persistent `PRODUCT.md`/`DESIGN.md`/tool state, hooks, frontend optimization, and Project OS completion without copying Impeccable command playbooks.
- [x] Step 3: Add the explicit-selection exemption to `skill-using-superpowers` and minimal non-contradictory routing edits to brainstorming, specification, planning, code-standards, component-engineering, and distinctive-design skills.
- [x] Step 4: Keep command mechanics, style catalogs, and detailed checklists inside the selected design skill.

**Verification:**
- [x] `rg -n "impeccable|ui-ux-pro-max|skill-distinctive-frontend-design" .agents/skills docs/operating_system/templates/agents/root-AGENTS.template.md`
- Expected: explicit selection has one exclusive-overlap rule; existing eligibility language remains present; no canonical instruction requires all overlapping design skills together.

**Exit Criteria:**
- Canonical sources express one consistent boundary-only policy and contain no Impeccable version number or duplicated command catalog.

### Task 3: Regenerate maintained outputs

**Purpose:**
- Propagate canonical instruction changes into generated adapter files and starter-kit output without hand-editing generated surfaces.

**Task Function:**
- Generated-surface reconciliation

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic repository generation with existing scripts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: sync check and starter-kit validation provide direct proof.

**Specification Coverage:**
- Generated outputs remain derived from canonical sources.
- Starter-kit manifest continues to include `docs/operating_system` and `.agents/skills` without adding Impeccable distribution.

**Required Skills:**
- `none`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`
- Inspect: `scripts/build_starter_kit.py`
- Verify: `AGENTS.md`
- Verify: `.agents/rules/**`
- Verify: `generated_agents/**`
- Verify: `generated_exports/project-OS-starter-kit/**`

**Dependencies:**
- Task 2 complete
- Task 1 confirms no unsafe dirty-path collision with generator destinations.

**Authority:**
- Preauthorized local actions: run existing generation commands and update generated outputs they own.
- Stop for: generator failure, unexpected deletion, a dirty-path collision, or generated changes outside the edited routing surfaces.

**Steps:**
- [x] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 2: Run `py -3 scripts/build_starter_kit.py`.
- [x] Step 3: Inspect generated diffs for source headers, routing consistency, and absence of accidental external-skill copies.
- [x] Step 4: Run `git diff --name-only` and reconcile every changed path against declared canonical targets, `AGENTS.md`, `.agents/rules/**`, `generated_agents/**`, and `generated_exports/project-OS-starter-kit/**`.

**Verification:**
- [x] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: adapter drift check passes.

**Exit Criteria:**
- Generated agent surfaces and starter export reflect canonical routing changes and no generated file was edited manually.

### Task 4: Validate policy and repository integrity

**Purpose:**
- Prove metadata, generation, contract, stale-reference, and formatting integrity after integration.

**Task Function:**
- Final repository verification

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused validation of documentation, generation, and repository contracts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository validators and focused tests are authoritative.

**Specification Coverage:**
- Existing native skill metadata schema remains unchanged.
- No stale routing or deleted-skill references remain in maintained sources.
- Required generated and starter-kit outputs reconcile with canonical sources.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `scripts/validate_agent_metadata_schema.py`
- Verify: `scripts/validate_repo_contracts.py`
- Verify: `tests/test_sync_agent_adapters.py`
- Verify: `tests/test_starter_kit_generation.py`
- Verify: `tests/test_validate_template_required_sections.py`
- Verify: `tests/test_validate_agent_metadata_schema.py`
- Verify: canonical and generated frontend routing references

**Dependencies:**
- Task 3 complete

**Authority:**
- Preauthorized local actions: run declared validators, focused tests, stale-reference searches, and formatting checks.
- Stop for: failed required validation, stale generated output, unexpected user-file changes, or any scope expansion.

**Steps:**
- [x] Step 1: Run `py -3 scripts/validate_agent_metadata_schema.py`.
- [x] Step 2: Run `py -3 scripts/validate_repo_contracts.py`.
- [x] Step 3: Run `py -3 -m pytest -q tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_template_required_sections.py tests/test_validate_agent_metadata_schema.py`.
- [x] Step 4: Run the diff-scoped forbidden-integration search and the broader routing inventory search.
- [x] Step 5: Run `git diff --name-only` and reconcile every path against the declared allowlist.
- [x] Step 6: Run `git diff --check` and reconcile only declared changes.

**Verification:**
- [x] `git diff --unified=0 -- .agents docs generated_agents generated_exports | rg -n '^\+.*(npx impeccable install|impeccable.*(3\.6\.1|4\.1\.1)|vendor(ed|ing)? Impeccable|enable.*Impeccable.*hook)'`
- Expected: no output; `rg` exit code 1 means no forbidden vendor, version, installer, or hook addition.
- [x] `rg -n "ui-ux-pro-max|skill-distinctive-frontend-design|impeccable" .agents docs README.md scripts tests -g '*.md' -g '*.py' -g '*.yaml' -g '*.json'`
- Expected: broader inventory is reviewed for awareness; only routing contradictions are changed.
- [x] `git diff --name-only`
- Expected: every changed path is a declared canonical target or generator-owned output; any other path is recorded as a scope deviation.
- [x] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- Verification returns fresh passing output, generated surfaces match canonical sources, and any pre-existing failures or scope deviations are recorded before handoff.

## Verification

- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_agent_metadata_schema.py`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 -m pytest -q tests/test_sync_agent_adapters.py tests/test_starter_kit_generation.py tests/test_validate_template_required_sections.py tests/test_validate_agent_metadata_schema.py`
- `git diff --check`
- `rg -n "ui-ux-pro-max|skill-distinctive-frontend-design|impeccable" .agents docs generated_agents generated_exports -g '*.md' -g '*.json' -g '*.yaml'`

## Completion Criteria

The plan is ready for completion verification when:

1. Canonical routing gives explicitly selected Impeccable exclusive overlap within its task scope.
2. When Impeccable is not explicitly selected, existing frontend skill eligibility and routing behavior remains unchanged.
3. Project OS SSOT, accessibility, performance, testing, and final-verification ownership remains explicit.
4. No Impeccable version, vendored source, command catalog, hook, metadata exception, registry, or competing `PRODUCT.md`/`DESIGN.md` authority is added.
5. `AGENTS.md`, `.agents/rules`, `generated_agents`, and `generated_exports/project-OS-starter-kit` are regenerated from canonical sources.
6. Metadata validation, repository contract validation, focused tests, stale-reference search, and `git diff --check` pass with fresh output.
7. No unrelated user changes are overwritten and no Git commit, push, merge, or publication occurs without explicit authorization.

Deferred work requires a separate approved scope based on current Impeccable version review, distribution ownership, routing evidence, and real adoption results.
