import re
import os
import json
import random
import math

########
# Globals
canPrint = True

SETTING = 'simulation.in'
DIRECTORY = 'simulation'
OUTFILE = 'simuResult'

DEF_SETTING = {
    'glob_tries': 10,
    'enemy_lives': 60,
    'enemy_wpn_missile': 4,
    'enemy_wpn_beam': 8,
    'enemy_success_missile': 6,
    'enemy_success_beam': 4,
    'enemy_speed': 20,
    'ship_speed': 21,
    'ship_other_head': 40,
    'ship_other_body': 50,
    'ship_munition_storage': 4,
    'ship_service_room': 6,
    'ship_ring': 4,
    'ship_wpn_head_missile': 2,
    'ship_wpn_head_beam': 1,
    'ship_wpn_side_missile': 7,
    'ship_wpn_side_beam': 4,
    'ship_special_rooms': 4,
    'ship_success_missile': 5,
    'ship_success_beam': 4,
    'ship_wpn_effectiveness': [2.2, 0.1],
	'ship_max_damage': 20,
    'init_distance': 100,
    'glob_distance_close': 40,
    'glob_distance_death': 0,
    'glob_log_out': 10,
#    'sequence': [0,1,1],
    'sequence': [2],
    'enemy_lost_beam': 30,
    'enemy_lost_missile': 20,
    'enemy_lost_speed': 15,
    'repair_crews': 10,
    'repair_delay': 5,
}

STANDS = [
    {
        'name': 'Run',
        'enemy_success': -2,
        'poll': 'poll_head',
        'weapons': 'head',
        'speed': 0,
    },
    {
        'name': 'Dodge',
        'enemy_success': -1,
        'poll': 'poll_head',
        'weapons': 'head',
        'speed': -3,
    },
    {
        'name': 'Side',
        'enemy_success': 0,
        'poll': 'poll_side',
        'weapons': 'side',
        'speed': -6,
    },
    {
        'name': 'Wedge',
        'enemy_success': +2,
        'poll': 'poll_side',
        'weapons': 'none',
        'speed': -6,
    },
]

log = []
setting = {}

########
# Superglobals

def printError(text):
    global canPrint
    print('!ERR '+text)
    canPrint = False

def printWarning(text):
	print('WARN '+text)

def addLog(lev, line):
    global log
    global setting
    log.append([lev,line])
    if setting['glob_log_out']>lev: print(line)
def writeLine(f, intention, text):
	f.write('\t'*intention+text+'\n')

def writeLineCondition(f, intention, textNo, textYes, condition):
	if(condition):
		f.write('\t'*intention+textYes+'\n')
	else:
		f.write('\t'*intention+textNo+'\n')

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

def addShipParts( code, count ):
    theList = []
    for i in range(0,count):
        theList.append(code+str(i))
    return theList

def reRollDice( extraNum ):
    n = random.randint(1, 6)
    if n<4: return False
    if extraNum==1: return True
    return reRollDice( extraNum-1 )

def rollDice( num, chance ):
    success = 0;
    for i in range(0, num):
        n = random.randint(1, 6)
        if n>=chance:
            success += 1
            continue
        if chance>6 and n==6:
            if reRollDice(chance-6):
                success += 1
                continue
    addLog(5, ' - - diceRoll: dices:'+str(num)+'('+str(chance)+'): '+str(success))
    return success

def doPoll( poll, hits ):
	if hits>=len(poll):
		return poll[:]
	idx = range(0, len(poll))
	pick = random.sample(idx, hits)
	selection = []
	for i in pick: selection.append(poll[i])
	return selection

def doDamage( hit, isDestroyed ):
	return 1

def getCICReport( damage, ship ):
	report = []
	for d in damage:
		report.append([d, ship[d]])
	return report

def getShipWeapons( stand, setting, state, turnCount ):
    out = [0, 6]
    wpnType = 'missile' if state['onDistance'] else 'beam'
    wpnStand = stand['weapons']
    if wpnStand == 'none': return out
    out[1] = setting['ship_success_'+wpnType]

    count = setting['ship_wpn_'+wpnStand+'_'+wpnType] - state[wpnStand+'_'+wpnType+'_down']
    effect = setting['ship_wpn_effectiveness'][0] - (setting['ship_wpn_effectiveness'][1] * state['wpn_effectiveness_down'])

    count1 = count * effect
    count2 = math.floor(count1)
    if (count1 != count2) and (turnCount % 2 == 0): count2 += 1
    out[0] = int(count2)
    return out

