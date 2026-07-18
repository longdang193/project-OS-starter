---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: audit-report-evidence-governance-and-automation
parent_workstream: none
targets:
  - docs/operating_system/rules/
  - docs/operating_system/templates/
  - .agents/skills/
  - docs/superpowers/plans/audit/
  - scripts/
related_features: []
related_stages: []
---

## Goal

Establish mandatory audit-report behavior for problem cases and provide systematic, low-administration evidence artifact handling (images, result JSON/logs, reproducibility commands) with validator-backed quality gates.

## Key Deliverables

### 1) Audit mandate rule and trigger policy

Introduce operating-system rule that requires drafting audit report when problem is detected without existing active audit record, with clear triggers, allowed bypass cases, and closure requirements.

### 2) Canonical audit template and storage contract

Add single source-of-truth template for audit reports and define standardized folder structure for evidence artifacts, reproducibility assets, and manifest indexing.

### 3) Low-admin automation and verification gates

Provide script tooling to scaffold audits, register evidence artifacts, and enforce completeness checks. Wire checks into verification/closeout workflows and skill guidance without duplicated policy text.

## Task/Wave Breakdown

### Task 1: Define governance rule and contract boundaries

**Purpose:**
- Create explicit policy: problem without audit must produce audit report before completion claims.

**Files:**
- Inspect: `docs/operating_system/rules/`
- Modify: `docs/operating_system/rules/audit-evidence-mandate-rule.md` (new)
- Verify: `AGENTS.md`, `.codex/rules/*.rules` (generated surfaces after sync)

**Preconditions:**
- Confirm rule naming and placement follow existing rule catalog conventions.
- Confirm operating-system scope (not product feature scope).

**Steps:**
- [ ] Draft rule with: trigger matrix, bypass criteria, required report fields, closure gate.
- [ ] Add policy language for evidence integrity (hashes, timestamps, expected-vs-actual, repro determinism).
- [ ] Define non-goal boundary to avoid forcing audits for trivial non-behavior edits.
- [ ] Ensure rule references canonical template path (single source, no duplicate mini-format).

**Verification:**
- [ ] Rule text contains trigger, bypass, required outputs, closure conditions.
- [ ] Rule avoids duplicating lifecycle policy already owned by canonical docs.

**Exit Criteria:**
- New rule approved and structurally consistent with operating-system governance docs.

### Task 2: Author canonical audit template and storage layout

**Purpose:**
- Create reusable template + path convention to standardize evidence reporting with minimal ambiguity.

**Files:**
- Inspect: `docs/operating_system/templates/`
- Modify: `docs/operating_system/templates/audit-report-with-evidence-template.md` (new)
- Modify: `docs/superpowers/plans/audit/README.md` (new index/usage guide)
- Verify: template references in related docs/skills/workflows

**Preconditions:**
- Task 1 rule semantics finalized enough to mirror in template sections.

**Steps:**
- [ ] Define required sections: scope, findings, evidence per finding, reproduction, impact/risk, fix verification, appendix/index.
- [ ] Define canonical audit folder shape: `docs/superpowers/plans/audit/<audit_id>/` with `report.md`, `evidence/`, `repro/`, `manifest.yaml`.
- [ ] Add naming convention for `<audit_id>` and artifact file naming.
- [ ] Add redaction and sensitive-data handling guidance.

**Verification:**
- [ ] Template includes mandatory evidence link structure (images + JSON/log/result refs).
- [ ] Storage layout documented in one canonical location.

**Exit Criteria:**
- Team can create consistent audit artifact set from one template without extra interpretation.

### Task 3: Build low-administration audit tooling

**Purpose:**
- Reduce manual overhead through scaffolding, artifact registration, and automated completeness checks.

**Files:**
- Inspect: `scripts/`
- Modify: `scripts/new_audit.ps1` (new)
- Modify: `scripts/audit_capture.ps1` (new)
- Modify: `scripts/audit_check.py` (new)
- Verify: `tests/` (new or updated tests for audit_check parser/validator behavior)

