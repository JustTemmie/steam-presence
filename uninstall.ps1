# Requires Windows PowerShell or PowerShell on Windows

$ErrorActionPreference = "Stop"

try {
    if ($env:OS -ne "Windows_NT") {
        throw "Unsupported OS. This script is designed for Windows only."
    }

    Write-Host "Uninstalling Steam Presence for Windows. Please confirm you want to continue."
    Read-Host "Press the Enter key to continue" | Out-Null
    Write-Host ""

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir

    $mainScriptPath = Join-Path $scriptDir "main.py"
    $startupScriptPath = Join-Path $scriptDir "steam-presence-startup.vbs"
    $venvDir = Join-Path $scriptDir "venv"
    $projectLogPath = Join-Path $scriptDir "steam-presence.log"

    Write-Host "Stopping running Steam Presence processes"
    $mainScriptPattern = [Regex]::Escape($mainScriptPath)
    $startupScriptPattern = [Regex]::Escape($startupScriptPath)

    $processes = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -in @("python.exe", "pythonw.exe") -and $_.CommandLine -and $_.CommandLine -match $mainScriptPattern) -or
        ($_.Name -in @("wscript.exe", "cscript.exe") -and $_.CommandLine -and $_.CommandLine -match $startupScriptPattern)
    }

    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
            Write-Host "Stopped process $($process.ProcessId) ($($process.Name))"
        } catch {
            Write-Host "Warning: Failed to stop process $($process.ProcessId) ($($process.Name))."
        }
    }

    $startupFolder = [Environment]::GetFolderPath("Startup")
    if ($startupFolder -and (Test-Path $startupFolder)) {
        $shortcutPath = Join-Path $startupFolder "Steam Presence.lnk"
        if (Test-Path $shortcutPath) {
            Write-Host "Removing startup shortcut"
            Remove-Item -Path $shortcutPath -Force
        } else {
            Write-Host "Startup shortcut was not found."
        }
    }

    if (Test-Path $venvDir) {
        Write-Host "Removing virtual environment"
        Remove-Item -Path $venvDir -Recurse -Force
    } else {
        Write-Host "Virtual environment was not found."
    }

    if (Test-Path $projectLogPath) {
        Write-Host "Removing log file"
        Remove-Item -Path $projectLogPath -Force
    }

    $tempStdoutPath = Join-Path $env:TEMP "steam-presence-test.stdout.log"
    $tempStderrPath = Join-Path $env:TEMP "steam-presence-test.stderr.log"
    Remove-Item -Path $tempStdoutPath -ErrorAction SilentlyContinue
    Remove-Item -Path $tempStderrPath -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Uninstallation completed. If you want to remove project files, delete this folder manually."
}
catch {
    Write-Error $_
    exit 1
}