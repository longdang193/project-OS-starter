# Adoption Guide

Adopt only layers needed by current repository:

1. Copy root agent instructions and canonical skills.
2. Keep executable repository configuration in `repo_config/` only when an active script consumes it.
3. Run `python scripts/validate_repo_contracts.py --fast`.
4. Add planning artifacts only when complexity requires them.

Code discovery remains source-first. Use Serena for exact symbols and references, `semble_codebase_search` for unknown-location discovery, and `ast_grep_preview` for structural preview when available. Use private read-only GitNexus only when available and fresh.
