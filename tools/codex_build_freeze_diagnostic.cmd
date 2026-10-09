@echo off
setlocal
set "TASK_DIR=%~dp0"
set "TASK_RUNNER_OUTPUT=ps2EntryRunner-freeze-diagnostic"
if not "%~1"=="" set "TASK_RUNNER_OUTPUT=%~1"
set "PATH=C:\Program Files\CMake\bin;C:\Users\JUAN\AppData\Local\Microsoft\WinGet\Packages\Ninja-build.Ninja_Microsoft.Winget.Source_8wekyb3d8bbwe;C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin;%PATH%"
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%TASK_DIR%repo"
if "%~2"=="--incremental" goto build
cmake -S . -B build "-DPS2X_RUNNER_OUTPUT_NAME=%TASK_RUNNER_OUTPUT%" -DFETCHCONTENT_UPDATES_DISCONNECTED=ON -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DPS2X_DISABLE_PGS=OFF -DPS2X_DISABLE_SEAMVK=OFF -DPS2X_GRANITE_DIR="%TASK_DIR%repo/ps2xRuntime/third_party/parallel-gs/Granite"
if errorlevel 1 exit /b %errorlevel%
:build
cmake --build build --target ps2EntryRunner --config Release -j 7
exit /b %errorlevel%
