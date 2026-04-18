#!/usr/bin/env sh
set -eu

repo_root="$(git rev-parse --show-toplevel)"
hook_path="$repo_root/.git/hooks/pre-commit"
mkdir -p "$(dirname "$hook_path")"

cat > "$hook_path" <<'HOOK'
#!/bin/sh
set -eu

if [ -x "./.venv/Scripts/python.exe" ]; then
  ./.venv/Scripts/python.exe scripts/sync_architecture_docs.py --check
else
  ./.venv/bin/python scripts/sync_architecture_docs.py --check
fi
HOOK

chmod +x "$hook_path"
printf 'Installed pre-commit hook at %s\n' "$hook_path"
