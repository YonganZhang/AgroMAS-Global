#!/usr/bin/env bash
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PCSE_PROJECT_HOME="$PROJECT_ROOT/cache/pcse-home"
export MPLCONFIGDIR="$PROJECT_ROOT/cache/matplotlib"
export XDG_CACHE_HOME="$PROJECT_ROOT/cache"
export TMPDIR="$PROJECT_ROOT/cache/tmp"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
export MPLBACKEND=Agg
export PYTHONPATH="$PROJECT_ROOT/NUE_PCSE-Gym:$PROJECT_ROOT/pcse${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$PROJECT_ROOT/.venv/bin:$PATH"

export PCSE_MP_START_METHOD=fork
