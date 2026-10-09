@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin\clang-cl.exe" /nologo /O2 /EHsc /std:c++20 /DPS2X_RAM_MB=128 /I repo\ps2xRuntime\include codex_ki_trace_check.cpp repo\ps2xRuntime\src\lib\ps2_ki_trace.cpp /Fe:power-scale-trial\codex_ki_trace_check.exe /Fo:power-scale-trial\
if errorlevel 1 exit /b %errorlevel%
power-scale-trial\codex_ki_trace_check.exe
exit /b %errorlevel%
