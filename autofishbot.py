#------------------------ IMPORTS --------------------------#
import json
import curses #pip install windows-curses / curses (linux)
import requests
import websocket 
import webbrowser
from threading import Thread
from os import getcwd, path, system
from re import sub, findall
from math import ceil
from time import sleep
from random import uniform, randint
from configparser import ConfigParser


#------------------------ CONSTANTS --------------------------#

MARGIN = 1.5
BOT_UID = "574652751745777665"
REPO_CONFIG = 'https://github.com/thejoabo'
OPCODES = [
    {'code': 0, 'name': 'Dispatch', 'action': 'Receive', 'description': 'An event was dispatched.'},
    {'code': 1, 'name': 'Heartbeat', 'action': 'Send/Receive', 'description': 'Fired periodically by the client to keep the connection alive.'},
    {'code': 2, 'name': 'Identify', 'action': 'Send', 'description': 'Starts a new session during the initial handshake.'},
    {'code': 3, 'name': 'Presence Update', 'action': 'Send', 'description': 'Update the client\'s presence.'},
    {'code': 4, 'name': 'Voice State Update', 'action': 'Send', 'description': 'Used to join/leave or move between voice channels.'},
    {'code': 6, 'name': 'Resume', 'action': 'Send', 'description': 'Resume a previous session that was disconnected.'},
    {'code': 7, 'name': 'Reconnect', 'action': 'Receive', 'description': 'You should attempt to reconnect and resume immediately.'},
    {'code': 8, 'name': 'Request Guild Members', 'action': 'Send', 'description': 'Request information about offline guild members in a large guild.'},
    {'code': 9, 'name': 'Invalid Session', 'action': 'Receive', 'description': 'The session has been invalidated. You should reconnect and identify/resume accordingly.'},
    {'code': 10, 'name': 'Hello', 'action': 'Receive', 'description': 'Sent immediately after connecting, contains the heartbeat_interval to use.'},
    {'code': 11, 'name': 'Heartbeat ACK', 'action': 'Receive', 'description': 'Sent in response to receiving a heartbeat to acknowledge that it has been received.'},
]
QUERYS = [
    {'CODE': 0, 'PAYLOAD': ['%fish', '%f'], 'ACTION': 'Catch some fish.'},
    {'CODE': 1, 'PAYLOAD': ['%sell all', '%s all'], 'ACTION': 'Sell all the fishes you caught.'},
    {'CODE': 2, 'PAYLOAD': '%profile', 'ACTION': 'View your inventory.'},
    {'CODE': 3, 'PAYLOAD': '%daily', 'ACTION': 'Get your daily reward.'},
    {'CODE': 4, 'PAYLOAD': '%stats', 'ACTION': 'Check your stats.'},
    {'CODE': 5, 'PAYLOAD': {'default' : '%coinflip', 'options' : ['h', 't']}, 'ACTION': 'Flip a coin to have a chance at doubling your money.'},
    {'CODE': 6, 'PAYLOAD': {'default' : ['%top', '%servertop'], 'options' : ['xp', 'money', 'fish', 'quests', 'chests', 'net', 'weekly']}, 'ACTION': 'View the global or server leaderboards.'},
    {'CODE': 7, 'PAYLOAD': ['%verify', '%v'], 'ACTION': 'Verifies captcha result.'}
]
MENUART = """ ___        _         ___  _      _     ___       _   
/   \ _  _ | |_  ___ | __|(_) ___| |_  | _ ) ___ | |_ 
| - || || ||  _|/ _ \| _| | |(_-/|   \ | _ \/ _ \|  _|
|_|_| \_._| \__|\___/|_|  |_|/__/|_||_||___/\___/ \__|"""

MENUART2 = [
    ' ▀▄▀ ▄▀▄ █ █   ▄▀▀ ▄▀▄ █ █ ▄▀  █▄█ ▀█▀',
    '  █  ▀▄▀ ▀▄█   ▀▄▄ █▀█ ▀▄█ ▀▄█ █ █  █ '
    ]

KEYBINDS = [
    {'key': 'KEYBINDS ', 'description': '   INFORMATION   '},
    {'key': '   Q     ', 'description': '   Exit         '},
    {'key': '   p     ', 'description': '   Pause/resume '},
    {'key': '   u     ', 'description': '   Update info  '},
    {'key': '   H     ', 'description': '   Help Page    '},
    {'key': '   M     ', 'description': '   Manual mode  '}
    ]

