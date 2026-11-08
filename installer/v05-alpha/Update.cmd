@echo off
setlocal
set "GAME=%~1"
if not defined GAME set /p "GAME=Existing BT3 Tag Team 0.4.1 or 0.5.alpha installation folder: "
if not exist "%GAME%\runtime\python.exe" (echo Supported installation not found.& pause& exit /b 1)
"%GAME%\runtime\python.exe" -B "%~dp0update.py" "%GAME%"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
