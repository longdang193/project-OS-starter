# OCR Delegation Procedure

## Contract

OpenCodeReview (OCR) is an optional advisory overlay for immutable Git-range
review. Review requester owns the caller-supplied repository, `base_sha`,
`head_sha`, and Git inventory. The shared adapter does not infer rename,
deletion, or coverage identity from OCR.

Use `scripts/ocr_delegate_adapter.py` only for range preparation. It returns a
normalized `prepared` or `fallback` manifest:

- `prepared` preserves full Git inventory and adds OCR `reviewable_paths`,
  `excluded_paths`, normalized `rules`, `scope_identity`, `payload_digests`,
  schema evidence, and `observed_version`.
- `fallback` records OCR failure and returns responsibility to native review for
  the complete inventory.
- Invalid Project OS input is a contract error, not fallback.

Canonical Project OS rules outrank OCR rule text. OCR never owns `PASS`, `FAIL`,
or `BLOCKED`.

## Installation and Version

Install OCR externally. Do not vendor its package, binary, credentials, or
installer in this repository or Starter Kit. Current tested release is
`1.12.4` as of September 16, 2026; record observed executable version as
provenance, not an exact-version runtime gate.

Every OCR subprocess must set `OCR_NO_UPDATE=1`:

```powershell
$env:OCR_NO_UPDATE = "1"
```

This prevents OCR's updater from changing the externally installed executable
during review. Upgrade only through an explicit external installation change,
then rerun the live upgrade test and compatibility checks.

## Invocation

First validate immutable range identity and caller inventory. Invoke preview
with repository, full commit SHAs, and JSON output:

```text
ocr delegate preview --repo <repo> --from <base_sha> --to <head_sha> --format json
```

Invoke rules only for OCR reviewable paths, with `--` before external Git paths
and bounded argument batches:

```text
ocr delegate rule --repo <repo> --format json -- <path>...
```

Accept only `schema_version: "1"`. Validate payload shape, range/path
membership, counts, and rule coverage before using OCR output. Keep every Git
inventory path in native review coverage, including OCR exclusions.

Committed review evidence binds to `base_sha` and `head_sha`. Working-tree
review evidence binds to frozen `scripts/review-package` output plus its
SHA-256 and Git-inventory digest when `HEAD` does not identify implementation
changes. Any package or inventory digest change invalidates that evidence.

## Proof and Fallback

Record executable path, observed version, schema version, immutable range,
inventory digest, and OCR payload digests. Run the live compatibility test only
when explicitly enabled with `PROJECT_OS_OCR_LIVE_TEST=1`; it must use a
temporary Git repository and must not make network or LLM calls. The test proves
installed executable behavior, Windows discovery where applicable, flags, JSON
shape, rule grouping, and coverage reconciliation.

Missing executable, version-probe failure, timeout, command failure, malformed
JSON, unsupported schema, or reconciliation failure produces native fallback.
Do not emit a partial prepared manifest.

## Boundaries

OCR is not integrated with `tokenpilot-codex-hook.cmd`, pre-commit hooks, Stop
hooks, installers, or generated runtime files. Starter Kit distributes only the
shared `scripts/ocr_delegate_adapter.py` path; it does not distribute OCR
package files, binaries, fixtures, tests, credentials, or hook invocations.
