---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: cos-canonical-work-coordination
parent_spec: docs/superpowers/specs/2026-08-30-cos-canonical-work-coordination-spec.md
targets:
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - tests/test_skill_chief_of_staff.py
  - generated_agents/codex/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/claude/skills/skill-chief-of-staff/SKILL.md
  - generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md
---

# CoS Canonical Work Coordination

## Goal

Implement the approved canonical-work CoS contract. CoS coordinates canonical
work; it does not own work execution or canonical work truth. V2 supports only:

1. existing plan-bound execution
2. exact-commit repository-snapshot advisory audit

Do not add new runtime, state, adapter, routing, or authority systems.

## Implementation Outcomes

### Canonical Work Binding

`.agents/skills/skill-chief-of-staff/SKILL.md` defines common Work Binding and
keeps existing deterministic Plan Binding as a plan-bound specialization. It
adds repository-snapshot advisory binding with repository identity, exact commit
SHA, scoped target, evidence authority, source-relative freshness, and resolved
acceptance authority.

### Mode-separated authority

The skill separates common attention/evidence rules from advisory and
plan-bound-execution branches. Advisory CoS can inspect, synthesize, challenge,
and recommend but cannot mutate. `skill-executing-plans` remains sole approved-
plan execution owner; existing plan, Git, GitHub, verification, and finishing
owners retain their authority.

### Contract and distribution proof

`tests/test_skill_chief_of_staff.py` proves new behavior and preserved V1
boundaries. Generated CoS surfaces derive from canonical source and pass sync,
Starter, repository-contract, focused-test, and diff checks.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-writing-skills`, `skill-test-driven-development`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing untracked changes
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared spec, plan, canonical skill, and focused tests; regenerate declared adapters; run declared validators, tests, and Starter build checks
- User-approval actions: commit, push, merge, publication, external writes, destructive cleanup, discard, hook/runtime changes, and scope expansion
- Parallel ownership: none; canonical source, tests, generated output, and validation share ordered dependencies
- Sequential fallback: Task 1 contract and canonical source, then Task 2 generation and final verification

## Task Breakdown

### Task 1: Implement canonical CoS contract with focused proof

**Purpose:**
- Add approved Work Binding and two-mode CoS behavior while preserving existing plan-bound semantics.

**Task Function:**
- Update canonical skill contract and its focused source assertions using RED→GREEN proof.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation and test edit; no independent lane or delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract tests and final repository validators directly prove the changed surface.

**Specification Coverage:**
- Common Work Binding includes work identity, evidence authority, reference anchors, source-relative freshness, acceptance-authority resolution, and coordination mode.
- Existing deterministic Plan Binding remains intact and does not require a repository audit to bind a plan.
- Repository Snapshot Advisory Binding requires repository identity, exact commit SHA, scoped target, and evidence authority.
- Modes are `advisory` and `plan-bound-execution`; no generic CoS execute authority exists.
- Common attention/evidence rules are separate from advisory audit and plan-bound task/lane execution.
- Advisory mode has no mutation authority; local mutation-risk inspection requires clean isolation or pre/post Git proof.
- `skill-executing-plans` remains approved-plan execution owner.
- `required_reads` is empty; Git-tracked coordination remains conditional for plan-bound execution.
- Acceptance authority resolves from explicit current-work owner, canonical work owner, or existing repository/workflow authority; unresolved acceptance-sensitive claims return `BLOCKED`.
- Source-relative freshness reuses commit-bound Git evidence while the anchor remains unchanged; runtime or external mutable evidence uses existing freshness rules.
- PR, release, incident, specification, research, cross-repository, timer, hook, scheduler, profile, registry, and persistent-state expansion remains excluded.

**Required Skills:**
- `skill-code-standards`
- `skill-writing-skills`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-chief-of-staff/SKILL.md:frontmatter`, `.agents/skills/skill-chief-of-staff/SKILL.md:Activation`, `.agents/skills/skill-chief-of-staff/SKILL.md:Plan Binding`, `.agents/skills/skill-chief-of-staff/SKILL.md:Attention`, `.agents/skills/skill-chief-of-staff/SKILL.md:Lane Contract`, `.agents/skills/skill-chief-of-staff/SKILL.md:Durable Truth And Escalation`, `.agents/skills/skill-chief-of-staff/SKILL.md:Output`
- Modify: `tests/test_skill_chief_of_staff.py`, `.agents/skills/skill-chief-of-staff/SKILL.md`
- Verify: `tests/test_skill_chief_of_staff.py`

**Dependencies:**
- Active spec `docs/superpowers/specs/2026-08-30-cos-canonical-work-coordination-spec.md`.
- Existing plan-bound CoS assertions and current `.playwright-mcp/`, `db/`, and `out/` workspace state remain preserved.

**Authority:**
- Preauthorized local actions: edit only the declared test and canonical skill; run focused pytest; inspect existing execution and coordination owners.
- Stop for: change to `skill-executing-plans`, `planning-dispatch.md`, Git coordination rules, runtime launcher, external hook, generated surfaces, or new durable artifact.

**Steps:**
- [x] Step 1: Add focused assertions for empty `required_reads`, Work Binding, repository-snapshot advisory binding, mode separation, acceptance-authority resolution, source-relative freshness, and risk-based isolation.
- [x] Step 2: Run `py -3 -m pytest tests/test_skill_chief_of_staff.py -q` and record expected RED failures.
- [x] Step 3: Add `## Work Binding` with common rules and `## Repository Snapshot Advisory Binding` without replacing `## Plan Binding`.
- [x] Step 4: Separate common attention/evidence rules from advisory and plan-bound-execution branches; retain plan-bound runtime, lane, review, integration, retirement, and durable-truth boundaries.
- [x] Step 5: Run `py -3 -m pytest tests/test_skill_chief_of_staff.py -q` and reconcile failures without weakening preserved gates.

