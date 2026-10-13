#!/bin/bash
# Mac: double-click this file (or run:  bash run_app.command).
# First run sets everything up, then opens the Study-to-Career app in your browser.
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Get it from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close"; exit 1
fi
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
echo "Installing what the app needs (first time takes a minute or two)..."
pip install -q -r step6_app/requirements-light.txt || { echo "Install failed. Check your internet and try again."; read -r -p "Press Enter to close"; exit 1; }
if ! python -c "import sentence_transformers" >/dev/null 2>&1; then
  read -r -p "Also install the deeper (hybrid) method? Downloads about 2 GB. [y/N] " ans
  if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
    pip install -q sentence-transformers torch || echo "Could not install it. The fast method still works."
  fi
fi
# Skip Streamlit's one-time email prompt
mkdir -p "$HOME/.streamlit"
[ -f "$HOME/.streamlit/credentials.toml" ] || printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
echo "Opening the app. Close this window to stop it."
python -m streamlit run step6_app/app.py
