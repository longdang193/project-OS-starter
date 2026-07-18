---
artifact_type: plan
status: completed
layer: change
date: 2026-07-18
---

# MCP Memory And UI/UX Integration Plan

## Goal

Replace repository-file agent memory with official MCP Memory Server, route memory use through relevant rules and skills, and make `ui-ux-pro-max` conditional design method for front-end work without copying its full instructions into repository rules.

## Implementation Outcomes

### Official MCP Memory Server Available In Codex

Codex starts `@modelcontextprotocol/server-memory` through Windows-compatible MCP configuration, stores its knowledge graph at an explicit durable local path, and exposes server tools after restart. Setup documentation provides client-neutral guidance without committing machine-specific paths or memory data.

### Memory Policy Has One Canonical Owner

A canonical agent-memory rule defines when agents fetch, create, update, and delete memory; what must never be stored; how source and tests outrank memory; and how work proceeds when server is unavailable. Root agent instructions summarize routing only. Relevant skills reference rule instead of repository memory files.

### Front-End Work Routes Through `ui-ux-pro-max`

A canonical front-end rule defines trigger conditions, reuse and accessibility requirements, verification expectations, and fallback behavior when `ui-ux-pro-max` is unavailable. Relevant design, planning, coding, and verification skills invoke installed skill conditionally rather than duplicating its detailed checklist.

### Generated And Published Surfaces Stay Consistent

Canonical templates, rule mappings, manifests, generated provider outputs, README material, governance documentation, and validation tests agree on new memory and front-end contracts. Private MCP memory data remains excluded from publication and version control.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-central-config-layer`, `skill-writing-skills`, `skill-private-public-repo-governance`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve all unrelated existing changes
- Parallel ownership: none; adapter mappings and generated outputs are shared surfaces
- Sequential fallback: install and verify server, add canonical rules, update skill routing, migrate memory, regenerate adapters, run final validation

## Task Breakdown

### Task 1: Establish MCP Memory Runtime

**Purpose:**
- Install and verify official MCP Memory Server for Codex with durable local storage.

**Specification Coverage:**
- Official server package only.
- Windows-compatible launch command.
- No committed machine-specific path, credentials, or memory database.

**Required Skills:**
- `skill-central-config-layer`

**Files And Symbols:**
- Inspect: `C:\Users\HOANG PHI LONG DANG\.codex\config.toml:[mcp_servers]`
- Modify: `C:\Users\HOANG PHI LONG DANG\.codex\config.toml:[mcp_servers.memory]`
- Create: `C:\Users\HOANG PHI LONG DANG\.codex\memory\project-os-starter-memory.json` through server initialization only
- Create: `docs/operating_system/procedures/mcp-memory-server-setup.md`
- Verify: active Codex MCP tool list after application restart

**Dependencies:**
- Node.js and `npx` available.
- Preserve existing MCP server entries and local model configuration.

**Steps:**
- [x] Add `[mcp_servers.memory]` using `cmd` with `args = ["/c", "npx", "-y", "@modelcontextprotocol/server-memory"]`.
- [x] Set `MEMORY_FILE_PATH` to explicit durable user-local JSON path under `%USERPROFILE%\.codex\memory\`; do not use repository storage.
- [x] Add short setup procedure containing prerequisites, Codex configuration, restart requirement, smoke test, backup location, uninstall steps, and optional examples for other MCP clients.
- [x] Restart Codex once configuration is saved so new MCP tools can register.
- [x] Run one temporary create/read/delete smoke test through MCP Memory tools; leave no test entity behind.

**Verification:**
- [x] `npx -y @modelcontextprotocol/server-memory --help`
- Expected: package resolves and process starts without package-install failure.
- [x] Fetch MCP tool inventory after restart.
- Expected: memory tools for entities, relations, observations, search, open, and deletion are available.
- [x] Create, retrieve, then delete a temporary entity.
- Expected: round trip succeeds and durable JSON file exists outside repository.

**Exit Criteria:**
- Codex can use official Memory Server and no machine-local memory content enters Git.

### Task 2: Create Canonical Agent-Memory Rule

**Purpose:**
- Give memory behavior one concise canonical policy owner.

**Specification Coverage:**
- Fetch timing, update timing, quality, privacy, precedence, failure fallback, and lifecycle cleanup.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Create: `docs/operating_system/rules/agent-memory-rule.md`
- Modify: active adapter generation ownership in `scripts/sync_agent_adapters.py`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md:Working Expectations`
- Modify: `docs/operating_system/governance/repo-governance.md:Agent Memory`
- Modify: `docs/operating_system/README.md`
- Modify: `README.md:Agent Memory`
- Verify: `.codex/rules/agent-memory.rules` and generated provider rule outputs

