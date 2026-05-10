# Audit Artifact Storage

Canonical path for each audit:

- `docs/superpowers/plans/audit/<audit_id>/`

Recommended structure:

```text
docs/superpowers/plans/audit/<audit_id>/
  report.md
  manifest.yaml
  evidence/
    images/
    results/
  repro/
    steps.md
    commands.ps1
    inputs/
```

## Rules

1. `report.md` should follow:
   - `docs/operating_system/templates/audit-report-with-evidence-template.md`
2. `manifest.yaml` tracks artifact path, type, timestamp, checksum.
3. Use repo-relative paths in report links.
4. Redact secrets before storage.
5. Enforce trigger/closure behavior from:
   - `docs/operating_system/rules/audit-evidence-mandate-rule.md`

## Rollout Policy

### Effective date behavior

- New qualifying problems discovered on or after policy adoption: audit is mandatory before closeout claims.
- Existing audits continue under same canonical template/storage contract.

### Legacy and in-flight issues

- In-flight qualifying issue with no audit yet: create minimum viable audit bundle before next closeout/verification claim.
- Minimum viable backfill:
  - `report.md` with finding, expected vs actual, root cause boundary
  - at least one reproducible command sequence in `repro/commands.ps1`
  - at least one evidence artifact registered in `manifest.yaml`

### Allowed bypass (must be explicit)

- docs-only or typo-only non-behavior change
- same failure already tracked by active audit bundle in same scope

When bypass used, record reason in verification/closeout notes.

## Operator Quickstart

1. Create scaffold:

```powershell
.\scripts\new_audit.ps1 -AuditId <audit_id>
```

2. Capture evidence artifacts:

```powershell
.\scripts\audit_capture.ps1 -AuditId <audit_id> -SourceFile <path> -Type image
.\scripts\audit_capture.ps1 -AuditId <audit_id> -SourceFile <path> -Type result
```

3. Validate audit bundle completeness:

```powershell
.\.venv\Scripts\python.exe scripts\audit_check.py docs/superpowers/plans/audit/<audit_id>
```

4. Link audit path in workflow/skill execution notes for debugging, verification, and closeout.

## Known Limitations And Future Hardening

- `audit_check.py` currently validates required structure/sections, not deep semantic quality.
- workflow-level hard gates are enforced; repo-global hard gate not enabled in this rollout.
- future hardening options:
  - enforce manifest checksum uniqueness
  - verify referenced evidence links exist in report body
  - optional repo-wide CI gate for qualifying lanes
