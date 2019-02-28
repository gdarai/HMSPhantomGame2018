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
    checkForKeys('root', ['players', 'cardsPerPlayer', 'initialPackage', 'events', 'packets'], lines)
    addKeyAndCheck(lines, setting, setting, 'players', 'glob_')
    addKeyAndCheck(lines, setting, setting, 'cardsPerPlayer', 'glob_')
    addKeyAndCheck(lines, setting, setting, 'initialPackage', 'glob_')
    for eventName in lines['events']:
        addKeyAndCheck(lines['events'], setting['events'], setting, eventName, 'events_')
        setting['state']['events'][eventName] = 0
    packetIdx = 0
    for packet in lines['packets']:
        packetIdx += 1
        checkForKeys('packet_'+str(packetIdx), ['name', 'cardsTotal', 'addExtra', 'removeOld', 'cards'], packet)
        newPacket = dict()
        newPacket['name'] = packet['name']
        newPacket['idx'] = packetIdx
        packCheckKey = 'pack_'+str(packetIdx)+'_'
        cardCheckKey = 'pack_'+str(packetIdx)+'_card_'
        addKeyAndCheck(packet, newPacket, setting, 'cardsTotal', packCheckKey)
        addKeyAndCheck(packet, newPacket, setting, 'addExtra', packCheckKey)
        addKeyAndCheck(packet, newPacket, setting, 'removeOld', packCheckKey)
        cardIdx = 0
        newCards = dict()
        for card in packet['cards'].keys():
			cardIdx += 1
			addKeyAndCheck(packet['cards'], newCards, setting, card, packCheckKey)
        newPacket['cards'] = newCards
        setting['packets'][packetIdx] = newPacket
    setting['packets']['count'] = packetIdx
	setting['currentPacket'] = dict()

def checkForKeys( inSource, keys, theSource ):
    for keyName in keys:
        if keyName not in theSource:
            print('!! missing key '+keyName+' in source '+inSource )
            exit()

def addKeyAndCheck(source, target, checkTarget, keyName, prefix):
    target[keyName] = source[keyName]
    checkTarget['check'][prefix+keyName] = len(source[keyName])

########
# One Round
def doNextDraw( setting ):


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
setting['state']['events'] = dict()
setting['state']['packets'] = dict()
setting['players'] = [2]
setting['events'] = dict()
setting['packets'] = dict()
setting['check'] = dict()
setting['check']['glob_players'] = 1
setting['run'] = True
setting['idx'] = 0
processingSettings( source, setting )
print(setting)

for x in range(0, setting['initialPackage'][setting['idx']]):
	doNextDraw(setting)

while setting['run']:
	print('Round: '+str(setting['_round']))
	doNextDraw(setting)
	setting['run'] = False
