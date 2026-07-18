---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: serena-code-intelligence-and-operating-system-cleanup
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-07-18-12-29-serena-code-intelligence-and-operating-system-cleanup-spec.md
targets:
  - AGENTS.md
  - .gitignore
  - .agents/skills/
  - .agents/rules/
  - docs/operating_system/
  - docs/architecture_templates/
  - docs/generated/
  - repo_config/
  - scripts/
  - tests/
  - tools/docs/
related_features: []
related_stages: []
---

# Serena Code Intelligence And Operating-System Cleanup Implementation Plan

## Goal

Install and include Serena as the exact-symbol half of a GitNexus/Serena
code-intelligence combination, then remove inactive persistent architecture
lineage generation and reduce repository operating-system duplication without
weakening security, publication, destructive-operation, or verification gates.

Execution stays serial because later schema, adapter, prompt, and validator
changes depend on earlier ownership decisions and share many files.

## Key Deliverables

### Working Serena Integration

Serena is installed user-locally, configured for Codex with `no-memories`,
verified against this repository, ignored by Git, and documented through one
canonical code-intelligence policy.

### Removed Architecture-Lineage Runtime

Architecture generator, sync wrapper, audit wrapper, generated architecture
maps, architecture-only templates, CI gates, validators, tests, metadata, and
active policy references are removed together.

### Smaller Governance Surface

Rules contain hard invariants, skills contain reusable methods, workflows own
transitions, prompts contain reusable wording, and executable validators own
schemas.

### Consolidated Execution Lifecycle

Skill count is at most 15, workflow count at most five, prompt count at most
12, live-run logic exists once, closeout logic exists once, and small local
changes require no planning artifact.

### Verified Starter And Publication Boundaries

Adapter generation, starter-kit validation, repository validation, tests, and
publication dry run pass after cleanup. Serena and GitNexus remain private,
derived, and absent from public output.

## Task/Wave Breakdown

### Task 1: Capture Baseline And Install Serena

**Purpose:**
- establish fresh baseline evidence and a working user-local Serena installation
  before repository policy references Serena

**Files:**
- Inspect: `%USERPROFILE%/.codex/config.toml`
- Modify: `%USERPROFILE%/.codex/config.toml` through `serena setup codex`
- Modify: `%USERPROFILE%/.serena/serena_config.yml`
- Create temporarily: `%TEMP%/project-os-serena-config-backup/`
- Verify: `docs/superpowers/specs/2026-07-18-12-29-serena-code-intelligence-and-operating-system-cleanup-spec.md`

**Preconditions:**
- working tree contains only accepted planning artifacts
- `uv` and `uvx` are available
- repository fast validation passes

**Steps:**
- [x] record `git status --short`, current skill/workflow/prompt counts, hook
      counts, required-read counts, and current test baseline
- [x] copy existing Codex and Serena config files into a timestamped temporary
      backup directory before setup
- [x] run `uv tool install -p 3.13 serena-agent`
- [x] run `serena init`
- [x] run `serena setup codex`
- [x] configure `base_modes: [no-memories]` in Serena global config
- [x] ensure Serena uses `--context codex --project-from-cwd`
- [x] restart or reload Codex MCP configuration
- [x] diff user config against backup and confirm unrelated MCP/provider settings
      are unchanged; restore backup if setup damages unrelated configuration
- [x] record installed Serena version
- [x] activate this repository and run symbol overview, symbol lookup,
      reference lookup, and diagnostics
- [x] confirm no Serena dashboard or MCP listener is exposed beyond local host

**Verification:**
- [x] `serena --help`
- [x] `serena --version`
- [x] inspect `%USERPROFILE%/.codex/config.toml` for Serena MCP entry
- [x] inspect `%USERPROFILE%/.serena/serena_config.yml` for `no-memories`
- [x] compare both configs with temporary backups
- [x] Serena symbol/reference operations return repository results

**Exit Criteria:**
- Serena works in Codex for this repository without committed project state

### Task 2: Add Thin Code-Intelligence Policy