DEBUG = False

#------------------------ VARIABLES --------------------------#

#Switches
disconnected = False
fish_paused = True
in_cooldown = False

#Counters
streak = 0
bypasses = 0
buff_countdown = 0
cooldown_lifetime= 0

#Strings
log_message = "[!] Welcome back."

#-------------------- CONFIG LOADER --------------------#
def to_bool(param: str) -> bool:
    if param.lower() in ['1', 'true']:
        return True
    else:
        return False

def configLoader(param : str = 'default') -> bool:
    '''Generate and load configuration files'''
    global CHANNEL_ID,USER_TOKEN,USER_COOLDOWN,BAIT,AUTO_BUFF,AUTOFISH_ON_EXIT,BUFF_LENGTH,OCR_API_KEY

    configPath = f'{getcwd()}/autofish.config'

    if path.isfile(configPath) and param == 'default':
        try:
            config = ConfigParser()
            config.read(configPath)
            cfg = config['PREFERENCES']
            
            #?-------------------- USER CONSTANTS --------------------#
            CHANNEL_ID = cfg['CHANNEL_ID']
            USER_TOKEN = cfg['USER_TOKEN']
            OCR_API_KEY = cfg['OCR_API_KEY']
            USER_COOLDOWN = float(cfg['USER_COOLDOWN']) 
            BAIT = cfg['BAIT']
            AUTO_BUFF = to_bool(cfg['AUTO_BUFF']) 
            _tmp = int(cfg['BUFF_LENGTH'])
            if _tmp or _tmp != 0:
                if _tmp > 12.5: BUFF_LENGTH = 20
                else: BUFF_LENGTH = 5
            else: BUFF_LENGTH = 5
            #?---------------------------------------------------------#
            
            return True
        except Exception as e:
            print(f'\n[E] Config couldn\'t be loaded -> {e}')
            configLoader('force')
    else:
        if path.isfile(configPath) and param == 'force':
            print(f'\n[E] Configuration exists but doesn\'t follow the expected format.')
            if input(f'Would you like to generate a new one ? (y/n)').lower() == 'n':
                exit(f'[!] User exited.')
        
        #*CREATE NEW CONFIG
        newConfig = ConfigParser()
        newConfig['PREFERENCES'] = {
                'CHANNEL_ID' : 'YOUR CHANNEL ID',
                'USER_TOKEN' : 'YOUR TOKEN',
                'OCR_API_KEY' : 'YOUR API KEY',
                'USER_COOLDOWN' : 'YOUR COOLDOWN',
                'BAIT' : 'WORMS, LEECHES, ...',
                'AUTO_BUFF' : 'TRUE',
                'BUFF_LENGTH' : '5'
        }
        try:
            with open(configPath, 'w') as f:
                newConfig.write(f)
            exit_message = f'\n[!] Config successfully created at "{configPath}".\n[!] Please fill in the configuration information...'
            webbrowser.open(configPath)
        except webbrowser.Error as e:
            exit_message = f'\n[E] Unable to open default text editor, please edit it manually.\n[!] Details: {e}'
        except Exception as e:
            exit_message =f'\n[E] Unable to create new config -> {e}\n[!] NOTE: If keeps failing download a sample config file at: {REPO_CONFIG}'
        finally:
            exit(exit_message)



#-------------------- CLASSES --------------------#

