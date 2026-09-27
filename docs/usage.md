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

Use this loop for governed coding-agent work:

1. Write or select a Git-tracked plan with explicit task ownership and proof.
2. Admit only dependency-ready work through the selected runtime path.
3. Run each bounded lane inside its allowed repository and workspace scope.
4. Collect runtime facts, structured task results, tests, and Git evidence.
5. Reconcile evidence with the plan before deciding `PASS`, `FAIL`, or `BLOCKED`.

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
