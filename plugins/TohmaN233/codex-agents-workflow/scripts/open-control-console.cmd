@echo off
setlocal

where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js 20 or newer is required.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0open-installed-console.ps1" %*
set "exit_code=%ERRORLEVEL%"
if not "%exit_code%"=="0" pause
exit /b %exit_code%
