@echo off
setlocal
set "HERE=%~dp0"
set "PATH=C:\Program Files\CMake\bin;C:\Users\JUAN\AppData\Local\Microsoft\WinGet\Packages\Ninja-build.Ninja_Microsoft.Winget.Source_8wekyb3d8bbwe;C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin;%PATH%"
set "PS2X_SETUP_NO_SUBMODULES=1"
set "PS2X_TARGET_PROFILE=power-scale-beta151"
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%HERE%repo"
python games\bt3\setup.py "%HERE%..\experiments\.full-install\game\maps\expanded-2x.iso" --stage 3 --gen-only --no-deps --yes --non-interactive --plain --log build\power-scale-generation.log
exit /b %errorlevel%