**Verification:**
- [ ] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- Expected: focused CoS contract suite passes.

**Exit Criteria:**
- Canonical skill and focused tests define exactly two V2 modes, preserve Plan Binding, separate advisory semantics, and grant no new mutation or durable-state authority.

### Task 2: Regenerate derived surfaces and verify final state

**Purpose:**
- Propagate canonical CoS changes safely and prove generated, Starter, repository, and workspace consistency.

**Task Function:**
- Preflight generated drift, sync canonical outputs, run validators, and reconcile final changed-file scope.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic generation and validation; no independent lane or delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: sync check, Starter validation, repository contracts, focused tests, and diff inspection provide direct proof.

**Specification Coverage:**
- Generated Codex, Claude, and Antigravity CoS surfaces derive from canonical `.agents/skills` source.
- Starter build uses existing manifest behavior; no direct Starter output edits occur.
- Pre-existing unrelated generated drift blocks mutating sync before any generated file is written.
- Existing untracked `.playwright-mcp/`, `db/`, and `out/` remain preserved and out of scope.

**Required Skills:**
- `skill-executing-plans`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/sync_agent_adapters.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`, `scripts/validate_repo_contracts.py`
- Modify: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`, and `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md` through `scripts/sync_agent_adapters.py` only
- Verify: `generated_exports/project-OS-starter-kit`, `git status --short`, and `git diff --name-only`

**Dependencies:**
- Task 1 focused tests pass.
- Before write-mode sync, `py -3 scripts/sync_agent_adapters.py --all-platforms --check` reports either clean state or only the three declared CoS mirror drifts caused by the canonical skill change; any other drift blocks.

**Authority:**
- Preauthorized local actions: run non-mutating sync preflight, adapter sync, Starter build/validation, declared tests and validators, `git diff --check`, and inspect generated diffs.
- Stop for: baseline sync drift, generated drift outside declared CoS surfaces, manifest changes, publication changes, destructive cleanup, or modification of preserved untracked paths.

**Steps:**
- [x] Step 1: Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check`; permit only the three declared CoS mirror drifts caused by Task 1 and stop for any other drift.
- [x] Step 2: Run `py -3 scripts/sync_agent_adapters.py --all-platforms`.
- [x] Step 3: Inspect generated CoS diffs and confirm canonical-source headers; do not edit generated files directly.
- [x] Step 4: Run `py -3 scripts/sync_agent_adapters.py --all-platforms --check`.
- [x] Step 5: Run `py -3 scripts/build_starter_kit.py --output-root generated_exports` and `py -3 scripts/validate_starter_kit.py`.
- [x] Step 6: Run repository contract validation, focused CoS tests, and `git diff --check`.
- [x] Step 7: Confirm tracked diff scope and untracked declared spec/plan scope with `git status --short`; preserve `.playwright-mcp/`, `db/`, and `out/`.

**Verification:**
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `py -3 scripts/build_starter_kit.py --output-root generated_exports`
- [ ] `py -3 scripts/validate_starter_kit.py`
- [ ] `py -3 scripts/validate_repo_contracts.py --fast`
- [ ] `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- [ ] `git diff --check`
- Expected: all commands exit 0; only declared files change; preserved untracked paths remain untouched.

**Exit Criteria:**
- Canonical skill, spec, plan, focused tests, generated mirrors, Starter output, and validators agree; no unrelated generated or runtime surface changes exist.

## Verification

- `py -3 scripts/validate_planning_lifecycle.py --strict`
- `py -3 scripts/validate_template_required_sections.py --require-template-selection`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/build_starter_kit.py --output-root generated_exports`
- `py -3 scripts/validate_starter_kit.py`
- `py -3 scripts/validate_repo_contracts.py --fast`
- `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`
- `git diff --check`
- `git status --short`
- Inspect `git diff --name-only` for tracked canonical, focused-test, and generated CoS changes; inspect `git status --short` for declared untracked spec/plan files and preserved `.playwright-mcp/`, `db/`, and `out/`.

### Fresh Evidence (2026-08-30)

- `py -3 -m pytest tests/test_skill_chief_of_staff.py -q`: `11 passed`.
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`: passed.
- `py -3 scripts/validate_agent_runtime_drift.py --all-platforms --skip-deploy-check`: passed.
- `py -3 scripts/validate_planning_lifecycle.py --strict`: passed.
- `py -3 scripts/validate_template_required_sections.py --require-template-selection`: passed.
- `py -3 scripts/build_starter_kit.py --output-root generated_exports`: passed.
- `py -3 scripts/validate_starter_kit.py`: passed.
- `py -3 scripts/validate_repo_contracts.py --fast`: passed.
- `git diff --check`: passed with only Git LF/CRLF normalization warnings.
- Tracked changes are limited to canonical CoS source, focused tests, and three generated CoS mirrors; untracked declared spec/plan files and preserved `.playwright-mcp/`, `db/`, and `out/` remain outside generated sync scope.

## Completion Criteria

The plan is ready for completion verification when:

1. active spec and plan agree on Work Binding and exactly two V2 modes
2. common attention/evidence rules are distinct from advisory and plan-bound execution branches
3. deterministic Plan Binding and existing execution ownership remain intact
4. advisory mode has no CoS mutation or durable-state authority
5. source-relative freshness and risk-based isolation are explicit
6. pre-write adapter drift check passes before generated sync
7. focused tests and all final validators pass with fresh output
8. declared files are the only changed surfaces; existing untracked paths remain preserved

Plan status became `active` because user explicitly requested execution. Fresh
verification passed; no branch disposition is authorized.
