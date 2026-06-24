@echo off
REM ===========================================================================
REM  run_all.bat  —  ONE click to rebuild every crude-inventory output.
REM  Double-click this file, or run it from a terminal. Pass --watch on a
REM  Wednesday morning to wait for the 10:30 a.m. ET EIA release first:
REM      run_all.bat --watch
REM ===========================================================================
"%~dp0.venv\Scripts\python.exe" "%~dp0analytics\run_all.py" %*
echo.
pause
