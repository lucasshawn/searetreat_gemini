# ===================================================
# Sea Retreat Windows Task Scheduler Registration
# ===================================================

$TaskName = "SeaRetreat_Monthly_Melio_Automation"
$ScriptPath = Join-Path -Path $PSScriptRoot -ChildPath "run_automation.bat"

Write-Host "Registering Scheduled Task: $TaskName"
Write-Host "Target Action: $ScriptPath"

# Register Task using schtasks.exe (Monthly on the 2nd day of every month at 9:00 AM)
schtasks /Create /TN "$TaskName" /TR "`"$ScriptPath`"" /SC MONTHLY /D 2 /ST 09:00 /F

if ($LASTEXITCODE -eq 0) {
    Write-Host "Task '$TaskName' successfully registered to run at 9:00 AM on the 2nd of every month."
} else {
    Write-Error "Failed to register task '$TaskName'."
}
