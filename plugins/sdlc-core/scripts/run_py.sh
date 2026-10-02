#!/bin/sh
# Run a Python script with the first interpreter that actually works.
# Usage: sh run_py.sh <script.py> [args...]
#
# Hooks used to call `python3` directly. On many Windows machines `python3` is
# missing or is the Microsoft Store stub (which exits non-zero), so we probe
# python3, python and the py launcher in turn. Each candidate is tested with
# `-c ""` before use, so a stub is skipped and the script itself runs only once.
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done
echo "Agentic SDLC: no working Python 3 found (tried python3, python, py). Install Python 3 and add it to PATH." >&2
exit 1
