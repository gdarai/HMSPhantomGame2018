import re
import os
import json
import random
import math

########
# Globals
canPrint = True

SETTING = 'cards.json'
DIRECTORY = 'cards'
OUTFILE = 'cards_print'

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
# Process
def readParameters(setting, source):
	if '_count' in source: setting['_count'] = source['_count']

	return setting

def checkParameters(setting):
	return True

def readAndProcessList(level, name, sourceList, setting):
	index = 0
	for s in sourceList:
		index = index + 1
		newName = name + '-' + str(index);
		if '_key' in s:
			newName = name + '-' + s['_key']
		readAndProcess(level, newName, s, setting)

def readAndProcess(level, name, source, setting):
	separator = '  ' * level
	print(separator+name)
	newLevel = level + 1
	setting = readParameters(setting, source)
	if '_sub' in source:
		readAndProcessList(newLevel, name, source['_sub'], setting)
	else:
		doPrint = checkParameters(setting)
		if doPrint:
			print(separator+' -printing '+str(setting['_count'])+'x')

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
setting = dict()
setting['_count'] = 1
setting['_cardParams'] = {}
readAndProcessList(0, "in", source, setting)