def getEnemyWeapons( state, setting ):
    wpn = 'missile' if state['onDistance'] else 'beam'
    return [
        int(max(setting['enemy_wpn_'+wpn]-(math.floor(state['enemy_damage'] / setting['enemy_lost_beam'])), 1)),
        setting['enemy_success_'+wpn]+stand['enemy_success']
    ]

def addDamagedSystem( state, hit ):
    if hit[0] == 'V': # Missile
        if hit[1] == '0':
            state['head_missile_down'] += 1
        else:
            state['side_missile_down'] += 1
    elif hit[0] == 'D': # Beam
        if hit[1] == '0':
            state['head_beam_down'] += 1
        else:
            state['side_beam_down'] += 1
    elif hit[0] == 'M' or hit[0] == 'S': # Service
        state['wpn_effectiveness_down'] += 1
    elif hit[0] == 'P': # Rings
        state['speed_down'] += 1

def calcNewSpeed( setting, state ):
    out = setting['enemy_speed']-setting['ship_speed']-STANDS[state['stand']]['speed']
    out += state['speed_down'] - math.floor(state['enemy_damage']/setting['enemy_lost_speed'])
    return int(out)

########
# Process

# Settings file
print('\nReading parameters --> '+SETTING)
files = getFiles(SETTING)
if(len(files)!=1):
    print('\nPrinting default setting into: '+SETTING)
    with open(SETTING, 'w') as outfile:
        json.dump(DEF_SETTING, outfile, sort_keys=True, indent=4)

setting = json.load(open(SETTING))
currKeys = setting.keys();
allKeys = DEF_SETTING.keys();
test = False

for key in currKeys:
    if key not in allKeys:
        del setting[key]
        test = True
        printError('Removing unwanted key "'+key+'" from the setting.')

for key in allKeys:
    if key not in currKeys:
        setting[key] = DEF_SETTING[key]
        test = True
        printError('Adding missing key "'+key+'" to the setting, value:'+str(DEF_SETTING[key]))

if test:
    print('\nSetting changed, reprinting into: '+SETTING)
    with open(SETTING, 'w') as outfile:
        json.dump(setting, outfile, sort_keys=True, indent=4)

# Can simulate?
print('\nCan Run: '+str(canPrint))
if canPrint == False:
	exit()

# Geting Simulation output file
if(not os.path.isdir(DIRECTORY)):
    os.mkdir(DIRECTORY)
files = getFiles(DIRECTORY+'/'+OUTFILE+'\.*.txt')
fileName = DIRECTORY+'/'+OUTFILE+'_'+str(len(files)+1)+'.txt'
print('\nResults will be printed in --> '+fileName)

# Setting the ship
poll_side = ['R0','R1','K0','K1'];
poll_side.extend(addShipParts('X', setting['ship_special_rooms']))
poll_side.extend(addShipParts('M', setting['ship_munition_storage']))
poll_side.extend(addShipParts('S', setting['ship_service_room']))
poll_side.extend(addShipParts('P0', setting['ship_ring']))
poll_side.extend(addShipParts('P5', setting['ship_ring']))
poll_side.extend(addShipParts('V0', setting['ship_wpn_head_missile']))
poll_side.extend(addShipParts('D0', setting['ship_wpn_head_beam']))
poll_side.extend(addShipParts('V5', setting['ship_wpn_side_missile']))
poll_side.extend(addShipParts('D5', setting['ship_wpn_side_beam']))

other_head = setting['ship_wpn_head_missile'] + setting['ship_wpn_head_beam'] + 1 + setting['ship_ring']
other_head = int(other_head * setting['ship_other_head'] / 100)
other_body = int(len(poll_side) * setting['ship_other_body'] / 100);

poll_side.extend(addShipParts('O', other_head))
poll_side.extend(addShipParts('O5', other_body))

