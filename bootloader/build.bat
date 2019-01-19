@echo off
rem
rem		Delete old files
rem
del /Q bootloader.sna 
del /Q ..\files\bootloader.sna
rem
rem		Assemble bootloader
rem
..\bin\snasm bootloader.asm 
rem
rem		Copy to file area if exists
rem
if exist bootloader.sna copy bootloader.sna ..\files


