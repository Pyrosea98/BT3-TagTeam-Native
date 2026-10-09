@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /O2 /EHsc /std:c++17 /I repo\ps2xRuntime\include codex_target_trace_check.cpp /Fe:power-scale-trial\codex_target_trace_check.exe /Fo:power-scale-trial\codex_target_trace_check.obj
if errorlevel 1 exit /b %errorlevel%
power-scale-trial\codex_target_trace_check.exe
exit /b %errorlevel%
