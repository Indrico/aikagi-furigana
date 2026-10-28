@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0mod\Install-Furigana.ps1" -Restore %*
pause
