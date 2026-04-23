@echo off
cd /d "d:\PycharmProjects\pachislot"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=".venv\Scripts\python.exe"
) else (
    set PYTHON_EXE=python
)

%PYTHON_EXE% main.py

if %ERRORLEVEL% NEQ 0 (
    powershell -ExecutionPolicy Bypass -File notify.ps1 -Title "サーバー停止エラー" -Message "Pachislotサーバーがエラーで終了しました。確認してください。"
)
