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
TEX_FILE = 'cards.tex'
A4_WIDTH = 21
A4_MARGIN = 1.5

A4_TEXT_W = A4_WIDTH - (2*A4_MARGIN)
COUNTERS = dict()
IMAGES = list()

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
	return isinstance(variable, (float, double))
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
		checkField(cardName, props, 'type', ['text'], 'text')
		if props['type'] == 'text':
			checkField(cardName, props, 'position', 'list', None)
			checkField(cardName, props, 'padding', 'list', [[0, 0], [0, 0]])
			checkField(cardName, props, 'font', list(FONTS.keys()), list(FONTS.keys())[0])
			checkField(cardName, props, 'align', list(ALIGN.keys()), list(ALIGN.keys())[0])
			checkField(cardName, props, 'line', 'int', 1)
			checkField(cardName, props, 'color', 'list', [0, 0, 0])

			theText = setting[fieldName].nextVal()

			font = FONTS[props['font']]
			thickness = props['line']
			color = props['color']
			tgtPos0 = props['position']
			tgtPos1 = props['padding']
			tgtPos = [np.add(tgtPos0[0], tgtPos1[0]), np.subtract(tgtPos0[1],tgtPos1[1])]

			align = ALIGN[props['align']]
			size, _ = cv2.getTextSize(theText, font, 1, thickness)
			if size[1]*size[0] == 0 :
				print('!! text-to-insert is empty ... skipping.')
				continue

			imgScale = min((tgtPos[1][1] - tgtPos[0][1]) / size[1], (tgtPos[1][0] - tgtPos[0][0]) / size[0])
			finSize, _ = cv2.getTextSize(theText, font, imgScale, thickness)

			finPos = (align(tgtPos[0][0], tgtPos[1][0], finSize[0]), ALIGN_CENTER(tgtPos[0][1], tgtPos[1][1], finSize[1])+finSize[1])

			img = cv2.putText(img, theText, finPos, font, imgScale, color, thickness, cv2.LINE_AA)

		else:
			print('!! Card '+setting['_card']+' field '+fieldName+' is of unknown type.')
			exit()
	fileName = DIRECTORY+'/'+name+'.png'
	cv2.imwrite(fileName, img[:, :, :3])
	imageDict = dict()
	imageDict['file'] = name
	imageDict['onOneLine'] = setting['_onOneLine']
	IMAGES.append(imageDict)
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
		else:
			print('!! Parameter '+paramName+' is wrongly formated.')
			exit()

	else:
		newParam = ANALYZE_CONST(paramSource)

	setting[paramName] = newParam
	return setting

def readParameters(setting, source):
	if '_count' in source:
		setting['_count'] = source['_count']

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
				tableData = tableData.transpose()
				sourceCsv.close()
				expLen = len(theList)
				if tableData.shape[0] != expLen:
					print('!! Key List '+listName+' should be '+str(expLen)+' long, but this may be intentional.')
					expLen = min(expLen, tableData.shape[0])
				for idx in range(0, tableData.shape[0]):
					oneData = dict()
					oneData['list'] = list(tableData[idx])
					print(theList[idx])
					print(oneData)
					setting = readOneParameter(setting, theList[idx], oneData)
				sourceCsv.close()
			else:
				print('!! Key List '+listName+' must contain array or existing filename.')
				exit()

	for paramName in setting['_cardParamNames']:
		if paramName in source:
			setting = readOneParameter(setting, paramName, source[paramName])

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

def printImages():
	onOneLine = IMAGES[0]['onOneLine']
	imgWidth = str(A4_TEXT_W / onOneLine)
	for img in IMAGES:
		if img['onOneLine'] != onOneLine:
			onOneLine = img['onOneLine']
			writeLine(f,0,'\\newline')
			imgWidth = str(A4_TEXT_W / onOneLine)
		writeLine(f,1,'\\includegraphics[width='+imgWidth+'cm]{'+img['file']+'}')


########
# Settings file

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
setting['_onOneLine'] = 4
setting['_cardParams'] = dict()
setting['_card'] = ''
setting['_lists'] = dict()

readAndProcessList(0, "img", source, setting)

if len(IMAGES) == 0 :
	print('\n!! There are NO images to print, skipping PDF part')
	exit()

print('\nPrinting with pdf latex\n')

f = open(TEX_FILE,'w')
imgw = A4_TEXT_W / 4

writeLine(f,0,'\\documentclass[a4paper]{article}')
writeLine(f,0,'\\usepackage[a4paper, margin='+str(A4_MARGIN)+'cm]{geometry}')
writeLine(f,0,'\\usepackage{graphicx}')
writeLine(f,0,'\\graphicspath{ {./cards/} }')
writeLine(f,0,'\\setlength{\\parindent}{0cm}')
writeLine(f,0,'\\begin{document}')
printImages()
writeLine(f,0,'\end{document}')
f.close()

os.system('pdflatex '+TEX_FILE);
