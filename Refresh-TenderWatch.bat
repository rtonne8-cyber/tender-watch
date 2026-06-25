@echo off
setlocal
set "PATH=C:\Program Files\GitHub CLI;C:\Program Files\nodejs;%PATH%"
title TenderWatch Refresh

echo ============================================
echo  TenderWatch - triggering live data refresh
echo ============================================
echo.

gh workflow run refresh.yml --repo rtonne8-cyber/tender-watch
if errorlevel 1 (
    echo.
    echo Something went wrong. Make sure you're logged in: gh auth status
    pause
    exit /b 1
)

echo.
echo Triggered. Usually takes 1-2 minutes to refresh data and redeploy.
echo.
echo Progress:  https://github.com/rtonne8-cyber/tender-watch/actions
echo Dashboard: https://rtonne8-cyber.github.io/tender-watch/
echo.
pause
