@echo off
REM Launches EPP Viewer using pythonw (no console window) if available,
REM otherwise falls back to python. Double-click this file to run the app.

cd /d "%~dp0"

where pythonw >nul 2>nul
if %ERRORLEVEL%==0 (
    start "" pythonw epp_viewer.py %*
) else (
    python epp_viewer.py %*
    if errorlevel 1 pause
)
