@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
py matching.py
echo.
echo Results are in step5_matching\outputs
pause
