#------------------------ IMPORTS --------------------------#
import json
import requests
import websocket 
from re import sub
from math import ceil
from time import sleep, time
from threading import Thread
from app.MenuManager import MainMenu
from app.Util import pauser, debugger
from app.CooldownManager import Cooldown
from app.ConfigManager import ConfigManager
from app.DiscordWrapper import OPCODES, DiscordWrapper
from app.Message import Message


#------------------------ CONSTANTS --------------------------#

VERSION = '1.2.1'
BOT_UID = '574652751745777665'
MAX_ATTEMPTS = 3
CONFIG = ConfigManager()

#------------------------ VARIABLES --------------------------#

#Class variables
debugger.setactive(CONFIG.debug)

menu = MainMenu(autorun=False)

session = DiscordWrapper(CONFIG.user_token, auto_connect=False)
session.setpointers(menu=menu, channel_id=CONFIG.channel_id, application_id=BOT_UID)

cd = Cooldown(CONFIG.user_cooldown)

pauser.setmenu(menu)

message = Message()


#Switches
disconnected = False
receiver_ready = True


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
        self.detecting = False
        self.solving = False
        self.regens = 0
        self.answer_list = []
        return None


    def detect(self, event) -> bool:
        self.detecting = True
        self.event = event
        #Costs more memory but is safer
        for target in ['captcha', 'verify']:
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
                            menu.kill()
                        else:
                            debugger.debug(f'{self.detected=} | {self.event=} | Cause: Unkown type. No image but flagged as target.', 'Captcha')
                        print('\nERR ! Report the log above in: https://github.com/thejoabo/virtualfisher-bot/issues/new')
                        menu.kill()
                
                #Image detected in embed
                self.detecting = False
                return True
            else:
                debugger.debug(f'{self.detected=} | {self.event=} | Cause: No embeds but flagged as target', 'Captcha')
                print('\nERR ! Report the log above in: https://github.com/thejoabo/virtualfisher-bot/issues/new')
                menu.kill()
        else:
            #Not detected
            self.detecting = False
            return False
        
    def solve(self) -> None:
        if self.image_url:
            self.solving = True
            self.answer_list = []
            
            #Generate captcha values using all engines
            for engine in [2, 1, 3, 5]:
                if engine in [3, 5]:
                    notify(f'Using OCR Engine {engine} | This engine may take longer to return (up to 20 seconds).', 'notice')
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
                try:
                    r = requests.post(self.ocr_url, data=payload, timeout=20)
                    response = json.loads(r.content.decode())
                except requests.exceptions.ReadTimeout:
                    notify(f'Engine {engine} took too long to respond (20), skipping.')
                    continue

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




class Profile:
    def __init__(self, event = []) -> None:
        self.queries = ['profile', 'stats']
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

    def update(self, session : DiscordWrapper = session) -> None:
        for query in self.queries:
            session.request(command=query)
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
                            if len(self.balance) > 15:
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


def make_command(cmd: str, name: str, value: str, type: int = 3) -> tuple:
    '''Builds a tuple containing the command (str) and the 'options' parameter (dict).'''
    parameters = {
        "type": type,
        "name": name,
        "value": value
    }
    return (cmd, parameters)


def notify(message : str, type: str = 'normal') -> None:
    '''Changes the value of menu.notification (alert message on the top) and calls debug function'''
    msg = sub(r'\n\r', '', str(message))
    if type == 'normal':
        menu.notify(f'[*] {msg}')
    elif type == 'notice':
        menu.notify(f'[!] {msg}')
    else:
        menu.notify(f'[E] {msg}')
    debugger.debug(message, 'Log')


def check_recipients(event: dict) -> bool:
    '''Checks if incoming message is sent by the application and targeted to the given channel'''
    if event['channel_id'] == CONFIG.channel_id:
        if event['author']['id'] == BOT_UID:
            return True
    return False


#---------------------------- MAIN ------------------------------#


