---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: deepagents-role-ssot-integration
targets:
  - agents
  - adapters
  - .deepagents
  - scripts/sync_agent_adapters.py
  - docs/operating_system
  - repo_config/starter-kit-manifest.json
  - tests
---

# DeepAgents Role SSOT Integration Plan

## Goal

Make `agents/high.toml`, `agents/normal.toml`, and `agents/low.toml` the only
repository-owned delegated-role definitions for Codex and DeepAgents while
keeping primary-agent profiles, provider configuration, credentials, execution
state, MCP configuration, and thread state runtime-local.

Preserve `native-personal-local` as the single workspace, scope, verification,
and Git-disposition procedure. Codex and DeepAgents differ only by selected
local executor and runtime-native delegated-role syntax.

## Implementation Outcomes

### Shared Role Source

`agents/*.toml` owns delegated-role name, description, and developer
instructions. Parseable Codex delegated-agent TOML and DeepAgents project
subagent prompts are generated from that source. No runtime-specific role
content is maintained manually.

### Symmetric Executor Procedure

The native personal-local procedure and implementation-plan template support
`codex` and `deepagents` without separate lifecycle, workspace, task-contract,
verification, or branch-finishing systems. Executor selection does not convert
the shared delegated roles into a DeepAgents primary `dcode --agent` profile.

### Single-Controller Resume

One lead controller owns coordination-state updates. Git owns implementation
state and checkpoint commits; this plan owns task state, dependencies, last
verified checkpoint, and next action. A new Codex or DeepAgents thread resumes
by reconciling the plan with Git rather than depending on prior thread state.

### Portable Starter Output

Starter-kit output includes shared role sources and generated DeepAgents agent
views, while excluding DeepAgents provider configuration, credentials, MCP
configuration, hooks, memories, threads, and other mutable user state.

### Fresh Runtime Proof

Automated checks prove generated parity, syntax validity, and drift detection.
Installed DeepAgents Code in WSL loads `low`, `normal`, and `high` as project
subagents from generated files without copying primary-agent profiles into
`~/.deepagents`. A bounded live delegation probe proves one generated role only
when a working user-local DeepAgents provider/model binding is available.

## Execution Approach

- Mode: `inline sequential`
- Executor: `codex`
- Controller: `single lead controller`
- Required skills: `skill-code-standards`, `skill-test-driven-development`
- Isolation: `current workspace`
- Commit policy: `checkpoint commits authorized after each completed task and task-local proof; no push during execution`
- Parallel ownership: `none`
- Sequential fallback: `complete canonical renderer before docs, kit, and runtime proof`

Execution must preserve and incorporate the current uncommitted role-template
restoration under `agents/`, its Codex mapping, starter-kit manifest changes,
runtime-adapter documentation, and focused tests. Do not overwrite or discard
those changes as stale work.

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `10a49a23332a4c24eddbd46a61d4281f2c1fb573`
- Active task: `none`
- Last checkpoint: `this checkpoint commit`
- Expected workspace: `clean approved role integration after this checkpoint commit`
- Next action: `choose branch disposition`
- Blockers: `none`

Only the lead controller updates this section and the task ledger. Codex or
DeepAgents workers may return task results, but they do not change task state,
select the next task, commit, push, merge, or alter scope unless the lead
controller explicitly delegates that exact action.

This plan is the controller-owned coordination write path for every task.
Task workers own only their listed implementation files. After task-local proof,
the lead controller may update this plan's coordination state and ledger in the
same checkpoint commit without treating that controller-only update as worker
scope expansion.

### Expected Uncommitted Paths At Plan Creation

- `agents/high.toml`
- `agents/normal.toml`
- `agents/low.toml`
- `adapters/codex/mapping.yaml`
- `generated_agents/codex/agents/high.toml`
- `generated_agents/codex/agents/normal.toml`
- `generated_agents/codex/agents/low.toml`
- `docs/operating_system/procedures/runtime-adapter-procedure.md`
- `repo_config/starter-kit-manifest.json`
- `tests/test_sync_agent_adapters.py`
- `tests/test_deploy_agent_runtime.py`
- `tests/test_starter_kit_generation.py`
- `docs/superpowers/plans/2026-08-12-21-32-deepagents-role-ssot-integration-plan.md`

