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
import matplotlib.pyplot as plt

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
    checkForKeys('root', ['players', 'cardsPerPlayer', 'initialPackage', 'events', 'packets', 'rounds'], lines)
    addKeyAndCheck(lines, setting, setting, 'rounds', 'glob_')
    addKeyAndCheck(lines, setting, setting, 'players', 'glob_')
    addKeyAndCheck(lines, setting, setting, 'cardsPerPlayer', 'glob_')
    addKeyAndCheck(lines, setting, setting, 'initialPackage', 'glob_')
    for eventName in lines['events']:
        addKeyAndCheck(lines['events'], setting['events'], setting, eventName, 'events_')
        setting['state']['events'][eventName] = 0
    packetIdx = 0
    for packet in lines['packets']:
        packetIdx += 1
        checkForKeys('packet_'+str(packetIdx), ['name', 'cardsTotal', 'addExtra', 'removeOld', 'chanceToShuffle', 'cards'], packet)
        newPacket = dict()
        newPacket['name'] = packet['name']
        newPacket['idx'] = packetIdx
        packCheckKey = 'pack_'+str(packetIdx)+'_'
        cardCheckKey = 'pack_'+str(packetIdx)+'_card_'
        addKeyAndCheck(packet, newPacket, setting, 'cardsTotal', packCheckKey)
        addKeyAndCheck(packet, newPacket, setting, 'addExtra', packCheckKey)
        addKeyAndCheck(packet, newPacket, setting, 'removeOld', packCheckKey)
        addKeyAndCheck(packet, newPacket, setting, 'chanceToShuffle', packCheckKey)
        cardIdx = 0
        newCards = dict()
        for card in packet['cards'].keys():
            cardIdx += 1
            addKeyAndCheck(packet['cards'], newCards, setting, card, packCheckKey)
        newPacket['cards'] = newCards
        setting['packets'][packetIdx] = newPacket
    setting['packets']['count'] = packetIdx

def checkForKeys( inSource, keys, theSource ):
    for keyName in keys:
        if keyName not in theSource:
            print('!! missing key '+keyName+' in source '+inSource )
            exit()

def addKeyAndCheck(source, target, checkTarget, keyName, prefix):
    target[keyName] = source[keyName]
    checkTarget['check'][prefix+keyName] = len(source[keyName])

def doSettingInit(setting):
	setting['run'] = True
	setting['_haveCards'] = True
	setting['_undrawenCards'] = 0
	setting['_cardsToDraw'] = 0
	setting['_haveCardsToUndraw'] = True
	setting['idx'] = 0
	setting['currentPacket'] = dict()
	setting['_cardsToDraw'] = 0
	setting['newPacket'] = dict()
	setting['newPacketCardCount'] = 0
	setting['inPacket'] = 1
	setting['_shouldShuffle'] = False
	setting['_chanceToShuffle'] = 0
	setting['_draw'] = dict()
	for packetIdx in range(1, setting['packets']['count']+1):
		setting['packets'][packetIdx]['_freeCards'] = copy.deepcopy(setting['packets'][packetIdx]['cardsTotal'])

########
# One Round
def drawOneCard( setting, cardName, packetCards, idx, amount ):
	prevValue = [0, 0]
	if(cardName in setting['newPacket']):
		prevValue = setting['newPacket'][cardName]
	setting['newPacket'][cardName] = [prevValue[0] + (amount * packetCards[cardName][idx]), prevValue[1] + amount]

def doCardDraw( setting, amount ):
	idx = setting['idx']
	packetIdx = setting['inPacket']
	setting['newPacketCardCount'] = setting['newPacketCardCount'] + amount
	while (amount > 0 and packetIdx <= setting['packets']['count']):
		cardsToTake = min(setting['packets'][packetIdx]['_freeCards'][idx], amount);
		setting['packets'][packetIdx]['_freeCards'][idx] -= cardsToTake
		amount = amount - cardsToTake
		for card in setting['packets'][packetIdx]['cards'].keys():
			drawOneCard(setting, card, setting['packets'][packetIdx]['cards'], idx, cardsToTake)
		if (amount > 0):
			packetIdx += 1
			setting['inPacket'] = packetIdx
	if (packetIdx > setting['packets']['count']):
		print('No more cards to draw (missing '+str(amount)+')')
		setting['_haveCards'] = False
		setting['newPacketCardCount'] = setting['newPacketCardCount'] - amount