def autoBuff(session: DiscordWrapper, queries: list = []) -> None:
    global disconnected, captcha, receiver_ready

    #Sell fishes
    queries.append(make_command('sell', 'amount', 'all'))
    #Profile
    queries.append(('profile', None))
    #Stats
    #queries.append(('stats', None))
    
    #Autobuff
    if CONFIG.auto_buff:
        #More fish buff
        queries.append(make_command('buy', 'item', f'fish{CONFIG.buff_length}m'))
        #More treasures buff
        queries.append(make_command('buy', 'item', f'treasure{CONFIG.buff_length}m'))
        
    #Baits
    if CONFIG.bait:
        amount = (((CONFIG.buff_length * 60) / CONFIG.user_cooldown) - 10) * 0.5
        #Purchase baits
        queries.append(make_command('buy', 'item', f'{CONFIG.bait} {ceil(amount)}'))
        
    def resupply(e = None) -> None:
        for query in queries:
            while captcha.detecting or not session.commands:
                sleep(0.5)
            while captcha.detected or captcha.solving: 
                sleep(3) 
            try:
                if receiver_ready:
                    session.request(command=query[0], options=query[1])
                sleep(3)
            except Exception as e:
                notify(f'Failed to send query -> {e}', 'e')
        return None
    
    while not disconnected:
        menu.countdown = 0
        pauser.pause(func=resupply)
        countdown = (CONFIG.buff_length * 60)
        
        #Timer
        for seconds in range(countdown):
            menu.countdown = (countdown - seconds)
            while pauser.paused: 
                sleep(1) #halts while paused
            sleep(1)




def message_dispatcher(session : DiscordWrapper) -> None:
    global captcha, receiver_ready
    
    def timeout(x : int = 5):
        '''Maximum timeout between captcha events like "verify" and "regen".''' 
        sleep(x)
    
    while True:
        s = time()
        if captcha.detected:
            while captcha.solving: 
                sleep(1)
            
            if len(captcha.answer_list) > 0:
                answer = captcha.answer_list.pop(0)
                
                cmd = make_command('verify', 'answer', answer)
                session.request(command=cmd[0], options=cmd[1])
                
                timeout()
            else:
                if captcha.regens <= MAX_ATTEMPTS: 
                    captcha.regens += 1
                    captcha.detected = False
                    
                    notify(f'Results failed. Re-generating captcha ({captcha.regens}/{MAX_ATTEMPTS}).')
                    
                    cmd = make_command('verify', 'answer', 'regen')
                    session.request(command=cmd[0], options=cmd[1])
                    
                    timeout()
                else:
                    notify(f'Maximun re-gen attempts reached. Manual captcha required !', 'notice')
                    while captcha.detected: 
                        sleep(1)
        else:
            while captcha.detecting:
                sleep(0.1)
            if not pauser.paused and not captcha.detected and receiver_ready:
                try: 
                    if message.id and message.play_id:
                        if session.request(message_id=message.id, custom_id=message.play_id):
                            pass
                        else:
                            #Something went wrong, but able to continue
                            message.id = None
                            message.play_id = None
                    else:
                        if not session.guild_id:
                            continue
                        else:
                            session.request(command='fish')
                    _cd = cd.new()
                    menu.cooldown = f'~{round(_cd, 4)}'
                    diff = (time() - s)
                    try: 
                        sleep(_cd - diff) #takes value and disconts the "poison" coming form the processing/request time.
                    except Exception as e: 
                        debugger.debug(e, 'Exception - Cooldown')
                        pass
                except Exception as e:
                    debugger.debug(e, 'Exception')
                    menu.kill()
            else: 
                sleep(0.5)




