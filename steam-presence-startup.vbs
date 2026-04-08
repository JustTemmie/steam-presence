Option Explicit

Dim fso, shell
Dim scriptDir, mainScript, pythonwExe, pythonExe, command

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
mainScript = fso.BuildPath(scriptDir, "main.py")
pythonExe = fso.BuildPath(scriptDir, "venv\Scripts\python.exe")

If fso.FileExists(pythonExe) Then
    command = pythonExe & " -u " & """" & mainScript & """"
Else
    WScript.Quit 1
End If

shell.CurrentDirectory = scriptDir
shell.Run command, 0, False
