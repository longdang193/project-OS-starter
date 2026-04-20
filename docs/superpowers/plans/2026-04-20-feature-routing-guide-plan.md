---
layer: operating_system
artifact_type: plan
status: active
parent_workstream: none
targets:
  - docs/operating_system/feature-routing-guide.md
  - docs/adoption_guide.md
  - docs/features/README.md
  - docs/operating_system/doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Feature Routing Guide Implementation Plan

## Triage

Layer: operating_system
Feature type: ADD
Summary: Add reusable routing guidance so future projects do not model repo-method work as product features.
Reasoning: The change governs documentation placement, feature eligibility, dependency semantics, and starter adoption behavior. It does not add a product/domain feature.
Invariants:
- Product/domain features belong under `docs/features/` only when they represent product-specific capability.
- Repo method, agent behavior, adapter generation, publication boundaries, and docs governance belong to the operating-system layer.
- Feature `depends_on` expresses product/domain dependency only.
- Capability IDs are stable identifiers, not prose sentences.
Affected stages: none
Affected features: none
Primary lens: cross-cutting
Affected docs:
- feature_source: none
- feature_yaml: none
- feature_lineage: none
- feature_history: none
- stage_source: none
- stage_contract: none
- cross_cutting_docs:
  - `docs/operating_system/feature-routing-guide.md`
  - `docs/adoption_guide.md`
  - `docs/features/README.md`
  - `docs/operating_system/doc-system-lifecycle.md`
- readme: none
- generated: none
Generated refresh required: no
Capability IDs: none
Invariant IDs: none
Spec needed: yes
Plan needed: yes

## Source Spec

This plan implements:

- `docs/superpowers/specs/2026-04-20-feature-routing-guide-spec.md`

## Tasks

### 1. Add the routing guide

Create `docs/operating_system/feature-routing-guide.md` with:

- routing decision tree
- feature eligibility gate
- stage eligibility gate
- operating-system routing rules
- correct destination table
- capability ID rules
- feature dependency rules
- bad vs corrected `repo-operating-system` example
- cleanup guidance for misrouted features
- future validator guardrails

### 2. Update the adoption guide

Patch `docs/adoption_guide.md` so feature/stage creation requires reading the routing guide first.

Add explicit guidance that starter adoption, repo operating-system work, adapter generation, agent/rule work, publication policy, and docs governance must not become product features.

### 3. Update the features README

Patch `docs/features/README.md` with a short eligibility gate:

- product/domain capabilities only
- no repo-method work
- no feature metadata until real product/domain boundaries are clear
- expected source file path when managed architecture docs are adopted

### 4. Update doc-system lifecycle

Patch `docs/operating_system/doc-system-lifecycle.md` with:

- a direct anti-pattern warning against `docs/features/repo-operating-system.yaml`
- guidance that operating-system specs/plans use `targets`, not product feature `depends_on`
- a reminder that product feature dependency graphs must stay product/domain-focused

### 5. Verify

Run:

```powershell
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" diff --check
git -C "C:\Users\HOANG PHI LONG DANG\repos\project-OS-starter" status --short --branch
```

Inspect the final diff for accidental generated-file edits.

## Acceptance Criteria

- `docs/operating_system/feature-routing-guide.md` exists and explains routing decisions clearly.
- `docs/adoption_guide.md` links to the routing guide before feature/stage creation guidance.
- `docs/features/README.md` prevents treating repo-method work as product features.
- `docs/operating_system/doc-system-lifecycle.md` names the `repo-operating-system` anti-pattern.
- No generated files are edited.
- `git diff --check` passes.
