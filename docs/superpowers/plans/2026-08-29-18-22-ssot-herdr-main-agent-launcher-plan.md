---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: ssot-herdr-main-agent-launcher
targets:
  - scripts/herdr_main_launcher.py
  - tests/test_herdr_main_launcher.py
  - .agents/skills/skill-chief-of-staff/SKILL.md
  - tests/test_skill_chief_of_staff.py
  - repo_config/starter-kit-manifest.json
  - tests/test_starter_kit_generation.py
  - docs/operating_system/runtime/runtime-surfaces.md
  - docs/operating_system/planning/planning-dispatch.md
---

# SSOT Herdr Main-Agent Launcher

## Goal

Provide one registry-driven launch path for independent top-level Codex main
agents inside Herdr. Keep `agents/*.toml` as the only profile contract source,
keep Herdr responsible only for main-agent topology and terminal observability,
and keep executor selection separate from profile selection.

The launcher must resolve the complete runtime contract
`profile -> model_provider + model + developer_instructions`, verify exact
worktree identity, project those values ephemerally into Codex, and print
separate registry/launcher, Git, and Herdr evidence. Missing or mismatched
bindings fail closed. Do not introduce additional Herdr/top-level-Codex
per-profile config files; existing generated Codex delegated-role adapters
remain derived outputs for native subagents. No automatic fallback, native
Codex subagent, DeepAgents worker, Tura worker, or `multi_agent_v1` call belongs
in this change.

## Implementation Outcomes

### Registry-driven Herdr launch

Add one cross-platform Python launcher that accepts a discovered profile,
Herdr session, pane, and required exact worktree identity; loads the selected
profile through `scripts/agent_profile_registry.py`; resolves provider, model,
and developer instructions; and starts one `codex` agent through Herdr using
ephemeral runtime projection. The launcher fails closed when the profile,
registry, Herdr executable, pane, Git identity, or required binding is
unavailable.

### Symmetric verification and documentation

Use identical launch logic for every profile loaded from `agents/*.toml`,
including ranked and explicit-only profiles. Record profile source, executor,
provider, model, instruction digest, redacted projected config shape, and Git identity in
launcher evidence; record agent name/kind, session, pane, lifecycle, startup
screen, and marker output in Herdr evidence. Document ownership boundaries and
the single launch path without creating a second profile authority.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Default task executor: `codex`
- Required skills: `skill-code-standards`, `skill-writing-skills`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing uncommitted changes
- Commit policy: `no commits during execution`; Git disposition requires separate explicit authorization
- Preauthorized local actions: inspect named source and tests; add the declared launcher and focused test; update the declared operating-system docs; run declared local checks; inspect and run one task-owned bounded Herdr probe plus retirement in an existing user-approved disposable pane
- User-approval actions: install or update tools; authenticate; change provider configuration; create or delete Herdr sessions; stop or discard existing panes; delete untracked user data; commit; push; merge; publish
- Parallel ownership: none; registry contract, launcher, tests, docs, and runtime proof have one dependency chain
- Sequential fallback: complete Tasks 1–3 in order, run Task 4 after focused and repository checks pass, then run Task 5 only after generated and Starter checks pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `0c3b6578428901626b168e32c9e5f4003e4f2215`
- Expected workspace: existing tracked changes and tracked historical-plan deletions preserved; existing user untracked `.playwright-mcp/` and `db/` preserved; task-owned `out/` handled only under explicit cleanup authorization
- Next action: none; implementation, validation, live probe, evidence capture, and disposable-pane retirement completed
- Blockers: none
- Runtime note: Herdr 0.8.2 and Codex 0.151.0 resolved; probe pane retired; pre-existing reviewer panes preserved

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | launcher help plus registry-backed dry-run contract | launcher emitted registry/Git/Herdr/Codex evidence; failed-closed tests passed |
| Task 2 | `completed` | current | `codex` | Task 1 | focused launcher tests | focused suite: 24 passed |
| Task 3 | `completed` | current | `codex` | Task 2 | docs and contract validators | repository and planning validators passed |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | canonical skill sync and Starter build/validation | adapter check, fresh Starter build, and Starter validation passed |
| Task 5 | `completed` | current | `codex` | Tasks 1–4 | Herdr agent detection, startup screen, live marker acknowledgement, terminal readback | xhigh-main launched in w1:p7; marker acknowledged; pane retired; reviewer panes preserved |

