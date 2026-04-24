Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
BatchPath = fso.BuildPath(ScriptDir, "run_with_notify.bat")

WshShell.Run "cmd.exe /c """ & BatchPath & """", 0, False
