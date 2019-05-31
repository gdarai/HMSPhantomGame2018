import sys
import re
import os
import json
import random
import math
import copy
import cv2
import numpy as np
import csv

########
# Globals
canPrint = True

SETTING = 'cards.json'
DIRECTORY = 'cards'
BREAK_CHAR = '|'
Y_SPACE = 5
TEX_FILE = 'cards.tex'
A4_WIDTH = 21
A4_MARGIN = 1.5
RESIZE_FILE = 'resize.png'
RESIZE_HEIGHT = 300

A4_TEXT_W = A4_WIDTH - (2*A4_MARGIN)
COUNTERS = dict()
IMAGES = dict()
IMAGES[TEX_FILE] = list()

FONTS = dict()
FONTS['HERSHEY_SIMPLEX'] = cv2.FONT_HERSHEY_SIMPLEX
FONTS['HERSHEY_PLAIN'] = cv2.FONT_HERSHEY_PLAIN
FONTS['HERSHEY_DUPLEX'] = cv2.FONT_HERSHEY_DUPLEX
FONTS['HERSHEY_COMPLEX'] = cv2.FONT_HERSHEY_COMPLEX
FONTS['HERSHEY_TRIPLEX'] = cv2.FONT_HERSHEY_TRIPLEX
FONTS['HERSHEY_COMPLEX_SMALL'] = cv2.FONT_HERSHEY_COMPLEX_SMALL
FONTS['HERSHEY_SCRIPT_SIMPLEX'] = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
FONTS['HERSHEY_SCRIPT_COMPLEX'] = cv2.FONT_HERSHEY_SCRIPT_COMPLEX

def ALIGN_LEFT(xmin, xmax, imgwidth):
	return xmin
def ALIGN_RIGHT(xmin, xmax, imgwidth):
	return xmax - imgwidth
def ALIGN_CENTER(xmin, xmax, imgwidth):
	return xmin + int((xmax - xmin - imgwidth) / 2)
ALIGN = dict()
ALIGN['left'] = ALIGN_LEFT
ALIGN['right'] = ALIGN_RIGHT
ALIGN['center'] = ALIGN_CENTER

def VALTYPE_INT(variable):
	return isinstance(variable, int)
def VALTYPE_FLOAT(variable):
	return isinstance(variable, (float))
def VALTYPE_IMG(variable):
	return isinstance(variable, complex)
def VALTYPE_STR(variable):
	return isinstance(variable, basestring)
def VALTYPE_LIST(variable):
	return isinstance(variable, list)

VALTYPE = dict()
VALTYPE['int'] = VALTYPE_INT
VALTYPE['float'] = VALTYPE_FLOAT
VALTYPE['img'] = VALTYPE_IMG
VALTYPE['string'] = VALTYPE_STR
VALTYPE['list'] = VALTYPE_LIST


class ANALYZE_CONST:
	def __init__(self, value):
		self.value = str(value)
	def nextVal(self):
		return self.value

def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class ANALYZE_REG_CONST:
	def __init__(self, value):
		self.value = value
	def getValue(self, index):
		return self.value
	def getCount(self):
		return 1

class ANALYZE_REG_RANGE:
	def __init__(self, minV, maxV):
		if representsInt(minV) and representsInt(maxV):
			self.type = 'int'
			self.minV = int(minV)
			self.count = int(maxV) - self.minV + 1
		elif len(minV) == 1 and len(maxV) == 1 :
			self.type = 'ord'
			self.minV = ord(minV)
			self.count = ord(maxV) - self.minV + 1
		else:
			print('!! Regexp error, range ['+minV+'-'+maxV+'] is not understanded')
			exit()
	def getValue(self, index):
		value = self.minV + index
		if self.type == 'int':
			return str(value)
		return chr(value)
	def getCount(self):
		return self.count

