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
		self.keywords = "endproc,if,endif,while,endwhile,for,next"
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
		src = self.elementProcess(src,":global(&):")						# extract all globals.
		#
		src = re.split("(proc"+self.rxIdentifier+"\(.*?\))",src)			# split around proc defs
		AssemblerException.LINE = 1
		if not src[0].startswith("proc"):									# stuff at front.
			if src[0].replace(":","").replace("~","") != "":				# check no content
				raise AssemblerException("Code before first procedure")
			AssemblerException.LINE = src[0].count("~")+1					# set line correctly
			del src[0]														# remove that part.
		assert len(src) % 2 == 0											# pairs on defs / bodies
		#
		for p in range(0,len(src),2):										# go through in pairs.
			self.locals = {}												# new locals (static)
			src[p+1] = self.elementProcess(src[p+1],":local(&):")			# extract all locals.
			self.processHeader(src[p])										# process the header
			src[p+1] = self.processIdentifiers(src[p+1])					# replace identifiers.
			self.structureStack = [ ["marker"] ]							# structure stack.
			for cmd in [x for x in src[p+1].split(":") if x != ""]:			# work through commands
				if cmd == "~": 												# tracking source position
					AssemblerException.LINE += 1
				else:														# one command
					self.assembleInstruction(cmd)
			if len(self.structureStack) != 1:								# stack okay
				raise AssemblerException("Structure imbalance")
	#
	#		Process procedure definition. Split up, create parameter variables
	#		Mark procedure start, store passed values in local variables.
	#
	def processHeader(self,header):
		m = re.match("^proc("+self.rxIdentifier+")\((.*?)\)$",header)		# grab the header parts
		assert m is not None
		#
		params = [x for x in m.group(2).split(",") if x != ""]				# get parameters
		paramAddresses = []
		for p in params:													# check and define them.
			if p in self.locals:											# must be new identifier.
				raise AssemblerException("Duplicate parameter "+p)
			self.locals[p] = self.codeGen.allocVar(p+" (P)")				# create it
			paramAddresses.append(self.locals[p])							# keep for saving
		#
		if m.group(1) in self.globals:										# define the procedure.
			raise AssemblerException("Duplicate procedure "+m.group(1))
		self.globals[m.group(1)] = self.codeGen.getAddress()				# to start here
		#
		for i in range(0,len(paramAddresses)):								# code to save passed params
			self.codeGen.storeParamRegister(i,paramAddresses[i])			# into their local variables.
	#
	#		Assemble an instruction
	#
	def assembleInstruction(self,cmd):
		print("{0} {1} {0}".format("===========",cmd))
		if cmd == "endproc":												# end of procedure
			self.codeGen.returnSubroutine()
		else:																
			m = re.match("^\@(\d+)\((.*?)\)$",cmd) 							# check procedure call
			if m is not None:
				params = [x for x in m.group(2).split(",") if x != ""]		# parameters
				for i in range(0,len(params)):								# copy to registers
					mp = re.match("^(\@?)(\d+)$",params[i])
					if mp is None:
						raise AssemblerException("Bad parameter "+params[i])
					self.codeGen.loadParamRegister(i,mp.group(1)=="",int(mp.group(2)))
				self.codeGen.callSubroutine(int(m.group(1)))				# call code.
			else:
				self.assembleExpression(cmd)								# else try as expression
	#
	#		Assemble an expression.
	#
	def assembleExpression(self,expr):
		expr = [x for x in re.split("(\@?\d+)",expr) if x != ""]			# seperate around terms
		pendingOp = None 													# no pending operation.
		for term in expr:													# look at expr parts
			m = re.match("^(\@?)(\d+)$",term)								# figure it out
			if m is None:													# operator
				if "+-*/%&|^?!>".find(term) < 0 or pendingOp is not None:	# okay ?
					raise AssemblerException("Syntax Error "+term)
				pendingOp = term
			else:
				if pendingOp is None:										# load operator
					self.codeGen.loadDirect(m.group(1) == "",int(m.group(2)))
				else:														# operation.
					if pendingOp == ">" and m.group(1) == "":				# special case
						raise AssemblerException("> must operate on variable")
					self.codeGen.binaryOperation(pendingOp,m.group(1) == "",int(m.group(2)))
				pendingOp = None

	#
	#		Handle definitions that match a r-ex and are subsequently removed. Used
	#		for LOCAL <var> and GLOBAL <var>
	#
	def elementProcess(self,src,baseExpr):
																			# make it a splitter
		rex = baseExpr.replace("&",self.rxIdentifier).replace("(","").replace(")","")
		rcsp = re.compile(baseExpr.replace("&",self.rxIdentifier))			# the matcher
		parts = re.split("("+rex+")",src)									# split it up
		for i in range(0,len(parts)): 										# look through
			m = rcsp.match(parts[i])										# if match occurs
			if m is not None:
				self.elementProcessHandler(parts[i],m.groups())				# do whatever for that word
				parts[i] = ":"												# replace with empty statement
		return "".join(parts)												# rebuild and return.
	#
	#		When the above finds a match, this is called with the matching text
	#		and the groups of the match.
	#
	def elementProcessHandler(self,section,matchGroups):
		if section.startswith(":global"):									# global <name>
			if matchGroups[0] in self.globals:
				raise AssemblerException("Duplicate Global "+matchGroups[0])
			self.globals[matchGroups[0]] = self.codeGen.allocVar(matchGroups[0]+" (G)")
		elif section.startswith(":local"):									# local <name>
			if matchGroups[0] in self.locals:
				raise AssemblerException("Duplicate Local "+matchGroups[0])
			self.locals[matchGroups[0]] = self.codeGen.allocVar(matchGroups[0])
		else:
			assert False
	#
	#		Replace all identifiers with addresses from locals and globals.
	#
	def processIdentifiers(self,src):
		parts = re.split("("+self.rxIdentifier+")",src)						# split up.
		rxc = re.compile(self.rxIdentifier)									# compile matcher
		for i in range(0,len(parts)):										# found an identifier
			if rxc.match(parts[i]) and parts[i] not in self.keywords:		# match found, not keyword
				address = self.globals[parts[i]] if parts[i] in self.globals else None
				if address is None:											# not in globals
					if parts[i] not in self.locals:							# check locals.
						raise AssemblerException("Unknown identifier "+parts[i])
					address = self.locals[parts[i]]
				parts[i] = "@"+str(address)
		return "".join(parts).replace("@@","")								# rebuild, handle @var
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
		p1?g1>l1:g1?2+l1>g1:p1!g1
		"hello">g1
	endproc

	proc d2()
		local c1:global h2
		"test"*3/2%4>c1
		demo(1,3):+c1-4!@h2
	endproc

	proc d3(a)
		demo(a,69)
		4>a
	endproc
	""".split("\n")
	cg = DemoCodeGenerator()
	aw = AssemblerWorker(cg)		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()

# TODO: WHILE/ENDWHILE IF/ENDIF FOR/NEXT

