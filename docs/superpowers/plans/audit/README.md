# Audit Report Storage

Use formal audit report only when `docs/operating_system/rules/audit-evidence-mandate-rule.md` triggers or user explicitly requests one.

## Save Contract

Canonical path:

```text
docs/superpowers/plans/audit/<audit_id>/report.md
```

New IDs use:

```text
YYYY-MM-DD-HH-MM-<topic>
```

Existing audit IDs and bundles are grandfathered.

Minimum structure:

```text
docs/superpowers/plans/audit/<audit_id>/
  report.md
  evidence/    # optional; only when real evidence files exist
  repro/       # optional; only when runnable assets do not fit in report
```

Rules:

1. Use `docs/operating_system/templates/audit-report-with-evidence-template.md`.
2. Keep reproduction commands in `report.md` unless separate files add real value.
3. Link supporting files with repo-relative paths.
4. Redact secrets before saving evidence.
5. Do not create placeholder files, empty evidence folders, manifests, artifact indexes, or report checklists.

## Create

```powershell
.\scripts\new_audit.ps1 -AuditId <YYYY-MM-DD-HH-MM-topic>
```

`skill-systematic-debugging` owns report creation and updates. `skill-verification-before-completion` checks required audit evidence only when mandate applies.
