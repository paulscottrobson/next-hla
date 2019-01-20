# ***************************************************************************************
# ***************************************************************************************
#
#		Name : 		assembler.py
#		Author :	Paul Robson (paul@robsons.org.uk)
#		Date : 		20th January 2019
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
		print("*****",message,AssemblerException.LINE,"*****")

# ***************************************************************************************
#									 Worker Object
# ***************************************************************************************

class AssemblerWorker(object):
	def __init__(self,codeGen):
		self.codeGen = codeGen 												# code generator.
		self.globals = {}													# global identifiers.
		self.rxIdentifier = "[\$a-z][a-z0-9\_\.]*"							# identifier rx match
		self.keywords = "defproc,endproc,if,endif,while,endwhile,for,next"
		self.keywords = [x for x in self.keywords.split(",") if x != ""]
	#
	#		Assemble an array of strings.
	#
	def assemble(self,src):
		#
		src = [x.replace("\t"," ").rstrip() for x in src]					# tidy up
		src = [x if x.find("//") < 0 else x[:x.find("//")] for x in src]	# remove comments
		#
		for l in range(0,len(src)):											# remove quoted strings
			if src[l].find('"') >= 0:										# any quotes ?
				if src[l].count('"') % 2 != 0:		
					AssemblerWorker = l + 1
					raise AssemblerException("Imbalance in quotes")					
				src[l] = self.processQuotes(src[l])							# Replace quotes with addresses
		#
		src = (":~:".join(src)).replace(" ","").lower()						# make one long string.
		#
		src = re.split("(defproc"+self.rxIdentifier+"\(.*?\))",src)			# split around proc defs
		#
		AssemblerException.LINE = 1
		if not src[0].startswith("defproc"):								# stuff at front.
			if src[0].replace(":","").replace("~","") != "":				# check no content
				raise AssemblerException("Code before first procedure")
			AssemblerException.LINE = src[0].count("~")+1					# set line correctly
			del src[0]														# remove that part.
		assert len(src) % 2 == 0											# pairs on defs / bodies
		#
		for i in range(0,len(src),2):										# scan through.
			self.locals = {}												# new locals each procedure.
			src[i] = self.processIdentifiers(src[i])						# pre-process identifiers out.
			src[i+1] = self.processIdentifiers(src[i+1])					# at this point the procedure isn't defined.
			self.processHeader(src[i])										# do the header.
			for cmd in [x for x in src[i+1].split(":") if x != ""]:			# work through body
				if cmd == "~":												# handle line position
					AssemblerException.LINE += 1
				else:
					print(cmd)
	#
	#		Replace all quoted strings with addresses
	#
	def processQuotes(self,l):
		l = re.split("(\".*?\")",l)											# split up into bits
		for i in range(0,len(l)):
			if l[i].startswith('"') and l[i].endswith('"'):					# string found.
				l[i] = str(self.codeGen.createStringConstant(l[i][1:-1]))				
		return "".join(l)
	#
	#		Process out all identifiers.
	#
	def processIdentifiers(self,src):
		parts = re.split("("+self.rxIdentifier+"\(?)",src)					# split it up.
		rxCheck = re.compile("^("+self.rxIdentifier+")(\(?)$")				# tester, is it an identifier.
		for i in range(0,len(parts)):
			if rxCheck.match(parts[i]) and parts[i] not in self.keywords:	# if identifier and not a keyword ?
				if not (parts[i].startswith("defproc") and parts[i][-1] == "("):  # and not a definition, handled elsewhere
					#
					if parts[i][-1] != "(":									# if not a procedure call, define if required.
						target = self.globals if parts[i].startswith("$") else self.locals
						if parts[i] not in target:							# create variable if does not exist
							target[parts[i]] = self.codeGen.allocVar(parts[i])
					#														# where to find it, locals first then globals
					lookup = self.locals if parts[i] in self.locals else self.globals
					if parts[i] not in lookup:								# is it there ?
						raise AssemblerException("Unknown identifier "+parts[i])
																			# do substitution adding ( for procedures invoke
					parts[i] = "@"+str(lookup[parts[i]])+("(" if parts[i].endswith("(") else "")		
		return "".join(parts).replace("@@","")								# rebuild. replace does @variable operator.
	#
	#		Process the header.
	#
	def processHeader(self,header):
		m = re.match("^defproc("+self.rxIdentifier+"\()(.*)\)$",header)		# split it up
		if m is None:
			raise AssemblerException("Bad procedure definition "+header)
		self.globals[m.group(1)] = self.codeGen.getAddress()				# create procedure
		params = [x for x in m.group(2).split(",") if x != ""]				# write out parameters.
		for i in range(0,len(params)):										# work through them
			m = re.match("^\@(\d+)$",params[i])								# term ?
			if m is None:
				raise AssemblerException("Bad parameter "+params[i])
			self.codeGen.storeParamRegister(i,int(m.group(1)))				# save param register
	#
	#		Assemble an expression.
	#
	def assembleExpression(self,expr):
		expr = [x for x in re.split("(\@?\d+)",expr) if x != ""]			# seperate around terms
		pendingOp = None 													# no pending operation.
		for term in expr:													# look at expr parts
			m = re.match("^(\@?)(\d+)$",term)								# figure it out
			if m is None:													# operator
				if "+-*/%&|^?!".find(term) < 0 or pendingOp is not None:	# okay ?
					raise AssemblerException("Syntax Error "+term)
				pendingOp = term
			else:
				if pendingOp is None:										# load operator
					self.codeGen.loadDirect(m.group(1) == "",int(m.group(2)))
				else:														# operation.
					self.codeGen.binaryOperation(pendingOp,m.group(1) == "",int(m.group(2)))
				pendingOp = None

if __name__ == "__main__":
	src = """
	//
	// Blah blah blah
	//
	defproc demo(p1,p2)			// Comments
		l1=p1!$g1:
		$g1 = $g1!2+l1
		"hello">$g1
	endproc

	defproc d2()
		c1="test"*3/2%4
		demo(1,3):$h2!4=c1-4
	endproc

	defproc d3(a)
		d2(a,69)
		a = 4
	endproc
	""".split("\n")
	cg = DemoCodeGenerator()
	aw = AssemblerWorker(cg)		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()

# TODO: WHILE/ENDWHILE IF/ENDIF FOR/NEXT

