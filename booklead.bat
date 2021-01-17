@echo off
setlocal enableDelayedExpansion

set APP_DIR=%~dp0
set APP_DIR=%APP_DIR:~0,-1%
set WORK_DIR=%APP_DIR%\work
set PY_VER=python-3.9.1
set PY_EXE=%APP_DIR%\work\%PY_VER%\python.exe
set PY_URL=https://github.com/zencd/git-distribution/releases/download/python-3.9.1/python-3.9.1.exe
set PY_SFX=%APP_DIR%\work\%PY_VER%.exe
set MAIN_PY=%APP_DIR%\main.py

if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"

:: Install python if not yet
if not exist "%PY_EXE%" (
    echo Downloading python from %PY_URL%
    cscript //nologo "%APP_DIR%\tools\dl.vbs" "%PY_URL%" "%PY_SFX%"
    if !errorlevel! neq 0 exit /b 1
    if not exist "%PY_SFX%" exit /b 1

    echo Extracting python sfx
    "%PY_SFX%" -y "-o%WORK_DIR%"
    if !errorlevel! neq 0 exit /b 1

    del /f "%PY_SFX%"

    echo Installing python requirements
    "%PY_EXE%" -m pip install -r "%APP_DIR%\requirements.txt" > nul
    if !errorlevel! neq 0 exit /b 1
)

:: Update the app. Called from update.bat
if "%1" == "--update" (
    set PYTHONPATH=%APP_DIR%\tools
    set DO_HARD_RESET=1
    "%PY_EXE%" "%APP_DIR%\tools\update.py"
    if !errorlevel! neq 0 exit /b 1

    "%PY_EXE%" -m pip install -r "%APP_DIR%\requirements.txt" > nul
    if !errorlevel! neq 0 exit /b 1

    goto end
)

:: Start the app
"%PY_EXE%" "%MAIN_PY%" %*

:end