---
name: runtime-performance-batch1
description: Batch 1 performance optimization summary for runtime governance scripts.
---

# Runtime Performance Batch 1

## Scope

- `scripts/sync_agent_adapters.py`
- `scripts/validate_repo_contracts.py`
- `scripts/validate_adoption_shape.py`

## Implemented Optimizations

1. `sync_agent_adapters.py`
- Added `_write_text_if_changed(...)` to skip rewriting unchanged generated files.
- Applied no-op-write avoidance to single-file sync, tree sync, and codex-rules tree sync paths.
- Expected impact: less filesystem I/O, lower CPU on hashing/comparison-heavy runs, improved maintainability through shared write path.

2. `validate_repo_contracts.py`
- Introduced shared adoption-mode loader helper to avoid duplicated file parse logic.
- Reused helper in `managed_architecture_metadata_enabled` and `read_adoption_mode`.
- Expected impact: reduced duplicated computation and clearer code path.

3. `validate_adoption_shape.py`
- Replaced broad `Path.rglob` scan in `metadata_marker_files` with pruned `os.walk(..., topdown=True)`.
- Prunes skipped directories before traversal and normalizes suffix lookup once.
- Expected impact: faster metadata marker scans and lower traversal overhead in large repos.

## Verification

- `python scripts/sync_agent_adapters.py --check` -> PASS
- `python scripts/validate_generated_header_format.py` -> PASS
- `python scripts/validate_repo_contracts.py --fast` -> PASS

## Measured Runtime (post-batch sample)

- `python scripts/validate_repo_contracts.py --fast`: ~2.891s
- `python scripts/sync_agent_adapters.py --check`: ~0.375s
- `python scripts/validate_adoption_shape.py`: ~0.532s
- `python scripts/validate_agent_runtime_drift.py --skip-deploy-check`: ~0.445s

## Follow-up Candidates

- Add per-run parse cache for repeated YAML/frontmatter reads in deep validators.
- Add optional benchmark harness script for repeatable N-run median/p95 reporting.
- Reduce subprocess orchestration overhead in `validate_repo_contracts.py` via grouped in-process execution where safe.


## Batch 3 Delta (vs Batch 2)

- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_repo_contracts.py --fast`: median 3.0421s -> 2.8131s (-7.53%)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/sync_agent_adapters.py --check`: median 0.3598s -> 0.3862s (+7.34%)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_adoption_shape.py`: median 0.5259s -> 0.5148s (-2.11%)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_agent_runtime_drift.py --skip-deploy-check`: median 0.4425s -> 0.4502s (+1.74%)

## Consolidated Delta (Batch 2 -> Batch 4)

- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/sync_agent_adapters.py --check`
  batch2=0.3598s, batch3=0.3862s (+7.34%), batch4=0.3798s (+5.56% vs batch2)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_adoption_shape.py`
  batch2=0.5259s, batch3=0.5148s (-2.11%), batch4=0.5333s (+1.41% vs batch2)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_agent_runtime_drift.py --skip-deploy-check`
  batch2=0.4425s, batch3=0.4502s (+1.74%), batch4=0.4421s (-0.09% vs batch2)
- `C:\Users\HOANG PHI LONG DANG\AppData\Local\Programs\Python\Python313\python.exe scripts/validate_repo_contracts.py --fast`
  batch2=3.0421s, batch3=2.8131s (-7.53%), batch4=2.7732s (-8.84% vs batch2)