### Task Ledger

| Task | State | Executor | Depends On | Checkpoint | Evidence |
| --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | `codex` | none | none | focused sync, config, and header tests; all-platform sync check; header validator |
| Task 2 | `completed` | `codex` | Task 1 | none | focused docs and template tests; full adapter sync check; fresh-shell resume audit |
| Task 3 | `completed` | `codex` | Task 2 | none | starter tests; build, validate, sync, and sibling parity proof |
| Task 4 | `completed` | `codex` | Tasks 1-3 | this commit | Codex deploy, TOML parse, and normal-role probe pass; DeepAgents loader resolved all project roles with no model override; live `task` trace selected `normal` and returned `DEEPAGENTS_ROLE_OK`; no user-home role views created; 92 tests and required repository, adapter, starter, and diff checks pass |

Allowed task states are `pending`, `active`, `blocked`, and `completed`. Exactly
one task may be `active`. A task becomes `completed` only after its task-local
checks pass, changed paths match its declared scope, the lead controller updates
this ledger, and the same checkpoint commit records implementation plus ledger
state. Push remains a separate explicitly authorized branch-finishing action.

### New-Thread Resume Audit

A new lead-controller thread must perform this sequence before implementation:

1. read `AGENTS.md` and this plan
2. confirm repository root, branch, `HEAD`, status, and worktree identity
3. compare `HEAD` with `Last checkpoint`
4. compare staged, unstaged, and untracked paths with expected plan state
5. confirm no task other than the recorded active task has uncheckpointed work
6. reconcile any mismatch as `plan stale`, `Git ahead`, `Git behind`, or
   `unexpected workspace change`; block implementation until resolved
7. continue the recorded active task, or first pending task whose dependencies
   are completed, and update coordination state before dispatch

DeepAgents `dcode -r` and Codex thread continuity are optional conveniences.
Neither is coordination evidence and no thread ID is stored in the repository.

## Task Breakdown

### Task 1: Generate Parseable Runtime Role Views

**Purpose:**
- Generate valid Codex and DeepAgents delegated-role views through the existing adapter sync path.

**Specification Coverage:**
- `agents/*.toml` remains role SSOT.
- DeepAgents output contains no provider, model, endpoint, credential, MCP, or mutable state fields.
- Codex and DeepAgents consume equivalent role semantics through runtime-native syntax.
- Generated Codex files remain valid TOML; generated DeepAgents files start with required YAML frontmatter.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `scripts/sync_agent_adapters.py:Mapping`
- Modify: `scripts/sync_agent_adapters.py:_load_mapping`
- Add: `scripts/sync_agent_adapters.py:_render_codex_agent`
- Add: `scripts/sync_agent_adapters.py:_render_deepagents_agent`
- Add: `scripts/sync_agent_adapters.py:_expected_codex_agent_paths`
- Add: `scripts/sync_agent_adapters.py:_expected_deepagents_agent_paths`
- Add: `scripts/sync_agent_adapters.py:_sync_codex_agents_tree`
- Add: `scripts/sync_agent_adapters.py:_sync_deepagents_agents_tree`
- Modify: `scripts/sync_agent_adapters.py:run`
- Modify: `adapters/codex/mapping.yaml`
- Add: `adapters/deepagents/mapping.yaml`
- Regenerate: `generated_agents/codex/agents/high.toml`
- Regenerate: `generated_agents/codex/agents/normal.toml`
- Regenerate: `generated_agents/codex/agents/low.toml`
- Add generated: `.deepagents/agents/high/AGENTS.md`
- Add generated: `.deepagents/agents/normal/AGENTS.md`
- Add generated: `.deepagents/agents/low/AGENTS.md`
- Modify: `.gitignore`
- Modify: `scripts/validate_generated_header_format.py`
- Modify: `tests/test_sync_agent_adapters.py`
- Add: `tests/test_validate_generated_header_format.py`
- Modify: `tests/test_validate_repo_config.py:test_deepagents_project_agents_are_tracked_but_local_state_is_ignored`

