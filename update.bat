@echo off
setlocal enableDelayedExpansion

set APP_DIR=%~dp0
set APP_DIR=%APP_DIR:~0,-1%
"%APP_DIR%\booklead.bat" --update