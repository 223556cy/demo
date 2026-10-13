@echo off
rem Import Hermes sessions and restart Claude Code Viewer to force fullSync.
rem
rem Usage: import-hermes.bat
rem
rem Side effects:
rem   - Adds N session files to %USERPROFILE%\.claude\projects\<encoded cwd>\
rem   - Kills any running CCV server on :3400 and starts a fresh one
rem   - Leaves /tmp/ccv.log containing the most recent server output

setlocal
set "PROJECT_DIR=%~dp0.."
pushd "%PROJECT_DIR%"

where python >nul 2>&1
if errorlevel 1 (
    echo [error] python not found in PATH
    popd
    exit /b 1
)

echo === Converting Hermes sessions ===
python "%PROJECT_DIR%\dev\hermes-to-ccv.py"
if errorlevel 1 (
    echo [error] conversion failed
    popd
    exit /b 1
)

echo === Restarting CCV to force fullSync ===
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":3400.*LISTENING"') do (
    if not "%%P"=="" (
        taskkill /PID %%P /F >nul 2>&1
        echo Killed stale PID %%P
    )
)
timeout /t 3 /nobreak >nul

start "" /b node "%PROJECT_DIR%\dist\main.js" --port 3400 --executable "%AppData%\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
echo Started fresh CCV server on http://localhost:3400
popd
endlocal
