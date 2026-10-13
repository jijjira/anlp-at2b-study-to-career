@echo off
REM Windows: double-click this file. First run sets everything up, then opens the app in your browser.
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py) || (set PY=python)
if not exist .venv\Scripts\python.exe %PY% -m venv .venv
call .venv\Scripts\activate.bat
echo Installing what the app needs (first time takes a minute or two)...
pip install -q -r step6_app\requirements-light.txt
python -c "import sentence_transformers" >nul 2>nul
if not errorlevel 1 goto launch
set /p ANS=Also install the deeper hybrid method? Downloads about 2 GB. [y/N] 
if /i "%ANS%"=="y" pip install -q sentence-transformers torch
:launch
REM Skip Streamlit's one-time email prompt
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
  echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"
)
echo Opening the app. Close this window to stop it.
python -m streamlit run step6_app\app.py
pause