class ANALYZE_REG_FULL:
	def __init__(self, script, counterName, isMaster):
		self.script = script
		self.counterName = counterName
		self.isMaster = isMaster
		COUNTERS[counterName] = 0
		maxIndex = 1
		for oneItem in script:
			maxIndex = maxIndex * oneItem.getCount()
		self.maxIndex = maxIndex
	def nextVal(self):
		index = COUNTERS[self.counterName]
		if self.isMaster == True:
			COUNTERS[self.counterName] = index + 1
		index = index % self.maxIndex
		value = ''
		for sc in reversed(self.script):
			count = sc.getCount()
			idx = index % count
			index = index // count
			value = sc.getValue(idx) + value
		return value

class ANALYZE_LIST:
	def __init__(self, values, counterName, isMaster):
		self.values = values
		self.counterName = counterName
		self.isMaster = isMaster
		COUNTERS[counterName] = 0
	def nextVal(self):
		index = COUNTERS[self.counterName]
		if self.isMaster == True:
			COUNTERS[self.counterName] = index + 1
		index = index % len(self.values)
		return str(self.values[index])

def ANALYZE_REG(regStr, counterName, isMaster):
	script = list()
	while regStr != '':
		nextStr = ''
		if regStr[0] == '[':
			nextStr = (regStr[1:].split(']'))[0]
			regStr = regStr[len(nextStr)+2:]
			regSplit = nextStr.split('-')
			if len(regSplit) == 2:
				script.append(ANALYZE_REG_RANGE(regSplit[0], regSplit[1]))
			else:
				print('!! Regexp error, range ['+nextStr+'] is not understanded')
				exit()
		else:
			nextStr = (regStr.split('['))[0]
			regStr = regStr[len(nextStr):]
			script.append(ANALYZE_REG_CONST(nextStr))
	return ANALYZE_REG_FULL(script, counterName, isMaster)
########
# Superglobals

def getFiles( wildch ):
	mypath = os.getcwd()
	onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
	filtered = []
	for f in onlyfiles:
		if(re.match(wildch, f) != None):
			filtered.append(f)
	return filtered

########
# Printing
def writeLine(f, intention, text):
    f.write('\t'*intention+text+'\n');

def checkField(cardName, props, fieldName, values, defaultVal):
	if fieldName not in props:
		if defaultVal is None:
			print('!! Card '+cardName+' is missing mandatory field '+fieldName)
			exit()
		props[fieldName] = defaultVal
		return
	else:
		value = props[fieldName]
		if isinstance(values, list):
			if value not in values:
				print('!! Card '+cardName+' field '+fieldName+' must be one of '+str(values))
				exit()
		else:
			if not VALTYPE[values](value):
				print('!! Card '+cardName+' field '+fieldName+' must be '+values)
				exit()
	return

def int_to_bool_list(num, maxL):
    return [bool(num & (1<<n)) for n in range(maxL)]

def addLine(out, size, newLine, data):
	newLineString = ' '.join(newLine)
	out.append(newLineString)
	lnSize, _ = cv2.getTextSize(newLineString, data['font'], 1, data['line'])
	size[0] = max(size[0], lnSize[0])
	size[1] = size[1] + lnSize[1]

def getNewTextAnalysis(index, data):
	indexSplit = int_to_bool_list(index, data['maxBitIdx'])
	out = list()
	size = [0, 0]
	indexInUse = 0
	for lnIdx in range(0, len(data['text'])):
		ln = data['text'][lnIdx]
		if lnIdx > 0:
			addLine(out, size, newLine, data)
		newLine = list()

		for wIdx in range(0, len(ln)):
			if wIdx == 0:
				newLine.append(ln[wIdx])
			else:
				if indexSplit[indexInUse]:
					addLine(out, size, newLine, data)
					newLine = list()
				newLine.append(ln[wIdx])
				indexInUse = indexInUse + 1
	if len(newLine) > 0:
		addLine(out, size, newLine, data)

	scale = [1, 1];
	if size[0] > 0:
		scale[0] = data['size'][0] / size[0];
	spacing = (len(out) - 1) * data['space'];
	if size[1] > 0:
		scale[1] = (data['size'][1] - spacing) / size[1];

	result = dict()
	result['score'] = min(scale[0], scale[1])
	result['text'] = out
	return result

