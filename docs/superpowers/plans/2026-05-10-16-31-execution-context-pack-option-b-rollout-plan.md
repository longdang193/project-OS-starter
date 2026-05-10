---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: execution-context-pack-option-b-rollout
parent_workstream: none
targets:
  - docs/operating_system/governance/
  - docs/operating_system/templates/execution-context-pack-template.md
  - .agents/skills/skill-executing-plans/SKILL.md
  - docs/operating_system/prompt_templates/execute-prompt.md
  - docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md
  - scripts/
  - scripts/validate_repo_contracts.py
related_features: []
related_stages: []
---

## Goal

Roll out Option B for execution context packs: canonical repo storage with optional worktree mirror, enforced by policy, lightweight sync automation, and validator coverage.

## Key Deliverables

### Canonical storage policy and path contract

Define and publish one canonical storage location for execution context packs:
`docs/superpowers/execution_context_packs/<lane-id>/latest.md`, with optional timestamped snapshots and clear ownership/lifecycle rules.

### Sync script for low-admin operation

Add one script to sync context pack between active worktree artifact and canonical repo path, so manual copy/paste is minimized.

### Validation and execution-surface enforcement

Ensure execution skill/prompts and repo validation checks enforce canonical path usage, template shape, and source-first resume behavior.

## Task/Wave Breakdown

### Task 1: Publish governance + path policy

**Purpose:**
- Make canonical storage and lifecycle rules explicit and durable.

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Add: `docs/operating_system/governance/execution-context-pack-governance.md`
- Verify: `docs/operating_system/templates/task-start-routing-guide.md`

**Steps:**
- [ ] Define canonical path contract and naming rules for `<lane-id>`.
- [ ] Define lifecycle triggers (task-state change, verification change, blocker change, pre-handoff).
- [ ] Define mirror semantics: worktree artifact is optional runtime mirror, canonical repo path is durable source.
- [ ] Define conflict resolution order: source/docs/tests -> canonical context pack -> optional raw log.

**Verification:**
- [ ] Governance text has no ambiguous dual-source wording.

**Exit Criteria:**
- Policy is clear enough to implement script and prompt/skill updates without reinterpretation.

### Task 2: Implement sync script and minimal index metadata

**Purpose:**
- Reduce administration overhead with one repeatable command.

**Files:**
- Add: `scripts/sync_execution_context_pack.py`
- Add: `docs/superpowers/execution_context_packs/` (structure)
- Modify: `scripts/validate_repo_contracts.py` (hook-in, if needed)

**Steps:**
- [ ] Implement script modes:
  - `--from-worktree` (mirror -> canonical latest)
  - `--to-worktree` (canonical latest -> mirror)
  - `--snapshot` (write timestamped snapshot)
- [ ] Require lane id and validate path safety.
- [ ] Write/update `latest.md` under canonical path.
- [ ] Optionally write simple `index.yaml` per lane with pointers and update time.

**Verification:**
- [ ] Script is idempotent for same input.
- [ ] Script fails safely on missing input and invalid lane id.

**Exit Criteria:**
- One command can update canonical pack reliably with minimal manual steps.

### Task 3: Wire execution surfaces to canonical policy

**Purpose:**
- Ensure agents consistently use canonical path and template.

**Files:**
- Modify: `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: `docs/operating_system/prompt_templates/execute-prompt.md`
- Modify: `docs/operating_system/prompt_templates/implementation-next-action-gate-prompt.md`
- Verify: `docs/operating_system/templates/execution-context-pack-template.md`

**Steps:**
- [ ] Add explicit canonical path referral in skill/prompt text.
- [ ] Keep template as schema source; avoid duplicating field schema elsewhere.
- [ ] Add exact wording to refresh canonical pack during execution progress, not only at handoff.

**Verification:**
- [ ] Prompt/skill wording stays concise and non-duplicative.

**Exit Criteria:**
- Execution surfaces point to one template and one canonical storage rule.

### Task 4: Add validator coverage and rollout checks

**Purpose:**
- Prevent drift and keep operation reliable over time.

**Files:**
- Modify: `scripts/validate_template_required_sections.py` (if needed)
- Modify: `scripts/validate_repo_contracts.py`
- Verify: `scripts/validate_repo_contracts.py --fast`

**Steps:**
- [ ] Add validation that canonical template metadata remains compliant.
- [ ] Add lightweight check for canonical context-pack path contract references in execution surfaces.
- [ ] Run fast validation and fix any contract gaps.

**Verification:**
- [ ] `py scripts/validate_repo_contracts.py --fast` passes.

**Exit Criteria:**
- Rollout guarded by existing fast validation lane.

## Verification

- `py scripts/validate_repo_contracts.py --fast`
- Targeted dry-run of sync script examples:
  - `py scripts/sync_execution_context_pack.py --lane <lane-id> --from-worktree`
  - `py scripts/sync_execution_context_pack.py --lane <lane-id> --from-worktree --snapshot`
  - `py scripts/sync_execution_context_pack.py --lane <lane-id> --to-worktree`

## Completion Criteria

This plan is complete when:

1. canonical policy and path are documented
2. sync script supports low-admin canonical updates
3. execution surfaces point to canonical template/path without schema duplication
4. fast repo validation passes with new checks in place
