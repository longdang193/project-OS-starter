from __future__ import annotations

import subprocess
from pathlib import Path


def resolve_repo_root(explicit: str | Path | None = None, *, cwd: Path | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise RuntimeError(f"Repository root does not exist: {root}")
        return root
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode or not completed.stdout.strip():
        raise RuntimeError("Run Project OS script inside a Git repository or pass --repo-root.")
    return Path(completed.stdout.strip()).resolve()
