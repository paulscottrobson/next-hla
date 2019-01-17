# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		assembler.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		17th January 2019
#		Purpose :	Next High Level Assembler, assembler worker.
#
# ***************************************************************************************
# ***************************************************************************************

from democodegen import *
import re

# ***************************************************************************************
#									Exception for HLA
# ***************************************************************************************

class AssemblerException(Exception):
	def __init__(self,message):
		Exception.__init__(self)
		self.message = message
		print(message,AssemblerException.LINE)

# ***************************************************************************************
#									 Worker Object
# ***************************************************************************************

class AssemblerWorker(object):
	def __init__(self,codeGen):
		self.codeGen = codeGen 												# code generator.
		self.globals = {}													# global identifiers.
		self.rxIdentifier = "[\$a-z][a-z0-9\_\.]*"							# identifier rx match
	#
	#		Assemble an array of strings.
	#
	def assemble(self,src):
		#
		src = [x.replace("\t"," ").rstrip() for x in src]					# tidy up
		src = [x if x.find("//") < 0 else x[:x.find("//")] for x in src]	# remove comments
		for l in range(0,len(src)):											# remove quoted strings
			if src[l].find('"') >= 0:										# any quotes ?
				if src[l].count('"') % 2 != 0:		
					AssemblerWorker = l + 1
					raise AssemblerException("Imbalance in quotes")					
				src[l] = self.processQuotes(src[l])							# Replace quotes with addresses
		src = (":~:".join(src)).replace(" ","").lower()						# make one long string.
		# TODO: Global scan
		# TODO: Split it up
		# TODO: Locals scan (same code as Global Scan) with parameters
		# TODO: Each code body.
		print(src)
	#
	#		Replace all quoted strings with addresses
	#
	def processQuotes(self,l):
		l = re.split("(\".*?\")",l)											# split up into bits
		for i in range(0,len(l)):
			if l[i].startswith('"') and l[i].endswith('"'):					# string found.
				l[i] = str(self.codeGen.createStringConstant(l[i][1:-1]))				
		return "".join(l)

if __name__ == "__main__":
	src = """
	proc demo(p1,p2)			// Comments
		local l1:global g1
		p1@4>l1:g1+l1>g1:p1!g1
		"hello">g1
	endproc

	proc d2()
		local c1,h2
		"test">c1
		demo(1,3):+c1.4!@h2
	endproc

	proc d3(a)
		demo(a,69)
	endproc
	""".split("\n")
	cg = DemoCodeGenerator()
	aw = AssemblerWorker(cg)		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()
