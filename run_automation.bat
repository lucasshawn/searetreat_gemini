@echo off
REM ===================================================
REM Sea Retreat Monthly Melio Automation Runner
REM ===================================================
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo [%DATE% %TIME%] Starting Sea Retreat Monthly Automation >> logs\runner.log
python src\monthly_automation.py >> logs\runner.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Monthly automation failed with code %ERRORLEVEL% >> logs\runner.log
    exit /b %ERRORLEVEL%
)

echo [%DATE% %TIME%] Monthly automation completed successfully >> logs\runner.log

