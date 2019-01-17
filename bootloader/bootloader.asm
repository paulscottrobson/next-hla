; ***************************************************************************************
; ***************************************************************************************
;
;		Name : 		bootloader.asm
;		Author :	Paul Robson (paul@robsons.org.uk)
;		Date : 		28th December 2018
;		Purpose :	Boot-Loads code by loading "boot.img" into memory
;					from $8000-$BFFF then banks 32-94 (2 per page) into $C000-$FFFF
;
; ***************************************************************************************
; ***************************************************************************************

FirstPage = 32 												; these are the pages for an 
LastPage = 95 												; unexpanded ZXNext.

		org 	$4000-27
		db 		$3F
		dw 		0,0,0,0,0,0,0,0,0,0,0
		org 	$4000-4
		dw 		$5AFE
		db 		1
		db 		7

		org 	$5AFE
		dw 		$7F00	
		org 	$7F00 							

Start:	ld 		sp,Start-1 									; set up the stack.
		;db 	$DD,$01
		ld 		ix,ImageName 								; read the image into memory
		call 	ReadNextMemory
		jp	 	$8000 										; run.

; ***************************************************************************************
;
;								 Access the default drive
;
; ***************************************************************************************

FindDefaultDrive:
		xor 	a
		rst 	$08 										; set the default drive.
		db 		$89
		ld 		(DefaultDrive),a
		ret

; ***************************************************************************************
;
;			Read ZXNext memory from $8000-$BFFF then pages from $C000-$FFFF
;
; ***************************************************************************************

ReadNextMemory:
		call 	FindDefaultDrive 							; get default drive
		call 	OpenFileRead 								; open for reading
		ld 		ix,$8000 									; read in 8000-BFFF
		call 	Read16kBlock
		ld 		b,FirstPage 								; current page
__ReadBlockLoop:
		call 	SetPaging 									; access the pages
		ld 		ix,$C000 									; read in C000-FFFF
		call 	Read16kBlock 								; read it in
		inc 	b 											; there are two 8k blocks
		inc 	b 											; per page
		ld 		a,b
		cp 		LastPage+1 									; until read in pages 32-95
		jr 		nz,__ReadBlockLoop
		call 	CloseFile 									; close file.
		ret

; ***************************************************************************************
;
;						   Map $C000-$FFFF onto blocks b and b+1
;
; ***************************************************************************************

SetPaging:
		ld 		a,b 										; set $56
		db 		$ED,$92,$56
		inc 	a 											; set $57
		db 		$ED,$92,$57
		ret


; ***************************************************************************************
;
;									Open file read
;
; ***************************************************************************************

OpenFileRead:
		push 	af
		push 	bc
		push 	ix
		ld 		b,1
__OpenFile:
		ld 		a,(DefaultDrive)
		rst 	$08
		db 		$9A
		ld 		(FileHandle),a 
		pop 	ix
		pop 	bc
		pop 	af
		ret

; ***************************************************************************************
;
;									Read 16k block
;
; ***************************************************************************************

Read16kBlock:
		push 	af
		push 	bc
		push 	ix
		ld 		a,(FileHandle)
		ld 		bc,$4000
		rst 	$08
		db 		$9D
		pop 	ix
		pop 	bc
		pop 	af
		ret

; ***************************************************************************************
;
;										Close open file
;
; ***************************************************************************************

CloseFile:
		push 	af
		ld 		a,(FileHandle)
		rst 	$08
		db 		$9B
		pop 	af
		ret		

DefaultDrive:
		db 		0
FileHandle:
		db 		0

		org 	$7FF0
ImageName:
		db 		"boot.img",0

		org 	$FFFF
		db 		0