**Dependencies:**
- Task 1 server interface and storage boundary confirmed.

**Steps:**
- [x] Define fetch triggers: shared workflows, architecture or publication invariants, resumed work, recurring failures, and high-risk changes.
- [x] Define write triggers: verified reusable decisions, invariants, failure causes, operational constraints, and costly-to-rediscover lessons.
- [x] Ban transient progress, guesses, secrets, credentials, personal data, raw sensitive source content, and facts already obvious from authoritative sources.
- [x] Require narrow project-prefixed entities, atomic observations, source-path evidence where useful, correction of stale facts, and deletion of obsolete entries.
- [x] State precedence: explicit instructions, source, tests, ADRs, and current governance outrank memory.
- [x] State fallback: MCP unavailability never blocks safe source-first work; do not silently recreate repository memory layer.
- [x] Reduce root `AGENTS.md` template to routing-level requirements and remove obsolete directory-definition bullets identified in approved scope.
- [x] Add rule to adapter mappings so provider rule outputs are generated rather than edited directly.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: after regeneration, all mapped memory rule outputs match canonical source.
- [x] `rg -n "docs/operating_system/agent_memory|failure-ledger" AGENTS.md README.md docs .agents repo_config generated_agents`
- Expected: no active instruction points agents to repository-file memory; publication exclusions may retain generic `agent memory` wording.

**Exit Criteria:**
- Memory policy exists once canonically and all root/runtime summaries route to it.

### Task 3: Route Memory Through Relevant Skills

**Purpose:**
- Replace direct file-memory reads with precise MCP Memory actions at existing decision points.

**Specification Coverage:**
- Memory use only where current skills already identify reusable-history value.
- No blanket memory fetch on every task.

**Required Skills:**
- `skill-writing-skills`

