@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\Llvm\x64\bin\clang-cl.exe" /nologo /O2 /EHsc /std:c++20 /I repo\ps2xRuntime\include codex_glyph_atlas_check.cpp /Fe:power-scale-trial\codex_glyph_atlas_check.exe /Fo:power-scale-trial\codex_glyph_atlas_check.obj
if errorlevel 1 exit /b %errorlevel%
for %%F in (ui-assets\glyph-atlas-v2\*.gatl) do (
 power-scale-trial\codex_glyph_atlas_check.exe "%%F"
 if errorlevel 1 exit /b 1
)
