---
artifact_type: plan
template_id: implementation-plan
status: proposed
layer: change
name: native-personal-local-worktree-flow
parent_spec: docs/superpowers/specs/2026-08-12-native-personal-local-worktree-flow.md
targets:
  - docs/operating_system/procedures/personal-local-worktree-procedure.md
  - docs/operating_system/procedures/harness-core-consumer-setup.md
  - docs/operating_system/rules/multi-agent-orchestration-rule.md
  - docs/operating_system/templates/agents/root-AGENTS.template.md
  - README.md
  - repo_config/starter-kit-manifest.json
---

# Native Personal-Local Worktree Flow Implementation Plan

## Goal

Route ordinary one-user development through native Git and Codex. Reuse clean
checkout for small reversible work. Use `git worktree` only when existing skill
rules select isolation. Keep launcher closure and host-backed execution as
explicit managed-advanced mode.

## Implementation Outcomes

### One canonical native procedure

`docs/operating_system/procedures/personal-local-worktree-procedure.md` owns
ordinary development guidance: workspace identity, native Git evidence, review,
and handoff. It adds no package, command, record, parser, matcher, provider, or
cleanup implementation.

### Reused Git ownership

Existing `skill-using-git-worktrees` remains sole owner of workspace selection
and identity. Existing `skill-finishing-a-development-branch` remains sole
owner of authorized commit, merge, push, discard, and cleanup. This plan edits
neither skill.

### Clear managed boundary

README, consumer setup, orchestration rule, and generated guidance call
ordinary development `native-personal-local`. Existing
`harness-core-launcher controller-init` and `close` remain managed-outcome
authority operations. Native-personal-local never reads or writes `.harness`.

## Execution Approach

- Mode: `inline sequential`
- Required skills: `skill-using-git-worktrees`, `skill-verification-before-completion`
- Isolation: current workspace; documentation-only shared writes
- Commit policy: no commits in project workspace during execution. Task 3 may
  create one baseline commit only inside disposable proof repository.
- Parallel ownership: none
- Sequential fallback: procedure first, boundary docs second, regeneration and proof last

## Task Breakdown

### Task 1: Publish canonical native procedure

**Purpose:**
- Add shortest complete native-personal-local workflow without recreating harness lifecycle.

**Specification Coverage:**
- Workspace selection, writer context, Git-owned scope proof, review/disposition, invariants, and Docker boundary.

**Required Skills:**
- `skill-using-git-worktrees`

**Files And Symbols:**
- Inspect: `.agents/skills/skill-using-git-worktrees/SKILL.md:When To Use`
- Inspect: `.agents/skills/skill-finishing-a-development-branch/SKILL.md:Keep Path`
- Modify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Verify: `docs/operating_system/procedures/personal-local-worktree-procedure.md`

**Dependencies:**
- Approved parent spec.

**Steps:**
- [ ] State task objective, declared repository-relative paths, `$base` commit, and declared checks before work starts. Treat missing objective, paths, base, or required checks as `block`.
- [ ] Reuse existing worktree skill unchanged: inspect Git topology/status; reuse clean current checkout for small reversible work; otherwise obtain explicit isolation consent and create/reuse native worktree through skill-owned flow.
- [ ] Require absolute selected workspace for every controller command. Use native writer only when Codex starts it from selected-workspace context; otherwise controller works directly or stops. Never use provider-host fallback.
- [ ] Require declared checks from selected workspace. Record `git diff --name-status -z -M -C --find-copies-harder $base --` and `git ls-files --others --exclude-standard -z`; use readable `git diff --name-status -M -C --find-copies-harder $base --` for review. Review every reported path against declared task paths; treat each `R` or `C` source/destination pair as two paths.
- [ ] Block acceptance for failed Git command/check, conflict, unsafe or outside-declared path, nested repository/submodule change, uncertain workspace context, or missing Git evidence. Record `accept` or `block` in handoff only.
- [ ] Hand off accepted review only to existing branch-finishing skill. A blocked review preserves workspace and evidence without handoff; later recovery or destructive discard needs separate explicit operator authorization. Neither disposition commits, merges, pushes, releases, stashes, resets, cleans, prunes, removes, or force-removes a worktree.
- [ ] State Docker commands may be declared task setup/checks only when repository already owns them; procedure never creates or manages containers.

