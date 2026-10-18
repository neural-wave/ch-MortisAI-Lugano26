#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Run ./setup.sh first.' >&2
  exit 1
fi
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
if [ "$#" -eq 0 ]; then
  exec .venv/bin/python -B run.py doctor
fi
exec .venv/bin/python -B run.py "$@"