def analyzeTextSplit(theText, tgtSize, yspace, font, lineTh, separator):
	data = dict()
	data['size'] = [float(tgtSize[1][0]-tgtSize[0][0]), float(tgtSize[1][1]-tgtSize[0][1])]
	data['space'] = yspace
	data['font'] = font
	data['line'] = lineTh
	data['text'] = theText.split(separator)
	data['maxBitIdx'] = 1
	for i in range(0, len(data['text'])):
		data['text'][i] = data['text'][i].split(' ')
		data['maxBitIdx'] = data['maxBitIdx'] + len(data['text'][i]) - 1
	data['maxIdx'] = 2 ** data['maxBitIdx']

	bestAnalysis = dict()
	nextIndex = 0
	bestAnalysis['score'] = 0
	bestAnalysis['text'] = theText.split(separator)
	while nextIndex < data['maxIdx']:
		newAnalysis = getNewTextAnalysis(nextIndex, data)
		if newAnalysis['score'] > bestAnalysis['score']:
			bestAnalysis = newAnalysis
		nextIndex = nextIndex + 1

	return bestAnalysis['text']

def printCardFile(setting, name):
	cardName = setting['_card']
	img = cv2.imread(cardName+'.png')

	# RGB to RGBA
	if img.shape[2] == 3:
		# First create the image with alpha channel
		rgba = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
		# Then assign the mask to the last channel of the image
		rgba[:, :, 3] = np.zeros(img.shape[:2], np.uint8)
		img = rgba

	for fieldName in setting['_cardParamNames']:
		if fieldName not in setting:
			continue
		props = setting['_cardParams'][fieldName]
		checkField(cardName, props, 'type', ['text', 'img'], 'text')
		if props['type'] == 'text':
			checkField(cardName, props, 'position', 'list', None)
			checkField(cardName, props, 'padding', 'list', [[0, 0], [0, 0]])
			checkField(cardName, props, 'font', list(FONTS.keys()), list(FONTS.keys())[0])
			checkField(cardName, props, 'align', list(ALIGN.keys()), list(ALIGN.keys())[0])
			checkField(cardName, props, 'line', 'int', 1)
			checkField(cardName, props, 'fixed', 'int', 1)
			checkField(cardName, props, 'color', 'list', [0, 0, 0])

			font = FONTS[props['font']]
			thickness = props['line']
			color = props['color']
			tgtPos0 = props['position']
			tgtPos1 = props['padding']
			tgtPos = [np.add(tgtPos0[0], tgtPos1[0]), np.subtract(tgtPos0[1],tgtPos1[1])]

			theText = setting[fieldName].nextVal()
			if props['fixed'] == 1:
				theText = theText.split(setting['_break'])
			else:
				theText = analyzeTextSplit(theText, tgtPos, setting['_yspace'], font, thickness, setting['_break'])

			align = ALIGN[props['align']]
			size = []
			sizeCheck = 0
			sizeTotal = [0, -setting['_yspace']]
			for ln in theText:
				oneSize, _ = cv2.getTextSize(ln, font, 1, thickness)
				size.append(oneSize)
				sizeCheck = max(sizeCheck, oneSize[1]*oneSize[0])
				sizeTotal[0] = max(sizeTotal[0], oneSize[0])
				sizeTotal[1] = sizeTotal[1]+oneSize[1]+setting['_yspace']
			if sizeCheck == 0 :
				print('!! text-to-insert is empty ... skipping.')
				continue
			imgScale = min((float(tgtPos[1][1]) - tgtPos[0][1]) / sizeTotal[1], (float(tgtPos[1][0]) - tgtPos[0][0]) / sizeTotal[0])
			finSizeY = int(imgScale * sizeTotal[1])
			oneSizeY = int(finSizeY / len(theText))
			shiftY = oneSizeY

			for ln in theText:
				finSize, _ = cv2.getTextSize(ln, font, imgScale, thickness)
				finPos = (align(tgtPos[0][0], tgtPos[1][0], finSize[0]), ALIGN_CENTER(tgtPos[0][1], tgtPos[1][1], finSizeY)+shiftY)
				img = cv2.putText(img, ln, finPos, font, imgScale, color, thickness, cv2.LINE_AA)
				shiftY = shiftY + oneSizeY
		elif props['type'] == 'img':
			fileName = setting[fieldName].nextVal()
			if fileName == '' :
				print('!! image-to-insert is empty ... skipping.')
				continue
			checkField(cardName, props, 'position', 'list', None)
			checkField(cardName, props, 'mask', 'list', [0, 0])
			checkField(cardName, props, 'maskTolerance', 'float', 0.05)
			pos = props['position']
			size = [pos[1][0]-pos[0][0], pos[1][1]-pos[0][1]]
			pos = pos[0]
			maskPos = props['mask']
			maskTol = props['maskTolerance']
			theImg = cv2.imread(fileName)
			# RGB to RGBA
			if theImg.shape[2] == 3:
				# First create the image with alpha channel
				rgba = cv2.cvtColor(theImg, cv2.COLOR_RGB2RGBA)
				# Then assign the mask to the last channel of the image
				rgba[:, :, 3] = np.zeros(theImg.shape[:2], np.uint8)
				theImg = rgba

			hsvImg = cv2.cvtColor(theImg, cv2.COLOR_BGR2HSV)
			thePixel = hsvImg[maskPos[0], maskPos[1]]
			thePixel0 = hsvImg[maskPos[0], maskPos[1]]-(125*maskTol)
			thePixel1 = hsvImg[maskPos[0], maskPos[1]]+(125*maskTol)
			imgSize = theImg.shape[:2]
			imgScale = min(float(size[0])/imgSize[1], float(size[1])/imgSize[0])
			theImg = cv2.resize(theImg, None, fx=imgScale, fy=imgScale)
			imgSize = theImg.shape[:2]
			pos = [pos[0]+int((size[0]-imgSize[1])/2), pos[1]+int((size[1]-imgSize[0])/2)]
			thePaste = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
			thePaste[pos[1]:pos[1]+imgSize[0], pos[0]:pos[0]+imgSize[1]] = theImg

			theMask = np.full((img.shape[0], img.shape[1]), 4, dtype=np.uint8)
			hsvImg = cv2.cvtColor(theImg, cv2.COLOR_BGR2HSV)
			subMask = cv2.bitwise_not(cv2.inRange(hsvImg, thePixel0, thePixel1))
			theMask[pos[1]:pos[1]+imgSize[0], pos[0]:pos[0]+imgSize[1]] = subMask

			maskedImg = cv2.bitwise_or(thePaste, thePaste, mask=theMask)
			maskedMainImg = cv2.bitwise_or(img, img, mask=cv2.bitwise_not(theMask))

			img = cv2.bitwise_or(maskedMainImg, maskedImg)
		else:
			print('!! Card '+setting['_card']+' field '+fieldName+' is of unknown type.')
			exit()
	fileName = DIRECTORY+'/'+name+'.png'
	cv2.imwrite(RESIZE_FILE, img[:, :, :3])
	resizeCmd = 'convert '+RESIZE_FILE+ ' -resize '+str(setting['_resize'])+' '+fileName
	os.system(resizeCmd)
	imageDict = dict()
	imageDict['file'] = name
	imageDict['onOneLine'] = setting['_onOneLine']
	imageDict['randomize'] = setting['_randomize']
	IMAGES[setting['_out']].append(imageDict)
	return