def message_receiver(session : DiscordWrapper) -> None:
    global profile, captcha, disconnected, receiver_ready
    while True:    
        try: 
            response = session.receive_event()
            receiver_ready = True
        #except websocket.WebSocketConnectionClosedException as e:
            # if menu.is_alive and menu.streak > 1:
            #     notify(f'Connection lost. Attempting to reconnect.', 'e')
            #     if session.connect(reconnect=True):
            #         break
            #     else:
            #         menu.kill()
        except Exception as e:
            receiver_ready = False
            debugger.debug(e, 'Exception - Response')
            menu.kill()
            break

        if response:
            #Set sequence for possible reconnect
            session.seq = response['s']

            if response['op'] == 0:
                #Information about profile and guilds (ready state)
                if response['t'] == 'READY':
                    selected_guild = None
                    event = response['d']

                    #Guild Structure
                    for guild in event['guilds']:
                        for channel in guild['channels']:
                            if str(channel['id']) == CONFIG.channel_id:
                                try:
                                    selected_guild = str(int(guild['id']))
                                except Exception as e:
                                    debugger.debug(e, 'Exception - Guild Id')
                                    menu.kill()
                                break
                    
                    if selected_guild:
                        session.setpointers(guild_id = selected_guild)
                        menu.notify(f'Done. Guild Id: {selected_guild}')
                    else:
                        print(f'Your channel id "{CONFIG.channel_id}" is invalid.')
                        menu.kill()
                        break

                    #Get command list from the channel
                    if session.get_commands():
                        #All ok
                        continue
                    else:
                        print(f'Failed to load commands. Aborting.')
                        menu.kill()
                        break
                
                #Messages
                elif response['t'] in ['MESSAGE_CREATE', 'MESSAGE_UPDATE']:
                    event = response['d']
                    if check_recipients(event):
                        try:
                            message.make(event)
                        except Exception as e:
                            receiver_ready = False
                            debugger.debug(e, 'Exception - Message.make()')
                            menu.kill()
                        
                        #Captcha detection
                        if captcha.detected:
                            if message.content == 'You may now continue.':
                                notify('Captcha bypassed successfully !')
                                menu.bypasses += 1
                                captcha.reset()
                            #break
                        else:
                            captcha = Captcha()
                            if captcha.detect(event):
                                captcha.solve()
                                #break
                            else:
                                if message.title:
                                    #Normal messages
                                    if message.title == 'You caught:':
                                        message.build()
                                        menu.setmessage(message.items)
                                        menu.streak += 1
                                    #Profile update
                                    elif message.title.find('Statistics for') > -1:
                                        profile.rebuild_lists(event, 'stats')
                                        menu.setstats(profile.stats)
                                        menu.notify(f'Stats information updated.')
                                    #Stats update
                                    elif message.title.find('Inventory of') > -1:
                                        profile.rebuild_lists(event, 'inv')
                                        menu.setinventory(profile.inventory)
                                        menu.notify('Profile information updated.')
                                    else:
                                        #Unhandled (but titled)
                                        menu.notify(f'{message.title}.')
                                else:
                                    #Untitled
                                    if message.content:
                                        if message.content.find('You must wait') > -1:
                                            menu.notify(f'[!] If automatic, this short cooldown is intentional to ensure non-bot behavior.')
                                        else:
                                            menu.notify(f'{message.sanatize(message.content)}')
                                    else:
                                        menu.notify(f'{message.sanatize(message.d)}')
                    else:
                        #Not addressed to user
                        pass
                elif response['t'] not in ['INTERACTION_CREATE', 'INTERACTION_SUCCESS', 'MESSAGE_REACTION_ADD']:
                    #Unhandled gateway events
                    if CONFIG.debug:
                        menu.notify(f'Gateway event: {response["t"]}.')
                        #print(response) #for development reasons only
                    pass
                else:
                    #Harmless gateway events
                    pass
            else:
                #Unhandled op codes
                if CONFIG.debug:
                    for op in OPCODES:
                        if op == response['op']:
                            notify(f'RCV: {op["name"]} -> {op["description"]}', 'notice')
                            break
                else:
                    pass
        else:
            #No event
            pass
    receiver_ready = False

#------------------------ INIT --------------------------#
if __name__ == "__main__":
    #Start Session
    print(f'\n[*] Starting...')
    session.connect()
    profile = Profile()
    captcha = Captcha()
    
    #Main (Listener) - Threaded
    listener = Thread(target=message_receiver, args=(session, ), daemon=True)
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

    pauser.pause(func=sleep, args=(1.5,))
    
    #Fish on exit
    if CONFIG.fish_on_exit:
        if not captcha.detected and menu.streak > 1:
            cmd = make_command('buy', 'item', 'auto30m')
            if session.request(command=cmd[0], options=cmd[1]):
                print(f'[!] You hired a worker for the next 30 minutes. The fish he catches will automatically be added to your inventory.')
                
    session.disconnect()
    
    #End
    if CONFIG.debug:
        try: cd.evaluate()
        except Exception: pass
    
    exit(f'\n[!] User exited.')
