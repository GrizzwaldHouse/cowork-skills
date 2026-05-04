' launch_silent.vbs
' Developer: Marcus Daley
' Date: 2026-05-01
' Purpose: Silently launches launch_dashboard.py (PyQt6) via pythonw so no
'          console window flashes on desktop shortcut double-click.
'          Uses the real pythonw.exe — NOT the Windows App Execution Alias
'          stub which silently fails when called by absolute path in scripts.
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\ClaudeSkills"
WshShell.Run """C:\Users\daley\AppData\Local\Python\bin\pythonw.exe"" -m AgenticOS.launch_dashboard", 0, False
Set WshShell = Nothing
