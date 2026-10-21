@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title Greek to Greeklish Renamer v2.0.0
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0rename_greek_to_greeklish.py" %*
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        python "%~dp0rename_greek_to_greeklish.py" %*
    ) else (
        echo Python 3 is needed. Install Python 3.10 or newer.
        echo https://www.python.org/downloads/
    )
)
echo.
pause
