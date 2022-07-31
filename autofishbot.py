#------------------------ IMPORTS --------------------------#
import json
import requests
import websocket 
from re import sub
from math import ceil
from random import randint
from time import sleep, time
from threading import Thread
from app.MenuManager import MainMenu
from app.Util import pauser, debugger
from app.CooldownManager import Cooldown
from app.ConfigManager import ConfigManager
from app.DiscordWebgate import DiscordWebgate


#------------------------ CONSTANTS --------------------------#

VERSION = '1.2.0'
BOT_UID = '574652751745777665'
MAX_ATTEMPTS = 3
CONFIG = ConfigManager()
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
 

#------------------------ VARIABLES --------------------------#

#Class variables
session = DiscordWebgate(CONFIG.user_token, CONFIG.channel_id, auto_connect=False)
cd = Cooldown(CONFIG.user_cooldown)
debugger.setactive(CONFIG.debug)
menu = MainMenu(autorun=False)
pauser.setmenu(menu)


#Switches
disconnected = False


#-------------------------- CLASSES --------------------------#
class Captcha:
    def __init__(self) -> None:
        self.ocr_url = 'https://api.ocr.space/parse/image'
        self.reset()
    
    def reset(self) -> None:
        self.event = None
        self.embeds = None
        self.content = None
        
        #Changeable
        self.solved = False
        self.detected = False
        self.solving = False
        self.regens = 0
        self.answer_list = []
        return None


    def detect(self, event) -> bool:
        self.event = event
        #Costs more memory but is safer
        for target in ['captcha', '%verify']:
            if str(event).find(target) > -1:
                #Captcha detected
                self.detected = True
                break
            else: 
                pass
        
        if self.detected:
            if len(self.event['embeds']) > 0:
                self.embeds = self.event['embeds']
                for item in self.embeds:
                    try: #Assign Image 
                        self.image_url = item['image']['url']
                        break
                    except KeyError:
                        if item['description'].find('solve the captcha posted above') > -1:
                            debugger.debug(f'{self.detected=} | {self.event=} | Cause: query sent after captcha detection.', 'Captcha')
                        else:
                            debugger.debug(f'{self.detected=} | {self.event=} | Cause: Unkown type. No image but flagged as target.', 'Captcha')
                        print('\nERR ! Report the log above in: https://github.com/thejoabo/virtualfisher-bot/issues/new')
                        menu.kill()
                
                #Image detected in embed
                return True
            else:
                debugger.debug(f'{self.detected=} | {self.event=} | Cause: No embeds but flagged as target', 'Captcha')
                print('\nERR ! Report the log above in: https://github.com/thejoabo/virtualfisher-bot/issues/new')
                menu.kill()
        else:
            #Not detected
            return False
        
    def solve(self) -> None:
        if self.image_url:
            self.solving = True
            self.answer_list = []
            
            #Generate captcha values using all engines
            for engine in [2, 1, 3]:
                notify(f'Using OCR Engine {engine}')
                if engine in [3, 5]:
                    notify(f'Using OCR Engine {engine} | This engine may take longer to return.', 'notice')
                else:
                    notify(f'Using OCR Engine {engine}')
                
                payload = {
                    'apikey': CONFIG.ocr_api_key,
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

                #Filter results which are reasonable
                if response['OCRExitCode'] == 1:
                    raw = response['ParsedResults'][0]['ParsedText']
                    answer = sub('[\n\r ]', '', sub(r'/[\@a-zA-Z0-9]/g', '', raw))
                    if len(answer) == 6:
                        if answer not in self.answer_list:
                            #New valid result
                            notify(f'The code \'{answer}\' was added to possible results.')
                            self.answer_list.append(answer)
                        else: 
                            #Duplicate result
                            notify(f'Duplicate result (\'{answer}\') ignored.', 'notice')
                    else:
                        #Invalid results
                        notify(f'OCR Engine {engine} failed to provide reasonable certainty | Result: "{answer}".', 'notice')
                else:
                    #API error
                    notify(f'OCR Engine {engine} returned exit code {response["OCRExitCode"]}.', 'err')
                sleep(0.5) 
            self.solving = False
            
            return None
        else:
            debugger.debug(f'{self.detected=} | {self.event=} | Cause: Assigned to solve but no image found.', 'Captcha')
            print('\nERR ! Report the log above in: https://github.com/thejoabo/virtualfisher-bot/issues/new')
            menu.kill()

class Message:
    def __init__(self, event = []) -> None:
        self.items_list = []
        self.title = None
         
        if event != []:
            try: self.content = event['content']
            except KeyError as e: 
                debugger.debug(e, 'Exception')
                self.content = None
                       
            for embed in event['embeds']:
                try:
                    #Main embed
                    if embed['title']:
                        self.title = embed['title']
                        try: self.description = embed['description']
                        except KeyError as e: 
                            self.description = None
                except KeyError:
                    self.items_list.append(self.sanatize(embed['description']))
                except Exception as e:
                    debugger.debug(e, 'Exception')
        else:
            pass

    def sanatize(self, content : any) -> str:
        content = sub(r':.+?: ', '', str(content))
        content = sub(r'[\*_`\n<>]', '', content)
        return content
    
    def buildList(self, custom_list: list = []) -> None:
        _tmp = self.description.split('\n')
        for line in _tmp:
            final = ''
            if line.find('LEVEL UP!') > -1:
                #Level up information
                level = sub('[^\d+]', '', sub(r'<.+?> ', '', line))
                final = f'<< LEVEL UP: {int(level) - 1} -> {level} >>'
            elif line.find('<:') > -1:
                #Emotes 
                final = sub(r'  ', ' ', sub(r'<.+?>', '', line))
            elif line.find(':') > -1:
                #Duplicator Emote (and commom emotes)
                final = sub(r'  ', ' ', sub(r':.+?: ', '', line))
            elif line.find('#') > -1: 
                #Global boost information
                pass
            elif line == '' or line == None or line == '\n':
                pass
            else:
                final = line
            self.items_list.append(sub('[\*+]', '', final))
        if custom_list != []:
            self.items_list = custom_list + self.items_list
        return None

class Profile:
    def __init__(self, event = []) -> None:
        self.queries = ['%inv', '%stats'] #top...
        self.balance = None
        self.level = None
        self.rod = None
        self.biome = None
        self.golden = {'total': None, 'current': None}
        self.emerald = {'total': None, 'current': None}
        self.lava = {'total': None, 'current': None}
        self.diamond = {'total': None, 'current': None}
        self.crates = None
        self.quests = None
        self.trips = None
        self.daily = None

    def update(self, session : DiscordWebgate = session) -> None:
        for query in self.queries:
            session.send_query(query)
            sleep(2)
        return None

    def rebuild_lists(self, event, target) -> None:
        if target == 'inv':
            self.build_inventory(event)
        elif target == 'stats':
            self.build_stats(event)
        return None

    def build_stats(self, event) -> None:
        if event != []:
            for embed in event['embeds']:
                try: embed['title']
                except KeyError: continue
                if embed['title'].find('Statistics for') > -1:
                    lines = embed['description'].split('\n')
                    for line in lines:
                        if line == '': continue
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
                        elif line.find('diamond') > -1:
                            self.diamond['total'] = sub('[^\d+$]', '', line)
        self.stats = [
            {'title': 'TOTAL STATS   ', 'content': ''},
            {'title': 'DIAMOND:      ', 'content': f'{self.diamond["total"]}'},
            {'title': 'LAVA:         ', 'content': f'{self.lava["total"]}'},
            {'title': 'GOLDEN:       ', 'content': f'{self.golden["total"]}'},
            {'title': 'EMERALD:      ', 'content': f'{self.emerald["total"]}'},
            {'title': 'CRATES:       ', 'content': f'{self.crates}'},
            {'title': 'QUESTS:       ', 'content': f'{self.quests}'},
            {'title': 'TOTAL TRIPS:  ', 'content': f'{self.trips}'},
            {'title': 'DAILY STREAK: ', 'content': f'{self.daily}'},
        ]
        
    def build_inventory(self, event) -> None:
        if event != []:
            for embed in event['embeds']:
                try: embed['title']
                except KeyError: continue
                if embed['title'].find('Inventory of') > -1:
                    lines = embed['description'].split('\n')
                    for line in lines:
                        if line == '': pass
                        elif line.find('Balance:') > -1:
                            #Balance
                            self.balance = sub('[^\d+]', '', line)
                            if len(self.balance) > 10:
                                self.balance = '$ {:.3e}'.format(int(self.balance))
                            else:
                                self.balance = '$ {:,.2f}'.format(int(self.balance))
                        elif line.find('XP to next level.') > -1:
                            #Level
                            level = sub(' ', '', sub('[.*a-z]', '',  sub(', ', '|', line)))
                            if level.startswith('P'):
                                level = sub('L', '|L', level) 
                            else: level = sub('L', '', level)
                            self.level = sub('\|', ' | ', level)
                        elif line.find('Rod') > -1:
                            #Rod
                            self.rod = sub(rf'{line[0]}.+?> ', '', line)
                            self.rod = sub('[*.]', '', self.rod)
                        elif line.find('Current biome:') > -1:
                            #Biome
                            self.biome = sub(rf'{line[0]}.+?> ', '', line)
                            self.biome = sub('[*.]', '', self.biome)
                            #biome = line
                        elif line.find('Gold Fish') > -1:
                            #Golden Fish
                            golden = sub(r'<.+?> ', '', line)
                            self.golden['current'] = sub('[^\d+$]', '', golden)
                        elif line.find('Emerald Fish') > -1:
                            #Emerald Fish
                            emerald = sub(r'<.+?> ', '', line)
                            self.emerald['current'] = sub('[^\d+$]', '', emerald)
                        elif line.find('Lava Fish') > -1:
                            #Lava Fish
                            lava = sub(r'<.+?> ', '', line)
                            self.lava['current'] = sub('[^\d+$]', '', lava)
                        elif line.find('Diamond Fish') > -1:
                            #Diamond Fish
                            diamond = sub(r'<.+?> ', '', line)
                            self.diamond['current'] = sub('[^\d+$]', '', diamond)
        self.inventory = [
            {'title': 'INVENTORY     ', 'content': ''},
            {'title': 'BALANCE:      ', 'content': f'{self.balance}'},
            {'title': 'LEVEL:        ', 'content': f'{self.level}'},
            {'title': 'ROD:          ', 'content': f'{self.rod}'},
            {'title': 'BIOME:        ', 'content': f'{self.biome}'},
            {'title': 'DIAMOND FISH: ', 'content': f'{self.diamond["current"]}'},
            {'title': 'LAVA FISH:    ', 'content': f'{self.lava["current"]}'},
            {'title': 'GOLD FISH:    ', 'content': f'{self.golden["current"]}'},
            {'title': 'EMERALD FISH: ', 'content': f'{self.emerald["current"]}'}
        ]


#------------------------ AUX FUNCTIONS ------------------------#

def autoBuff(session : DiscordWebgate, _queries = ['%s all', '%inv', '%stats']):
    global disconnected, captcha
    
    #More fish and more treasure
    if CONFIG.auto_buff:
        _queries = _queries + [f'%buy fish{CONFIG.buff_length}m', f'%buy treasure{CONFIG.buff_length}m']

    #Bait resuply
    if CONFIG.bait:
        _amount = (( (CONFIG.buff_length  * 60) / CONFIG.user_cooldown) - 10) * 0.75 
        _queries.append(f'%buy {CONFIG.bait} {ceil(_amount)}')

    def resuply(e = None) -> None:
        for _query in _queries:
            try:
                while captcha.detected: 
                    sleep(1) #waits until solved
                session.send_query(_query)
                sleep(2)
            except Exception as e:
                notify(f'Failed to send query -> {e}', 'e')
        return True if not e else False
    
    while not disconnected:
        menu.countdown = 0
        pauser.pause(func=resuply)
        countdown = (CONFIG.buff_length * 60)
        for seconds in range(countdown):
            menu.countdown = (countdown - seconds)
            while pauser.paused: 
                sleep(1) #halts while paused
            sleep(1)


def notify(message : any, type: str = 'normal') -> None:
    '''Change the value of menu.notification (alert message on the top) and calls debug function'''
    msg = sub(r'\n\r', '', str(message))
    if type == 'normal':
        menu.notify(f'[*] {msg}')
    elif type == 'notice':
        menu.notify(f'[!] {msg}')
    else:
        menu.notify(f'[E] {msg}')
    debugger.debug(message, 'Log')


def isTargetMessage(e: dict) -> bool:
    if e['channel_id'] == CONFIG.channel_id:
        if e['author']['id'] == BOT_UID:
            return True
    return False


#---------------------------- MAIN ------------------------------#

def message_dispatcher(session : DiscordWebgate) -> None:
    global captcha
    
    def timeout(x : int = 5):
        '''Maximum timeout between captcha events like "verify" and "regen".''' 
        sleep(x)
    
    while True:
        s = time()
        if captcha.detected:
            #print(f'detectad: {captcha.answer_list=} | {len(captcha.answer_list)=} | {captcha.regens=} | {captcha.solving=} ')
            while captcha.solving: sleep(1)
            if len(captcha.answer_list) > 0:
                #print('in')
                answer = captcha.answer_list.pop(0)
                session.send_query(f'%verify {answer}')
                
                timeout()
            else:
                print('do regen')
                if captcha.regens <= MAX_ATTEMPTS: #and not captcha.solving:
                    #print(f'm {captcha.regens}')
                    captcha.regens += 1
                    notify(f'Results failed. Re-generating captcha. {captcha.regens}/{MAX_ATTEMPTS}')
                    captcha.detected = False
                    session.send_query(f'%verify regen')
                    
                    timeout()
                else:
                    #print('do halt')
                    notify(f'Maximun re-gen attempts reached. Manual captcha required !', 'notice')
                    while captcha.detected: sleep(1) #halts until solved
        else:
            if not pauser.paused and not captcha.detected:
                try: 
                    session.send_query(QUERYS[0]['PAYLOAD'][randint(0, 1)])
                    #this does the cooldown time and updates the menu -> the round() does not change the sleep time.
                    _cd = cd.new()               
                    menu.cooldown = f'~{round(_cd, 6)}'
                    diff = (time() - s)
                    try: sleep(_cd - diff) #takes value and disconts the "poison" coming form the processing/request time.
                    except Exception as e: pass
                    if CONFIG.debug:
                        print(diff)
                except Exception as e:
                    debugger.debug(e, 'Exception')
                    menu.kill()
            else: sleep(0.5)


def message_listener(session : DiscordWebgate) -> None:
    global message, profile, captcha, disconnected
    while True:
        while True:
            try: 
                response = session.recieve_event()
            except websocket.WebSocketConnectionClosedException as e:
                if menu.is_alive:
                    notify(f'Connection lost -> {e} Probable cause: incorrect token.', 'e')
            except Exception as e:
                debugger.debug(e, 'Exception')
                exit(f'[E] Something went wrong -> {e}')

            try: #Message handling
                if response and response['t'] in ['MESSAGE_CREATE', 'MESSAGE_UPDATE']:
                    event = response['d']
                    if isTargetMessage(event):
                        message = Message(event)

                        #Captcha detection
                        if captcha.detected:
                            if message.content == 'You may now continue.':
                                notify('Captcha bypassed successfully !')
                                menu.bypasses += 1
                                captcha.reset()
                            break
                        else:
                            captcha = Captcha()
                            if captcha.detect(event):
                                captcha.solve()
                                break
                            else:
                                if message.title:
                                    #Normal messages
                                    if message.title == 'You caught:':
                                        #menu.d = f'S:{cd.calc_sigma(cd.values)}'
                                        message.buildList()
                                        menu.setmessage(message.items_list)
                                        menu.streak += 1
                                        break
                                    #Profile update
                                    elif message.title.find('Statistics for') > -1:
                                        profile.rebuild_lists(event, 'stats')
                                        menu.setstats(profile.stats)
                                        notify(f'Stats information updated.')
                                        break
                                    #Stats update
                                    elif message.title.find('Inventory of') > -1:
                                        profile.rebuild_lists(event, 'inv')
                                        menu.setinventory(profile.inventory)
                                        notify('Profile information updated.')
                                        break
                                    else:
                                        #Unhandled
                                        notify(message.title)
                                else:
                                    #Untitled
                                    notify(message.items_list[0])
                                    if message.items_list[0].find('You must wait') > -1:
                                        notify(f'If automatic, this short cooldown is intentional to ensure non-bot behavior.', 'notice')
                                    break
                    else: 
                        pass
                else: 
                    pass
            except Exception as e:
                debugger.debug(e, 'Exception')
                menu.kill()


#------------------------ INIT --------------------------#
if __name__ == "__main__":
    #Start Session
    print(f'\n[*] Starting...')
    session.connect()
    message = Message()
    profile = Profile()
    captcha = Captcha()
    
    #Main (Listener) - Threaded
    listener = Thread(target=message_listener, args=(session, ), daemon=True)
    #Main (Sender) - Threaded
    dispatcher = Thread(target=message_dispatcher, args=(session, ), daemon=True)
    #Secondary (Autobuff - sender) - Threaded
    autobuffer = Thread(target=autoBuff, args=(session, ), daemon=True)
    
    #Async Flow
    listener.start()
    autobuffer.start()
    dispatcher.start()
    
    #Menu
    menu.configure(CONFIG.bait, CONFIG.auto_buff, CONFIG.buff_length, profile)
    menu.__call_run__(mode=CONFIG.compact_mode)
    #menu.__call_run__(mode='custom', func=menu.custom) #custom call example
    
    session.disconnect()
    
    #End
    if CONFIG.debug:
        try: cd.evaluate()
        except Exception: pass
    exit(f'\n[!] User exited.')