class discordWebgate:
    def __init__(self, auto_connect = True, payload = None) -> None:
        self._query = f'https://discord.com/api/v9/channels/{CHANNEL_ID}/messages'
        self._webgateApi = 'wss://gateway.discord.gg/?v=9&encoding=json'
        self._payload = {
                'op': 2,
                'd': { 
                    'token': USER_TOKEN,
                    'properties': { 
                        '$os': 'windows',
                        "$browser": 'chrome',
                        '$device': 'pc'
                    }
                }
            }
        self._ws = websocket.WebSocket()
        self._keepAlive = True
        if auto_connect:
            self.connect()  
            self.sendRequest()
            print('[*] Session stablished !')
     
    def connect(self) -> None:
        try:
            self._ws.connect(self._webgateApi)
            self._interval = self._getInterval()
            self._heartbeathread = Thread(target=self._sendHeartbeat, daemon=True)
            self._heartbeathread.start()
        except Exception as e:
            exit(f'\n[E] Something went wrong while connecting: {e}')
    
    def disconnect(self) -> bool:
        try:
            self._keepAlive = False
            self._ws.close()  
            return True
        except Exception as e:
            print(f'\n[E] Something went wrong while disconnecting: {e}')
            return False
        
    def recieveEvent(self) -> list:
        _response = self._ws.recv()
        if _response:
            return json.loads(_response)
        
    def sendQuery(self, payload) -> None:
        r = requests.post(self._query, data = {'content': payload}, headers = {'authorization': USER_TOKEN})
   
    def sendRequest(self, request = None) -> None:
        if request:
            _request = request
        else:
            _request = self._payload
        self._ws.send(json.dumps(_request))
    
    def _getInterval(self) -> int:
        try:
            tmp = self.recieveEvent()
            return int(tmp['d']['heartbeat_interval']) / 1000
        except:
            return int(41.25)
    
    def _sendHeartbeat(self) -> None:
        while True:
            if self._keepAlive:
                log('Heartbeat sent.', 'notice')
                sleep(self._interval)
                self.sendRequest({ 'op': 1, 'd': 'null' })
            else:
                break


class Captcha:
    def __init__(self) -> None:
        self.reset()
        pass
    
    def reset(self) -> None:
        self.event = None
        self.solved = False
        self.detected = False
        self.embed = None
        self.content = None
        self.ocr_url = 'https://api.ocr.space/parse/image'
        self.answerList = []

    def detect(self, event) -> bool:
        self.event = event
        if len(event['embeds']) > 0:
            self.embed = event['embeds']
            for item in self.embed:
                for testcase in ['captcha', 'verify']:
                    if str(item).find(testcase) > -1:
                        #*Image verification
                        try: 
                            self.image_url = item['image']['url']
                            self.detected = True 
                            return True
                        except KeyError:
                            self.image_url = None
                        
                        try: self.description = item['description']
                        except KeyError:
                            self.description = None
                            
                        if event['content']:
                            self.content = event['content']
                        self.detected = True 
                        return True
            self.solved = True
            return False
        else:
            if str(event).find('%verify') > -1:
                #Is captcha
                debug(event)
                exit(f'[E] Unknown captcha.')
                #return True

    def solve(self, session: discordWebgate) -> bool:
        if self.image_url:
            #Generate captcha values using all engines
            for engine in [2, 1]: #[2, 3, 1]
                log(f'Using OCR Engine {engine}')
                
                payload = {
                    'apikey': OCR_API_KEY,
                    'url': self.image_url,
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': False,
                    'OCREngine': engine,
                    'language': 'eng',
                }
                
                #Send request to OCR.SPACE
                r = requests.post(self.ocr_url, data=payload)
                response = json.loads(r.content.decode())

                #Filter results there are reasonable
                if response['OCRExitCode'] == 1:
                    answer = sub(r'/[\@a-zA-Z0-9]/g', '', response['ParsedResults'][0]['ParsedText'])
                    answer = sub('[\n\r ]', '', answer)
                    if len(answer) == 6:
                        log(f'The code \'{answer}\' was added to possible results.')
                        self.answerList.append(answer)
                    else:
                        log(f'OCR Engine {engine} failed to provide reasonable certainty.', 'notice')
                else:
                    log(f'OCR Engine {engine} returned exit code {response["OCRExitCode"]}.', 'err')
                sleep(3)
                
            #Atempt to solve
            if self.answerList != []:
                for testcase in self.answerList:
                    if not self.solved:
                        log(f'Attempting code: \'{testcase}\'')
                        session.sendQuery(f'%verify {testcase}')
                        sleep(3)
                    else:
                        return True
        else:
            session.disconnect()
            debug(self.event)
            print('should exit here. if you are seeing this, report on github')
            exit('[E] Unknown captcha.')


