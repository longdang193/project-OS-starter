---
layer: operating_system
artifact_type: plan
status: completed
template_id: implementation-plan
name: metadata-linkage-governance-patch
parent_workstream: none
parent_spec: none
targets:
  - docs/operating_system/rules/python-contracts-rule.md
  - .agents/skills/skill-doc-system-lifecycle/SKILL.md
  - scripts/validate_python_meta_headers.py
  - tests/
related_features: []
related_stages: []
---

## Goal

Patch governance guidance so Python `@meta` drafting is feature-grounded, capability-linked, and validator-aligned; remove ambiguous generic-schema interpretation from rule/skill/workflow surfaces.

## Key Deliverables

### Metadata-linkage rule hardening

`docs/operating_system/rules/python-contracts-rule.md` explicitly defines Python metadata linkage protocol: source read order, capability-ID derivation, forbidden unlinked capabilities, lifecycle shape, and conditional omission policy for non-feature infra files.

### Skill guardrail hardening

`.agents/skills/skill-doc-system-lifecycle/SKILL.md` includes mandatory Python metadata grounding checklist so plan/doc sessions cannot draft disconnected `@meta` blocks.

### Workflow and validator follow-up lane

Preflight workflow and validator follow-up tasks documented and executed (or intentionally deferred with rationale), including command-level verification and rollback notes.

## Task/Wave Breakdown

### Task 1: Patch Python contracts rule

**Purpose:**
- Make metadata-linkage obligations explicit in canonical Python rule surface.

**Files:**
- Inspect: `docs/operating_system/rules/python-contracts-rule.md`
- Modify: `docs/operating_system/rules/python-contracts-rule.md`
- Verify: `docs/operating_system/rules/python-contracts-rule.md`

**Preconditions:**
- Confirm current lifecycle ownership chain from `docs/operating_system/lifecycle/doc-system-lifecycle.md` and `docs/operating_system/lifecycle/feature-lifecycle.md`.

**Steps:**
- [x] Add a "Metadata Linkage Protocol" subsection with mandatory source read order.
- [x] Add explicit requirement: `@meta.capabilities` must come from upstream feature capability IDs when such IDs exist.
- [x] Add explicit forbidden pattern: generic/unmapped capability IDs and placeholder responsibilities.
- [x] Clarify conditional omission rules for infra-only scripts that do not map to feature capability ownership.

**Verification:**
- [x] Confirm rule text contains both required and forbidden linkage statements without conflicting existing contract language.

**Exit Criteria:**
- Rule text is unambiguous about capability-first, feature-grounded metadata drafting.

### Task 2: Patch doc-system lifecycle skill

**Purpose:**
- Ensure skill users follow lifecycle source-of-truth chain before drafting Python metadata.

**Files:**
- Inspect: `.agents/skills/skill-doc-system-lifecycle/SKILL.md`
- Modify: `.agents/skills/skill-doc-system-lifecycle/SKILL.md`
- Verify: `.agents/skills/skill-doc-system-lifecycle/SKILL.md`

**Preconditions:**
- Task 1 complete.

**Steps:**
- [x] Add mandatory checklist section for Python metadata grounding.
- [x] Encode required read order: `feature.source.yaml` → generated feature contract (as needed) → lineage evidence (as needed).
- [x] Add explicit mapping bullets: `@meta.capabilities` ↔ `capability_id`, `@capability`, `@proves`.
- [x] Add “no generic draft first” guardrail.

**Verification:**
- [x] Confirm checklist is present and references canonical lifecycle ownership wording.

**Exit Criteria:**
- Skill text enforces linkage-first drafting path.

### Task 3: Patch preflight workflow guardrail (if in scope)

**Purpose:**
- Add runtime preflight check to catch disconnected metadata before completion claims.

**Files:**

**Preconditions:**
- Task 2 complete.

**Steps:**
- [x] Add preflight step for Python metadata-capability linkage validation when Python files are touched.
- [x] Add command references for architecture/check validators.
- [x] Keep step conditional to avoid over-broad runtime cost.

**Verification:**
- [x] Confirm workflow text stays concise and non-duplicative with canonical rules.

**Exit Criteria:**
- Workflow contains actionable linkage preflight gate.

### Task 4: Validator hardening follow-up (optional separate commit)

**Purpose:**
- Close enforcement gap between textual guidance and script checks.

**Files:**
- Inspect: `scripts/validate_python_meta_headers.py`, `tools/docs/generate_architecture_metadata.py`, related tests under `tests/`
- Modify: `scripts/validate_python_meta_headers.py`, targeted tests
- Verify: `scripts/validate_repo_contracts.py`, test suite subset

**Preconditions:**
- Tasks 1–3 complete or accepted.

**Steps:**
- [ ] Decide strictness policy (hard fail vs opt-in flag) for capability-linkage checking.
- [ ] Implement lightweight check path in validator (only when capability IDs are expected and discoverable).
- [ ] Add tests for pass/fail linkage scenarios.
- [ ] Document migration policy for grandfathered files.

> Status: deferred to follow-up commit/lane to avoid broad validator behavior change in governance-text patch.

**Verification:**
- [x] `py scripts/validate_repo_contracts.py --fast`
- [x] Targeted tests for metadata validator behavior.

**Exit Criteria:**
- Enforcement behavior matches updated rule/skill contract.

## Verification

- `py scripts/validate_repo_contracts.py --fast` ✅
- `py tools/docs/generate_architecture_metadata.py --check` ⚠️ fails currently due to existing unrelated baseline issue: `generated_exports/project-OS-starter-kit/scripts/audit_check.py: missing @meta top-of-file metadata`

## Completion Criteria

1. Key deliverables are present with no policy contradiction.
2. Updated rule/skill/workflow text consistently enforces linkage-first Python metadata drafting.
3. Validation commands pass, or any deferred validator hardening is explicitly documented with follow-up ownership.
