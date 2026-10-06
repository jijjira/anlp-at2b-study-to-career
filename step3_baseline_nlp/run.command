#!/bin/bash
# Double-click this file (Mac) or run:  bash run.command
# It sets everything up the first time, checks the code works, then opens the main notebook.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Get it from https://www.python.org/downloads/ and run this again."; read -r -p "Press Enter to close"; exit 1
fi
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
echo "Installing what the project needs (first time takes a minute or two)..."
pip install -q -r requirements.txt || { echo "Install failed. Check your internet and try again."; read -r -p "Press Enter to close"; exit 1; }
echo "Checking the code works..."
python -m pytest -q -p no:cacheprovider
[ -n "$NO_JUPYTER" ] && exit 0
echo "Opening the main notebook in your browser. Use Kernel > Restart Kernel and Run All Cells."
jupyter lab 08_real_curriculum_case_study.ipynb
