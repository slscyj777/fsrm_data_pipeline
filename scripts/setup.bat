@echo off
cd /d "%~dp0.."

where uv  2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)
uv sync  2>sync_error.log
if %errorlevel% neq 0 (
    echo Setup failed:
    type sync_error.log
    pause
    exit /b 1
)
del sync_error.log
pause