@echo off
cd /d %~dp0
cd..

set paths=%*
if "%~1"=="" (echo Please drag the file^(only folders^) to be converted into this file!&pause&exit /b)

python mmp_convert.py --type mmp_convert --func packing --path %paths%
pause
