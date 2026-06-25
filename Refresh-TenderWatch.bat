@echo off
setlocal enabledelayedexpansion
set "PATH=C:\Program Files\GitHub CLI;C:\Program Files\nodejs;%PATH%"
set "REPO=rtonne8-cyber/tender-watch"
title TenderWatch Refresh

echo ============================================
echo  TenderWatch - triggering live data refresh
echo ============================================
echo.

for /f "tokens=*" %%i in ('gh run list --workflow=refresh.yml --repo %REPO% --limit 1 --json databaseId --jq ".[0].databaseId // 0"') do set "PREV_ID=%%i"

gh workflow run refresh.yml --repo %REPO%
if errorlevel 1 (
    echo.
    echo Could not trigger the run. Make sure you're logged in: gh auth status
    pause
    exit /b 1
)

echo Waiting for the run to start...
set "NEW_ID=%PREV_ID%"
:waitloop
ping -n 4 127.0.0.1 >nul
for /f "tokens=*" %%i in ('gh run list --workflow=refresh.yml --repo %REPO% --limit 1 --json databaseId --jq ".[0].databaseId // 0"') do set "NEW_ID=%%i"
if "%NEW_ID%"=="%PREV_ID%" goto waitloop

echo Run started: https://github.com/%REPO%/actions/runs/%NEW_ID%
echo.
echo Watching progress - this usually takes 1-2 minutes...
echo.

gh run watch %NEW_ID% --repo %REPO% --exit-status
set "RESULT=%errorlevel%"

echo.
if "%RESULT%"=="0" (
    echo Refresh complete. Opening the dashboard...
    start "" "https://rtonne8-cyber.github.io/tender-watch/"
) else (
    echo The run did not finish successfully. Check the log here:
    echo https://github.com/%REPO%/actions/runs/%NEW_ID%
)

echo.
pause