**Preconditions:**
- Task 2 folder/schema contract finalized.

**Steps:**
- [ ] Implement scaffold script to generate audit folder + starter report + manifest.
- [ ] Implement capture script to append artifacts with SHA256, timestamp, and classification.
- [ ] Implement check script to enforce mandatory fields and resolved-state verification evidence.
- [ ] Add minimal tests for validator behavior and expected failure messages.

**Verification:**
- [ ] Script dry-run creates expected directory structure and files.
- [ ] Check script fails on missing repro/evidence and passes on complete bundle.

**Exit Criteria:**
- Audit bundle lifecycle (create -> capture -> validate) executable with minimal manual bookkeeping.

### Task 4: Integrate with workflows/skills and generated runtime surfaces

**Purpose:**
- Enforce usage through approved hard scope: workflow procedural gates + MUST-PATCH skills + `skill-executing-plans`, while avoiding duplicated policy text.

**Files:**
- Modify (workflows):
- Modify (skills MUST PATCH):
  - `.agents/skills/skill-systematic-debugging/SKILL.md`
  - `.agents/skills/skill-verification-before-completion/SKILL.md`
  - `.agents/skills/skill-finishing-a-development-branch/SKILL.md`
  - `.agents/skills/skill-executing-plans/SKILL.md`
- Modify: rule/manifest source docs if required for runtime adapter generation
- Verify: generated `AGENTS.md`, runtime skill surfaces, and any sync checks

**Preconditions:**
- Tasks 1-3 complete and reviewed.

**Steps:**
- [ ] Add workflow steps/gates for mandatory audit creation and closure checks in approved workflow set.
- [ ] Patch approved MUST-PATCH skills and `skill-executing-plans` to require canonical audit flow when trigger conditions are met.
- [ ] Ensure all touched workflows/skills reference canonical template/storage path only (no duplicated mini-template sections).
- [ ] Run required sync/generation script(s) for agent/runtime surfaces.
- [ ] Validate no duplicated section-level template text introduced.

**Verification:**
- [ ] Approved workflow files include audit step/gate language aligned to rule.
- [ ] Approved skill files include audit trigger/closure behavior aligned to rule.
- [ ] Referencing surfaces point to canonical template path.
- [ ] Generated adapter/rules surfaces updated and validation passes.

**Exit Criteria:**
- Audit mandate discoverable and enforceable in normal operator flow across approved workflow and skill surfaces with minimal maintenance burden.

### Task 5: Rollout, migration notes, and adoption guardrails

**Purpose:**
- Enable incremental adoption and avoid disruption for existing open work.

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md` (if policy index update needed)
- Modify: `docs/operating_system/agent_memory/failure-ledger.md` (if reusable lesson captured)
- Modify: `docs/superpowers/plans/audit/README.md` (rollout policy + migration)

**Preconditions:**
- Core rule/template/tooling integrated.

**Steps:**
- [ ] Define effective-date behavior for new problems vs legacy unresolved issues.
- [ ] Define minimum acceptable backfill for ongoing incidents.
- [ ] Publish short operator quickstart command sequence.
- [ ] Record known limitations and future hardening items.

**Verification:**
- [ ] Rollout guidance clear for both new and in-flight issues.
- [ ] No conflicting governance text across operating-system docs.

**Exit Criteria:**
- Policy is adoptable immediately with bounded migration burden.

## Verification

- `.\.venv\Scripts\python.exe scripts/validate_planning_lifecycle.py`
- `.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py --fast`
- `.\.venv\Scripts\python.exe scripts/validate_repo_contracts.py`
- (if rule/skill/workflow generation changed) run canonical sync command used by this repo and re-run checks

## Completion Criteria

1. All Key Deliverables are satisfied.
2. Rule + template + tooling + workflow/skill references are in place with single canonical template ownership.
3. Validation gates pass and generated instruction surfaces are synchronized.
4. Audit process can be executed end-to-end with reproducible evidence and minimal manual administration.