poll_head = ['R0', 'S0', 'M0', 'X0']
poll_head.extend(addShipParts('P0', setting['ship_ring']))
poll_head.extend(addShipParts('V0', setting['ship_wpn_head_missile']))
poll_head.extend(addShipParts('D0', setting['ship_wpn_head_beam']))
poll_head.extend(addShipParts('O', other_head))

# Run the Simulation

results = {}
for tryIndex in range(0, setting['glob_tries']):
	# One Game
    state = {
        'distance': setting['init_distance'],
        'onDistance': True,
        'stand': setting['sequence'][0],
        'sequenceLength': len(setting['sequence']),
        'damage': 0,
        'victory': False,
        'lost': False,
        'head_missile_down': 0,
        'head_beam_down': 0,
        'side_missile_down': 0,
        'side_beam_down': 0,
        'wpn_effectiveness_down': 0,
        'speed_down': 0,
        'enemy_damage': 0,
        'our_damage_total': 0,
        'speed': setting['enemy_speed']-setting['ship_speed']-STANDS[setting['sequence'][0]]['speed'],
    }

    poll = {
        'poll_head': poll_head[:],
        'poll_side': poll_side[:],
    }
    toRepair = []
    destroyed = []

    ship = {};
    for key in poll_side:
        ship[key] = 0

    turnCount = 0;

    addLog(0, '==> Game #'+str(tryIndex+1)+' ==')
    while True:
        turnCount += 1
		# One Turn
        distText = 'on Distance' if state['onDistance'] else '!! UP CLOSE !!'
        stand = STANDS[state['stand']]
        we = getShipWeapons(stand, setting, state, turnCount)
        enemy = getEnemyWeapons(state, setting)
        addLog(0, 'Turn #'+str(turnCount)+', Distance: '+str(state['distance'])+' '+distText+', Stand: '+stand['name']+', Closing Speed: '+str(state['speed']))
        addLog(2, ' - We: '+str(we[0])+'('+str(we[1])+'), Enemy: '+str(enemy[0])+'('+str(enemy[1])+')')
		# Enemy Fires
        hits = rollDice(enemy[0], enemy[1])
        pollHits = doPoll(poll[stand['poll']], hits)
        state['our_damage_total'] += hits
        addLog(4, ' - Enemy hits: '+str(pollHits)+ ' ('+str(state['our_damage_total'])+')')

		# Do Damage
        for hit in pollHits:
            if ship[hit] == 2:
                state['damage'] += doDamage(hit, True)
                ship[hit] = 3
                if hit in poll['poll_head']: poll['poll_head'].remove(hit)
                poll['poll_side'].remove(hit)
                destroyed.append(hit)
                toRepair.remove(hit)
            elif ship[hit] == 1:
                state['damage'] += doDamage(hit, False)
                ship[hit] = 2
            elif ship[hit] == 0:
                ship[hit] = 1
                toRepair.append(hit)
                addDamagedSystem(state, hit)

        # We Fires
        hits = rollDice(we[0], we[1])
        state['enemy_damage'] += hits
        addLog(4, ' - We hits: +'+str(hits)+' ('+str(state['enemy_damage'])+'/'+str(setting['enemy_lives'])+')')


		# Lost Condition
        if state['damage'] >= setting['ship_max_damage']:
            state['lost'] = True
            break

		# Win Condition
        if state['enemy_damage'] >= setting['enemy_lives']:
            state['victory'] = True
            break

		# Ship Summary
        addLog(2, ' - Ship Damage('+str(state['damage'])+'/'+str(setting['ship_max_damage'])+'): '+str(getCICReport(toRepair, ship)))
        addLog(2, ' - - Destroyed: '+str(destroyed))

		# Calc new Distances
        state['distance'] -= state['speed']
        state['onDistance'] = state['distance'] > setting['glob_distance_close']

		# Lost Distance Condition
        if state['distance'] <= setting['glob_distance_death']:
            state['lost'] = True
            break

		# Evasive Action
        state['stand'] = setting['sequence'][turnCount % state['sequenceLength']]
        state['speed'] = calcNewSpeed(setting, state)

    addLog(0, '')
    if state['lost']: addLog(0, 'GAME LOST')
    if state['victory']: addLog(0, 'VICTORY')
    addLog(0, '')