Each ledger transition records task, state, timestamp, exact command, exit code,
bounded output or output digest, runtime identity, and disposition
`passed|failed|blocked|not-run`. A checked box without this evidence does not
establish completion. Failed, blocked, skipped, and scope-deviating checks stay
recorded; they are not silently omitted.

## Execution Evidence

- Timestamp: 2026-08-29T20:01:04+02:00; branch main; HEAD and expected base 0c3b6578428901626b168e32c9e5f4003e4f2215; exact Git worktree root verified as C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter.
- Runtime discovery: herdr --version returned herdr 0.8.2; codex --version returned codex-cli 0.151.0; codex-probe agent list showed existing cosreview and cosxhigh reviewer agents.
- Launcher command: py -B scripts/herdr_main_launcher.py --profile xhigh --session codex-probe --pane w1:p7 --cwd C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter --expected-base 0c3b6578428901626b168e32c9e5f4003e4f2215 --name xhigh-main; exit 0; resolved agents/xhigh.toml, executor codex, provider 9router, model combo-xhigh, instruction digest 839833239f441151841623ea25252c7e99178749efafdd3cb1f4612758aedc1.
- Herdr runtime: agent get xhigh-main returned agent_kind=codex, session codex-probe, pane w1:p7, matching worktree, and agent_status=idle; agent read with recent-unwrapped source returned exact LIVE_SSO_HERDR_XHIGH_ACK.
- Retirement: herdr --session codex-probe pane close w1:p7 returned ok; final agent list showed only pre-existing cosreview on w1:p4 and cosxhigh on w1:p5.
- Validation: py -m pytest -q returned 287 passed; repository validation returned 58 passed; planning, template, adapter, repo-contract, and git diff --check validations returned exit 0; fresh Starter build and validation returned exit 0.

## Task Breakdown

### Task 1: Add registry-driven Herdr launcher

**Purpose:**
- Start one independent top-level Codex main-agent pane from a canonical repository profile without duplicating profile/runtime configuration.

**Task Function:**
- Resolve and bind one profile to one Herdr Codex pane.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small, deterministic launcher change with direct repository and runtime contracts; no delegated benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and final verification cover the bounded launcher contract.