**Dependencies:**
- Current `agents/high.toml`, `agents/normal.toml`, and `agents/low.toml` restoration remains intact.
- Existing generated Codex role files contain an HTML header and fail `tomllib`; Task 1 must replace that invalid output rather than preserve it.

**Steps:**
- [ ] Add mapping modes `render_codex_agents_tree` and `render_deepagents_agents_tree`; keep existing mapping schema and dispatch loop instead of adding another sync command.
- [ ] Parse every matched source file once with Python `tomllib`; require non-empty string values for `name`, `description`, and `developer_instructions`.
- [ ] Reject source filename/name mismatch and reject runtime-owned keys `model`, `model_provider`, `model_reasoning_effort`, `base_url`, `api_key`, and `model_providers`.
- [ ] Render `generated_agents/codex/agents/<name>.toml` with TOML-safe `#` provenance comments followed by canonical role fields; verify every generated and deployed file with `tomllib`.
- [ ] Render `.deepagents/agents/<name>/AGENTS.md` with `---` at byte zero, YAML frontmatter containing `name` and folded `description`, standard generated-file HTML provenance after frontmatter, then exact normalized `developer_instructions`.
- [ ] Update generated-header validation to scan both `generated_agents/**` and tracked `.deepagents/agents/*/AGENTS.md`, accept canonical TOML comment headers, and retain existing Markdown/frontmatter and JSON checks.
- [ ] Calculate transformed expected paths so sync check and stale-file cleanup operate on flat Codex TOML files and nested DeepAgents agent directories.
- [ ] Register `adapters/deepagents/mapping.yaml` so `--all-platforms` includes DeepAgents while default sync remains Codex-only.
- [ ] Ignore `.deepagents/*` except `.deepagents/agents/**`; do not allow project `config.toml`, `.env`, `.mcp.json`, `hooks.json`, memory, thread, or state files into Git.
- [ ] Add focused tests for TOML parsing, DeepAgents frontmatter position, source validation, check-mode drift, stale generated agent removal, generated-header validation, and `.deepagents` ignore exceptions.

**Verification:**
- [ ] `py -3 -m pytest tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py tests/test_validate_repo_config.py -q`
- Expected: both generated formats parse, preserve identical semantic fields, reject forbidden role keys, and enforce project `.deepagents` boundary.
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: no generated drift after synchronization.
- [ ] `py -3 scripts/validate_generated_header_format.py`
- Expected: TOML, Markdown, and existing generated surfaces use their canonical provenance form.

**Exit Criteria:**
- One edit to `agents/normal.toml` changes both generated Codex and DeepAgents normal-role outputs after one adapter sync.
- Every generated and deployed Codex role file parses with `tomllib`.
- Every generated DeepAgents role file loads as a project subagent and keeps frontmatter at byte zero.
- No DeepAgents generated file contains runtime provider or secret-bearing fields.

### Task 2: Make Native Procedure Executor-Symmetric

**Purpose:**
- Reuse the existing native task contract and Git workflow for either local executor.

