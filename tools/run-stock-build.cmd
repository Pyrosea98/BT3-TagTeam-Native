@echo off
setlocal
set "HERE=%~dp0"
set "PATH=C:\Program Files\CMake\bin;C:\Users\JUAN\AppData\Local\Microsoft\WinGet\Packages\Ninja-build.Ninja_Microsoft.Winget.Source_8wekyb3d8bbwe;C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin;%PATH%"
set "PS2X_SETUP_NO_SUBMODULES=1"
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%HERE%repo"
python games\bt3\setup.py --skip-setup --stage 3 --no-deps --yes --non-interactive --plain --no-package --log build\stock-build.log
exit /b %errorlevel%
