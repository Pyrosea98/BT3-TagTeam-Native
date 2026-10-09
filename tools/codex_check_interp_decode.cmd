@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /EHsc /std:c++17 /I repo\ps2xRuntime\include codex_interp_decode_check.cpp /Fe:power-scale-trial\codex_interp_decode_check.exe /Fo:power-scale-trial\codex_interp_decode_check.obj
if errorlevel 1 exit /b %errorlevel%
power-scale-trial\codex_interp_decode_check.exe
exit /b %errorlevel%
