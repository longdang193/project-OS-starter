---
name: live-run-verification-workflow
description: Run the live run verification workflow procedure.
required_reads:
- docs/operating_system/repo-governance.md
related_skills:
- verification-before-completion
- test-driven-development
tags:
- workflow
- closeout
- change
---

# GENERATED FILE - do not edit directly.
# Source: `docs/operating_system/workflows/live-run-verification-workflow.md`

# Live Run Verification Workflow

## Goal

Confirm issue resolution and expected behavior using evidence, while screening
for regressions before closeout.

## Execution Flow

1. Validate expected outputs against scenario/spec acceptance criteria.
2. Validate resolution evidence against prior failure boundary.
3. Run targeted regression checks for impacted scope.
4. Decide:
   - pass -> closeout
   - fail/regression -> debugging

## Decision Gates

1. Evidence gate:
   - verification fails if expected output evidence is incomplete.
2. Regression gate:
   - verification fails if new regressions are detected.
3. Contract gate:
   - reject fixes that pass run status but violate intended behavior/spec.

## Exit Criteria

- Verification pass with explicit evidence and regression assessment, or
- Verification fail with debug re-entry reason.