**Files And Symbols:**
- Modify: `.agents/skills/skill-systematic-debugging/SKILL.md:Phase 1`
- Modify: `.agents/skills/skill-executing-plans/SKILL.md:Conditional Reads`
- Modify: `.agents/skills/skill-plan-document-reviewer/SKILL.md:Conditional Reads`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md:Conditional Reads`
- Inspect: `.agents/skills/skill-subagent-driven-development/SKILL.md:conversation memory guidance`
- Verify: corresponding `generated_agents/*/skills/` outputs

**Dependencies:**
- Task 2 canonical memory terminology settled.

**Steps:**
- [x] Change debugging flow from reading `failure-ledger.md` to searching MCP memory for similar failure symptoms, causes, and confirmed fixes.
- [x] Make plan execution and plan review fetch memory only for known reusable workflows, invariants, or repeated failure modes.
- [x] Make verification update memory only after a reusable lesson is confirmed by fresh evidence.
- [x] Keep subagent context-pack guidance separate from persistent MCP memory; do not treat memory as task-state synchronization.
- [x] Link skills to canonical rule instead of restating full storage and privacy policy.

**Verification:**
- [x] `rg -n "agent_memory|failure-ledger" .agents/skills generated_agents`
- Expected: no direct repository-file memory dependency remains.
- [x] Run skill validation command documented by `skill-writing-skills` for each changed canonical skill.
- Expected: changed skills retain valid frontmatter and focused workflow scope.

**Exit Criteria:**
- Relevant skills use MCP memory conditionally and consistently.

### Task 4: Add Canonical Front-End Rule

**Purpose:**
- Route significant front-end work through installed `ui-ux-pro-max` while preserving repository-native fallback requirements.

**Specification Coverage:**
- Triggering, design reuse, native controls, accessibility, responsive behavior, theme support, and visual verification.

**Required Skills:**
- `ui-ux-pro-max`
- `skill-writing-skills`

**Files And Symbols:**
- Create: `docs/operating_system/rules/frontend-ui-rule.md`
- Modify: active adapter generation ownership in `scripts/sync_agent_adapters.py`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md:Front-End Work`
- Verify: `.codex/rules/frontend-ui.rules` and generated provider rule outputs

**Dependencies:**
- Installed skill path exists locally: `C:\Users\HOANG PHI LONG DANG\.codex\skills\ui-ux-pro-max\SKILL.md`.

**Steps:**
- [x] Trigger `ui-ux-pro-max` for new screens, substantial restyling, design systems, responsive layout, interaction design, accessibility remediation, or visual critique.
- [x] Skip skill invocation for copy-only edits, mechanical selector changes, or isolated nonvisual front-end logic.
- [x] Require reuse of existing components, tokens, typography, spacing, icon family, and interaction patterns before new design primitives.
- [x] Require semantic/native controls, keyboard use, focus visibility, labels, contrast, reduced motion, responsive layouts, supported themes, and affected-state verification.
- [x] Define fallback when skill is unavailable: follow repository front-end rule and existing product design system; never block safe local fix.
- [x] Keep detailed style catalogs and checklists inside `ui-ux-pro-max`; root and rule files contain routing and invariants only.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: front-end rule exists in each configured provider output.
- [x] Inspect rule and root template for duplicated `ui-ux-pro-max` checklist content.
- Expected: no copied catalog; only triggers, invariants, and fallback remain.

**Exit Criteria:**
- Front-end work has clear skill routing and baseline requirements without making private skill installation a hard repository dependency.

### Task 5: Route UI/UX Through Relevant Skills

**Purpose:**
- Add front-end method selection to existing lifecycle skills at their natural decision points.

**Specification Coverage:**
- Design before implementation, plan-level UI verification, code-level accessibility, and completion evidence.

**Required Skills:**
- `skill-writing-skills`
- `ui-ux-pro-max`

**Files And Symbols:**
- Modify: `.agents/skills/skill-brainstorming/SKILL.md:UI or visual work routing`
- Modify: `.agents/skills/skill-spec-drafting/SKILL.md:design constraints and acceptance criteria`
- Modify: `.agents/skills/skill-writing-plans/SKILL.md:required skills and verification design`
- Modify: `.agents/skills/skill-code-standards/SKILL.md:front-end standards routing`
- Modify: `.agents/skills/skill-verification-before-completion/SKILL.md:UI verification evidence`
- Verify: corresponding `generated_agents/*/skills/` outputs

**Dependencies:**
- Task 4 front-end rule settled.

**Steps:**
- [x] In brainstorming, invoke `ui-ux-pro-max` when visual direction or interaction design is unresolved; keep text-only design questions lightweight.
- [x] In specifications, require explicit responsive, theme, accessibility, and affected-state acceptance criteria when front-end scope exists.
- [x] In plans, name `ui-ux-pro-max` only for tasks that need design judgment and include viewport/theme/accessibility proof.
- [x] In code standards, route to front-end rule rather than embedding another UI checklist.
- [x] In completion verification, require fresh rendered or browser evidence for material visual changes; do not accept source inspection alone.

**Verification:**
- [x] Run changed-skill validation.
- Expected: each skill remains focused and references `ui-ux-pro-max` only at a real lifecycle decision point.
- [x] `rg -n "ui-ux-pro-max" .agents/skills docs/operating_system/rules docs/operating_system/templates generated_agents`
- Expected: references appear only in approved routing surfaces and generated copies.

**Exit Criteria:**
- UI/UX method participates in discovery, specification, planning, coding, and verification without redundant instruction copies.

### Task 6: Migrate And Retire Repository Memory Files

**Purpose:**
- Preserve useful history in MCP memory, then remove obsolete repository-memory ownership.

**Specification Coverage:**
- No data loss, no duplicate source of truth, private-only memory, reversible migration until verified.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Inspect: `docs/operating_system/agent_memory/*.md`
- Modify: MCP Memory graph through its tools
- Delete: `docs/operating_system/agent_memory/` after migration proof
- Modify: `repo_config/starter-kit-manifest.json`
- Modify: `docs/operating_system/publication/public-safe-doc-rewrite-guide.md` only if wording assumes file-backed memory
- Verify: repository search and MCP retrieval

**Dependencies:**
- Tasks 1–3 complete.
- Durable memory file backed up before deleting repository files.

**Steps:**
- [x] Review each existing memory entry; discard obsolete, duplicated, transient, or source-obvious content.
- [x] Create compact project-prefixed MCP entities and atomic observations for remaining verified lessons.
- [x] Retrieve migrated entries by representative search terms and compare meaning against source files.
- [x] Back up MCP JSON file.
- [x] Remove `docs/operating_system/agent_memory/` and its starter-kit manifest entry only after retrieval proof succeeds.
- [x] Keep publication rule generic: MCP memory data and backups are private local state and must never enter public exports.

**Verification:**
- [x] Search MCP memory for every migrated lesson category.
- Expected: each retained lesson is retrievable and accurate.
- [x] `rg -n "docs/operating_system/agent_memory|failure-ledger" . --glob '!generated_exports/**'`
- Expected: zero active references after generated outputs are refreshed.
- [x] `git status --short`
- Expected: no MCP JSON, backup, credential, or machine-specific config path appears in repository changes.

**Exit Criteria:**
- Useful memory survives in MCP; repository file-memory layer and manifest ownership are gone.

### Task 7: Regenerate And Validate Runtime Surfaces

**Purpose:**
- Reconcile canonical edits with all maintained outputs and prove no contract drift.

**Specification Coverage:**
- Generated files are never hand-edited.
- Existing unrelated worktree changes remain intact.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Generate: `AGENTS.md`
- Generate: `.codex/rules/*.rules`
- Generate: `generated_agents/codex/**`
- Generate: `generated_agents/claude/**`
- Generate: `generated_agents/antigravity/**`
- Verify: adapter, repository-contract, and starter-kit validators

**Dependencies:**
- Tasks 2–6 complete.

**Steps:**
- [x] Run adapter sync for all configured platforms.
- [x] Review generated diff for only intended memory, front-end, and root-instruction changes.
- [x] Run adapter drift, repository contract, generated-header, and starter-kit validation.
- [x] Run focused tests for adapter synchronization and changed validators.
- [x] Record any intentional deviation in this plan before completion verification.

**Verification:**
- [x] `python scripts/sync_agent_adapters.py --all-platforms`
- [x] `python scripts/sync_agent_adapters.py --all-platforms --check`
- [x] `python scripts/validate_agent_runtime_drift.py`
- [x] `python scripts/validate_repo_contracts.py`
- [x] `python scripts/validate_generated_header_format.py`
- [x] `python scripts/validate_starter_kit.py`
- [x] `python -m pytest tests/test_sync_agent_adapters.py tests/test_deploy_agent_runtime.py`
- Expected: every command exits successfully; generated outputs show no drift.

**Exit Criteria:**
- Canonical, generated, documented, and runtime surfaces agree.

## Verification

- `python scripts/sync_agent_adapters.py --all-platforms --check`
- `python scripts/validate_agent_runtime_drift.py`
- `python scripts/validate_repo_contracts.py`
- `python scripts/validate_generated_header_format.py`
- `python scripts/validate_starter_kit.py`
- `python -m pytest tests/test_sync_agent_adapters.py tests/test_deploy_agent_runtime.py`
- `rg -n "docs/operating_system/agent_memory|failure-ledger" . --glob '!generated_exports/**'`
- MCP smoke test: create, retrieve, and delete one temporary entity after Codex restart.
- MCP migration test: retrieve every retained historical lesson from durable memory storage.
- UI routing inspection: verify `ui-ux-pro-max` is conditional, front-end invariants are centralized, and detailed skill content is not copied.

## Completion Criteria

1. Official MCP Memory Server runs in Codex with explicit durable local storage.
2. Canonical agent-memory and front-end rules exist and generate provider outputs.
3. Relevant skills route memory and UI/UX work at precise lifecycle points.
4. Useful file-memory entries are migrated, backed up, and retrievable before old files are removed.
5. Root instructions contain concise actionable routing instead of obsolete repository definitions.
6. No secret, memory database, backup, or machine-specific configuration is committed or published.
7. All adapter, contract, starter-kit, focused test, MCP smoke, and migration checks pass.

Plan may be marked `completed` only when `skill-verification-before-completion` runs fresh final verification, reconciles required outcomes against repository evidence, and finds no unresolved required task or unrecorded deviation.

## Execution Notes

- Official Memory Server package resolved at version `2026.7.4`; direct MCP protocol smoke test initialized server, listed nine tools, created three migrated entities, and retrieved them successfully.
- Codex requires restart before newly configured `memory` MCP tools appear in this running task.
- Full `python scripts/validate_agent_runtime_drift.py` reported pre-existing drift in user-global deployed skills and `.codex/AGENTS.md`. No global runtime deployment was performed because it would overwrite unrelated user state. Repository runtime drift passed through `validate_repo_contracts.py`, which invokes the validator with `--skip-deploy-check`.
- Adapter sync removed tracked stale `skill-parallel-execution` generated copies because no canonical skill source exists; all-platform adapter check confirms generated outputs now match current canonical sources.
- Focused tests passed: 29 tests. Pytest emitted a Windows permission warning during temporary-directory cleanup after successful completion; test exit code remained 0.

- Follow-up SSOT refactor on 2026-07-18 moved root `AGENTS.md` generation into `scripts/sync_agent_adapters.py` and retired obsolete adapter-mapping JSON config.
