import re
import os

########
# Globals
canPrint = True;

########
# Superglobals

def printError(text):
	print('!ERR '+text);
	canPrint = False;

def printWarning(text):
	print('WARN '+text);

def writeLine(f, intention, text):
	f.write('\t'*intention+text+'\n');

def writeLineCondition(f, intention, textNo, textYes, condition):
	if(condition):
		f.write('\t'*intention+textYes+'\n');
	else:
		f.write('\t'*intention+textNo+'\n');

def	writeLineBlocks(f,intention, texts):
	allBut = texts[0:-1]
	last = texts[-1]
	for l in allBut:
		writeLine(f, intention, l+',')
	writeLine(f, intention, last)

def parseLine(line):
	line = re.sub(r"\s+#\s+","#", line)
	line = re.sub(r"\n","", line)
	line = re.sub(r"\r","", line)
	return line.split("#")

def expandCzechLetters(line):
    line = re.sub(r"\n","", line)
    return line

def parseName(name):
    name = name.lower()
    name = re.sub(r"\_","", name)
    return name

def getFiles( wildch ):
	mypath = os.getcwd()
	onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
	filtered = []
	for f in onlyfiles:
		if(re.match(wildch, f) != None):
			filtered.append(f)
	return filtered

def getLinesInFiles( wildch ):
	print('File search pattern: '+wildch)
	files = getFiles(wildch)
	print(files)

	lines = []
	for nm in files:
		with open(nm) as f:
			lns = f.readlines()
		f.closed
		print('File '+nm+', '+str(len(lns))+' lines')
		lines = lines + lns

	return lines

def expandWildchars( lst0, lstFull ):
	lst1 = []
	for it in lst0:
		if((it[0]=="<")and(it[-1]==">")):
			r = re.compile(it[1:-1])
			lst1.extend(list(filter(r.match, lstFull)))
		else:
			lst1.append(it)
	return lst1
########
# Process

# Comments file
print('\n--> comments.tex')
lines = getLinesInFiles('comments.txt')
f = open('comments.tex','w')
writeLine(f,0,'\\documentclass{article}')
writeLine(f,0,'\\usepackage[czech]{babel}')
writeLine(f,0,'')
for line in lines:
    text = expandCzechLetters(line)
    if(line[0]=='<'):
        text = expandCzechLetters(line[3:])
        if(line[1]=='T'):
            writeLine(f,0,'\\title{'+text+'}')
            writeLine(f,0,'\\date{2013-09-01}')
            writeLine(f,0,'\\author{Martin \'Gaimi\' Darai}')
            writeLine(f,0,'')
            writeLine(f,0,'\\begin{document}')
            writeLine(f,1,'\\maketitle')
        elif(line[1]=='C'):
            writeLine(f,1,'\\section{'+text+'}')
        else:
            printWarning('Strange LINE: '+line+', unknown tag')
            writeLine(f,2,text)
    else:
        writeLine(f,2,text)
writeLine(f,0,'\end{document}')
f.close()
