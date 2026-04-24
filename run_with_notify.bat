@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
"%PYTHON_EXE%" main.py
if %ERRORLEVEL% neq 0 (
    powershell -ExecutionPolicy Bypass -File notify.ps1 -ErrorCode %ERRORLEVEL%
)
endlocal