**Verification:**
- [ ] `rg -n -i "native-personal-local|managed-advanced|git diff --name-status -z -M -C --find-copies-harder|git ls-files --others --exclude-standard -z|provider.*fallback|Docker|accept|block" docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Expected: procedure delegates workspace and disposition ownership to existing skills and introduces no runtime behavior.

**Exit Criteria:**
- One procedure fully describes native work and no instruction duplicates Git workspace/cleanup implementation.

### Task 2: Align managed-boundary documentation and adapters

**Purpose:**
- Separate native development from existing managed-outcome closure without changing launcher behavior.

**Specification Coverage:**
- Workflow-not-runtime decision, managed-advanced isolation, compatibility/no migration, and generated-source consistency.

**Required Skills:**
- none

**Files And Symbols:**
- Inspect: `README.md:Harness`
- Inspect: `docs/operating_system/procedures/harness-core-consumer-setup.md:Personal Controller`
- Inspect: `docs/operating_system/rules/multi-agent-orchestration-rule.md:Personal local use`
- Inspect: `docs/operating_system/templates/agents/root-AGENTS.template.md:Subagent Routing`
- Modify: `README.md`
- Modify: `docs/operating_system/procedures/harness-core-consumer-setup.md`
- Modify: `docs/operating_system/rules/multi-agent-orchestration-rule.md`
- Modify: `docs/operating_system/templates/agents/root-AGENTS.template.md`
- Verify: `AGENTS.md`
- Verify: `generated_agents/codex/AGENTS.md`
- Verify: `generated_agents/claude/CLAUDE.md`
- Verify: `generated_agents/antigravity/GEMINI.md`

**Dependencies:**
- Task 1 complete.

**Steps:**
- [ ] Add one concise README choice: ordinary trusted one-user repository work follows native-personal-local procedure; managed-advanced remains opt-in for host-backed packet evidence.
- [ ] Rename consumer-setup and orchestration-rule references to launcher `controller-init`/`close` as personal managed-outcome authority operations, never native-personal-local development.
- [ ] Add same boundary once in root agent template. Link canonical procedure; do not duplicate its steps in README or template.
- [ ] Add `docs/operating_system/procedures/personal-local-worktree-procedure.md` to starter-kit manifest `requiredPaths`.
- [ ] Run `uv run --locked python scripts/sync_agent_adapters.py`. Do not hand-edit `AGENTS.md` or `generated_agents/`.

**Verification:**
- [ ] `uv run --locked python scripts/sync_agent_adapters.py --check`
- [ ] `rg -n -i "native-personal-local|managed-advanced|controller-init|harness-core-launcher close" README.md docs/operating_system/procedures/harness-core-consumer-setup.md docs/operating_system/rules/multi-agent-orchestration-rule.md AGENTS.md generated_agents`
- Expected: generated outputs match template; launcher commands retain managed-only meaning.

**Exit Criteria:**
- One native procedure and one explicit managed-advanced boundary appear consistently in canonical and generated guidance.

### Task 3: Prove native Git behavior and disposable distribution

**Purpose:**
- Produce fresh native Git proof without deployed-kit replacement or custom runtime code.

**Specification Coverage:**
- All acceptance criteria, Git change-form symmetry, dirty-worktree retention, generated-source consistency, and no runtime/package change.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `docs/operating_system/procedures/personal-local-worktree-procedure.md`
- Verify: `scripts/build_starter_kit.py`
- Verify: `scripts/validate_starter_kit.py`
- Verify: `scripts/validate_planning_lifecycle.py`
- Verify: `scripts/validate_repo_contracts.py`

**Dependencies:**
- Tasks 1–2 complete.

**Steps:**
- [ ] Record explicit authorization for manual worktree creation only inside disposable proof repository. Create retained `$proofRoot` below `$env:TEMP` with a GUID. Set `$repoRoot`, `$worktreeRoot`, `$laneRoot`, `$kitOutput`, and `$kitRoot = Join-Path $kitOutput 'project-OS-starter-kit'` below it. Print all paths in transcript; never remove them during task.
- [ ] Initialize `$repoRoot`, configure local Git identity, create tracked `allowed-edit.txt`, `rename-source.txt`, and `copy-source.txt`, add `.worktrees/` to `.gitignore`, then create one baseline commit in this disposable fixture only. Set `$base = (git -C $repoRoot rev-parse HEAD).Trim()`. Assert clean `git -C $repoRoot status --porcelain` and assert `git -C $repoRoot rev-parse --show-toplevel` equals resolved `$repoRoot`.
- [ ] Record clean-checkout choice as `$repoRoot`; do not call `git worktree add` before this record. Create unrelated root mutation, then run `git -C $repoRoot worktree add -b native-proof $laneRoot $base`. Assert lane `HEAD` equals `$base`; record `git -C $repoRoot worktree list --porcelain`.
- [ ] In `$laneRoot`, modify `allowed-edit.txt`, add `allowed-untracked.txt`, rename `rename-source.txt` to `rename-destination.txt`, and copy `copy-source.txt` to `copy-destination.txt`. Record both zero-delimited and readable change outputs using `git -C $laneRoot diff --name-status -z -M -C --find-copies-harder $base --`, `git -C $laneRoot diff --name-status -M -C --find-copies-harder $base --`, and `git -C $laneRoot ls-files --others --exclude-standard -z`. Review visible `R` and `C` records and both endpoints against declared paths.
- [ ] Create `outside-declared.txt`, run one declared failing command, and initialize `$laneRoot\nested-repository`. Record `git -C $laneRoot status --short` plus `git -C (Join-Path $laneRoot 'nested-repository') rev-parse --is-inside-work-tree`; inspect the nested root and record `block` for outside path, failed check, and nested repository. Leave lane unchanged as evidence.
- [ ] Run `git -C $repoRoot worktree remove $laneRoot` without `--force`; require nonzero exit and unchanged nonempty `git -C $laneRoot status --porcelain`. Retain `$proofRoot`; cleanup requires later explicit destructive authorization through branch-finishing skill.
- [ ] Run `uv run --locked python scripts/build_starter_kit.py --output-root $kitOutput`, then `uv run --locked python scripts/validate_starter_kit.py --output-root $kitOutput`. Never run `scripts/sync_starter_kit.py`; deployed-kit replacement is separate explicitly authorized work.
- [ ] Assert `Test-Path -LiteralPath (Join-Path $kitRoot 'docs/operating_system/procedures/personal-local-worktree-procedure.md')` is true.
- [ ] Run `uv run --locked python scripts/validate_planning_lifecycle.py`, `uv run --locked python scripts/validate_repo_contracts.py --fast`, `uv run --locked python scripts/sync_agent_adapters.py --check`, and `git diff --check`.

**Verification:**
- [ ] Retained transcript proves current-checkout reuse, exact-base linked worktree, visible `R`/`C` evidence, blocked unsafe/failed cases, and non-force dirty-worktree removal refusal.
- [ ] `uv run --locked python scripts/validate_starter_kit.py --output-root $kitOutput`
- [ ] `Test-Path -LiteralPath (Join-Path $kitRoot 'docs/operating_system/procedures/personal-local-worktree-procedure.md')`
- [ ] `uv run --locked python scripts/validate_planning_lifecycle.py`
- [ ] `uv run --locked python scripts/validate_repo_contracts.py --fast`
- [ ] `uv run --locked python scripts/sync_agent_adapters.py --check`
- [ ] `git diff --check`
- Expected: all pass. No deployed starter-kit replacement; no package, host, launcher, policy, `.harness`, runtime-profile, or managed-run changes.

**Exit Criteria:**
- Fresh retained proof covers every native-flow acceptance criterion and disposable starter-kit output validates.

## Verification

- Retained Task 3 Git transcript.
- `uv run --locked python scripts/build_starter_kit.py --output-root $kitOutput`
- `uv run --locked python scripts/validate_starter_kit.py --output-root $kitOutput`
- `uv run --locked python scripts/sync_agent_adapters.py --check`
- `uv run --locked python scripts/validate_planning_lifecycle.py`
- `uv run --locked python scripts/validate_repo_contracts.py --fast`
- `git diff --check`

## Completion Criteria

1. One canonical procedure owns ordinary native-personal-local development.
2. Existing worktree and branch-finishing skills retain their single ownership.
3. Launcher closure remains explicit managed-outcome authority operation.
4. Native Git proof covers workspace choice, change forms, blocked cases, and dirty-worktree retention.
5. Disposable starter-kit, generated-agent, planning, and repository validators pass.
6. No project-workspace package, host, launcher, runtime profile, policy schema, `.harness` state, deployed-kit sync, release, or commit occurs during execution; Task 3's disposable fixture baseline commit is allowed.
