@echo off
setlocal

set "BRAVE_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
if not exist "%BRAVE_PATH%" (
    set "BRAVE_PATH=C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
)
if not exist "%BRAVE_PATH%" (
    set "BRAVE_PATH=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"
)

if not exist "%BRAVE_PATH%" (
    echo [ERROR] Brave Browser was not found in standard directories.
    pause
    exit /b 1
)

echo ========================================================
echo       Brave Browser Remote Debugging Launcher
echo ========================================================
echo.
echo Choose an option:
echo   [1] Main Profile (Uses your existing logins & extensions)
echo       * Requires closing existing Brave instances first.
echo.
echo   [2] Dedicated Automation Profile (Runs alongside normal Brave)
echo       * Opens a separate Brave window. Log in once and it persists.
echo.
set /p choice="Enter choice (1 or 2, default is 1): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Checking for running Brave processes...
    tasklist /FI "IMAGENAME eq brave.exe" 2>NUL | find /I /N "brave.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo [!] Brave is currently running.
        echo To launch with remote debugging on your main profile,
        echo running Brave windows must be closed.
        set /p killchoice="Close existing Brave windows now? (Y/N): "
        if /i "%killchoice%"=="Y" (
            taskkill /F /IM brave.exe >nul 2>&1
            timeout /t 2 /nobreak >nul
        ) else (
            echo Aborted. Please close Brave manually or choose Option 2.
            pause
            exit /b 0
        )
    )
    echo Launching Brave with Remote Debugging on port 9222 (Main Profile)...
    start "" "%BRAVE_PATH%" --remote-debugging-port=9222 https://chatgpt.com
    echo Done! You can now run the Python automation script.
    timeout /t 3 >nul
    exit /b 0
)

if "%choice%"=="2" (
    set "DEDICATED_DIR=%LOCALAPPDATA%\BraveSoftware\Brave-ChatGPT-Automation\Profile"
    echo Launching Brave with Remote Debugging on port 9222 (Dedicated Profile)...
    start "" "%BRAVE_PATH%" --user-data-dir="%DEDICATED_DIR%" --remote-debugging-port=9222 --no-first-run --no-default-browser-check https://chatgpt.com
    echo Done! If this is your first time, please log in to ChatGPT in the opened window.
    timeout /t 3 >nul
    exit /b 0
)

echo Invalid choice.
pause
