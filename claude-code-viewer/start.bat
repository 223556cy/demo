@echo off
rem Start Claude Code Viewer with Windows-compatible claude executable (.exe, not .cmd shim)
cd /d %~dp0
node dist\main.js --port 3400 --executable "%AppData%\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe" %*