class Message:
    def __init__(self, event = []) -> None:
        self.items_list = []
        self.title = None
               
        if event == []:
            pass   
        else:
            #this variables assignment will change in the future
            try: self.content = event['content']
            except KeyError:
                self.content = None
            try: self.timestamp = event['timestamp']
            except KeyError:
                self.timestamp = None
            
            for embed in event['embeds']:
                try:
                    #*Main embed
                    if embed['title']:
                        self.title = embed['title']
                        try: self.description = embed['description']
                        except KeyError:
                            self.description = None
                except KeyError:
                    self.items_list.append(self.sanatize(embed['description']))
                
    def sanatize(self, content):
        content = sub(r':.+?: ', '', content)#Remove any emotes
        content = sub(r'\n', ' ', content)#Remove new lines
        content = sub(r'[\*_`\n]', '', content)#Remove Markdown
        return content
    
    def buildList(self, custom_list = []):
        _tmp = self.description.split('\n')
        for line in _tmp:
            final = ''
            if line.find('LEVEL') > -1:
                #Level up information
                level = [int(x) for x in findall(r'\b\d+\b', line)]
                final = f'<< LEVEL UP: {level[-1] - 1} -> {level[-1]} >>'
            elif line.find('<:') > -1:
                #Emotes 
                #!FIX NEEDED
                emotefix = line.split(' ')
                for word in emotefix:
                    if word.find('<:') < 0:
                        final += f'{word} '
            elif line.find('#') > -1: 
                #Global boost information
                pass
            elif line.find('Use **%bait**') > -1:
                #Useless bait purchase line information
                pass
            else:
                final = line
            self.items_list.append(sub('[\*+]', '', final))
        if custom_list != []:
            self.items_list = custom_list + self.items_list


class Profile():
    def __init__(self, event = []) -> None:
        self.queries = ['%inv', '%stats'] #top...
        self.balance = None
        self.level = None
        self.rod = None
        self.biome = None
        self.golden = {'total': None, 'current': None}
        self.emerald = {'total': None, 'current': None}
        self.lava = {'total': None, 'current': None}
        self.crates = None
        self.quests = None
        self.trips = None
        self.daily = None
        self.buildInventory(event)
        self.buildStats(event)

    def update(self, session : discordWebgate) -> None:
        global fish_paused
        fish_paused = True
        for query in self.queries:
            session.sendQuery(query)
            sleep(USER_COOLDOWN)
        fish_paused = False

    def rebuildLists(self, event, target) -> None:
        if target == 'inv':
            self.buildInventory(event)
        elif target == 'stats':
            self.buildStats(event)

    def buildStats(self, event) -> None:
        if event != []:
            for embed in event['embeds']:
                if embed['title'].find('Statistics for') > -1:
                    lines = embed['description'].split('\n')
                    for line in lines:
                        if line != '':
                            line = sub(r'<.+?> ', '', line)
                            if line.find('crates') > -1:
                                self.crates = sub('[^\d+]', '', line)
                            elif line.find('quests') > -1:
                                self.quests = sub('[^\d+]', '', line)
                            elif line.find('trips') > -1:
                                self.trips = sub('[^\d+]', '', line)
                            elif line.find('daily') > -1:
                                self.daily = sub('[^\d+]', '', line)
                            elif line.find('golden') > -1:
                                self.golden['total'] = sub('[^\d+]', '', line)
                            elif line.find('emerald') > -1:
                                self.emerald['total'] = sub('[^\d+]', '', line)
                            elif line.find('lava') > -1:
                                self.lava['total'] = sub('[^\d+$]', '', line)
        self.stats = [
            {'title': 'TOTAL STATS   ', 'content': ''},
            {'title': 'LAVA:         ', 'content': f'{self.lava["total"]}'},
            {'title': 'GOLDEN:       ', 'content': f'{self.golden["total"]}'},
            {'title': 'EMERALD:      ', 'content': f'{self.emerald["total"]}'},
            {'title': 'CRATES:       ', 'content': f'{self.crates}'},
            {'title': 'QUESTS:       ', 'content': f'{self.quests}'},
            {'title': 'TOTAL TRIPS:  ', 'content': f'{self.trips}'},
            {'title': 'DAILY STREAK: ', 'content': f'{self.daily}'},
        ]
        
    def buildInventory(self, event) -> None:
        if event != []:
            for embed in event['embeds']:
                if embed['title'].find('Inventory of') > -1:
                    lines = embed['description'].split('\n')
                    for line in lines:
                        if line != '':
                            if line.find('Balance') > -1:
                                #Balance
                                self.balance = sub('[^\d+]', '', line)
                                if len(self.balance) > 10:
                                    self.balance = '{:.2e}'.format(int(self.balance))
                            elif line.find('Level') > -1:
                                #Level
                                self.level = sub('[.*a-zA-Z]', '',  sub(', ', '|', line))
                                self.level = sub(' ', '', self.level)
                                self.level = f"{ sub('[|]', ' | ', self.level ) } XP"
                            elif line.find('Rod') > -1:
                                #Rod
                                self.rod = sub(rf'{line[0]}.+?> ', '', line)
                                self.rod = sub('[*.]', '', self.rod)
                            elif line.find('biome') > -1:
                                #Biome
                                self.biome = sub(rf'{line[0]}.+?> ', '', line)
                                self.biome = sub('[*.]', '', self.biome)
                                #biome = line
                            elif line.find('gold') > -1:
                                #Golden Fish
                                golden = sub(r'<.+?> ', '', line)
                                self.golden['current'] = sub('[^\d+$]', '', golden)
                            elif line.find('emerald') > -1:
                                #Emerald Fish
                                emerald = sub(r'<.+?> ', '', line)
                                self.emerald['current'] = sub('[^\d+$]', '', emerald)
                            elif line.find('lava') > -1:
                                #Lava Fish
                                lava = sub(r'<.+?> ', '', line)
                                self.lava['current'] = sub('[^\d+$]', '', lava)
        self.inventory = [
            {'title': 'INVENTORY     ', 'content': ''},
            {'title': 'BALANCE:      ', 'content': f'${self.balance}'},
            {'title': 'LEVEL:        ', 'content': f'{self.level}'},
            {'title': 'ROD:          ', 'content': f'{self.rod}'},
            {'title': 'BIOME:        ', 'content': f'{self.biome}'},
            {'title': 'LAVA FISH:    ', 'content': f'{self.lava["current"]}'},
            {'title': 'GOLD FISH:    ', 'content': f'{self.golden["current"]}'},
            {'title': 'EMERALD FISH: ', 'content': f'{self.emerald["current"]}'}
        ]
            
    

