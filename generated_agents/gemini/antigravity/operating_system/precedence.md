# GENERATED FILE - do not edit directly.
# Source: `docs/operating_system/precedence.md`

# Precedence

1. emergency deny/block rules
2. workspace/project runtime rules
3. provider-specific overrides
4. canonical shared rules
5. personal preferences

Conflict policy:
- fail on duplicate rule/workflow/prompt names in the same layer
- fail on missing `required_reads` targets
- fail on broken prompt/workflow references in metadata next_steps
