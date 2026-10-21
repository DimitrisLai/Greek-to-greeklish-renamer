@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title Greek to Greeklish Renamer - Desktop UI
where pyw >nul 2>&1
if not errorlevel 1 (
  start "" pyw -3 "%~dp0greeklish_gui.py"
  exit /b 0
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0greeklish_gui.py"
) else (
  where python >nul 2>&1
  if not errorlevel 1 (
    python "%~dp0greeklish_gui.py"
  ) else (
    echo Python 3.10+ is required for this script edition.
    echo Download the standalone EXE from GitHub Releases to run without Python.
  )
)
pause
