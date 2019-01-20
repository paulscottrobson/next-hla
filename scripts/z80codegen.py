# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		z80codegen.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		20th January 2019
#		Purpose :	Z80 Code Generator
#
# ***************************************************************************************
# ***************************************************************************************

# ***************************************************************************************
#							This is the Z80 Code Generator
# ***************************************************************************************

class Z80CodeGenerator(object):
	def __init__(self):
		pass
	#
	#		Get current address
	#
	def getAddress(self):
	#
	#		Get word size
	#
	def getWordSize(self):
		return 2
	#
	#		Load a constant or variable into the accumulator.
	#
	def loadDirect(self,isConstant,value):
		pass
	#
	#		store A to an address
	#
	def storeDirect(self,address):
		pass
	#
	#		save A temporarily for writing later
	#
	def saveAccumulator(self):
		pass
	#
	#		save value saved by 'save Accumulator' at address A.
	#
	def saveIndirect(self):
		pass
	#
	#		Do a binary operation on a constant or variable on the accumulator
	#							+ - * / % 		& | ^ 		!
	#
	def binaryOperation(self,operator,isConstant,value):
		pass
	#
	#		Push and restore A on stack for FOR/NEXT
	#
	def pushA(self):
		pass
	#
	def popA(self):
		pass
	#
	#		Allocate count bytes of meory, default is word size
	#
	def allocVar(self,name = None):
		pass
	#
	#		Load parameter constant/variable to a temporary area,
	#
	def loadParamRegister(self,regNumber,isConstant,value):
		pass
	#
	#		Copy parameter to an actual variable
	#
	def storeParamRegister(self,regNumber,address):
		pass
	#
	#		Create a string constant (done outside procedures)
	#
	def createStringConstant(self,string):
		pass
	#
	#	Compile a loop instruction. Test are z, nz, p or "" (unconditional). No target
	#	address is provided at compile time.
	#
	def jumpInstruction(self,test):
		pass
	#
	#		Set Jump Address for a jump already compile.
	#
	def setJumpAddress(self,jumpAddress,target):
		pass
	#
	#		Call a subroutine
	#
	def callSubroutine(self,address):
		pass
	#
	#		Return from subroutine.
	#
	def returnSubroutine(self):
		pass