**Specification Coverage:**
- `agents/*.toml` is the SSOT for profile identity, provider, model, rank, and instructions.
- Executor selection remains independent from profile selection.
- Herdr owns only independent top-level Codex main-agent topology and observability.
- Missing or mismatched profile, provider, model, instruction, Git, pane, or executable binding returns `BLOCKED` or nonzero failure; no fallback.
- All profiles use one symmetric launch path.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:load_agent_profiles`
- Inspect: `agents/*.toml:profile records`
- Inspect: installed `herdr --help`, `herdr agent start --help`, and `codex --help`; unavailable or incompatible runtime syntax is `BLOCKED`.
- Modify: `scripts/herdr_main_launcher.py:main`, `resolve_launch`, `run_launch` (new symbols)
- Verify: `scripts/herdr_main_launcher.py`

**Dependencies:**
- Existing `AgentProfile` loader and Herdr `agent start` command remain available.
- The launch contract includes the exact allocated worktree and expected base commit; the launcher does not create or choose worktrees.
- Herdr executable is resolved from current PATH; no stale absolute path is stored.

**Authority:**
- Preauthorized local actions: add launcher file; read registry and executable help; run dry-run and missing-input checks.
- Stop for: registry schema changes; provider/auth changes; new fallback behavior; direct edits to generated agent surfaces; Herdr session or pane deletion.

**Steps:**
- [x] Step 1: Define required CLI inputs `--profile`, `--session`, `--pane`, `--cwd`, and `--expected-base`, plus optional `--name` and `--dry-run`.
- [x] Step 2: Load selected profile with `load_agent_profiles`, resolve `herdr` and `codex` with `shutil.which`, and reject unknown or unavailable bindings before launch.
- [x] Step 3: Verify absolute `--cwd` is the expected Git worktree, recording repository root, Git common directory, branch, HEAD, expected base, and the Herdr pane cwd before launch.
- [x] Step 4: Build one symmetric Herdr `agent start --kind codex` command that passes verified `--cwd` as Codex `-C` and projects registry-resolved `model_provider`, `model`, and `developer_instructions` through ephemeral Codex `-c` overrides; accept no caller-supplied runtime override.
- [x] Step 5: Print sorted JSON with separate `registry_launcher`, `git`, and `herdr` evidence, including `profile_source`, exact projected Codex config keys, redacted argv/config shape, value digests including `developer_instructions_sha256`, `agent_name`, and `agent_kind`; never print raw developer instructions; propagate Herdr exit status and stderr.

**Verification:**
- [x] `py -B scripts/herdr_main_launcher.py --help`
- Expected: help lists required profile/session/pane inputs and dry-run mode.
- [x] `py -B scripts/herdr_main_launcher.py --profile xhigh --session codex-probe --pane w1:p5 --cwd $PWD --expected-base 0c3b6578428901626b168e32c9e5f4003e4f2215 --dry-run`
- Expected: JSON reports `profile=xhigh`, `executor=codex`, `model_provider=9router`, `model=combo-xhigh`, instruction digest, redacted projected Codex config shape and keys, Git identity, pane cwd, and no process launch.
- [x] Unknown profile and missing Herdr executable checks
- Expected: nonzero exit with actionable failure; no fallback model or alternate executor.

**Exit Criteria:**
- One launcher resolves every profile through the existing registry, projects the complete runtime contract through ephemeral Codex arguments, and emits exact launch facts without duplicate authority.

### Task 2: Add focused launcher contract tests

**Purpose:**
- Prevent profile/runtime-contract drift, fallback behavior, and asymmetric profile handling.

**Task Function:**
- Exercise launcher resolution and failure boundaries with deterministic subprocess seams.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded test authoring; low ambiguity and low runtime risk.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent contract inspection is sufficient; no rank relationship required.

**Specification Coverage:**
- Registry is sole profile/runtime-contract source.
- Every profile discovered from `agents/*.toml` follows same command shape; targeted `xhigh` and `review` checks remain representative regressions.
- Provider, model, developer instructions, and executor cannot be caller-injected or replaced by fallback.
- Launcher propagates runtime failure and does not mutate repository state.

**Required Skills:**
- `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/agent_profile_registry.py:AgentProfile`
- Modify: `tests/test_herdr_main_launcher.py:test_dry_run_uses_registry_model`, `test_profiles_share_launch_shape`, `test_unknown_profile_fails`, `test_herdr_missing_fails` (new symbols)
- Verify: `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`

**Dependencies:**
- Task 1 launcher CLI and pure resolution seam complete.
- Tests use temporary profile files and mocked subprocess/`shutil.which`; no Herdr process, credentials, network, or repository mutation.

**Authority:**
- Preauthorized local actions: add one focused test file and run it.
- Stop for: broad test refactor; new dependency; tests that create persistent runtime artifacts.

**Steps:**
- [x] Step 1: Load all profiles from repository `agents/*.toml` and assert identical command shape for ranked and explicit-only profiles.
- [x] Step 2: Assert targeted `xhigh` and `review` bindings, including provider, model, developer-instruction digest, and default `agent_name`/`agent_kind` fields.
- [x] Step 3: Test unknown profile, missing Herdr or Codex, invalid registry, mismatched Git or pane identity, and Herdr nonzero exit paths.
- [x] Step 4: Assert missing `--cwd` or `--expected-base` is rejected; supplied cwd/base values are mandatory expectations whose mismatches fail Git validation; no caller model, provider, developer-instruction, or executor override can replace registry facts; subprocess receives an argument list without shell reconstruction.

**Verification:**
- [x] `py -m pytest tests/test_herdr_main_launcher.py -q`
- Expected: all focused tests pass without creating persistent files outside pytest temporary storage.

**Exit Criteria:**
- Focused tests fail on profile/runtime-contract drift, fallback, asymmetric launch paths, and missing runtime boundaries.

### Task 3: Document ownership and runtime contract

**Purpose:**
- Make SSOT, executor selection, Herdr topology, and evidence boundaries discoverable without duplicating profile data.

**Task Function:**
- Reconcile operating-system documentation with implemented launcher behavior.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded documentation reconciliation with low implementation ambiguity.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent source-to-doc contract check; no rank relationship required.

**Specification Coverage:**
- `agents/*.toml` remains canonical profile registry.
- `scripts/agent_profile_registry.py` remains canonical loader.
- Herdr manages only independent top-level Codex main-agent sessions.
- Codex, DeepAgents, and Tura executor paths remain distinct.
- Runtime output reports enough identity for transparent observation.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `docs/operating_system/runtime/runtime-surfaces.md:Canonical Sources`, `Policy`
- Inspect: `docs/operating_system/planning/planning-dispatch.md:Executor Selection`, `CoS boundaries`
- Modify: `docs/operating_system/runtime/runtime-surfaces.md:canonical launcher ownership`
- Modify: `docs/operating_system/planning/planning-dispatch.md:Herdr top-level Codex launch rule`
- Verify: `scripts/validate_repo_contracts.py`, `scripts/validate_planning_lifecycle.py`

**Dependencies:**
- Task 1 command contract is fixed and Task 2 focused tests pass.
- Canonical CoS skill and generated adapter ownership remains reserved for Task 4.

**Authority:**
- Preauthorized local actions: edit the two declared canonical docs; run documentation and repository validators.
- Stop for: changes to generated adapters, profile schema, executor behavior, Herdr server behavior, or public documentation.

**Steps:**
- [x] Step 1: Add launcher ownership to runtime surfaces: registry owns profile/provider/model/instructions; launcher resolves and projects; Herdr owns pane/session topology.
- [x] Step 2: Add dispatch rule that CoS may choose Herdr only for independent top-level Codex main agents and may not route DeepAgents, Tura, native subagents, or internal workers through Herdr.
- [x] Step 3: Document separate registry/launcher, Git, Herdr, and Codex evidence fields without copying profile records or creating durable runtime state.

**Verification:**
- [x] `py -B scripts/validate_repo_contracts.py`
- Expected: repository contracts pass.
- [x] `py -B scripts/validate_planning_lifecycle.py`
- Expected: planning lifecycle passes with no stale status or unchecked required evidence introduced.

**Exit Criteria:**
- Documentation names one source for each fact and one symmetric Codex launch path for every registry profile; DeepAgents and Tura executor paths remain separate.

### Task 4: Reconcile CoS skill and Starter packaging

**Purpose:**
- Make the canonical CoS skill use the launcher and ship the launcher through the manifest-driven Starter kit.

**Task Function:**
- Update canonical skill and manifest owners, regenerate derived adapters, and prove package coverage.

**Template Profile:**
- Controller-selected: `normal`
- Selection basis: bounded cross-surface contract update with deterministic generation.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent inspection of canonical ownership, generated parity, and Starter boundaries.

**Specification Coverage:**
- CoS dispatches only independent top-level Codex main agents through one generic launcher.
- CoS never calls `multi_agent_v1`, native Codex subagents, DeepAgents internal workers, Tura workers, or executor-local helpers.
- Existing generated delegated-role adapters remain derived outputs; no additional Herdr/top-level-Codex per-profile config files are introduced.
- Starter packaging includes launcher and focused tests without shipping forbidden adapter-regeneration or runtime-bundle surfaces.

**Required Skills:**
- `skill-writing-skills`, `skill-code-standards`

**Files And Symbols:**
- Modify canonical: `.agents/skills/skill-chief-of-staff/SKILL.md`
- Regenerate only: `generated_agents/codex/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/claude/skills/skill-chief-of-staff/SKILL.md`, `generated_agents/antigravity/skills/skill-chief-of-staff/SKILL.md`
- Modify: `repo_config/starter-kit-manifest.json`, `tests/test_starter_kit_generation.py`, `tests/test_skill_chief_of_staff.py`
- Verify: `scripts/sync_agent_adapters.py`, `scripts/build_starter_kit.py`, `scripts/validate_starter_kit.py`

**Dependencies:**
- Tasks 1–3 pass; launcher runtime contract is fixed before skill wording or manifest entries change.

**Authority:**
- Preauthorized local actions: edit canonical skill and manifest; run adapter sync, Starter tests, and temporary-output build/validation.
- Stop for: direct generated-file edits, public-surface changes, provider/auth changes, or runtime-resource mutation.

**Steps:**
- [x] Step 1: State in canonical CoS skill that launcher resolves the complete registry contract and Herdr owns only independent top-level Codex session/pane lifecycle.
- [x] Step 2: State separate registry/launcher, Git, Herdr, and Codex evidence requirements plus fail-closed mismatch handling.
- [x] Step 3: Run `py -B scripts/sync_agent_adapters.py --all-platforms` and verify generated CoS adapters match canonical source without manual edits.
- [x] Step 4: Add `scripts/herdr_main_launcher.py`, `tests/test_herdr_main_launcher.py`, and `tests/test_skill_chief_of_staff.py` to manifest `copyPaths`; add launcher to `requiredPaths`; preserve forbidden and omitted runtime surfaces.
- [x] Step 5: Extend `tests/test_starter_kit_generation.py` to assert manifest coverage, built launcher/test presence, and Starter validation success.

**Verification:**
- [x] `py -m pytest tests/test_starter_kit_generation.py -q`
- Expected: manifest, build, forbidden-path, and required-path checks pass using temporary output trees.
- [x] `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- Expected: generated adapters match canonical sources.
- [x] `$kitParent = Join-Path $env:TEMP 'project-os-starter-kit-plan'`
- [x] `py -B scripts/build_starter_kit.py --output-root $kitParent`
- Expected: manifest builds launcher, registry dependency, consumer skill, and focused tests into temporary output.
- [x] `py -B scripts/validate_starter_kit.py --output-root $kitParent`
- Expected: Starter output passes without adding forbidden generated/runtime surfaces.

**Exit Criteria:**
- Canonical CoS, generated adapters, and Starter manifest describe one launcher path and one profile authority.

### Task 5: Run bounded live Herdr proof

**Purpose:**
- Prove the launcher starts a visible top-level Codex agent and Herdr exposes identity, lifecycle, startup readiness, and output.

**Task Function:**
- Capture direct runtime boundary and terminal evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime control and acceptance remain with native Codex controller.

**Validator Profile:**
- Controller-selected: `review`
- Selection basis: independent read-only observation; no rank relationship required.

**Specification Coverage:**
- Herdr owns main-agent topology.
- Executor selection resolves Codex.
- `agents/xhigh.toml` resolves to `9router` and `combo-xhigh` with its instruction surface.
- Exact worktree and pane cwd remain bound through startup.
- Live output is visible in the managed pane.
- No nested Herdr client, native subagent, DeepAgents worker, Tura worker, or executor-local helper is used.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `agents/xhigh.toml`
- Inspect: `scripts/herdr_main_launcher.py` preflight and runtime output
- Verify: `herdr --session codex-probe agent list`, `herdr --session codex-probe agent get xhigh-main`, `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`, `codex --version`, `herdr --version`
- Record: plan Coordination State Evidence column and final Verification section

**Dependencies:**
- Tasks 1–4 pass.
- Existing `codex-probe` session is running and contains a user-approved disposable pane; otherwise stop and request approval before creating one.

**Authority:**
- Preauthorized local actions: inspect existing session/panes, launch one task-owned bounded top-level agent in an approved empty pane, send one read-only marker prompt, wait, read output, inspect state, and retire only that task-owned agent after evidence capture.
- Stop for: nested Herdr error; missing session/pane; pane cwd mismatch; unexpected provider/model/instructions; startup not ready; any write-capable prompt; need to create/delete/stop unrelated or pre-existing runtime resources. Task-owned agent retirement remains permitted after evidence capture.

**Steps:**
- [x] Step 1: From external PowerShell, run `herdr --session codex-probe agent list`, select an available pane, record `$pane` and exact `$worktree`, and confirm session/pane ownership, no conflicting agent or unrelated process, and pane cwd equals `$worktree`.
- [x] Step 2: Run `py -B scripts/herdr_main_launcher.py --profile xhigh --session codex-probe --pane $pane --cwd $worktree --expected-base 0c3b6578428901626b168e32c9e5f4003e4f2215 --name xhigh-main`; capture registry/launcher, Git, and Herdr evidence plus exit code.
- [x] Step 3: Run `herdr --session codex-probe agent get xhigh-main`; confirm `agent_name=xhigh-main`, `agent_kind=codex`, matching session/pane/cwd, lifecycle, and visible startup readiness; reject hook-trust, login, approval, first-run, and unknown interactive blockers before sending any marker; compare launcher projected provider/model/instruction digests and redacted Codex argv/config keys separately; record `codex --version` and `herdr --version`.
- [x] Step 4: Send marker `LIVE_SSO_HERDR_XHIGH_2026-08-29` with read-only instructions; wait for `LIVE_SSO_HERDR_XHIGH_ACK`; read recent unwrapped output.
- [x] Step 5: Record exact commands, returned facts, exit codes, startup evidence, and output marker in plan evidence; transition ledger state only after evidence is written.
- [x] Step 6: Invoke provider-resolved Herdr retire/stop for task-owned `xhigh-main` only, then verify no live process owns `$worktree`; never stop or discard unrelated sessions, panes, or processes.

**Verification:**
- [x] `herdr --session codex-probe agent list`
- Expected: named `xhigh-main` appears as `agent_kind=codex` with a live pane ID and matching cwd.
- [x] `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`
- Expected: output contains exact acknowledgement marker.
- [x] `git status --short`
- Expected: only declared tracked implementation/doc/test changes and pre-existing user files remain.

**Exit Criteria:**
- Direct Herdr evidence proves session, pane, agent identity, lifecycle, startup readiness, cwd, and terminal output; combined registry/launcher, Git, and Codex evidence proves profile, complete runtime contract, executor, and worktree binding with no hidden fallback, followed by task-owned retirement proof.

## Verification

- `py -m pytest tests/test_herdr_main_launcher.py -q`
- `py -m pytest tests/test_starter_kit_generation.py tests/test_skill_chief_of_staff.py -q`
- `py -B scripts/validate_repo_contracts.py`
- `py -B scripts/validate_planning_lifecycle.py`
- `py -B scripts/validate_template_required_sections.py`
- `py -B scripts/sync_agent_adapters.py --all-platforms --check`
- `$kitParent = Join-Path $env:TEMP 'project-os-starter-kit-plan'`
- `py -B scripts/build_starter_kit.py --output-root $kitParent`
- `py -B scripts/validate_starter_kit.py --output-root $kitParent`
- `git diff --check`
- `herdr --session codex-probe agent list`
- `herdr --session codex-probe agent read xhigh-main --source recent-unwrapped --lines 30`

Expected final state: focused tests pass; repository, planning, template,
Starter, and adapter checks pass; Herdr shows `xhigh-main` as a `codex` agent;
terminal readback contains `LIVE_SSO_HERDR_XHIGH_ACK`; separate evidence binds
registry/launcher facts to Git, Codex, and Herdr facts; no unapproved files,
runtime resources, provider settings, or Git disposition changes occur.

## Completion Criteria

The plan is ready for completion verification when:

1. `agents/*.toml` remains the only profile/runtime-contract source.
2. One launcher handles ranked and explicit-only profiles with identical logic.
3. Herdr receives only resolved Codex launch facts and owns only top-level pane/session lifecycle.
4. Missing profile, missing Herdr, invalid registry, and runtime failure paths fail closed.
5. Focused tests prove registry binding, symmetry, no fallback, and error propagation.
6. Operating-system docs state the same ownership boundaries without copied profile data.
7. Fresh live Herdr evidence proves visible agent identity, lifecycle, startup readiness, and output; registry/launcher, Git, and Codex evidence proves complete binding.
8. Plan ledger transitions and evidence contain exact commands and outputs; checked boxes alone do not establish completion.
9. No commit, push, merge, cleanup, or session deletion occurs without separate explicit authorization.
