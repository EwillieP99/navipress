#!/bin/bash
# Mac setup for the NaviGator WordPress Agent.
# In Terminal, drag this folder in after typing "cd ", press Return, then run:
#   bash setup.sh

cd "$(dirname "$0")" || exit 1
echo "== NaviGator WordPress Agent setup (Mac) =="

# 1. Find Python 3.10 or newer. The python3 that comes with macOS is 3.9: too old.
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo
  echo "You need Python 3.10 or newer."
  echo "Download the macOS installer from https://www.python.org/downloads/ ,"
  echo "install it, close Terminal, open a new one, and run: bash setup.sh"
  exit 1
fi
echo "Using $($PY --version)"

# 2. Create a private Python environment for this project.
if [ ! -d .venv ]; then
  echo "Creating .venv (about 30 seconds)..."
  "$PY" -m venv .venv || { echo "Couldn't create .venv"; exit 1; }
fi

# 3. Install the four packages listed in requirements.txt.
echo "Installing packages..."
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements.txt || { echo "Package install failed"; exit 1; }

# 4. Create your private settings file and open it.
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env. It's opening in TextEdit: fill it in and save."
  open -e .env
else
  echo ".env already exists (left unchanged)."
fi

echo
echo "Setup done. Next, in this Terminal window:"
echo "  source .venv/bin/activate"
echo "  python navipress.py login    # one-time WordPress sign-in"
echo "  python navipress.py check    # confirm everything works"
