---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: deepagents-role-ssot-integration
targets:
  - agents
  - scripts/dcode_project.py
  - scripts/setup_deepagents_runtime.ps1
  - docs/operating_system
  - repo_config/starter-kit-manifest.json
  - tests
---

# DeepAgents Role SSOT Integration Plan

## Goal

Reuse canonical `agents/high.toml`, `agents/normal.toml`, and `agents/low.toml`
for Codex and DeepAgents. Keep provider endpoint, credential source, model
binding, generated DeepAgents views, threads, MCP state, and runtime state
outside Git.

Use `native-personal-local` for both executors. Git and plan coordination stay
single-controller and executor-neutral.

## Decisions

- `agents/*.toml` owns only role name, description, and developer instructions.
- `scripts/sync_agent_adapters.py` renders only tracked Codex role TOML.
- `dcode-project` is user-local command wrapper. It resolves current Git
  workspace and runs tracked `scripts/dcode_project.py`.
- Tracked launcher reads active provider and controller model from local Codex
  config, then reads API key from configured local secret file.
- Launcher derives `normal` and `low` from an active `*-high` model. Local
  `[roles]` overrides exist only when provider alias naming differs.
- Launcher regenerates ignored `.deepagents/agents/<role>/AGENTS.md` only for
  a `dcode` run, then removes marker-recorded generated views in `finally`.
  It refuses unowned or modified local content and never deletes it.
- `dcode-project` rejects caller `--model`; controller and delegated tier model
  bindings remain one local configuration decision.
- Launcher supplies canonical and `DEEPAGENTS_CODE_` OpenAI environment names
  only to `dcode` child because its server child requires canonical names.
- Starter ships canonical roles and launcher/install scripts, never `.deepagents`
  runtime state, local provider settings, credentials, or test-only runtime code.

## Implementation Outcomes

- Codex remains adapter-synchronized from canonical role TOML.
- DeepAgents consumes ignored per-workspace role views generated at launch.
- Provider endpoint and API key stay local and are read only by launcher process.
- One local wrapper works across repositories without copied launcher code.
- Starter output contains reusable bootstrap, never personal runtime state.

## Coordination State

- Coordination owner: `single lead controller`
- Branch: `main`
- Base commit: `4631c693fe1db6b8c09d2c2f4bafeb00ab0626c2`
- Active task: `none`
- Last checkpoint: `fresh live delegation and generated-view cleanup verified`
- Expected workspace: `approved DeepAgents SSOT patch; no .deepagents runtime state`
- Next action: `explicit Git disposition`
- Blockers: `none`

Only controller updates this section and task ledger. Git plus this plan own
resume state; Codex and DeepAgents thread IDs remain runtime-local.

## Task Ledger

| Task | State | Executor | Depends On | Evidence |
| --- | --- | --- | --- | --- |
| Remove tracked DeepAgents role views | `completed` | `codex` | none | Adapter mapping and `.deepagents/agents/*` removed; `.deepagents/` ignored; focused sync and contract checks pass. |
| Add native local launcher | `completed` | `codex` | role source | Launcher and installer tests pass; installer writes local config and wrapper only; wrapper invokes tracked launcher source. Marker-recorded role views clean up after success or child-launch failure without deleting unowned files. |
| Align starter and guidance | `completed` | `codex` | launcher | Starter manifest, procedures, runtime surface, root guidance, and tests match local-runtime boundary. |
| Install and prove live delegation | `completed` | `codex` | launcher | Native `dcode` 0.1.55 installed; fresh `normal` task returned `DEEPAGENTS_NORMAL_OK`; usage shows Terra controller and Luna delegated role; process exit removed `.deepagents/`. |

## Task Breakdown

Tasks execute in order: retire tracked DeepAgents views, add user-local launcher,
align portable starter guidance, then prove native normal-tier delegation.

## Implementation Tasks

### Task 1: Retire Tracked DeepAgents Runtime Views

**Files:**

- Delete `adapters/deepagents/mapping.yaml`
- Delete `.deepagents/agents/{high,normal,low}/AGENTS.md`
- Modify `.gitignore`
- Modify `scripts/sync_agent_adapters.py`
- Modify `scripts/validate_generated_header_format.py`
- Modify `scripts/validate_repo_contracts.py`
- Modify focused tests

**Steps:**

1. Remove DeepAgents render mode and mapping from tracked adapter synchronization.
2. Ignore all repository `.deepagents/` content.
3. Remove validators that treat ignored local views as generated tracked output.
4. Preserve canonical role validation: exactly `name`, `description`, and
   `developer_instructions`; reject runtime-owned fields.

**Proof:**

```powershell
py -3 scripts/sync_agent_adapters.py --check --all-platforms
py -3 scripts/validate_generated_header_format.py
py -3 scripts/validate_repo_contracts.py --fast
```

