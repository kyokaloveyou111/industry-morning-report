param(
    [string]$TaskName = "Industry_Morning_Report",
    [string]$At = "08:35"
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "run_report.ps1"
$projectRoot = Split-Path -Parent $PSScriptRoot
$powershell = (Get-Command powershell.exe -ErrorAction Stop).Source

$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runner`"" `
    -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
Write-Host "Created task '$TaskName' at $At. The task runs only while this user is logged on."