#-------------------- AUX FUNCTIONS --------------------#

def autoBuff(_queries = ['%s all', '%inv', '%stats']):
    global session, disconnected, buff_countdown, fish_paused
    fish_paused = True
    
    #More fish and more treasure
    if AUTO_BUFF:
        _queries = _queries + [f'%buy fish{BUFF_LENGTH}m', f'%buy treasure{BUFF_LENGTH}m']

    #Bait resuply
    if BAIT:
        _ammount = (( (BUFF_LENGTH  * 60) / USER_COOLDOWN) - 10) * 0.75 
        _queries.append(f'%buy {BAIT} {ceil(_ammount)}')

    #Needed to continue fishing
    _queries.append('%f')
    
    while not disconnected:
        fish_paused = True
        for _query in _queries:
            try:
                while captcha.detected:
                    sleep(1)
                session.sendQuery(_query)
                sleep(3)
            except Exception as e:
                log(f'Failed to send query -> {e}', 'e')
        fish_paused = False
        
        countdown = (BUFF_LENGTH * 60)
        for seconds in range(countdown):
            buff_countdown = (countdown - seconds)
            while fish_paused:
                sleep(1)
            sleep(1)


def log(message : any, type: str = 'normal') -> None:
    global log_message
    debug(message)
    msg = sub(r'\n\r', '', str(message))
    if type == 'normal':
        log_message = f'[*] {msg}'
    elif type == 'notice':
        log_message = f'[!] {msg}'
    else:
        log_message = f'[E] {msg}'

def resize(message : str, max_width: int, delimiter: str = '...') -> str:
    if len(message) > max_width:
        return f'{message[:max_width - len(delimiter)]}{delimiter}'
    return message

def buffstatus(param: bool):
    if param: return 'ON'
    else: return 'OFF'

def debug(event):
    if DEBUG:
        print(f'\n\n{event}\n\n')



