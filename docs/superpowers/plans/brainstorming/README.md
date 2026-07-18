# Brainstorming Report Storage

Create saved brainstorming report only when user requests detailed report.

## Save Contract

Canonical path:

```text
docs/superpowers/plans/brainstorming/<report_id>/report.md
```

New IDs use:

```text
YYYY-MM-DD-HH-MM-<topic>
```

Existing report IDs and bundles are grandfathered.

Minimum structure:

```text
docs/superpowers/plans/brainstorming/<report_id>/
  report.md
```

Rules:

1. Use `docs/operating_system/templates/brainstorming-detailed-report-template.md`.
2. Keep report exploratory; accepted recommendations move to approved scope or specification.
3. Link supporting files directly only when they materially help.
4. Redact secrets before saving linked inputs.
5. Do not create context summaries, manifests, placeholder evidence folders, or duplicate planning artifacts.

## Create

```powershell
.\scripts\new_brainstorming_report.ps1 -ReportId <YYYY-MM-DD-HH-MM-topic>
```

`skill-brainstorming` owns report creation and updates.
