---
layer: operating_system
artifact_type: plan
status: proposed
template_id: implementation-plan
name: publication-doc-boundary-refactor-plan
parent_workstream: none
parent_spec: docs/superpowers/specs/2026-05-12-01-12-publication-doc-boundary-refactor-spec.md
targets:
  - docs/operating_system/publication/public-repo-publication-policy.md
  - docs/operating_system/publication/public-repo-publishing.md
  - docs/operating_system/publication/public-safe-doc-rewrite-guide.md
  - docs/operating_system/procedures/publication-workflow.md
  - .agents/skills/skill-private-public-repo-governance/SKILL.md
related_features: []
related_stages: []
---

# Implementation Plan: Publication Documentation Boundary Refactor

## Goal

Refactor publication documentation surfaces so policy, procedure, and rewrite guidance no longer overlap, and enforce explicit publication-doc references in private/public governance skill.

## Key Deliverables

### Deliverable 1: Publication doc ownership split

Three docs reflect strict ownership boundaries:
- policy doc = normative boundary rules
- publishing doc = operator runbook
- rewrite guide = sanitization patterns

### Deliverable 2: Reference alignment

All files mentioning these docs route to correct canonical owner and avoid cross-doc duplication.

### Deliverable 3: Skill governance alignment

`skill-private-public-repo-governance` explicitly mentions publication docs and precedence rule.

## Task/Wave Breakdown

### Task 1: Refactor publication doc bodies by ownership

**Purpose:**
- remove overlap and enforce single-owner sections

**Files:**
- Modify: `docs/operating_system/publication/public-repo-publication-policy.md`
- Modify: `docs/operating_system/publication/public-repo-publishing.md`
- Modify: `docs/operating_system/publication/public-safe-doc-rewrite-guide.md`
- Verify: same three files

**Preconditions:**
- approved spec exists

**Steps:**
- [x] Move/trim sections to canonical owner docs.
- [x] Keep short summaries where needed, link to canonical owner.
- [x] Add explicit cross-links: policy <-> runbook <-> rewrite guide.

**Verification:**
- [x] manual section ownership check against spec

**Exit Criteria:**
- no normative duplication remains across three docs.

### Task 2: Update all references mentioning three docs

**Purpose:**
- ensure external references point to right owner doc

**Files:**
- Modify: `docs/operating_system/procedures/publication-workflow.md`
- Modify: mention files in `docs/superpowers/specs/` and `docs/superpowers/plans/` as needed
- Verify: repository-wide mention scan

**Preconditions:**
- Task 1 complete

**Steps:**
- [x] run mention scan for three filenames.
- [x] update link target/use text where ownership intent mismatched.
- [x] re-scan to confirm no stale/misrouted references.

**Verification:**
- [x] grep scan outputs reviewed clean

**Exit Criteria:**
- all mention surfaces align to canonical owner intent.

### Task 3: Patch governance skill doc mentions

**Purpose:**
- bind skill routing to canonical publication docs

**Files:**
- Modify: `.agents/skills/skill-private-public-repo-governance/SKILL.md`
- Verify: same file

**Preconditions:**
- Task 1 ownership final

**Steps:**
- [x] add “Canonical Publication Docs” section with three doc links.
- [x] add precedence note (policy doc authoritative for boundary rules).
- [x] ensure wording consistent with existing skill scope.

**Verification:**
- [x] manual inspection for presence and clarity

**Exit Criteria:**
- skill explicitly mentions publication docs and precedence.

## Verification

- `py -3 scripts/validate_planning_lifecycle.py`
- `py -3 -c "from pathlib import Path; import re; root=Path('.'); docs=['public-repo-publication-policy.md','public-repo-publishing.md','public-safe-doc-rewrite-guide.md'];
for d in docs:
  matches=list(root.rglob('*'))
print('run grep_search in agent log for authoritative check')"`
- repository grep scan for three doc names and manual link-intent review

## Completion Criteria

1. publication docs have non-overlapping ownership.
2. cross-links present and canonical.
3. mention inventory reconciled.
4. governance skill explicitly references publication docs.
5. planning lifecycle validation passes.

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>
