@echo off
set startupLocation=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
if exist "%startupLocation%\SteamRichPresence.lnk" (
    echo Removing startup script
    del "%startupLocation%\SteamRichPresence.lnk"
    echo To reinstall the startup script rerun this installer
    pause
) else (
    echo Installing startup script
    powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%startupLocation%\SteamRichPresence.lnk');$s.TargetPath='%CD%\windows-run.bat';$s.Save()"
    echo To disable the autorunner rerun this installer
    pause
)