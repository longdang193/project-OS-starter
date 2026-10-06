# Usage

Use this document after [setup](setup.md). Project OS supports three common
journeys:

- **Understand:** read the [architecture](architecture.md), [pipeline](pipeline.md),
  and Guided Story.
- **Evaluate:** run repository validation and tests.
- **Adopt:** follow the [Project Adoption Migration](operating_system/adoption/project-adoption-migration-guide.md)
  for another repository.

## Source Validation

From the repository root:

```powershell
python scripts/validate_repo_contracts.py
python -m pytest -q
git diff --check
```

Install `requirements-benchmark.txt` before running the complete suite when the
benchmark tests are included. See [setup](setup.md) for dependency paths.

## Reference Task Flow

Use this loop for governed or coordinated coding-agent work:

1. Optionally activate Project Secretary when unresolved attention or
   cross-workstream priority needs to survive the current turn.
2. Select direct execution, one bounded executor, or Git-tracked coordination;
   existing selection remains directly callable when Secretary is absent.
3. For coordinated work, write or select a Git-tracked plan with explicit task
   ownership and proof, then admit only dependency-ready work.
4. Run selected work inside its allowed repository and workspace scope.
5. Collect runtime facts, bounded receipts, structured task results, tests, and
   Git evidence.
6. Reconcile evidence with the plan before deciding `PASS`, `FAIL`, or `BLOCKED`.

The [runtime surfaces](operating_system/runtime/runtime-surfaces.md) document
the canonical dispatcher and executor boundaries. The
[planning dispatch](operating_system/planning/planning-dispatch.md) document
owns executor selection and task routing.

## Blocked Work

`BLOCKED` means required admission, evidence, ownership, or acceptance proof is
missing or invalid. It does not mean a safe retry is ready. Reconcile plan and
Git state, settle ownership, record the missing proof, and make an explicit
controller decision before starting another attempt.

Runtime completion, pane output, or transport acknowledgement does not prove
acceptance. Keep lifecycle facts, structured results, tests, and Git state as
the evidence trail.

## Daily Loop

- Read the active plan before editing.
- Keep changes inside the assigned write set.
- Run focused checks before broad checks.
- Review the diff and preserve unrelated workspace changes.
- Retire completed work only after verification and explicit Git disposition.