**Specification Coverage:**
- Git remains workspace and change-evidence SSOT.
- Plan remains task objective, paths, checks, isolation, and approval SSOT.
- Executor selection adds no authority and creates no new lifecycle or state registry.
- One controller owns task transitions and checkpoint reconciliation.
- Fresh threads resume from plan plus Git without runtime-session identity.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md:Start`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md:Check And Review`
- Modify: `docs/operating_system/templates/implementation-plan-template.md:Execution Approach`
- Add: `docs/operating_system/templates/implementation-plan-template.md:Coordination State`
- Modify: `docs/operating_system/procedures/runtime-adapter-procedure.md:Contract`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:Generated Runtime Outputs`
- Modify canonical: `docs/operating_system/templates/agents/root-AGENTS.template.md:Native Personal-Local Work`
- Modify: `README.md:Native Personal-Local Work`
- Generated: `AGENTS.md`
- Modify: `tests/test_native_personal_local_workflow.py`
- Modify: `tests/test_validate_template_required_sections.py`
- Add: `tests/test_native_personal_local_workflow.py:test_single_controller_resume_contract`

**Dependencies:**
- Task 1 establishes parseable Codex roles and generated DeepAgents project-subagent loading.

**Steps:**
- [ ] Replace Codex-only executor wording with `selected local executor: Codex or DeepAgents` while preserving all current workspace, scope, evidence, block, verification, and Git-disposition rules.
- [ ] Add optional plan line `Executor: codex | deepagents`; state that it selects runtime only and grants no permissions.
- [ ] Add optional single-controller coordination section to the implementation-plan template with branch, base commit, active task, last checkpoint, expected workspace, next action, blockers, and task ledger.
- [ ] Define only four task states: `pending`, `active`, `blocked`, and `completed`; prohibit multiple active tasks.
- [ ] Require completed-task checkpoint commits to include task changes and ledger update after task-local proof; keep push under separate explicit authorization.
- [ ] Add the seven-step new-thread resume audit from this plan to the native procedure, with mismatch blocking before implementation.
- [ ] State that DeepAgents thread IDs, Codex thread IDs, and `dcode -r` never become repository coordination state.
- [ ] Document that Codex loads generated delegated-agent TOML while DeepAgents loads generated project subagents; both inherit provider/model selection from their active user-local primary runtime because generated roles contain no model binding.
- [ ] State that DeepAgents `dcode --agent` primary profiles, mutable state, and secrets remain under user-local `~/.deepagents`; project `.deepagents` owns generated project-subagent prompts only.
- [ ] Update README and runtime-surface inventory so starter guidance names both executors and distinguishes DeepAgents primary profiles from project subagents.
- [ ] Regenerate root agent guidance through the existing adapter sync.
- [ ] Add assertions that native procedure supports both executors and retains explicit Git authorization boundaries.

**Verification:**
- [ ] `py -3 -m pytest tests/test_native_personal_local_workflow.py tests/test_validate_template_required_sections.py -q`
- Expected: both executor wording and existing native safety gates pass.
- [ ] Start a fresh shell process and manually perform documented seven-step resume audit using only this plan and Git state; record reconciled task, checkpoint, workspace result, and any block in task handoff or ledger evidence.
- Expected: controller identifies recorded active task or first dependency-ready pending task without prior thread data; any plan/Git mismatch blocks before implementation. No coordinator parser or new state service is added.
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: root and runtime guidance are synchronized.

**Exit Criteria:**
- No separate DeepAgents mode, controller, task schema, worktree procedure, verification path, or branch-finishing path exists.
- Existing procedure remains valid when executor field is absent; Codex stays default.
- One-controller coordination survives a new thread through Git checkpoint and plan ledger only.

### Task 3: Ship Only Portable DeepAgents Project Inputs

**Purpose:**
- Make fresh starter clones immediately expose shared DeepAgents roles without shipping personal runtime state.

**Specification Coverage:**
- Starter output contains shared TOML role sources and generated DeepAgents views.
- User-local provider configuration remains outside repository and starter output.

**Required Skills:**
- `skill-private-public-repo-governance`

**Files And Symbols:**
- Modify: `repo_config/starter-kit-manifest.json:copyPaths`
- Modify: `repo_config/starter-kit-manifest.json:requiredPaths`
- Modify: `repo_config/starter-kit-manifest.json:forbiddenPaths`
- Modify: `scripts/validate_starter_kit.py`
- Modify: `tests/test_starter_kit_generation.py`
- Generated: `generated_exports/project-OS-starter-kit/`
- Synced local kit: `C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit`

**Dependencies:**
- Tasks 1 and 2 complete.

**Steps:**
- [ ] Keep `agents/` in starter copy and required paths.
- [ ] Add `.deepagents/agents` to starter copy and require all three generated `AGENTS.md` files.
- [ ] Forbid `.deepagents/config.toml`, `.deepagents/.env`, `.deepagents/.mcp.json`, `.deepagents/hooks.json`, and `.deepagents/.state` in starter output.
- [ ] Add starter tests proving allowed generated agent files ship and forbidden personal files fail validation.
- [ ] Rebuild and synchronize the local starter-kit checkout only through existing kit scripts.

**Verification:**
- [ ] `py -3 -m pytest tests/test_starter_kit_generation.py tests/test_validate_repo_config.py -q`
- Expected: portable role files ship; personal DeepAgents files remain forbidden.
- [ ] `py -3 scripts/build_starter_kit.py`
- [ ] `py -3 scripts/validate_starter_kit.py`
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/sync_local_starter_kit_repo.ps1`
- Expected: generated and local kit trees match.

