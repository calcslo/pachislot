@echo off
echo タスクスケジューラに自動実行タスクを登録します...
echo.

:: 実行ポリシーを一時的にBypassしてPowerShellスクリプトを実行
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0setup_task_scheduler.ps1'"

echo.
pause
