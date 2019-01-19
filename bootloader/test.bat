@echo off
call build.bat
rem
rem		Create a dummy boot.img file
rem
del /Q boot.img
python makedemoimage.py
if exist bootloader.sna ..\bin\CSpect.exe -zxnext -cur -brk -exit -w3 bootloader.sna 