**Exit Criteria:**
- Fresh starter clone contains role SSOT and DeepAgents project agent views without any personal provider or state file.

### Task 4: Prove Codex Deployment And DeepAgents Project Loading

**Purpose:**
- Verify Codex consumes parseable deployed roles and DeepAgents consumes project subagents while retaining separate user-local primary profiles and provider configuration.

**Specification Coverage:**
- One source change has symmetric runtime-visible effect.
- No Windows-to-WSL deployment bridge or `~/.deepagents` role copy exists.
- `dcode agents list` is not project-subagent proof and is not used as acceptance evidence.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: `generated_agents/codex/agents/*.toml`
- Verify: `C:\Users\HOANG PHI LONG DANG\.codex\agents\*.toml`
- Verify: `.deepagents/agents/*/AGENTS.md`
- Verify installed WSL command: `/home/longdang193/.local/bin/dcode`

**Dependencies:**
- Tasks 1 through 3 complete.
- DeepAgents Code remains installed in WSL Ubuntu.
- A working user-local DeepAgents provider/model binding is available for the final live delegation probe. If unavailable, loader proof may pass but this task remains blocked; repository files must not add fallback bindings or credentials.

**Steps:**
- [x] Run full adapter synchronization and deploy Codex runtime through existing scripts.
- [x] Run runtime drift validation; do not add DeepAgents home deployment because project discovery owns its generated role views.
- [x] Parse all generated and deployed Codex role TOML, then dispatch one bounded read-only Codex `normal` subagent probe through the platform agent-type selector and record its success marker.
- [x] From repository root in WSL, call installed `deepagents_code.subagents.list_subagents` with `.deepagents/agents`; assert names are `high`, `low`, and `normal`, every source is `project`, every model is `None`, and `system_prompt` bodies match normalized canonical developer instructions.
- [x] Record current absence for user-home `~/.deepagents/{high,normal,low}/AGENTS.md`. No role profile was created by sync, deployment, loader, or blocked preflight. Repeat before/after comparison around a successful delegation probe after user-local provider setup.
- [x] Run one bounded non-interactive `dcode --json` task that explicitly delegates through `normal` project subagent; stored task trace confirms `task` selected `normal` and returned `DEEPAGENTS_ROLE_OK`. Provider binding remains user-local.
- [x] Run repository contracts and focused test suite, then inspect Git diff and untracked files against approved paths.
- [x] Repeat manual new-thread resume audit in a fresh PowerShell process; Git `HEAD`, plan base, expected paths, active task, and uncommitted approved scope reconcile without Codex or DeepAgents thread state.