### Task 2: Add Native `dcode-project`

**Files:**

- Add `scripts/dcode_project.py`
- Add `scripts/setup_deepagents_runtime.ps1`
- Add `tests/test_dcode_project.py`

**Steps:**

1. Install DeepAgents Code through `uv tool install --reinstall deepagents-code`.
2. Write user-local `%USERPROFILE%\.local\share\dcode-project\config.toml`
   once, containing only paths to local Codex config and secret file/key name.
3. Install user-local `%USERPROFILE%\.local\bin\dcode-project.{cmd,ps1}`.
4. Resolve current Git workspace in wrapper, then run tracked launcher source.
5. Resolve controller model and provider base URL from active Codex local config.
6. Read secret only in process memory; pass it only to child `dcode` environment.
7. Materialize ignored role views with per-role `model: openai:<local model>`
   only while `dcode` runs; clean up only marker-recorded exact content in
   `finally`.
8. Refuse `--model`, conflicting user `~/.deepagents/config.toml` OpenAI
   `base_url`, and non-empty unowned role directories.

**Proof:**

```powershell
./scripts/setup_deepagents_runtime.ps1 -SecretFile <local-env-file>
dcode-project --print-config
py -3 -m pytest -q tests/test_dcode_project.py
```

### Task 3: Align Portable Starter And Guidance

**Files:**

- Modify `repo_config/starter-kit-manifest.json`
- Modify `README.md`
- Modify `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Modify `docs/operating_system/procedures/runtime-adapter-procedure.md`
- Modify `docs/operating_system/runtime/runtime-surfaces.md`
- Modify `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Modify starter and configuration tests

**Steps:**

1. Ship canonical roles, launcher, installer, and launcher regression test.
2. Forbid the whole `.deepagents` runtime directory from starter output.
3. State that launcher views are ignored local state, never tracked adapter output.
4. State that thread resume uses Git and plan, not `dcode -r`.

**Proof:**

```powershell
py -3 -m pytest -q tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py tests/test_validate_repo_config.py tests/test_validate_repo_contracts.py
py -3 scripts/build_starter_kit.py
py -3 scripts/validate_starter_kit.py
```

### Task 4: Run Fresh Native Live Probe

**Steps:**

1. Run `dcode-project --print-config`; confirm high, normal, low resolve to
   expected provider-local models without displaying secrets.
2. Confirm generated ignored role frontmatter selects `openai:combo-normal` for
   `normal` under active `combo-high` controller.
3. Run bounded non-interactive task through `dcode-project` asking controller
   to delegate to `normal` and return `DEEPAGENTS_NORMAL_OK`.
4. Confirm output shows task invocation, marker, controller model tier, and
   delegated model tier.

**Proof:**

```powershell
dcode-project --no-mcp --json --max-turns 4 --timeout 120 -n "Use the normal project subagent through the task tool. Ask it to return exactly DEEPAGENTS_NORMAL_OK, then return that marker."
```

**Observed August 13, 2026:** marker returned. Usage reported controller
`gpt-5.6-terra` and delegated `gpt-5.6-luna`; this proves `normal`, not `high`,
selected Luna. After exit, `.deepagents/` was absent and Git showed only the
planned deletion of retired tracked role views.

## Verification

- [x] `py -3 -m pytest -q tests/test_dcode_project.py tests/test_sync_agent_adapters.py tests/test_validate_generated_header_format.py tests/test_validate_repo_config.py tests/test_validate_repo_contracts.py tests/test_starter_kit_generation.py tests/test_native_personal_local_workflow.py`
- [x] `py -3 scripts/sync_agent_adapters.py --check --all-platforms`
- [x] `py -3 scripts/validate_generated_header_format.py`
- [x] `py -3 scripts/validate_repo_contracts.py --fast`
- [x] Native `dcode-project` live `normal` delegation probe.
- [x] Full `py -3 -m pytest -q` suite: `97 passed`.
- [x] Starter build, local sibling sync, and parity validation.
- [x] `py -3 scripts/validate_agent_runtime_drift.py --all-platforms` after
  deployed Codex, Claude, and Gemini adapter sync.
- [x] `git diff --check` after final generated sync.

## Completion Criteria

1. Canonical repository role content exists only in `agents/*.toml`.
2. Codex role views remain generated tracked output; DeepAgents role views remain
   ignored local output generated per launch.
3. Current active Codex provider supplies DeepAgents controller endpoint and
   model without WSL gateway or duplicated provider config.
4. Local API key source stays outside repository and only reaches child process.
5. `normal` live delegation uses normal-tier model rather than high-tier model.
6. Starter contains portable runtime bootstrap only, not private DeepAgents state.
7. Git plus plan support fresh-thread controller resume.
