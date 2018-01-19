import re
import os
import json
import random

########
# Globals
canPrint = True

SETTING = 'simulation.in'
DIRECTORY = 'simulation'
OUTFILE = 'simuResult'

DEF_SETTING = {
    'glob_tries': 10,
    'enemy_lives': 100,
    'enemy_wpn_missile': 4,
    'enemy_wpn_beam': 6,
    'enemy_success_misile': 6,
    'enemy_success_beam': 5,
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
    'init_distance': 10,
    'glob_distance_close': 4,
    'glob_log_out': 10,
    'sequence': [0,1,1],
}

STANDS = [
    {
        'name': 'Run',
        'enemy_success': -2,
        'poll': 'poll_head',
    },
    {
        'name': 'Dodge',
        'enemy_success': -1,
        'poll': 'poll_head',
    },
    {
        'name': 'Side',
        'enemy_success': 0,
        'poll': 'poll_side',
    },
    {
        'name': 'Wedge',
        'enemy_success': +2,
        'poll': 'poll_side',
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
    addLog(5, 'diceRoll: dices:'+str(num)+'('+str(chance)+'): '+str(success))
    return success

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
poll_side.extend(addShipParts('P', setting['ship_ring']))
poll_side.extend(addShipParts('P5', setting['ship_ring']))
poll_side.extend(addShipParts('V', setting['ship_wpn_head_missile']))
poll_side.extend(addShipParts('D', setting['ship_wpn_head_beam']))
poll_side.extend(addShipParts('V5', setting['ship_wpn_side_missile']))
poll_side.extend(addShipParts('D5', setting['ship_wpn_side_beam']))

other_head = setting['ship_wpn_head_missile'] + setting['ship_wpn_head_beam'] + 1 + setting['ship_ring']
other_head = int(other_head * setting['ship_other_head'] / 100)
other_body = int(len(poll_side) * setting['ship_other_body'] / 100);

poll_side.extend(addShipParts('O', other_head))
poll_side.extend(addShipParts('O5', other_body))

poll_head = ['R0', 'S0', 'M0', 'X0']
poll_head.extend(addShipParts('P', setting['ship_ring']))
poll_head.extend(addShipParts('V', setting['ship_wpn_head_missile']))
poll_head.extend(addShipParts('D', setting['ship_wpn_head_beam']))
poll_head.extend(addShipParts('O', other_head))

poll = [poll_head, poll_side]

ship = {};
for key in poll_side:
    ship[key] = 0

# Run the Simulation
state = {
    'distance': setting['init_distance'],
    'onDistance': True,
    'stand': setting['sequence'][0],
}
results = {}
for tryIndex in range(0, setting['glob_tries']):
    distText = 'on Distance' if state['onDistance'] else 'up Close'
    addLog(0, 'Try '+str(tryIndex+1)+', '+distText)

    # Getting numbers
    stand = STANDS[state['stand']]

    # Enemy Fires
    enemy = [setting['enemy_wpn_missile'], setting['enemy_success_misile']+stand['enemy_success']]
    if not state['onDistance']: enemy = [setting['enemy_wpn_beam'], setting['enemy_success_beam']+stand['enemy_success']]
    hits = rollDice(enemy[0], enemy[1])
    poll = doPoll(poll[stand['poll']], hits)
    addLog(4, 'Enemy hits: '+str(poll))
