---
layer: operating_system
artifact_type: plan
status: proposed
parent_workstream: none
parent_thread: none
parent_spec: docs/superpowers/specs/2026-05-04-prompt-ladder-non-standalone-spec.md
targets:
  - docs/operating_system/prompt_templates/
  - scripts/validate_prompt_ladder.py
  - tests/test_validate_prompt_ladder.py
related_features: []
related_stages: []
---

# Prompt Ladder Non-Standalone Implementation Plan

## Goal

Implement a non-standalone prompt ladder contract so lifecycle-critical prompts
have explicit prerequisites, next-prompt routing, and validator-backed
structure/linkage checks.

## Key Deliverables

- add required ladder sections to canonical ladder prompts
- enforce prompt-ladder structure and linkage via a new validator script
- wire validator into repo contract validation and add test coverage

## Task Breakdown

- task 1:
  - update ladder prompts with required metadata sections:
    - `Use When`
    - `Prerequisites` (`Required` + `Optional`)
    - `Next Prompts`
    - `Not For`
- task 2:
  - create `scripts/validate_prompt_ladder.py` to validate:
    - required sections present in ladder prompts
    - next-prompt references resolve to real files
    - no dead-end prompt unless marked terminal
    - cycles blocked except allowed iterative next-action loop
- task 3:
  - add tests for ladder validator behavior
- task 4:
  - integrate ladder validator into `scripts/validate_repo_contracts.py`
  - run targeted validations and fix drift findings

## Verification

- `python scripts/validate_prompt_ladder.py`
- `python -m pytest tests/test_validate_prompt_ladder.py -q`
- `python scripts/validate_repo_contracts.py --fast`

## Completion Criteria

Plan is complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`
