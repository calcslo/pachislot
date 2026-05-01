@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "logs" mkdir "logs"

echo Checking for existing server on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a...
    taskkill /F /PID %%a
)
timeout /t 1 /nobreak >nul

"%PYTHON_EXE%" main.py 1>>"logs\server_stdout.log" 2>>"logs\server_stderr.log"
if %ERRORLEVEL% neq 0 (
    powershell -ExecutionPolicy Bypass -File notify.ps1 -ErrorCode %ERRORLEVEL%
)
endlocal
