# Usage

Use this guide after setup is complete and configuration values are available.

## Common Commands

```powershell
<run-command>
```

Expected result: `<expected-run-output>`.

```powershell
<test-or-check-command>
```

Expected result: `<expected-check-output>`.

## Normal Workflow

1. Confirm dependencies are installed with `<setup-check-command>`.
2. Select a runtime profile in `configs/starter-runtime.yaml` or through the documented environment value.
3. Run `<run-command>` from the repository root.
4. Inspect outputs under `<output-path>`.
5. Run `<validation-command>` before sharing results.

## Inputs

- Primary input: `<input-path-or-service>`
- Required format: `<input-format>`
- Sample fixture: `<sample-fixture-path>`

## Outputs

- Primary output: `<output-path-or-service>`
- Output format: `<output-format>`
- Retention rule: `<retention-or-cleanup-rule>`

## Failure Handling

If a command fails, capture the command, selected profile, config values that are safe to share, and the first relevant error message. Then check setup, configuration, and input availability in that order.
