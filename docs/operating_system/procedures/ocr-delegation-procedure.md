# OCR Delegation Procedure

## Contract

OpenCodeReview (OCR) is optional advisory overlay for immutable Git-range
review. Project OS adapter owns validation, complete Git inventory, protected
content policy, bounded process execution, and OCR payload reconciliation.
Callers provide repository, `base_sha`, and `head_sha`; caller inventory, when
provided, must equal adapter-derived inventory.

Use `scripts/ocr_delegate_adapter.py` only for range preparation. It returns a
normalized `prepared`, `fallback`, or `BLOCKED` manifest:

- `prepared` preserves full Git inventory and adds OCR reviewable/excluded
  paths, normalized rules, advisory system hints, identity, digests, schema
  evidence, and observed executable version.
- `fallback` records OCR failure and returns responsibility to native review
  for complete inventory.
- `BLOCKED` records unconfirmed process cleanup; reconcile cleanup first.
- Invalid Project OS input is contract error, not fallback.

Canonical Project OS rules outrank OCR rule text. OCR never owns `PASS`,
`FAIL`, or `BLOCKED`.

## Installation

Install OCR externally. Do not vendor its package, binary, credentials, or
installer in this repository or Starter Kit. Adapter records observed
executable version as provenance. Schema v1 is only compatibility gate.

Every OCR subprocess sets `OCR_NO_UPDATE=1`:

```powershell
$env:OCR_NO_UPDATE = "1"
```

## Invocation

Adapter derives exact Git inventory, including deletion, rename, copy,
exclusion, and `-leading-name` paths. Preview uses immutable range identity:

```text
ocr delegate preview --repo <repo> --from <base_sha> --to <head_sha> --format json
```

Rules use same range identity and `--` before external Git paths:

```text
ocr delegate rule --repo <repo> --from <base_sha> --to <head_sha> --format json -- <path>...
```

Adapter accepts only `schema_version: "1"`; validates payload shape, range,
path membership, counts, and rule coverage. Every Git inventory path remains
native review coverage, including OCR exclusions. Protected content policy
applies before OCR; both old and new paths of renames/copies remain accounted
for, but protected contents never enter OCR or native LLM review.

Committed evidence binds to `base_sha` and `head_sha`. Working-tree evidence
binds to frozen output from
`.agents/skills/skill-subagent-driven-development/scripts/review-package`,
its SHA-256, and Git-inventory digest. Any digest change invalidates evidence.

## Proof and Fallback

Record executable path, observed version, schema version, immutable range,
inventory digest, and OCR payload digests. Live test uses temporary Git repo,
no network, and no LLM call. Enable explicitly; missing executable or
incompatible contract fails closed. Ordinary runs skip only when opt-in absent:

```powershell
$env:PROJECT_OS_OCR_LIVE_TEST = "1"
python -m pytest -q tests/test_ocr_delegate_adapter.py -k live
```

Missing executable, version-probe failure, timeout, command failure, malformed
JSON, unsupported schema, or reconciliation failure produces native fallback.
Do not emit partial prepared manifest.

## Boundaries

OCR is not integrated with `tokenpilot-codex-hook.cmd`, hooks, installers, or
generated runtime files. Starter Kit distributes shared
`scripts/ocr_delegate_adapter.py`, `scripts/owned_process.py`, and
`scripts/review_content_policy.py` only; never OCR package files, binaries,
fixtures, tests, credentials, or hook invocations.
