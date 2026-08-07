$ErrorActionPreference = "Stop"

function Ensure-File {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [string]$InitialContent
    )

    if (Test-Path $Path) {
        return
    }

    $parent = Split-Path -Path $Path -Parent
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    Write-Host "Creating $(Split-Path -Path $Path -Leaf)"
    if ($null -ne $InitialContent) {
        Set-Content -Path $Path -Value $InitialContent -Encoding ASCII -NoNewline
    } else {
        New-Item -ItemType File -Path $Path -Force | Out-Null
    }
}

function Invoke-PythonCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @Arguments
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python @Arguments
    } else {
        throw "Python 3 was not found in PATH. Install Python 3.8+ first."
    }

    if ($LASTEXITCODE -ne 0) {
        $joined = $Arguments -join " "
        throw "Python command failed with exit code ${LASTEXITCODE}: $joined"
    }
}

try {
    if ($env:OS -ne "Windows_NT") {
        throw "Unsupported OS. This script is designed for Windows only."
    }

    Write-Host "Installing Steam Presence for Windows. If you encounter bugs, please open an issue."
    Read-Host "Press the Enter key to continue" | Out-Null
    Write-Host ""

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $scriptDir

    $configPath = Join-Path $scriptDir "config.json"
    if (-not (Test-Path $configPath)) {
        Write-Host "Error: config.json was not found. Make sure it exists in this directory."
        Write-Host "Files in current directory:"
        Get-ChildItem -Name
        exit 1
    }

    $dataMetaPath = Join-Path $scriptDir "data\meta.json"
    $useDataLayout = $false

    if (Test-Path $dataMetaPath) {
        try {
            $meta = Get-Content -Path $dataMetaPath -Raw | ConvertFrom-Json
            if ($meta."structure-version" -eq "1") {
                $useDataLayout = $true
            }
        } catch {
            Write-Host "Warning: Failed to parse data/meta.json. Falling back to legacy file layout for compatibility."
        }
    }

    if ($useDataLayout) {
        $dataDir = Join-Path $scriptDir "data"
        Ensure-File -Path (Join-Path $dataDir "games.txt")
        Ensure-File -Path (Join-Path $dataDir "icons.txt")
        Ensure-File -Path (Join-Path $dataDir "customGameIDs.json") -InitialContent "{}"
    } else {
        Ensure-File -Path (Join-Path $scriptDir "games.txt")
        Ensure-File -Path (Join-Path $scriptDir "icons.txt")
        Ensure-File -Path (Join-Path $scriptDir "customGameIDs.json") -InitialContent "{}"
    }

    Write-Host "Setting up virtual environment"
    $venvDir = Join-Path $scriptDir "venv"
    $venvPython = Join-Path $venvDir "Scripts\python.exe"

    if (-not (Test-Path $venvPython)) {
        Invoke-PythonCommand -Arguments @("-m", "venv", $venvDir)
    }

    & $venvPython -m pip install --upgrade pip wheel
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip and wheel."
    }

    & $venvPython -m pip install -r (Join-Path $scriptDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements.txt dependencies."
    }

    Write-Host ""
    Write-Host "Testing if the script works"
    Write-Host ""

    $stdoutPath = Join-Path $env:TEMP "steam-presence-test.stdout.log"
    $stderrPath = Join-Path $env:TEMP "steam-presence-test.stderr.log"

    Remove-Item $stdoutPath -ErrorAction SilentlyContinue
    Remove-Item $stderrPath -ErrorAction SilentlyContinue

    $testProcess = Start-Process -FilePath $venvPython -ArgumentList (Join-Path $scriptDir "main.py") -WorkingDirectory $scriptDir -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

    Start-Sleep -Milliseconds 2500
    if (-not $testProcess.HasExited) {
        Stop-Process -Id $testProcess.Id -Force
    }

    if ((Test-Path $stderrPath) -and ((Get-Item $stderrPath).Length -gt 0)) {
        Write-Host "The test run produced stderr output:"
        Get-Content -Path $stderrPath
    }

    Write-Host "Test finished."

    $startupRunnerPath = Join-Path $scriptDir "steam-presence-startup.vbs"
    if (-not (Test-Path $startupRunnerPath)) {
        throw "steam-presence-startup.vbs was not found in this directory."
    }

    $startupFolder = [Environment]::GetFolderPath("Startup")
    if (-not (Test-Path $startupFolder)) {
        New-Item -ItemType Directory -Path $startupFolder -Force | Out-Null
    }

    $shortcutPath = Join-Path $startupFolder "Steam Presence.lnk"
    $wscriptExe = Join-Path $env:SystemRoot "System32\wscript.exe"

    Write-Host "Creating startup shortcut in shell:startup"
    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $wscriptExe
    $shortcut.Arguments = "//B //Nologo `"$startupRunnerPath`""
    $shortcut.WorkingDirectory = $scriptDir
    $shortcut.Description = "Start Steam Presence silently when you sign in"
    $shortcut.IconLocation = "$venvPython,0"

    $shortcut.Save()

    Write-Host ""
    Write-Host "Installation complete. Starting Steam Presence."
    Start-Process -FilePath $shortcutPath

    Write-Host ""
    Write-Host "If you encountered errors with this script, please create an issue on the GitHub page."
    Write-Host "Startup shortcut created at: $shortcutPath"
    Write-Host "Script completed."
}
catch {
    Write-Error $_
    exit 1
}