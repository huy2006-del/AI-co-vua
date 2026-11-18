#!/bin/bash

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  python3 -m venv "$ROOT/.venv" || exit 1
fi

"$PYTHON" -c 'import chess, pygame, pandas, matplotlib' >/dev/null 2>&1 || {
  echo "Installing project dependencies..."
  "$PYTHON" -m pip install -r "$ROOT/requirements.txt" || exit 1
}

cd "$ROOT/AI-co-vua-Wood" || exit 1
export PYTHONPATH="$PWD/backend:$PWD${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m frontend.gui.app "$@"
