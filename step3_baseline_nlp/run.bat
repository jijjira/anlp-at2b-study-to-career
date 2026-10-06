@echo off
REM Double-click this file (Windows). Sets up the first time, checks the code, opens the main notebook.
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py) || (set PY=python)
if not exist .venv\Scripts\python.exe %PY% -m venv .venv
call .venv\Scripts\activate.bat
echo Installing what the project needs (first time takes a minute or two)...
pip install -q -r requirements.txt
echo Checking the code works...
python -m pytest -q -p no:cacheprovider
echo Opening the main notebook in your browser. Use Kernel, then Restart Kernel and Run All Cells.
jupyter lab 08_real_curriculum_case_study.ipynb
pause
