# Project Adoption Migration

Bootstrap shared runtime before adopting generated Starter kit:

1. Deploy shared Project OS runtime from the source repository with `py -3 scripts/deploy_agent_runtime.py --target all`.
2. Validate deployment with `py -3 scripts/deploy_agent_runtime.py --target all --check`.
3. Build and validate generated Starter kit from the source repository.
4. Copy that generated kit into the new repository without mixing in source-only factory files.
5. Preserve product code and tests, then replace starter identity and project-specific docs.
6. Remove optional layers only when their references and consumers are removed together.
7. Run `py -3 "$HOME/.agents/project-os/scripts/validate_repo_contracts.py" --repo-root . --fast` from the adopted repository.

Code discovery remains source-first. Describe required capability and evidence
before selecting a runtime tool. Resolve unmet capabilities through
`docs/operating_system/tooling/runtime-tool-resolution.md`; unavailable tools
never block safe work and never replace mandatory evidence.

Do not use manual file-by-file copying as the primary adoption path. Do not
import generated architecture lineage, private tooling state, or source-only
adapter machinery into consume-only repositories.
