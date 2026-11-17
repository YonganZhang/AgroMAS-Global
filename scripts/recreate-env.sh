#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
if [[ -e .venv ]]; then
    printf 'Refusing to replace existing environment: %s/.venv\n' "$PROJECT_ROOT" >&2
    exit 1
fi
export UV_CACHE_DIR="$PROJECT_ROOT/cache/uv"
export UV_PYTHON_INSTALL_DIR="$PROJECT_ROOT/cache/python"
export TMPDIR="$PROJECT_ROOT/cache/tmp"
mkdir -p "$TMPDIR"
uv venv --python 3.11.15 .venv
uv pip install --python .venv/bin/python 'torch==2.15.0+cpu' --index-url https://download.pytorch.org/whl/cpu
python3 - <<'PY'
from pathlib import Path
lines=Path('reports/requirements.lock').read_text().splitlines()
Path('cache/replay-requirements.txt').write_text('\n'.join(x for x in lines if not x.startswith(('-e ', 'torch==')))+'\n')
PY
uv pip install --python .venv/bin/python --no-deps -r cache/replay-requirements.txt
uv pip install --python .venv/bin/python --no-deps -e ./pcse
# Exact recorded stack intentionally retains the author's rllte --no-deps recipe.
