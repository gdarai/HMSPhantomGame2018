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

SETTING = 'coverage.json'
DIRECTORY = 'print'

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
# Processing setting file
def processingSettings( lines, setting ):
    if 'players' in lines:
        setting['players'] = lines['players']
    if 'cardsPerPlayer' in lines:
        setting['cardsPerPlayer'] = lines['cardsPerPlayer']
    if 'events' in lines:
        

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
setting['_round'] = 0
setting['state'] = dict()
setting['players'] = [2]
setting['events'] = []

processingSettings( source, setting )
