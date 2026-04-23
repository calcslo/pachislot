$taskName = "PachislotScraping"
$pythonExe = "d:\PycharmProjects\pachislot\.venv\Scripts\python.exe"
$scriptPath = "d:\PycharmProjects\pachislot\ogiya_pscube_slot_scraping.py"
$workingDir = "d:\PycharmProjects\pachislot"

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "$scriptPath --cron" -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Daily -At 5:00AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 4)

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName $taskName -Description "Scrape pachislot data daily at 5 AM"
    
    Write-Host "Task '$taskName' registered successfully." -ForegroundColor Green
} catch {
    Write-Host "Error occurred while registering the task: $_" -ForegroundColor Red
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
