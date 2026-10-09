@echo off
setlocal
set "HERE=%~dp0"
set "PATH=C:\Program Files\CMake\bin;C:\Users\JUAN\AppData\Local\Microsoft\WinGet\Packages\Ninja-build.Ninja_Microsoft.Winget.Source_8wekyb3d8bbwe;C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin;%PATH%"
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%HERE%repo"
cmake -S . -B build -DPS2X_DISABLE_PGS=OFF -DPS2X_DISABLE_SEAMVK=OFF -DPS2X_GRANITE_DIR="%HERE%repo/ps2xRuntime/third_party/parallel-gs/Granite"
if errorlevel 1 exit /b %errorlevel%
cmake --build build --target ps2EntryRunner --config Release -j 7
if errorlevel 1 exit /b %errorlevel%
copy /y "build\ps2xRuntime\ps2EntryRunner.exe" "build\ps2xRuntime\ps2EntryRunner-vulkan.exe"
