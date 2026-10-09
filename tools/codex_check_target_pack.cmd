@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /LD /O2 /EHsc /std:c++17 /I repo\ps2xRuntime\include codex_target_pack_test.cpp /Fe:power-scale-trial\codex_target_pack_test.dll /Fo:power-scale-trial\codex_target_pack_test.obj /link /IMPLIB:power-scale-trial\codex_target_pack_test.lib
if errorlevel 1 exit /b %errorlevel%
..\experiments\.full-install\.venv\Scripts\python.exe codex_check_target_pack.py
exit /b %errorlevel%
