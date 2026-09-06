from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_RUNTIME_ROOT = Path.home() / ".agents" / "project-os"


def runtime_script(name: str) -> Path:
    local_path = PROJECT_ROOT / "scripts" / name
    if local_path.is_file():
        return local_path
    return GLOBAL_RUNTIME_ROOT / "scripts" / name


def runtime_doc(relative_path: str) -> Path:
    local_path = PROJECT_ROOT / relative_path
    if local_path.is_file():
        return local_path
    return GLOBAL_RUNTIME_ROOT / relative_path


def add_runtime_import_roots() -> None:
    for root in (PROJECT_ROOT, GLOBAL_RUNTIME_ROOT):
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
