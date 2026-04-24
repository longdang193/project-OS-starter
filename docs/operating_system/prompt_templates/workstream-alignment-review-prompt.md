# Workstream Alignment Review Prompt

Use this when you want to check whether a proposed change really belongs to the
named workstream.

```text
Review whether this proposed change belongs to the named workstream.

Change context:
- proposed change:
- proposed workstream id:
- workstream doc:
- why I think it belongs there:
- possible operating_system angle:

Please:
1. assess whether the change fits the named workstream
2. recommend a different registered workstream if the fit is weak
3. say if this should really use `parent_workstream: none` because it is operating_system work
4. explain the reasoning briefly
5. recommend the next artifact or prompt to use
```

Expected output:
- alignment assessment plus the recommended next step
