#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
python3 matching.py
echo "Results are in step5_matching/outputs"
