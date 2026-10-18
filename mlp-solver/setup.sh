#!/bin/sh
set -eu
cd "$(dirname "$0")"
MLP_SOLVER_PYTHON="${MLP_SOLVER_PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then
  "$MLP_SOLVER_PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.venv/bin/python -B run.py doctor
