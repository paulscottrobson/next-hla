sh build.sh
#
#		Create a dummy boot.img file
#
rm boot.img
python makedemoimage.py

if [ -e bootloader.sna ]
then
	wine ../bin/CSpect.exe -zxnext -cur -brk -exit -w3 bootloader.sna 
fi