**Purpose:**
- make GitNexus/Serena ownership explicit before architecture discovery files
  are deleted

**Files:**
- Create: `docs/operating_system/tooling/code-intelligence-tools.md`
- Delete: `docs/operating_system/tooling/gitnexus-pilot.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify: `.gitignore`
- Modify: `repo_config/adapter-sync-policy.yaml` only if mapping changes are
  required
- Generate: `AGENTS.md`
- Generate: `GEMINI.md`
- Generate: `CLAUDE.md`
- Generate: `.codex/rules/*.rules`
- Verify: `tests/test_sync_agent_adapters.py`
- Verify: `tests/test_deploy_agent_runtime.py`

**Preconditions:**
- Task 1 complete
- Serena exact-symbol operations verified

**Steps:**
- [x] add `.serena/` to `.gitignore`
- [x] replace GitNexus-only pilot with one policy assigning native tools,
      Serena, GitNexus, tests/CI, `docs/architecture.md`, and ADRs
- [x] state conditional handoff rules and source-first fallback
- [x] keep root-agent text short; link detailed tooling policy instead of
      duplicating it
- [x] keep GitNexus freshness guidance conditional for high-trust graph use
- [x] explicitly forbid committed Serena memories, indexes, onboarding, and
      generated wikis
- [x] run canonical adapter sync from owning template
- [x] update adapter tests only for intentional policy output changes

**Verification:**
- [x] `python scripts/sync_agent_adapters.py`
- [x] `python scripts/sync_agent_adapters.py --check`
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1`
- [x] `python -m pytest tests/test_sync_agent_adapters.py tests/test_deploy_agent_runtime.py`
- [x] `git check-ignore .serena/project.yml`

**Exit Criteria:**
- one canonical policy owns tool selection and generated adapters match it

### Task 3: Remove Architecture Generator And Direct Runtime Consumers

**Purpose:**
- delete inactive executable architecture-lineage machinery in one bounded slice

**Files:**
- Delete: `tools/docs/generate_architecture_metadata.py`
- Delete: `scripts/sync_architecture_docs.py`
- Delete: `scripts/audit_architecture_linkage.py`
- Delete: `tests/test_sync_architecture_docs.py`
- Delete: `tests/test_architecture_metadata_generation.py`
- Delete: `tests/test_architecture_linkage_audit.py`
- Delete: `docs/generated/architecture_dag.yaml`
- Delete: `docs/generated/capability_lineage.yaml`
- Delete: `docs/architecture_templates/`
- Modify: `scripts/validate_repo_contracts.py`
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `repo_config/starter-kit-closure.json`
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `tests/test_starter_kit_generation.py`

**Preconditions:**
- Task 2 complete
- code-intelligence policy provides replacement discovery guidance
- confirmed no active downstream repository requires managed architecture
  generator from current starter revision

**Steps:**
- [x] delete generator, wrappers, architecture outputs, templates, and dedicated
      tests
- [x] remove architecture sync CI step and skip message
- [x] remove architecture sync orchestration from repository validator
- [x] remove deleted files from starter manifests and closure inventory
- [x] preserve `docs/generated/planning_lineage.yaml` and its generator
- [x] preserve `docs/architecture.md` and Mode A architecture template
- [x] adjust direct tests for removed steps without weakening unrelated checks
- [x] search executable surfaces for retired filenames before continuing

**Verification:**
- [x] `rg -n "sync_architecture_docs|generate_architecture_metadata|audit_architecture_linkage|architecture_dag|capability_lineage" scripts tests repo_config .github tools docs/generated`
- [x] search returns no active executable reference
- [x] `python -m pytest tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py`
- [x] `python scripts/validate_repo_contracts.py --fast`

**Exit Criteria:**
- no executable architecture-generation path or direct runtime dependency remains

### Task 4: Remove Architecture Metadata And Active Documentation Policy

**Purpose:**
- remove architecture-generation semantics from active governance while keeping
  historical plans/specs unchanged

**Files:**
- Modify: `repo_config/adoption-mode.yaml`
- Modify: `scripts/validate_adoption_shape.py`
- Modify: `scripts/validator_policy.py`
- Modify: `scripts/validate_agent_runtime_drift.py`
- Modify: `scripts/validate_provider_settings_schema.py`
- Modify: `scripts/sync_agent_adapters.py`
- Modify: `tests/test_validate_adoption_shape.py`
- Modify: `tests/test_validate_agent_runtime_drift.py`
- Modify: `tests/test_sync_agent_adapters.py`
- Modify: `docs/adoption_guide.md`
- Delete or rewrite: `docs/operating_system/adoption/mode-b-example-migration.md`
- Modify: `docs/operating_system/adoption/project-adoption-migration-guide.md`
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/governance/feature-routing-guide.md`
- Modify: `docs/operating_system/lifecycle/doc-system-lifecycle.md`
- Modify: `docs/operating_system/lifecycle/feature-lifecycle.md`
- Modify: `docs/operating_system/lifecycle/stage-lifecycle.md`
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `docs/features/README.md`
- Modify: `docs/stages/README.md`
- Modify: `docs/operating_system/agent_memory/patterns.md`

**Preconditions:**
- Task 3 complete
- historical `docs/superpowers/specs/` and `docs/superpowers/plans/` remain
  grandfathered and excluded from active-reference cleanup

**Steps:**
- [x] remove managed architecture config keys when consumer search reaches zero
- [x] delete adoption modes and migration guidance that exist only for generated
      feature/stage architecture contracts
- [x] remove feature/stage source-generated lifecycle requirements
- [x] remove architecture metadata routing, markers, capability IDs, and
      regeneration completion gates
- [x] retain normal product documentation guidance only when useful without the
      generator
- [x] retain planning lineage guidance separately
- [x] revise agent memory so it no longer instructs agents to regenerate retired
      files
- [x] update tests to reject stale active policy but ignore completed history

**Verification:**
- [x] `rg -n "managed_architecture_metadata|architecture_generator|lineage.generated|feature.source.yaml|stage.source.yaml|@architecture|@capability|@proves" docs/operating_system docs/adoption_guide.md docs/features docs/stages repo_config scripts tests --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**'`
- [x] remaining matches are independently justified non-architecture uses or
      removed
- [x] `python -m pytest tests/test_validate_adoption_shape.py tests/test_validate_agent_runtime_drift.py tests/test_sync_agent_adapters.py`

**Exit Criteria:**
- active governance no longer requires architecture-lineage generation

### Task 5: Simplify Python Metadata And Rules

**Purpose:**
- remove file-level architecture metadata while retaining enforceable coding and
  safety contracts

**Files:**
- Modify: `scripts/validate_python_meta_headers.py`
- Modify: `tests/test_validate_python_meta_headers.py`
- Delete: `.agents/skills/skill-python-file-metadata/`
- Modify: `.agents/skills/skill-code-standards/SKILL.md`
- Modify: `.agents/skills/skill-refactoring-assessment/SKILL.md`
- Modify: `docs/operating_system/rules/python-contracts-rule.md`
- Generate: `.agents/rules/python-contracts-rule.md`
- Modify: `docs/operating_system/rules/doc-contracts-rule.md`
- Generate: `.agents/rules/doc-contracts-rule.md`
- Delete: `docs/operating_system/rules/global-baseline-contract-rule.md`
- Delete: `docs/operating_system/rules/env-gitignore-contract-rule.md`
- Generate/remove through adapter sync: `.agents/rules/global-baseline-contract-rule.md`
- Generate/remove through adapter sync: `.agents/rules/env-gitignore-contract-rule.md`
- Modify: `docs/operating_system/rules/publication-boundary-rule.md`
- Modify: `scripts/validate_env_gitignore_contract.py`
- Modify: `tests/test_validate_repo_contracts.py`
- Modify: `repo_config/agent-adapter-mappings.json`

**Preconditions:**
- Task 4 complete
- adapter source/generated ownership understood before generated rule deletion

**Steps:**
- [x] remove mandatory `@meta` coverage and ownership/capability linkage from
      Python validator
- [x] retain only validation still protecting active Python contracts
- [x] merge Python standards and refactoring method later into
      `skill-code-standards`; do not preserve metadata workflow
- [x] reduce Python rule to typing, exceptions, non-lossy error handling, and
      focused verification
- [x] delete global baseline rule; keep adapter source-of-truth behavior in
      executable sync/verification
- [x] merge `.env` ignore invariant into publication/repository hygiene while
      keeping executable `.gitignore` validation
- [x] update adapter mappings and regenerate rule outputs
- [x] grandfather existing Python `@meta` blocks; do not perform mass removal
      during this task

**Verification:**
- [x] `python -m pytest tests/test_validate_python_meta_headers.py tests/test_validate_repo_contracts.py`
- [x] `python scripts/validate_python_meta_headers.py`
- [x] `python scripts/sync_agent_adapters.py --check`
- [x] `python scripts/validate_env_gitignore_contract.py`

**Exit Criteria:**
- Python files no longer require architecture metadata; remaining rules are hard
  invariants

### Task 6: Narrow Audit Mandate And Preserve Safety Rules

**Purpose:**
- stop requiring full audit bundles for ordinary failures without weakening
  serious incident evidence

**Files:**
- Modify: `docs/operating_system/rules/audit-evidence-mandate-rule.md`
- Generate: `.agents/rules/audit-evidence-mandate-rule.md`
- Modify: `docs/operating_system/templates/audit-report-with-evidence-template.md`
- Modify: `docs/operating_system/prompt_templates/audit-report-with-evidence-prompt.md`
- Modify: `.agents/skills/skill-systematic-debugging/SKILL.md`
- Modify: `scripts/audit_check.py`
- Modify: tests covering audit qualification, if present

**Preconditions:**
- Task 5 complete
- security, privacy, data-loss, publication, and destructive-command rules remain
  separately identifiable

**Steps:**
- [x] change audit qualification to security/privacy, data loss, serious data
      quality, repeated user-impacting runtime failure, unclear cross-boundary
      invariant failure, or explicit request
- [x] remove ordinary persistent test failure as automatic full-bundle trigger
- [x] define ordinary failure evidence as failing output, root cause, focused
      regression proof, and fresh verification
- [x] keep canonical formal audit template for qualifying incidents
- [x] update debugging and incident routing to select formal audit conditionally
- [x] add or update focused tests for trigger classification

**Verification:**
- [x] ordinary unit-test failure no longer requires report/manifest/evidence tree
- [x] security/privacy/data-loss fixture still requires formal audit bundle
- [x] focused audit tests pass
- [x] `python scripts/audit_check.py --help`

**Exit Criteria:**
- formal audits are proportional to incident severity

### Task 7: Consolidate Canonical Skills

**Purpose:**
- reduce 23 skills to at most 15 without losing reusable methods

**Files:**
- Create: `.agents/skills/skill-change-planning/SKILL.md`
- Delete: `.agents/skills/skill-spec-drafting/`
- Delete: `.agents/skills/skill-writing-plans/`
- Delete: `.agents/skills/skill-plan-document-reviewer/`
- Create: `.agents/skills/skill-execute-and-close/SKILL.md`
- Delete: `.agents/skills/skill-executing-plans/`
- Delete: `.agents/skills/skill-verification-before-completion/`
- Superseded by later approved restoration: Delete merged review skill
- Superseded by later approved restoration: Keep `.agents/skills/skill-requesting-code-review/`
- Superseded by later approved restoration: Keep `.agents/skills/skill-receiving-code-review/`
- Create: `.agents/skills/skill-parallel-execution/SKILL.md`
- Superseded by later approved restoration: Keep `.agents/skills/skill-dispatching-parallel-agents/`
- Superseded by later approved restoration: Keep `.agents/skills/skill-subagent-driven-development/`
- Superseded by later approved restoration: Create `.agents/skills/skill-code-standards/SKILL.md`
- Superseded by later approved restoration under `.agents/skills/skill-code-standards/`
- Superseded by later approved restoration: Create `.agents/skills/skill-refactoring-assessment/SKILL.md`
- Delete: `.agents/skills/skill-doc-system-lifecycle/`
- Modify: `.agents/skills/skill-using-superpowers/SKILL.md`
- Modify: `.agents/skills/skill-test-driven-development/SKILL.md`
- Modify: `.agents/skills/skill-writing-skills/SKILL.md`
- Modify: `scripts/validate_agent_metadata_schema.py`
- Modify: `scripts/deploy_agent_runtime.py`
- Modify: `tests/test_validate_agent_metadata_schema.py`
- Modify: `tests/test_deploy_agent_runtime.py`

**Preconditions:**
- Tasks 5 and 6 complete
- final hard invariants are known before methods are merged

**Steps:**
- [x] merge method bodies according to spec target skill set
- [x] remove every full-repo activation pre-hook and read-only post-hook
- [x] do not add Serena hooks
- [x] reduce unconditional `required_reads` to at most one for normal skills
- [x] remove empty metadata fields and generic tags only after consumer/schema
      changes are ready in same patch
- [x] keep `skill-writing-skills` in starter kit for this change; simplify its
      metadata and references but defer package extraction
- [x] update all canonical skill references in active docs, workflows, prompts,
      adapter tests, and runtime deployment tests
- [x] regenerate provider skill surfaces only after canonical set validates

**Verification:**
- [x] `(Get-ChildItem .agents/skills -Directory).Count` is at most 15
- [x] `rg -n "scripts/hooks/run_validator.py --fast" .agents/skills` returns no
      matches
- [x] metadata-count script proves no normal skill has more than one required read
- [x] `python scripts/validate_agent_metadata_schema.py`
- [x] `python -m pytest tests/test_validate_agent_metadata_schema.py tests/test_deploy_agent_runtime.py`

**Exit Criteria:**
- canonical skill set is at most 15 and contains no activation-time repository
  validation

### Task 8: Consolidate Workflows And Planning Transitions

**Purpose:**
- replace 13 overlapping workflows with five transition owners

**Files:**
- Modify: `docs/operating_system/planning/planning-dispatch.md`
- Modify: `scripts/validate_planning_lifecycle.py`
- Modify: `tests/test_validate_planning_lifecycle.py`

**Preconditions:**
- Task 7 complete
- new skill names are stable
- planning lineage generator remains active and unchanged unless transition
  schema changes require focused updates

**Steps:**
      verification, and closeout
      optional scenario, preflight, execute, verify, diagnose/fix/rerun, close
      reconciliation, and closeout
      procedure without duplicating it
- [x] keep drift reconciliation as the fifth workflow
- [x] remove roadmap/thread/spec artifact creation as universal transition path
- [x] encode complexity tiers: none, plan, spec+plan, roadmap+child plans
- [x] keep spec sets, authoring maps, and execution maps conditional
- [x] retain `docs/generated/planning_lineage.yaml` and existing generator because
      current validators actively consume it
- [x] update lifecycle validator only for intentional transition/schema changes

**Verification:**
- [x] one workflow contains live-run failure loop
- [x] one workflow contains closeout transition
- [x] `python scripts/validate_planning_lifecycle.py`
- [x] `python -m pytest tests/test_validate_planning_lifecycle.py`

**Exit Criteria:**
- workflows own transitions once and planning remains complexity-tiered

### Task 9: Consolidate Prompt Templates And Closeout Wording

**Purpose:**
- reduce 55 prompts to at most 12 reusable wording assets

**Files:**
- Create/rewrite: `docs/operating_system/prompt_templates/task-intake-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/design-spec-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/implementation-plan-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/execute-next-action-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/debug-incident-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/live-run-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/parallel-change-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/verification-closeout-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/documentation-update-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/publication-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/drift-reconciliation-prompt.md`
- Create/rewrite: `docs/operating_system/prompt_templates/code-review-prompt.md`
- Rewrite: `docs/operating_system/prompt_templates/README.md`
- Delete: all superseded prompt templates not in target set
- Convert into tooling/procedure text before deleting prompt versions:
  - `gitnexus-refresh-prompt.md`
  - `provider-history-sync-prompt.md`
  - `runtime-deploy-and-verify-prompt.md`
  - `starter-baseline-sync-prompt.md`
  - `mode-migration-prompt.md`
- Modify: `scripts/validate_prompt_metadata_schema.py`
- Modify: `scripts/validate_prompt_ladder.py`
- Modify: `tests/test_validate_prompt_ladder.py`
- Add: focused tests for prompt metadata schema if absent

**Preconditions:**
- Task 8 complete
- workflow names and transitions are final

**Steps:**
- [x] map every current prompt to one target prompt, tooling procedure, or delete
- [x] absorb planning/readiness/intake variants into `task-intake-prompt.md`
- [x] absorb spec/roadmap construction wording into design/spec and plan prompts;
      keep large-program templates under `docs/operating_system/templates/`
- [x] absorb execute/readiness/next-action/patch/regression wording into
      `execute-next-action-prompt.md`
- [x] absorb bug/audit/known-issue wording into conditional incident prompt
- [x] absorb all live-run prompts into `live-run-prompt.md`
- [x] absorb worktree prompts into `parallel-change-prompt.md`
- [x] absorb deliverable, lifecycle, thread, workstream, roadmap, reconciliation,
      parent/child, and next-actions closeout wording into one parameterized
      `verification-closeout-prompt.md`
- [x] absorb docs/readme/root-doc wording into `documentation-update-prompt.md`
- [x] make prompt README a short index; remove ladder diagrams and transition
      ownership
- [x] remove `next_steps`, `related_skills`, and normal `required_reads` when
      workflows/skills own those facts
- [x] retain only metadata fields with active validators/consumers

**Verification:**
- [x] prompt count excluding README is at most 12
- [x] `rg -n "thread-closeout|workstream-closeout|roadmap-closeout|live-run-closeout" docs/operating_system/prompt_templates` resolves only inside consolidated prompt text where needed
- [x] `python scripts/validate_prompt_metadata_schema.py`
- [x] `python scripts/validate_prompt_ladder.py`
- [x] `python -m pytest tests/test_validate_prompt_ladder.py`

**Exit Criteria:**
- prompts own wording only; workflow transition facts are not duplicated

### Task 10: Reconcile Metadata, Validators, Hooks, Manifests, And Adapters

**Purpose:**
- remove schema and runtime debris after canonical content consolidation

**Files:**
- Modify: `scripts/validate_agent_metadata_schema.py`
- Modify: `scripts/validate_prompt_metadata_schema.py`
- Modify: `scripts/deploy_agent_runtime.py`
- Modify: `scripts/sync_agent_adapters.py`
- Modify: `scripts/validate_agent_runtime_drift.py`
- Modify: `scripts/validate_repo_contracts.py`
- Delete if unused: `scripts/hooks/run_validator.py`
- Delete if unused: `scripts/setup_hooks.ps1`
- Delete if unused: `scripts/setup_hooks.sh`
- Delete if unused: `tests/test_setup_hooks.py`
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `repo_config/starter-kit-closure.json`
- Modify: `repo_config/agent-adapter-mappings.json`
- Modify: `repo_config/adapter-sync-policy.yaml`
- Modify: relevant validator, adapter, runtime, and starter-kit tests
- Generate: `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, `.agents/rules/*`, `.codex/rules/*`, and provider skill surfaces

**Preconditions:**
- Tasks 7 through 9 complete
- final canonical skill, rule, workflow, and prompt inventories are known

**Steps:**
- [x] build metadata consumer table for each retained field
- [x] delete fields without active consumer
- [x] make validators accept only final schemas
- [x] remove activation-hook runner and setup assets if search proves no consumer
- [x] update manifests to exact final file inventory
- [x] update adapter mappings for renamed/deleted skills and rules
- [x] regenerate all derived agent surfaces from canonical sources
- [x] update tests to assert new inventories and reject stale names
- [x] verify no user-local Serena path or config leaks into generated repo files

**Verification:**
- [x] `python scripts/validate_agent_metadata_schema.py`
- [x] `python scripts/validate_prompt_metadata_schema.py`
- [x] `python scripts/sync_agent_adapters.py`
- [x] `python scripts/sync_agent_adapters.py --check`
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1`
- [x] focused adapter/runtime/manifest test set passes

**Exit Criteria:**
- schemas, manifests, generated surfaces, and runtime consumers match final
  canonical inventories

### Task 11: Run Full Verification And Closeout

**Purpose:**
- prove cleanup is complete, smaller, safe, and publishable

**Files:**
- Verify: entire repository
- Update only if evidence requires: `README.md`
- Update: current plan status after all completion gates pass
- Do not update: historical architecture specs/plans

**Preconditions:**
- Tasks 1 through 10 complete
- no unresolved migration or consumer finding remains

**Steps:**
- [x] run stale-reference searches across active surfaces
- [x] run final inventory/count script and compare to Task 1 baseline
- [x] run focused tests for every changed validator and generator boundary
- [x] run full repository tests
- [x] run full repository contract validation
- [x] run starter-kit build and validation
- [x] run publication dry run without push
- [x] run adapter sync/check and drift verification one final time
- [x] inspect `git diff --check`, `git status --short`, and final diff summary
- [x] confirm `.serena/` and `.gitnexus/` remain untracked/private
- [x] record metadata-consumer table and deleted-line/file summary in closeout

**Verification:**
- [x] commands in top-level Verification all pass in fresh runs
- [x] skill count is at most 15
- [x] workflow count equals five
- [x] prompt count excluding README is at most 12
- [x] no full-repo skill activation hook remains
- [x] active architecture-generation references are zero
- [x] public dry run contains no private tooling or operating-system files

**Exit Criteria:**
- every acceptance criterion from parent spec has current evidence and no
  blocker remains

## Verification

Run from repository root after implementation:

```powershell
python scripts/sync_agent_adapters.py --check
powershell -ExecutionPolicy Bypass -File scripts/verify_agent_adapters.ps1
python scripts/validate_agent_metadata_schema.py
python scripts/validate_prompt_metadata_schema.py
python scripts/validate_prompt_ladder.py
python scripts/validate_planning_lifecycle.py
python scripts/validate_repo_contracts.py
python -m pytest
python scripts/build_starter_kit.py
python scripts/validate_starter_kit.py
powershell -ExecutionPolicy Bypass -File scripts/publish_public_repo.ps1
git diff --check
git status --short
```

Also verify external Serena state:

```powershell
serena --version
serena start-mcp-server --context codex --project-from-cwd
```

Repository searches must show no active references outside grandfathered
historical specs/plans:

```powershell
rg -n "sync_architecture_docs|generate_architecture_metadata|audit_architecture_linkage|architecture_dag|capability_lineage|managed_architecture_metadata|architecture_generator|@architecture|@capability|@proves" . --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**' --glob '!.git/**'
rg -n "scripts/hooks/run_validator.py --fast" .agents/skills
```

## Completion Criteria

Plan is complete only when:

1. Serena is installed, configured, and verified in Codex with `no-memories`.
2. one canonical policy owns GitNexus/Serena/native/test/doc responsibilities.
3. inactive architecture-lineage generation is absent from active code, config,
   CI, tests, docs, rules, skills, prompts, workflows, and manifests.
4. historical architecture specs/plans remain unchanged and clearly historical.
5. planning lineage remains functional and independently validated.
6. skill, workflow, and prompt target counts are met.
7. closeout and live-run logic each have one owner.
8. retained metadata fields have named consumers.
9. security, publication, destructive-operation, secret, data-loss, and
   verification invariants remain enforced.
10. all final verification commands pass with fresh evidence.
11. starter-kit and publication dry-run outputs contain no private Serena,
    GitNexus, or operating-system artifacts.
12. parent specification can move from `proposed` only after implementation
    evidence supports its acceptance criteria.
