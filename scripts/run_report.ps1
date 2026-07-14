param(
    [int]$TimeoutMinutes = 20
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$runnerLog = Join-Path $projectRoot "logs\runner.log"
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-RunnerLog([string]$Message) {
    $directory = Split-Path -Parent $runnerLog
    [IO.Directory]::CreateDirectory($directory) | Out-Null
    $line = "[{0}] {1}{2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message, [Environment]::NewLine
    [IO.File]::AppendAllText($runnerLog, $line, $utf8)
}

try {
    $python = (Get-Command python -ErrorAction Stop).Source
    Write-RunnerLog "Starting report run"
    $process = Start-Process -FilePath $python `
        -ArgumentList @("-m", "morning_report", "run") `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -PassThru

    if (-not $process.WaitForExit($TimeoutMinutes * 60 * 1000)) {
        $process.Kill()
        Write-RunnerLog "Timed out after $TimeoutMinutes minutes"
        exit 124
    }

    $exitCode = $process.ExitCode
    Write-RunnerLog "Finished with exit code $exitCode"
    exit $exitCode
} catch {
    Write-RunnerLog "Runner error: $($_.Exception.GetType().Name)"
    exit 1
}