########
# Process

def readOneParameter(setting, paramName, paramSource):
	newParam = None
	if isinstance(paramSource, dict) == True:
		if 'value' in paramSource:
			newParam = ANALYZE_CONST(paramSource['value'])
		elif 'reg' in paramSource:
			counterName = len(list(COUNTERS.keys()))
			isMaster = True
			if 'counter' in paramSource:
				counterName = paramSource['counter']
			if 'isMaster' in paramSource:
				isMaster = paramSource['isMaster']
			newParam = ANALYZE_REG(paramSource['reg'], counterName, isMaster)
		elif 'list' in paramSource:
			counterName = len(list(COUNTERS.keys()))
			isMaster = True
			if 'counter' in paramSource:
				counterName = paramSource['counter']
			if 'isMaster' in paramSource:
				isMaster = paramSource['isMaster']
			newParam = ANALYZE_LIST(paramSource['list'], counterName, isMaster)
			setting['_count'] = len(paramSource['list'])
		else:
			print('!! Parameter '+paramName+' is wrongly formated.')
			exit()

	else:
		newParam = ANALYZE_CONST(paramSource)

	setting[paramName] = newParam
	return setting

def readParameters(setting, source):
	if '_onOneLine' in source:
		setting['_onOneLine'] = source['_onOneLine']

	if '_card' in source:
		if setting['_card'] != '':
			print('!! multiple cards assinged in this branch, rewriting '+setting['_card']+' with '+source['_card'])
		setting['_card'] = source['_card']
		pngFiles = getFiles(setting['_card']+'.png')
		jsonFiles = getFiles(setting['_card']+'.json')
		if len(pngFiles) != 1 or len(jsonFiles) != 1:
			print('!! The cards files for '+setting['_card']+' (png/json) are wrong. There must be exactly one of each.')
			exit()
		setting['_cardParams'] = json.load(open(setting['_card']+'.json'))
		setting['_cardParamNames'] = list(setting['_cardParams'].keys())

	if '_list' in source:
		newLists = source['_list'].keys()
		for listName in newLists:
			theList = source['_list'][listName]
			if listName in setting['_lists']:
				print('!! Overwriting list '+listName+': '+str(theList))
			else:
				print(' - Adding list '+listName+': '+str(theList))
			setting['_lists'][listName] = list(theList)

	for listName in setting['_lists']:
		if listName in source:
			theList = setting['_lists'][listName]
			theData = source[listName]
			if isinstance(theData, list) == True:
				expLen = len(theList)
				if len(theData) != expLen:
					print('!! Key List '+listName+' should be '+expLen+' long, but this may be intentional.')
					expLen = min(expLen, len(theData))
				for idx in range(0, expLen):
					setting = readOneParameter(setting, theList[idx], theData[idx])
			elif isinstance(theData, basestring) == True:
				sourceCsv = open(theData, 'rb')
				lineReader = csv.reader(sourceCsv, delimiter=',', quotechar='|')
				tableData = []
				for row in lineReader:
					tableData.append(row)
				tableData = np.array(tableData)
				sourceCsv.close()

				expLen = len(theList)
				if tableData.shape[1] == (expLen+1):
					print('(i) File loading with counts, _count is the first column.')
					counts = tableData[:, 0]
					tableDataOrig = tableData[:, 1:]
					tableData = np.tile(tableDataOrig[0], (int(counts[0]), 1))
					for idx in range(1, len(counts)):
						tableData = np.append(tableData, np.tile(tableDataOrig[idx], (int(counts[idx]), 1)), axis=0)

				tableData = tableData.transpose()
				if tableData.shape[0] != expLen:
					expLen = min(expLen, tableData.shape[0])
					print('!! Key List '+listName+' should be '+str(expLen)+' long, but this may be intentional.')
				for idx in range(0, tableData.shape[0]):
					oneData = dict()
					oneData['list'] = list(tableData[idx])
					setting = readOneParameter(setting, theList[idx], oneData)
			else:
				print('!! Key List '+listName+' must contain array or existing filename.')
				exit()

	for paramName in setting['_cardParamNames']:
		if paramName in source:
			setting = readOneParameter(setting, paramName, source[paramName])

	if '_count' in source:
		setting['_count'] = source['_count']
	if '_resize' in source:
		setting['_resize'] = source['_resize']
	if '_break' in source:
		setting['_break'] = source['_break']
	if '_yspace' in source:
		setting['_yspace'] = source['_yspace']
	if '_out' in source:
		newFile = source['_out']
		setting['_out'] = newFile
		print('!! Swapping output to file '+newFile)
		if newFile not in IMAGES:
			IMAGES[newFile] = list()
	if '_randomize' in source:
		setting['_randomize'] = source['_randomize'] == 'True'

	return setting

