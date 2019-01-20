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
		self.rxIdentifier = "[\$a-z][a-z0-9\_]*"							# identifier rx match
		self.keywords = "defproc,endproc,if(,endif,while(,endwhile,for(,next"
		self.keywords = [x for x in self.keywords.split(",") if x != ""]
		self.testMap = { "=":"nz","#":"z","<":"p" }							# maps = # < onto inverse tests
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
			self.structureStack = [ ["marker"] ]							# set up structure stack.
			for cmd in [x for x in src[i+1].split(":") if x != ""]:			# work through body
				if cmd == "~":												# handle line position
					AssemblerException.LINE += 1
				else:														# assemble the rest.
					self.assembleCommand(cmd)
			if len(self.structureStack) != 1:								# check structures balance
				raise AssemblerException("Structure imbalance")
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
	#		Assemble a single command.
	#
	def assembleCommand(self,cmd):
		print("{0} {1} {0}".format("=========",cmd))
		if cmd == "endproc":												# handle endproc
			self.codeGen.returnSubroutine()
			return
		#
		if cmd.startswith("if(") or cmd.startswith("while("):				# code shared as while is if with loop.
			m = re.match("^(.*?)\((.*?)([\#\=\<])0\)$",cmd)					# split it up into bits.
			if m is None:
				raise AssemblerException("Syntax error in structure")
			info = [m.group(1),self.codeGen.getAddress()]					# info is name and loop position (for while)
			self.assembleExpression(m.group(2))								# value to be tested.
			jadr = self.codeGen.jumpInstruction(self.testMap[m.group(3)])	# assemble jump instruction
			info.append(jadr)												# add that patch address.
			self.structureStack.append(info)								# push on stack
			return
		#
		if cmd == "endif" or cmd == "endwhile":								# end of structure shared
			info = self.structureStack.pop()								# get info
			if cmd[3:] != info[0]:											# right ?
				raise AssemblerException("{0} not closed".format(info[0]))	# no !
			if cmd == "endwhile":											# loop back for while
				jmp = self.codeGen.jumpInstruction("")
				self.codeGen.setJumpAddress(jmp,info[1])
			self.codeGen.setJumpAddress(info[2],self.codeGen.getAddress())	# patch forward jump
			return
		#
		if cmd.startswith("for"):											# start of FOR
			m = re.match("^for\((.*)\)$",cmd)								# split up and check
			if m is None:
				raise AssemblerException("Syntax error in FOR")
			self.assembleExpression(m.group(1))								# loop count
			self.structureStack.append(["for",self.codeGen.getAddress()])	# mark loop start
			self.codeGen.binaryOperation("-",True,1)						# subtract 1
			self.codeGen.pushA()											# save value.	
			if "index" in self.locals:										# do we have an index local ?
				self.codeGen.storeDirect(self.locals["index"])				# write out that index value
			return
		#
		if cmd == "next":
			info = self.structureStack.pop()								# pop stack and check
			if info[0] != "for":
				raise AssemblerException("next without for")
			self.codeGen.popA()												# restore value
			jmp = self.codeGen.jumpInstruction("nz")						# loop if non zero
			self.codeGen.setJumpAddress(jmp,info[1])
			return
		#
		m = re.match("^\@(\d+)=(.*)$",cmd)									# is it variable = expression
		if m is not None:
			self.assembleExpression(m.group(2))
			self.codeGen.storeDirect(int(m.group(1)))
			return
		#
		m = re.match("^\@(\d+)\!(\@?)(\d+)=(.*)$",cmd)						# is it variable!term = expression
		if m is not None:
			self.assembleExpression(m.group(4))								# calc result
			self.codeGen.saveAccumulator()									# save result.
			self.codeGen.loadDirect(False,int(m.group(1)))					# evaluate LHS
			self.codeGen.binaryOperation("+",m.group(2) == "",int(m.group(3)))
			self.codeGen.saveIndirect()										# and save.
			return
		#
		m = re.match("\@(\d+)\((.*)\)$",cmd)								# is it procedure(parameters)
		if m is not None:
			params = [x for x in m.group(2).split(",") if x != ""]			# parameter list
			for i in range(0,len(params)):									# for each parameter
				m2 = re.match("^(\@?)(\d+)$",params[i])						# analyse it
				if m2 is None:
					raise AssemblerException("Bad Parameter")
				self.codeGen.loadParamRegister(i,m2.group(1) == "",int(m2.group(2)))
			self.codeGen.callSubroutine(int(m.group(1)))
			return
		#
		raise AssemblerException("Syntax Error")
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