**Verification:**
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms`
- [ ] `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- [ ] `py -3 scripts/deploy_agent_runtime.py --target codex --force`
- [ ] `py -3 scripts/validate_agent_runtime_drift.py`
- [ ] `py -3 -c "import pathlib,tomllib; paths=[*pathlib.Path('generated_agents/codex/agents').glob('*.toml'),*pathlib.Path.home().joinpath('.codex/agents').glob('*.toml')]; assert len(paths) == 6; [tomllib.load(path.open('rb')) for path in paths]"`
- Expected: three generated and three deployed Codex role files parse successfully.
- [ ] `wsl -d Ubuntu -- bash -lc 'cd "/mnt/c/Users/HOANG PHI LONG DANG/repos/project-OS-starter" && ~/.local/share/uv/tools/deepagents-code/bin/python -c "from pathlib import Path; from deepagents_code.subagents import list_subagents; agents=list_subagents(project_agents_dir=Path(\".deepagents/agents\")); assert {agent[\"name\"] for agent in agents} == {\"high\",\"low\",\"normal\"}; assert all(agent[\"source\"] == \"project\" and agent[\"model\"] is None for agent in agents)"'`
- Expected: installed DeepAgents loader resolves all three repository project subagents without model overrides.
- [ ] `wsl -d Ubuntu -- bash -lc 'cd "/mnt/c/Users/HOANG PHI LONG DANG/repos/project-OS-starter" && ~/.local/bin/dcode --json --no-mcp --max-turns 4 --timeout 120 -n "Use the normal project subagent through the task tool. Ask it to return exactly DEEPAGENTS_ROLE_OK, then return that marker."'`
- Expected: JSON records a `task` tool call selecting `normal` and final marker `DEEPAGENTS_ROLE_OK`; provider details remain user-local and are not copied into repository evidence.
- [ ] `py -3 -m pytest tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py tests/test_deploy_agent_runtime.py tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py tests/test_validate_template_required_sections.py tests/test_validate_repo_config.py -q`
- [ ] `py -3 scripts/validate_repo_contracts.py`
- [ ] `git diff --check`

**Exit Criteria:**
- Codex runtime drift passes.
- Generated and deployed Codex roles parse and one Codex delegated-role probe succeeds.
- DeepAgents project loader resolves all three roles and one live `normal` delegation probe succeeds.
- Repository scripts write no DeepAgents provider, credential, MCP, hook, memory, thread, or state file.
- Manual fresh-thread recovery identifies same task and checkpoint using only Git and this plan.
- All required checks pass with no out-of-scope changes.

## Verification

- `py -3 -m pytest tests -q`
- `py -3 scripts/validate_repo_contracts.py`
- `py -3 scripts/sync_agent_adapters.py --all-platforms --check`
- `py -3 scripts/validate_generated_header_format.py`
- `py -3 scripts/validate_agent_runtime_drift.py`
- `py -3 scripts/validate_starter_kit.py --compare-kit-root "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter-kit"`
- `py -3 -c "import pathlib,tomllib; paths=[*pathlib.Path('generated_agents/codex/agents').glob('*.toml'),*pathlib.Path.home().joinpath('.codex/agents').glob('*.toml')]; assert len(paths) == 6; [tomllib.load(path.open('rb')) for path in paths]"`
- `wsl -d Ubuntu -- bash -lc 'cd "/mnt/c/Users/HOANG PHI LONG DANG/repos/project-OS-starter" && ~/.local/share/uv/tools/deepagents-code/bin/python -c "from pathlib import Path; from deepagents_code.subagents import list_subagents; agents=list_subagents(project_agents_dir=Path(\".deepagents/agents\")); assert {agent[\"name\"] for agent in agents} == {\"high\",\"low\",\"normal\"}; assert all(agent[\"source\"] == \"project\" and agent[\"model\"] is None for agent in agents)"'`
- Bounded Codex `normal` subagent probe and bounded DeepAgents `normal` project-subagent probe recorded in task evidence.
- `git diff --check`

## Completion Criteria

The plan is ready for completion verification when:

1. `agents/*.toml` is the only maintained repository role definition
2. Codex and DeepAgents generated delegated-role views parse and match source semantics
3. native procedure and plan template differ only by executor selection
4. starter output contains portable role inputs and no personal DeepAgents state
5. Codex deployment, DeepAgents project-subagent loading, and one bounded live delegation probe per runtime pass
6. existing uncommitted role-template restoration is reconciled rather than discarded
7. single-controller task state and checkpoint commits can be manually reconciled in a fresh thread without runtime-session data or a new coordinator service
8. all focused and full verification commands pass

The plan may be marked `completed` only after
`skill-verification-before-completion` runs fresh final proof, reconciles every
task and deviation, and returns `verified`.
