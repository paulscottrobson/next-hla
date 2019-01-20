# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		z80codegen.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		13th January 2019
#		Purpose :	Z80 Code Generator class
#
# ***************************************************************************************
# ***************************************************************************************

from imagelib import *

# ***************************************************************************************
#					This is a code generator for an idealised CPU
# ***************************************************************************************

class Z80CodeGenerator(object):
	def __init__(self):
		self.image = MemoryImage()
		self.varAlloc = 0x8000
	#
	#		Get current address
	#
	def getAddress(self):
		return (self.image.getCodePage() << 16)+self.image.getCodeAddress()
	#
	#		Get word size
	#
	def getWordSize(self):
		return 2
	#
	#		Load a constant or variable into the accumulator.
	#
	def loadDirect(self,isConstant,value):
		self.image.cByte(0x21 if isConstant else 0x2A)							# ld hl,xxxx/(xxxx)
		self.image.cWord(value & 0xFFFF)
	#
	#		Do a binary operation on a constant or variable on the accumulator
	#
	def binaryOperation(self,operator,isConstant,value):
		if operator == "!" or operator == "?":
			self.binaryOperation("+",isConstant,value)
			if operator == "?":
				self.image.cByte(0x6E)											# ld l,(hl)
				self.image.cByte(0x26)											# ld h,0
				self.image.cByte(0x00)											
			else:
				self.image.cByte(0x7E)											# ld a,(hl)
				self.image.cByte(0x23)											# inc hl
				self.image.cByte(0x66)											# ld h,(hl)
				self.image.cByte(0x6F)											# ld l,a

		if isConstant:
			self.image.cByte(0x01)												# ld bc,xxxx
		else:
			self.image.cByte(0xED)												# ld bc,(xxxx)
			self.image.cByte(0x4B)
		self.image.cWord(value & 0xFFFF)										# value to use.

		if operator == "+":
			self.image.cByte(0x09)												# add hl,bc
			return
		if operator == "-":
			self.image.cByte(0xAF)												# xor a
			self.image.cByte(0xED)												# sbc hl,bc
			self.image.cByte(0x42)
			return

					
	#
	#		Store accumulator.to a memory address
	#
	def storeDirect(self,address):
		self.image.cByte(0x22)
		self.image.cWord(address & 0xFFFF)
	#
	#		Store accumulator.to an indirect memory address which is the first variable
	#		contents plus either a constant or another variable's contents.
	#
	def storeIndirect(self,address,offsetIsConstant,offset,byteData):
		self.image.cByte(0xEB)												# ex de,hl
		self.image.cByte(0x2A)												# ld hl,(variable)
		self.image.cWord(address & 0xFFFF)
		if offsetIsConstant:
			self.image.cByte(0x01)											# ld bc,xxxx
		else:
			self.image.cByte(0xED)											# ld bc,(xxxx)
			self.image.cByte(0x4B)
		self.image.cWord(offset)											# xxxx
		self.image.cByte(0x09)												# add hl,bc
		self.image.cByte(0x73)												# ld (hl),e
		if not byteData:
			self.image.cByte(0x23)											# inc hl
			self.image.cByte(0x72)											# ld (hl),d
	#
	#		Generate for code.
	#
	def forCode(self,indexVar):
		pass
	#
	#		Gemerate next code.
	#
	def nextCode(self,loopAddress):
		pass
	#
	#	Compile a loop instruction. Test are z, nz, p or "" (unconditional). The compilation
	#	address can be overridden to patch forward jumps.
	#
	def jumpInstruction(self,test,target,override = None):
		pass
	#
	#		Allocate count bytes of meory, default is word size
	#
	def allocSpace(self,count = None,reason = None):
		count = self.getWordSize() if count is None else count
		self.varAlloc = self.varAlloc - count
		if reason is not None:
			print("{0} := 0x{1:04x}".format(reason,self.varAlloc))
		return self.varAlloc
	#
	#		Load constant/variable to a temporary area
	#
	def loadParamRegister(self,regNumber,isConstant,value):
		loader = [ 0x2A, 0xED5B, 0xED4B, 0xDD2A][regNumber]
		if isConstant:
			loader = [ 0x21, 0x11, 0x01, 0xDD21][regNumber]
		if loader < 0x100:
			self.image.cByte(loader)
		else:
			self.image.cByte(loader >> 8)
			self.image.cByte(loader & 0xFF)
		self.image.cWord(value)
	#
	#		Copy parameter to a temporary area
	#
	def storeParamRegister(self,regNumber,address):
		saver = [ 0x22, 0xED53,0xED43,0xDD22 ][regNumber]
		if saver < 0x100:
			self.image.cByte(saver)
		else:
			self.image.cByte(saver >> 8)
			self.image.cByte(saver & 0xFF)
		self.image.cWord(address)
	#
	#		Create a string constant (done outside procedures)
	#
	def createStringConstant(self,string):
		strAddr = self.image.getCodeAddress()
		print("{0:04x} \"{1}\"".format(strAddr,string))
		for s in string:
			self.image.cByte(ord(s))
		self.image.cByte(0)
		return strAddr
	#
	#		Call a subroutine
	#
	def callSubroutine(self,address):
		assert (address >> 16) == self.image.getCodePage(),"add cross page !!"
		self.image.cByte(0xCD)												# call xxxx
		self.image.cWord(address & 0xFFFF)									# address
	#
	#		Return from subroutine.
	#
	def returnSubroutine(self):
		self.image.cByte(0xC9)												# ret
if __name__ == "__main__":
	cg = Z80CodeGenerator()
	cg.loadDirect(True,42)
	cg.loadDirect(False,42)	
	print("------------------")
	cg.binaryOperation("%",True,44)
	cg.binaryOperation("&",False,44)	
	print("------------------")
	cg.storeDirect(46)
	print("------------------")
	cg.allocSpace(4)
	cg.allocSpace(1)	
	print("------------------")
	cg.createStringConstant("Hello world!")
	print("------------------")
	cg.callSubroutine(42)
	cg.returnSubroutine()
	print("------------------")
