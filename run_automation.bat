@echo off
REM ===================================================
REM Sea Retreat Monthly Melio Automation Runner
REM ===================================================
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

echo [%DATE% %TIME%] Starting Sea Retreat Monthly Automation >> logs\monthly_automation.log
python src\monthly_automation.py >> logs\monthly_automation.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] ERROR: Monthly automation failed with code %ERRORLEVEL% >> logs\monthly_automation.log
    exit /b %ERRORLEVEL%
)

echo [%DATE% %TIME%] Monthly automation completed successfully >> logs\monthly_automation.log