def checkParameters(setting):
	missing = list()
	for paramName in setting['_cardParamNames']:
		if paramName not in setting:
			missing.append(paramName)
	return missing

def readAndProcessList(level, name, sourceList, setting):
	index = 0
	for s in sourceList:
		index = index + 1
		newName = name + '-' + str(index);
		if '_key' in s:
			newName = name + '-' + s['_key']
		readAndProcess(level, newName, s, copy.deepcopy(setting))

def readAndProcess(level, name, source, setting):
	separator = '  ' * level
	print(separator+name)
	newLevel = level + 1
	setting = readParameters(setting, source)
	if '_sub' in source:
		readAndProcessList(newLevel, name, source['_sub'], copy.deepcopy(setting))
	else:
		if setting['_card'] == '':
			print('!! Almost printing but still missing the mandatory "_card" key.')
			exit()
		missing = checkParameters(setting)
		if len(missing) > 0:
			print(separator+' -Missing '+str(missing))
		print(separator+' -Printing '+str(setting['_count'])+'x')
		for idx in range(0, setting['_count']):
			printCardFile(setting, name+'_'+str(idx))

def printImages(IMAGES):
	onOneLine = IMAGES[0]['onOneLine']
	doRandom = IMAGES[0]['randomize']
	imgWidth = str(A4_TEXT_W / onOneLine)
	if doRandom:
		random.shuffle(IMAGES)
	for img in IMAGES:
		if img['onOneLine'] != onOneLine:
			onOneLine = img['onOneLine']
			writeLine(f,0,'\\newline')
			imgWidth = str(A4_TEXT_W / onOneLine)
		writeLine(f,1,'\\includegraphics[width='+imgWidth+'cm]{'+img['file']+'}')


