# Adoption Guide

Adopt only layers needed by current repository:

1. Copy root agent instructions and canonical skills.
2. Keep executable repository configuration in `repo_config/` only when an active script consumes it.
3. Run `python scripts/validate_repo_contracts.py --fast`.
4. Add planning artifacts only when complexity requires them.

Code discovery remains source-first. Describe required capability and evidence
before selecting a runtime tool. Resolve unmet capabilities through
`docs/operating_system/tooling/runtime-tool-resolution.md`; unavailable tools
never block safe work and never replace mandatory evidence.
