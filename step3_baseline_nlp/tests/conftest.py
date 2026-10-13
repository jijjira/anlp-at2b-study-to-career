"""Run the Step 3 tests from anywhere: put the step folder on the path and use it as the working directory,
because the modules and tests read data files by relative name (job_cleaned.csv, sample_unit_outline.pdf, ...)."""
import os
import sys
from pathlib import Path

STEP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STEP))
os.chdir(STEP)
