from assembler import *
from democodegen import *

if __name__ == "__main__":
	src = """
	//
	// Blah blah blah
	//
	defproc demo(p1,p2)			// Comments
		l1=p1!$g1:
		$g1 = $g1!2+l1
		$g1="hello"
	endproc

	defproc d2()
		c1="test"*3/2%4
		demo(1,3):$h2!4=c1-4
	endproc

	defproc d3(a)
		d2(a,69)
		a = 4
		if(x<0):a=a+1:endif
		while(x=0):a=a+1:endwhile
		for(42):a=a+index:next
	endproc
	""".split("\n")
	cg = DemoCodeGenerator()
	aw = AssemblerWorker(cg)		
	aw.assemble(src)
	print(aw.globals)
	#aw.codeGen.image.save()
