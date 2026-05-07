---
layer: operating_system
artifact_type: plan
status: completed
parent_workstream: none
targets:
  - scripts/validator_policy.py
  - scripts/validate_adoption_shape.py
  - tests/test_validate_adoption_shape.py
  - docs/operating_system/governance/repo-governance.md
  - docs/operating_system/skill-doc-system-lifecycle.md
related_features: []
related_stages: []
---

# Validator Policy Extraction Implementation Plan

**Feature Source:** `none`  
**Feature Contract:** `none`  
**Spec:** `docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md`  
**Type:** modify  
**Plan Layer:** operating_system  
**Plan Status:** completed

> **For agentic workers:** Use `skill-executing-plans` or `skill-subagent-driven-development` to implement task-by-task.

**Goal:** Extract validator-owned policy from `validate_adoption_shape.py` into a shared internal Python policy module without changing validator behavior.

**Architecture:** Introduce a new `scripts/validator_policy.py` module that groups stable policy by responsibility: adoption/folder rules, root-doc rules, schema keys, template rules, and canonical field-class policy. Keep all parsing, traversal, and finding logic in `validate_adoption_shape.py`, and refactor that script to import policy constants from the new module instead of defining them inline.

**Key Invariants:**
- Validator behavior must remain stable after the refactor.
- Policy data moves; validation flow stays in `validate_adoption_shape.py`.
- The extracted layer remains starter-owned internal policy, not runtime config.
- This pass only targets `validate_adoption_shape.py`; any later sharing with `validate_repo_contracts.py` is explicitly deferred.

**Rollout / Revert:**  
- rollback_trigger: The refactor changes validator output unexpectedly, introduces import fragility, or makes policy harder rather than easier to follow.  
- rollback_method: Inline the extracted constants back into `validate_adoption_shape.py`, keep the spec/plan for a narrower retry, and revisit the grouping approach.

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
  - `docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md`
- README: none
- Generated discovery: none

## Files To Modify

```text
scripts/validator_policy.py
scripts/validate_adoption_shape.py
tests/test_validate_adoption_shape.py
docs/operating_system/governance/repo-governance.md
docs/operating_system/skill-doc-system-lifecycle.md
docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md
```

## Scope Boundary

Implement only the first extraction pass:

1. create `scripts/validator_policy.py`
2. move stable policy constants there
3. import them into `validate_adoption_shape.py`
4. keep behavior-preserving tests green
5. lightly document that validator policy now has an internal shared module

Do not:

- add repo-editable YAML config
- redesign validator flow
- split into a `scripts/validator_policy/` package unless a single module proves clearly unwieldy during implementation
- refactor `validate_repo_contracts.py` in this pass

## Task 1: Inventory And Group Current Policy Families

**Files:**
- Modify: `scripts/validate_adoption_shape.py`
- Create: `scripts/validator_policy.py`
- Docs: none

- [x] Step 1: Identify the current top-level constant families in `validate_adoption_shape.py`.
- [x] Step 2: Group them into responsibility sections for the new policy module:
  - adoption and folder policy
  - root-doc policy
  - schema-key policy
  - template policy
  - canonical style/ordering policy
- [x] Step 3: Decide which tiny local values should stay in the validator because they are helper-local, not shared policy.
- [x] Step 4: Create `scripts/validator_policy.py` with grouped sections and stable exported names.

## Task 2: Refactor `validate_adoption_shape.py` To Import Policy

**Files:**
- Create: `scripts/validator_policy.py`
- Modify: `scripts/validate_adoption_shape.py`
- Test: `tests/test_validate_adoption_shape.py`
- Docs: none

- [x] Step 1: Move the selected top-level policy constants into `scripts/validator_policy.py`.
- [x] Step 2: Import those constants back into `validate_adoption_shape.py`.
- [x] Step 3: Remove duplicated inline definitions from `validate_adoption_shape.py`.
- [x] Step 4: Keep import names readable so call sites still make sense without opening two files constantly.
- [x] Step 5: Run the full validator test file and confirm behavior stays unchanged.

Suggested verification command:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

## Task 3: Add A Small Structural Guard

**Files:**
- Modify: `tests/test_validate_adoption_shape.py`
- Create or Modify: `scripts/validator_policy.py`
- Docs: none

- [x] Step 1: Add a small regression check if needed to prove the policy module exports the key rule families the validator depends on.
- [x] Step 2: Keep the test narrow and behavior-oriented; do not overfit to every constant name unless that is necessary.
- [x] Step 3: Avoid turning the test suite into a second policy schema unless it provides real safety.

## Task 4: Light Documentation Pass

**Files:**
- Modify: `docs/operating_system/governance/repo-governance.md`
- Modify: `docs/operating_system/skill-doc-system-lifecycle.md`
- Modify: `docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md`

- [x] Step 1: Add a small note that validator contract policy now lives in an internal shared Python policy module.
- [x] Step 2: Keep the docs clear that this is internal validator policy, not runtime or downstream repo config.
- [x] Step 3: Avoid over-documenting internal module layout beyond what helps future maintenance.

## Task 5: Full Verification

**Files:**
- Test: `tests/test_validate_adoption_shape.py`
- Verify: `scripts/validate_adoption_shape.py`
- Docs: all modified docs above

- [x] Step 1: Run the full validator test file:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python -m pytest tests/test_validate_adoption_shape.py -q
```

- [x] Step 2: Run the starter validator:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python scripts/validate_adoption_shape.py
```

- [x] Step 3: Run generated metadata check:

```powershell
$env:UV_CACHE_DIR=$env:TEMP; uv run python tools/docs/generate_architecture_metadata.py --check
```

- [x] Step 4: Run whitespace validation:

```powershell
git diff --check
```

- [x] Step 5: Review `git diff` and confirm the pass stayed behavior-preserving and did not silently redesign validation flow.

## Task 6: Optional Future Follow-Up Capture

**Files:**
- Docs only: `docs/superpowers/specs/2026-04-23-validator-policy-extraction-spec.md` if needed

- [x] Step 1: Record whether the single-module extraction feels sufficient or whether a future package split is warranted.
- [x] Step 2: Record whether `validate_repo_contracts.py` appears to have a real shared-policy opportunity, without implementing it in this pass.