#-------------------- MENU --------------------#
def drawMenu(stdscr):
    global log_message, streak, bypasses, buff_countdown, fish_paused
    
    #*Init
    stdscr.nodelay(True)
    stdscr.erase()
    stdscr.refresh()
    
    #*Variables
    pressedKey = None

    #*Main loop
    while True:
        stdscr.erase()
        
        #*Config and general status update
        app_info = [
            {'title': 'CONFIG STATUS ', 'content': ' '},
            {'title': 'AUTOBUFF:     ', 'content': buffstatus(AUTO_BUFF)},
            {'title': 'DURATION:     ', 'content': f'{BUFF_LENGTH}'},
            {'title': 'BAIT:         ', 'content': f'{BAIT.upper()}'},
            {'title': 'STREAK:       ', 'content': f'{streak}'},
            {'title': 'BYPASSES:     ', 'content': f'{bypasses}'},
            {'title': 'RESUPLY IN:   ', 'content': f'{buff_countdown}'},
            {'title': 'COOLDOWN:     ', 'content': f'{cooldown_lifetime}'}
        ]
        
        #*Profile information
        inventory = profile.inventory
        stats = profile.stats
        
        
        #*Pressed keys
        if pressedKey == ord('p'):
            if fish_paused:
                if not in_cooldown:
                    fish_paused = False
                    session.sendQuery('%f')
                    log(f'Autofish resumed.')
                else:
                    log(f'Cooldown.', 'notice')
            else:
                fish_paused = True
                log(f'Autofish paused.')
        elif pressedKey == ord('u'):
            profile.update(session)
        elif pressedKey == ord('H'):
            log('Help page pressed - not implemented yet.', 'notice')
        elif pressedKey == ord('Q'):
            break
        elif pressedKey == ord('M'):
            log('Manual mode pressed - not implemented yet.', 'notice')
            
            
        try:
            #*Calculations
            height, width = stdscr.getmaxyx()
            column = width - round((75 * width) / 100)
            row = round((30 * height) / 100)
            m_height, m_width, m_column = (height // 2), (width // 2), (column // 2)
            #!stdscr.addstr(m_height, m_width, "C") #absolute center
            
            #------------------------ TEXT --------------------------#
            
            #*Render Last notification
            stdscr.addstr(0, 1, resize(log_message, width))
            
            #*Render Ascii art
            splitedAscii = MENUART.splitlines()
            ascii_pos_middle = (m_width - 1) - (max(len(x) for x in splitedAscii) // 2)
            for k, line in enumerate(splitedAscii):
                stdscr.addstr(k + 2, ascii_pos_middle, line)

            #*Render keybinds information panel
            for k, line in enumerate(KEYBINDS):
                _content = f'{line["key"]}-{line["description"]}'
                _content_pos_w = ((width - column) + m_column) - (len(_content) // 2)
                _content_pos_h = k + 3
                if line == KEYBINDS[0]:
                    _content_pos_h = k + 2
                stdscr.addstr(_content_pos_h, _content_pos_w, _content)
                
            #*Render app information
            for k, line in enumerate(app_info):
                _content = f'{line["title"]}{line["content"]}'
                _content_pos_w = ((width - column)) #-(len(_content) // 2)
                _content_pos_h = (height - row) + k + 2 
                if line == app_info[0]:
                    
                    _content_pos_w = ((width - column) + m_column) - (len(_content) // 2)
                    _content_pos_h = (height - row) + k + 1
                stdscr.addstr(_content_pos_h, _content_pos_w, _content)
                
            #*Render inventory
            for k, line in enumerate(inventory):
                _content = f'{line["title"]}{line["content"]}'
                _content_pos_w = m_width - column
                _content_pos_h = (height - row) + k + 2
                if line == inventory[0]:
                    _content_pos_w = m_width - (len(_content) // 2)
                    _content_pos_h = (height - row) + k + 1
                stdscr.addstr(_content_pos_h, _content_pos_w, _content)
                
            #*Render player stats
            for k, line in enumerate(stats):
                _content = f'{line["title"]}{line["content"]}'
                _content_pos_w = 0
                _content_pos_h = (height - row) + k + 2
                if line == stats[0]:
                    _content_pos_h = (height - row) + k + 1
                    _content_pos_w = m_column - (len(_content) // 2) - 2 
                stdscr.addstr(_content_pos_h, _content_pos_w, _content)
            
            #*Render middle ascii art
            for k, line in enumerate(MENUART2):
                _content = f'{line}'
                _content_pos_w = m_width - (len(_content) // 2) - 2 
                _content_pos_h = round(m_height * 0.45) + k
                stdscr.addstr(_content_pos_h, _content_pos_w, f'{_content}')

            #*Render middle information
            if len(message.items_list) > 1:
                for k, line in enumerate(message.items_list):
                    _content = f'{line}'
                    _content_pos_w = m_width - (max(len(x) for x in message.items_list) // 2)#- floor(len(_content) / 2) 
                    _content_pos_h = (m_height - (len(message.items_list) // 2)) + k
                    if _content != '': 
                        stdscr.addstr(_content_pos_h, _content_pos_w, f'{_content}')
            

            #------------------------ LINES --------------------------#
            
            #*Left
            stdscr.vline(1, column - 2, curses.ACS_VLINE, height)
            #*Right
            stdscr.vline(1, (width - column) - 2, curses.ACS_VLINE, height)
            #*Top
            stdscr.hline(1, 0, curses.ACS_HLINE, width)
            #*Logo bottom frame -> perfectly align with pair number of columns
            stdscr.hline(len(splitedAscii) + 3, column - 1, curses.ACS_HLINE, (column * 2) - 1)
            #*Bottom
            stdscr.hline((height - row), 0, curses.ACS_HLINE, width)
            

            #*Refresh screen
            if fish_paused:
                sleep(1)
            else:
                sleep(0.5)
            stdscr.refresh()
            pressedKey = stdscr.getch()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            exit(f'[E] Something wen\'t wrong -> {e}') 


def cooldown(cd: float) -> None:
    global in_cooldown, streak
    in_cooldown = True
    streak += 1
    sleep(cd)
    in_cooldown = False

def isTargetMessage(e):
    if e['channel_id'] == CHANNEL_ID:
        if e['author']['id'] == BOT_UID:
            return True
    return False

def main():
    global session, streak, bypasses, disconnected, message, cooldown_lifetime, fish_paused, profile, captcha
    atp = 0
    while True:
        cooldown_lifetime = round(uniform(USER_COOLDOWN, (USER_COOLDOWN + MARGIN)), 3)
        
        if not fish_paused and not in_cooldown and not captcha.detected:
            try:
                session.sendQuery(QUERYS[0]['PAYLOAD'][randint(0, 1)])
            except Exception as e:
                exit(f'\n[E] Fish query couldn\'t be sent -> {e}')
        
        while True:
            response = session.recieveEvent()
            if response['t'] in ['MESSAGE_CREATE', 'MESSAGE_UPDATE']:
                event = response['d']

                #try:
                if isTargetMessage(event):
                    message = Message(event)
                    
                    #*Captcha detection
                    if message.content == 'You may now continue.':
                        log('Captcha bypassed successfully !')
                        atp = 0
                        bypasses += 1
                        captcha.reset()
                        break

                    if captcha.detected:
                        log(f'Captcha detected !', 'notice')
                        if captcha.solved:
                            captcha = Captcha()
                            if captcha.detect(event):
                                captcha.solve(session)   
                        else:
                            atp += 1
                            if atp <= 3:
                                session.sendQuery('%v regen')
                                captcha.reset()
                                pass
                            else:
                                log(f'Waiting for manual captcha input !', 'notice')
                    else:
                        captcha = Captcha()
                        if captcha.detect(event):
                            captcha.solve(session)   
                    
                    
                    #*Normal messages
                    if message.title:
                        #Profile update
                        if message.title.find('Statistics for') > -1:
                            profile.rebuildLists(event, 'stats')
                            log(f'Stats information updated.')
                            break
                        elif message.title.find('Inventory of') > -1:
                            profile.rebuildLists(event, 'inv')
                            log('Profile information updated.')
                            break
                        
                        
                        if message.title == 'You caught:':
                            message.buildList()
                            break
                        else:
                            debug(event)
                            pass
                    else:
                        log(message.items_list[0])
                        pass

        cooldown(cooldown_lifetime)



#------------------------ MAIN --------------------------#


if __name__ == "__main__":
    if configLoader():
        
        #*Start Session
        print(f'\n[*] Starting...')
        session = discordWebgate()
        message = Message()
        profile = Profile()
        captcha = Captcha()
        
        #*Start background main routine
        bgMain = Thread(target=main, daemon=True)
        bgMain.start()
        
        #*Start background rebuff routine
        disconnected = False
        bgSync = Thread(target=autoBuff, daemon=True)
        bgSync.start()
        
        #*Draw menu
        curses.wrapper(drawMenu)
        session.disconnect()
        exit(f'\n[!] User exited.')
