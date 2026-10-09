@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
cl /nologo /EHsc /std:c++17 /O2 /MT /Irepo\build\_deps\nlohmann_json-src\include installer\disc_import.cpp /Fe:installer\disc-import.exe /Fo:installer\disc-import.obj bcrypt.lib
exit /b %errorlevel%
