@echo off
cd /d %~dp0
cd..

set paths=%*
if "%~1"=="" (echo Please drag the folders to be converted into this file!&pause&exit /b)

python mmp_convert.py --type mmp_convert --func StdUnify --path %paths%
REM python mmp_convert.py --type mmp_convert --func StdUnify --path %paths% --format bmp -kl

pause
