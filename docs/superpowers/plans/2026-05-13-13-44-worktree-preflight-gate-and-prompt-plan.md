---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: worktree-preflight-gate-and-prompt-plan
parent_workstream: none
targets:
  - .agents/skills/skill-using-git-worktrees/SKILL.md
  - docs/operating_system/prompt_templates/git-worktree-preflight-and-create-prompt.md
  - docs/operating_system/prompt_templates/README.md
  - docs/operating_system/prompt_templates/multi-worktree-dispatch-prompt.md
related_features: []
related_stages: []
---

## Goal

Adopt Option B by enforcing mandatory git worktree freshness preflight in the canonical worktree skill and adding a reusable operator prompt for safe worktree creation/reuse.

## Key Deliverables

### Deliverable 1: Worktree skill contract upgraded with freshness gate

`skill-using-git-worktrees` explicitly requires clean-branch check, fetch, ahead/behind decision gate, and base-SHA reporting before `git worktree add`.

### Deliverable 2: New reusable worktree preflight/create prompt template

A new prompt template is added under prompt templates with exact procedural language for create/reuse flows and required output fields.

### Deliverable 3: Prompt template discovery and routing linkage updated

Prompt README and related dispatch prompt include references to the new template so operators can discover and apply it consistently.

## Task/Wave Breakdown

### Task 1: Patch canonical worktree skill for Option B preflight

**Purpose:**
- Make freshness checks first-class and mandatory in worktree creation flow.

**Files:**
- Inspect: `.agents/skills/skill-using-git-worktrees/SKILL.md`
- Modify: `.agents/skills/skill-using-git-worktrees/SKILL.md`
- Verify: `.agents/skills/skill-using-git-worktrees/SKILL.md`

**Preconditions:**
- Approved Option B design decision.
- Existing worktree workflow remains authoritative source.

**Steps:**
- [x] Step 1: Add new “Branch Freshness Preflight” section before creation steps.
- [x] Step 2: Add explicit command sequence:
  - `git status --short`
  - `git fetch origin`
  - `git rev-list --left-right --count origin/main...main`
  - `git rev-parse --short main`
- [x] Step 3: Add decision gates:
  - dirty branch => stop and ask commit/stash/discard
  - ahead > 0 => ask push now (recommended) or local-only continue
  - behind > 0 => ask pull/rebase first or continue knowingly
- [x] Step 4: Update final report contract to require base SHA, ahead/behind counts, and decision record.
- [x] Step 5: Update Quick Reference, Common Mistakes, Red Flags to include skipped freshness checks as forbidden behavior.

**Verification:**
- [x] Confirm SKILL.md contains Option B flow with mandatory wording and exact command snippets.
- [x] Confirm no contradictions with existing directory-selection and ignore-protection rules.

**Exit Criteria:**
- SKILL.md reflects complete Option B policy and report requirements.

### Task 2: Create new git-worktree preflight/create prompt template

**Purpose:**
- Provide copyable operator prompt aligned to Option B for create/reuse actions.

**Files:**
- Inspect: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/git-worktree-preflight-and-create-prompt.md`
- Verify: `docs/operating_system/prompt_templates/git-worktree-preflight-and-create-prompt.md`

**Preconditions:**
- Task 1 complete so prompt mirrors canonical skill contract.

**Steps:**
- [x] Step 1: Create frontmatter aligned with existing prompt-template conventions (`name`, `description`, `type`, `stage`, `entry_points`, `related_skills`, `required_reads`, `distribution_tier`).
- [x] Step 2: Add prompt body with strict ordered checklist covering status/fetch/ahead-behind/base-SHA/directory-policy/ignore-protection/create-or-reuse/baseline tests.
- [x] Step 3: Require output payload fields:
  - worktree path
  - base branch and SHA
  - ahead/behind counts
  - user decision record
  - baseline test status

**Verification:**
- [x] Validate prompt follows existing template style and includes all required Option B gates.

**Exit Criteria:**
- New prompt template exists and is executable as-is for operators.

### Task 3: Link prompt into discovery and dispatch surfaces

**Purpose:**
- Ensure new prompt can be found and used during real routing.

**Files:**
- Inspect: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/README.md`
- Modify: `docs/operating_system/prompt_templates/multi-worktree-dispatch-prompt.md`
- Verify: both files

**Preconditions:**
- Task 2 complete.

**Steps:**
- [x] Step 1: Add new prompt to prompt-template README index/list.
- [x] Step 2: Add linkage from `multi-worktree-dispatch-prompt.md` (`next_steps` or body guidance) to preflight/create prompt.
- [x] Step 3: Ensure wording clarifies dispatch-vs-execution split (dispatch decides lanes; preflight prompt executes safe worktree setup).

**Verification:**
- [x] README references new prompt with clear purpose.
- [x] Dispatch prompt references new prompt without semantic overlap/conflict.

**Exit Criteria:**
- Prompt discoverability and workflow routing linkage complete.

### Task 4: Validate contracts and capture proof

**Purpose:**
- Confirm plan changes satisfy repo validators before handoff.

**Files:**
- Inspect: changed files from Tasks 1–3
- Verify: validator outputs/logs

**Preconditions:**
- Tasks 1–3 complete.

**Steps:**
- [x] Step 1: Run fast validator gate:
  - `py scripts/hooks/run_validator.py --fast`
- [x] Step 2: If failures occur, fix targeted issues and re-run until green.
- [x] Step 3: Record command outcomes for handoff to execution/closeout flow.

**Verification:**
- [x] Validator command exits 0.
- [x] No schema/format/lifecycle regressions introduced by new prompt or skill edits.

**Exit Criteria:**
- Validation proof available and ready for execution handoff.

## Verification

- `py scripts/hooks/run_validator.py --fast`

## Completion Criteria

1. Skill contract includes full Option B freshness gate and reporting fields.
2. New `git-worktree-preflight-and-create-prompt.md` exists with ordered operator flow and required outputs.
3. Prompt-template discovery/routing references are updated.
4. Fast validator gate passes with evidence.
