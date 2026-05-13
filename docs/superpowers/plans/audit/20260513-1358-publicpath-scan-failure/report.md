# Audit Report With Evidence

## Metadata

- Audit ID: `20260513-1358-publicpath-scan-failure`
- Status: `mitigated`
- Severity: `medium`
- Owner: `antigravity`
- Created At: `2026-05-13T13:58:23+02:00`
- Updated At: `2026-05-13T14:15:34+02:00`
- Related Thread/Plan: `docs/superpowers/plans/2026-05-13-14-01-publication-file-only-allowlist-guard-plan.md`

## Scope

- Environment: `Windows, PowerShell, git`
- Commit/Branch: `c5f3890 + feature/publication-allowlist-guard`
- Affected Surface: `publication pipeline: scripts/publish_public_repo.ps1 + repo_config/publication-config.json`

## Findings

### Finding `F-001`: Broad allowlist imports private-reference script and fails export scan

- Classification: `spec-mismatch`
- Impact: `Public mirror export fails when scripts/ is allowlisted; release lane blocked`
- Expected Behavior: `Curated export should include only approved public files and pass private-reference scan`
- Actual Behavior: `If scripts/ included in publicPaths, export contains scripts/audit_capture.ps1; Assert-NoPrivateReferences detects docs/superpowers/ and hard-fails`

## Evidence

- Logs/Text: `evidence/results/private_reference_failure_analysis.txt`
- Result JSON: `evidence/results/failure_fingerprint.json`
- Logs/Text: `evidence/results/guard_repro_output.txt`
- Logs/Text: `evidence/results/pattern_classification.txt`

Evidence metadata and checksums recorded in `manifest.yaml`.

## Reproduction

- Preconditions:
  - `repo contains scripts/audit_capture.ps1 with docs/superpowers path literal`
  - `publication config publicPaths includes scripts/`
- Steps:
  1. Add `scripts` entry into `repo_config/publication-config.json` `publicPaths`.
  2. Run publication script export.
  3. Observe hard fail from private-reference scan.
- Commands:

```powershell
git grep -n "docs/superpowers" scripts/audit_capture.ps1
./scripts/publish_public_repo.ps1
```

- Determinism notes: `Deterministic while scan patterns include docs/superpowers/ and exported scripts contain matching literal.`

## Root Cause And Boundary

- Failure boundary: `contract boundary between publication allowlist policy and content scanner gate`
- Root cause summary: `Directory-level allowlist (scripts/) pulls in files with private-only references; scanner enforces docs/superpowers/ deny-pattern across exported text.`

## Fix And Verification

- Fix summary: `Added Assert-PublicPathIsFile guard in publish_public_repo.ps1 and invoked before copy loop; script now rejects directory-level publicPaths entries early.`
- Verification commands:

```powershell
git diff -- scripts/publish_public_repo.ps1
./scripts/publish_public_repo.ps1
# temporary repro with scripts in publicPaths
./scripts/publish_public_repo.ps1
```

- Verification evidence links:
  - `evidence/results/guard_repro_output.txt`
  - `evidence/results/pattern_classification.txt`

## Risk And Disposition

- Residual risk: `Template/config surfaces can still reintroduce broad directory entries unless static lint/schema guard added.`
- Disposition decision: `mitigated`
- Follow-ups: `Add static validation rule for file-only publicPaths across publication configs (deferred).`

## Artifact Index

- Manifest: `manifest.yaml`
- Evidence root: `evidence/`
- Repro root: `repro/`

## Completion Checklist

- [x] qualifying trigger documented (or explicit bypass)
- [x] evidence bundle linked and hashed
- [x] deterministic repro steps included
- [x] expected vs actual included
- [x] verification evidence attached
- [x] final status recorded
