"""
Compatibility shim for legacy deploy command.

Use scripts/deploy_agent_runtime.py for new behavior.
"""

from __future__ import annotations

from deploy_agent_runtime import run


if __name__ == "__main__":
    raise SystemExit(run())