def doCardUndraw( setting, amount ):
	idx = setting['idx']
	packetIdx = 1
	cardsHave = setting['packets'][1]['cardsTotal'][idx] - setting['_undrawenCards']
	cardsToTake = min(cardsHave, amount);
	setting['newPacketCardCount'] = setting['newPacketCardCount'] - cardsToTake
	setting['_undrawenCards'] += cardsToTake
	for card in setting['packets'][1]['cards'].keys():
		drawOneCard(setting, card, setting['packets'][1]['cards'], idx, -cardsToTake)
	if (cardsToTake == cardsHave):
		print('No more cards to un-draw')
		setting['_haveCardsToUndraw'] = False

def drawFromCurrent(setting):
	packet = min(setting['inPacket'], setting['packets']['count'])
	chanceToShuffle = setting['packets'][packet]['chanceToShuffle'][setting['idx']]
	setting['_cardsToDraw'] -= setting['players'][setting['idx']]
	setting['_chanceToShuffle'] += setting['players'][setting['idx']] * chanceToShuffle
	setting['_shouldShuffle'] = setting['_chanceToShuffle'] >= 1 or setting['_cardsToDraw'] <= 0

def shufflePack( setting ):
	setting['currentPacket'] = copy.deepcopy(setting['newPacket'])
	setting['_cardsToDraw'] = setting['newPacketCardCount']
	setting['currentPacketCardCount'] = setting['newPacketCardCount']
	setting['_chanceToShuffle'] = 0
	print('Shuffling pack, new pack has '+str(setting['_cardsToDraw'])+' cards')

def addOneGraphData( setting, cardName, xData, yData ):
	if cardName in setting['_draw']:
		setting['_draw'][cardName]['x'].append(xData)
		setting['_draw'][cardName]['y'].append(yData)
	else:
		setting['_draw'][cardName] = { 'x':[xData], 'y':[yData] }

def addGraphData( setting ):
	x = setting['_round']
	count = setting['currentPacketCardCount']
	for cardName in setting['currentPacket'].keys():
		data = setting['currentPacket'][cardName]
		addOneGraphData(setting, cardName, setting['_round'], data[0]/(count))
	val = (float(setting['inPacket']))/(2*(setting['packets']['count']))
	if setting['inPacket'] > setting['packets']['count']:
		val = 0
	addOneGraphData(setting, 'In Packet', setting['_round'], val)

def plotGraph( setting ):
	names = []
	curveList = sorted(setting['_draw'].keys())
	for curve in curveList:
		isBar = curve in ['In Packet']
		data = setting['_draw'][curve]
		if isBar:
			plt.bar(data['x'], data['y'], alpha=0.2)
		else:
			plt.plot(data['x'], data['y'])
			names.append(curve)
	plt.figlegend(names)
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
setting['rounds'] = [20]
setting['state'] = dict()
setting['state']['events'] = dict()
setting['state']['packets'] = dict()
setting['players'] = [2]
setting['events'] = dict()
setting['packets'] = dict()
setting['check'] = dict()
setting['check']['glob_players'] = 1
setting['check']['glob_rounds'] = 1

processingSettings( source, setting )

doSettingInit(setting)
print(setting)

doCardDraw(setting, setting['initialPackage'][setting['idx']])
shufflePack(setting)
addGraphData(setting)

while setting['run']:
	setting['_round'] += 1
	cardsToDraw = 0
	cardsToRemove = 0
	if (setting['_haveCards']):
		cardsToDraw = setting['packets'][setting['inPacket']]['addExtra'][setting['idx']]
		cardsToDraw = cardsToDraw * setting['players'][setting['idx']]
	if (setting['_haveCardsToUndraw']):
		packet = min(setting['inPacket'], setting['packets']['count'])
		cardsToRemove = setting['packets'][packet]['removeOld'][setting['idx']]

	print('Round: '+str(setting['_round'])+'[in '+str(setting['inPacket'])+'], draw: '+str(cardsToDraw)+'(-'+str(cardsToRemove)+')')

	if (setting['_haveCards']):
		doCardDraw(setting, cardsToDraw)
	if (setting['_haveCardsToUndraw']):
		doCardUndraw(setting, cardsToRemove)

	drawFromCurrent(setting)
	if (setting['_shouldShuffle']):
		shufflePack(setting)

	if (setting['_round'] == setting['rounds'][setting['idx']]):
		setting['run'] = False

	addGraphData(setting)

plotGraph(setting)
plt.savefig('plot.png')
plt.show()
