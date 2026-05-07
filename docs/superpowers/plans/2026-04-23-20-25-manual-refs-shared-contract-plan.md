---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validator_policy.py
  - scripts/audit_architecture_linkage.py
  - tools/docs/generate_architecture_metadata.py
  - tests/test_architecture_linkage_audit.py
  - tests/test_architecture_metadata_generation.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Manual Refs Shared Contract Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-manual-refs-shared-contract-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Centralize the `manual_refs` prohibition so the architecture-linkage audit and architecture generator enforce one shared contract.

**Architecture:** Extend `scripts/validator_policy.py` with a tiny shared `manual_refs` contract: forbidden field name, aligned remediation text, and an optional narrow helper. Refactor `scripts/audit_architecture_linkage.py` and `tools/docs/generate_architecture_metadata.py` to consume that shared contract while keeping file walking, parsing, and generator flow local.

**Key Invariants:**
- `manual_refs` remains forbidden in `docs/features/*/feature.source.yaml`.
- Metadata-derived refs remain the only supported ref model.
- The audit stays a focused awareness/strict checker.
- The generator keeps its existing validation and generation flow.

**Rollout / Revert:**  
- rollback_trigger: The shared-contract extraction changes generator or audit behavior unexpectedly, or widens beyond the `manual_refs` seam.  
- rollback_method: Inline the `manual_refs` rule back into the audit and generator, keep the spec/plan, and retry with a smaller helper surface.

---

## Doc Update Matrix

- Feature source: none
- Feature contract: none
- Feature lineage: none
- Stage source: none
- Stage contracts: none
- Feature history: none
- Feature-specific docs: none
- Cross-cutting docs: none
- Operating-system docs:
  - `docs/operating_system/governance/repo-governance.md`
  - `docs/operating_system/skill-doc-system-lifecycle.md`
  - `docs/superpowers/specs/2026-04-23-manual-refs-shared-contract-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validator_policy.py
scripts/audit_architecture_linkage.py
tools/docs/generate_architecture_metadata.py
tests/test_architecture_linkage_audit.py
tests/test_architecture_metadata_generation.py
docs/operating_system/governance/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/superpowers/specs/2026-04-23-manual-refs-shared-contract-spec.md
```

## Scope Boundary

Implement only the narrow shared `manual_refs` contract:

1. add shared policy in `scripts/validator_policy.py`
2. use it from the audit
3. use it from the generator
4. keep tests aligned on the same rule and remediation text
5. lightly update operating-system docs

Do not:

- centralize unrelated generator constants
- redesign feature-source parsing
- broaden the forbidden-key system beyond `manual_refs`
- change generated outputs

## Task 1: Add Shared `manual_refs` Policy

**Files:**
- Modify: `scripts/validator_policy.py`

- [x] Step 1: Add explicit shared constants for the forbidden `manual_refs` field.
- [x] Step 2: Add aligned remediation text for the metadata-derived refs rule.
- [x] Step 3: Add a tiny helper only if it improves clarity without pulling in parsing flow.

## Task 2: Refactor The Architecture-Linkage Audit

**Files:**
- Modify: `scripts/audit_architecture_linkage.py`
- Test: `tests/test_architecture_linkage_audit.py`

- [x] Step 1: Replace local `manual_refs` string checks with shared policy imports.
- [x] Step 2: Keep the audit CLI behavior and reporting flow local.
- [x] Step 3: Preserve the strict-awareness failure path and the report-awareness success path.
- [x] Step 4: Run the audit tests and confirm unchanged behavior.

Suggested verification command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_architecture_linkage_audit.py -q
```

## Task 3: Refactor The Architecture Generator

**Files:**
- Modify: `tools/docs/generate_architecture_metadata.py`
- Test: `tests/test_architecture_metadata_generation.py`

- [x] Step 1: Replace the local `manual_refs` validation in `validate_feature_source()` with shared policy imports.
- [x] Step 2: Keep feature-source parsing and generator flow local.
- [x] Step 3: Preserve the existing failure mode when `manual_refs` is present.
- [x] Step 4: Run focused generator tests and confirm unchanged behavior.

Suggested verification command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_architecture_metadata_generation.py -k manual_refs -q
```

## Task 4: Align Tests On The Shared Contract

**Files:**
- Modify: `tests/test_architecture_linkage_audit.py`
- Modify: `tests/test_architecture_metadata_generation.py`

- [x] Step 1: Update the tests to align with the shared `manual_refs` contract wording where useful.
- [x] Step 2: Keep the tests narrow and behavior-oriented.
- [x] Step 3: Avoid copying large fixtures or over-testing the policy module directly.

## Task 5: Light Documentation Pass

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/superpowers/specs/2026-04-23-manual-refs-shared-contract-spec.md`

- [x] Step 1: Note that the `manual_refs` prohibition is part of shared internal policy.
- [x] Step 2: Keep the docs centered on metadata-derived refs as the rule, not implementation detail.
- [x] Step 3: Mark the spec complete once the implementation lands.

## Task 6: Full Verification

**Files:**
- Test: `tests/test_architecture_linkage_audit.py`
- Test: `tests/test_architecture_metadata_generation.py`
- Verify: `scripts/audit_architecture_linkage.py`
- Verify: `tools/docs/generate_architecture_metadata.py`

- [x] Step 1: Run the audit tests:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_architecture_linkage_audit.py -q
```

- [x] Step 2: Run the focused generator `manual_refs` test:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_architecture_metadata_generation.py -k manual_refs -q
```

- [x] Step 3: Run the full architecture metadata generation test file if the focused run passes:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_architecture_metadata_generation.py -q
```

- [x] Step 4: Run the architecture sync check path:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python tools/docs/generate_architecture_metadata.py --check
```

- [x] Step 5: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 6: Review the final diff and confirm this stayed a narrow shared-contract extraction.