########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]

print('\nReading input file --> '+SETTING)
files = getFiles(SETTING)
if(len(files)!=1):
	print('\nThere is something wrong with the file '+SETTING+'!!')
	exit()

source = json.load(open(SETTING))

if(len(source)==0):
	print('\nSource file should contain JSON array.')
	exit()
print('\nProcessing')
if(not os.path.isdir(DIRECTORY)):
    os.mkdir(DIRECTORY)

setting = dict()
setting['_count'] = 1
setting['_resize'] = RESIZE_HEIGHT
setting['_break'] = BREAK_CHAR
setting['_yspace'] = Y_SPACE
setting['_onOneLine'] = 4
setting['_cardParams'] = dict()
setting['_card'] = ''
setting['_lists'] = dict()
setting['_out'] = TEX_FILE
setting['_randomize'] = True


readAndProcessList(0, "img", source, setting)

for fileName in IMAGES.keys():
	IMGS = IMAGES[fileName]
	if len(IMGS) == 0 :
		print('\n!! There are NO images to print, skipping PDF print '+fileName)
		continue

	print('\nPrinting '+fileName+' ('+str(len(IMGS))+') with pdf latex\n')

	f = open(fileName,'w')
	writeLine(f,0,'\\documentclass[a4paper]{article}')
	writeLine(f,0,'\\usepackage[a4paper, margin='+str(A4_MARGIN)+'cm]{geometry}')
	writeLine(f,0,'\\usepackage{graphicx}')
	writeLine(f,0,'\\graphicspath{ {./cards/} }')
	writeLine(f,0,'\\setlength{\\parindent}{0cm}')
	writeLine(f,0,'\\begin{document}')
	printImages(IMGS)
	writeLine(f,0,'\end{document}')
	f.close()

	os.system('pdflatex '+fileName)
