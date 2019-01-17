#
#		Delete old files
#
rm bootloader.sna ../files/bootloader.sna
#
#		Assemble bootloader
#
zasm -buw bootloader.asm -l bootloader.lst -o bootloader.sna
#
#		Copy to file area if exists
#
if [ -e bootloader.sna ]
then
 	cp bootloader.sna ../files
fi


