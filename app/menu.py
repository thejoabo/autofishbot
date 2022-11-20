#------------------------ IMPORTS --------------------------#
from __future__ import annotations

if __name__ == '__main__':
    from autofishbot import Dispatcher
from . import *
from .utils import convert_time, debugger
from .scheduler import SchStatus
import curses
from time import sleep
from math import ceil
from threading import Thread
from os import path
from re import sub
import json

#------------------------ CONSTANTS --------------------------#
MENUART = [ ' ___        _         ___  _      _     ___       _   ',
            '/   \ _  _ | |_  ___ | __|(_) ___| |_  | _ ) ___ | |_ ',
            '| - || || ||  _|/ _ \| _| | |(_-/|   \ | _ \/ _ \|  _|',
            '|_|_| \_._| \__|\___/|_|  |_|/__/|_||_||___/\___/ \__|']

C_MENUART = [' ___  ___  ___       _   ',
             '/   \| __|| _ ) ___ | |_ ',
             '| - || _| | _ \/ _ \|  _|',
             '|_|_||_|  |___/\___/ \__|']

DEFAULT_KEYBINDS = {
    'pause': 'p',
    'quit': 'Q',
    'sell_inventory': 's',
    'update_inventory': 'I',
    'update_leaderboards': 'L',
    'update_cosmetics': 'K',
    'buy_morefish': 'F',
    'buy_moretreasures': 'T',
    'claim_daily': 'D',
    'show_quests': 'Y',
    'show_current_inv': 'o',
    'show_charms': 'C',
    'show_buffs': 'B',
    'show_exotic_fishes': 'e',
}

class NotificationPriority:
    '''Specifies the display time of each notification prio.'''
    VERY_LOW = 1
    LOW: int = 3
    NORMAL: int = 5
    HIGH: int = 10
    VERY_HIGH: int = 30

@dataclass(slots=True)
class Keybinder:
    '''Keybinder class is responsible to load/create/validate keybinds information to be used in menus.'''
    file: str = './app/keybinds.json'
    #file: str = './keybinds.json'
    
    keybinds: dict = field(init=False, repr=False)
    _list: list[tuple] = field(default_factory=list)
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    @property
    def list(self) -> list[tuple]:
        '''Returns the list of keybinds in a tupled format: key, action (name).'''
        if self._list == []:
            for key, value in self.keybinds.items():
                action = sub('_', ' ', key).title()
                self._list.append((value, action))
        return self._list

    def loader(self) -> dict:
        '''Loads and validates the stored keybinds.json file. If invalid 
        loads default and if nonexistent create new.'''
        if not path.exists(self.file):
            with open(self.file, 'w') as f:
                f.write(json.dumps(DEFAULT_KEYBINDS))
            self.keybinds = DEFAULT_KEYBINDS
            return True
        else:
            try:
                with open(self.file, 'r') as f:
                    self.keybinds = json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                print(f'Menu ({self.name}) - Err: {e}')
                return False
            
            try:
                if self.keybinds.keys() == DEFAULT_KEYBINDS.keys():
                    #Key names MUST BE the same.
                    return True
                else:
                    #Invalid keybinds
                    return False
            except AttributeError as e:
                print(f'[E] Menu ({self.name}) - Err: {e}')
                return False
    
    def __post_init__(self) -> None:
        if self.loader():
            if DEFAULT_KEYBINDS != self.keybinds:
                print('[*] Custom menu keybinds loaded.')
        else:
            print('[!] Invalid keybinds file, loading default.')
            self.keybinds = DEFAULT_KEYBINDS

@dataclass(slots=True)
class BaseMenu:
    '''Core menu class, contains all basics to elaborate a new Afb menu (GUI/CLI)'''
    
    #Pointers
    config: ConfigManager = field(init=False, repr=False)
    profile: Profile = field(init=False, repr=False)
    dispatcher: object = field(init=False, repr=False)
    sch: Scheduler = field(init=False, repr=False)

    #Attributes
    items: list[str] = field(default_factory=list)
    current_notification: str = ''
    notification_queue: list[tuple] = field(default_factory=list)
    keybinds: Keybinder = field(default_factory=Keybinder)
    
    #Dimentions
    x: int = 0
    y: int = 0
    minimum: tuple = (20, 5)
    
    #Flags
    autorun: bool = False
    is_alive: bool = False
    
    #Counters
    rcv_streak: int = 0
    rcv_bypasses: int = 0
        
    #Backend
    _config_list: list[tuple] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        if self.autorun:
            self.run()
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    @property
    def app_list(self) -> list[tuple]:
        '''Constructs and returns the content (in list format) of the app status - like counters and 
        countdowns - ready to be displayed.'''
        cd = self.dispatcher.cooldown.last
        sch_message = f'{self.sch.status.name} ({len(self.sch.queue)})'
        dsp_message = 'PAUSED' if self.dispatcher.paused else 'FISHING'
        
        if self.sch.status == SchStatus.BREAK:
            sch_message = f'{self.sch.status.name} ({round(self.sch._break_remaining, 1)}s)'
            dsp_message = 'SCH PAUSE'
        elif self.sch.status == SchStatus.BUSY:
            dsp_message = 'WAITING'

        return [
            ('STREAK', self.rcv_streak),
            ('BYPASSES', self.rcv_bypasses),
            ('COOLDOWN', round(cd, 4) if cd else ''),
            ('SCHEDULER', sch_message),
            ('DISPATCHER', dsp_message)
        ]
    
    @property
    def config_list(self) -> list[tuple]:
        '''Constructs and returns the content (in list format) of the config options (related to automations)
        ready to be displayed.'''
        if self._config_list == []:
            def switcher(val: bool) -> str:
                return 'ON' if val else 'OFF'

            self._config_list = [
                ('MORE FISH', switcher(self.config.more_fish)),
                ('MORE TREASURES', switcher(self.config.more_fish)),
                ('AUTO DAILY', switcher(self.config.auto_daily)),
                ('AUTO SELL', switcher(self.config.auto_sell)),
                ('AUTO UPDATE INV', switcher(self.config.auto_update_inventory)),
                ('AUTO BUY BAITS', switcher(self.config.auto_buy_baits)),
                ('FISH ON EXIT', switcher(self.config.fish_on_exit)),
            ]
        return self._config_list
    
    @property
    def minimum_info(self) -> list[str]:
        '''Returns the content (in list format) to be displayed if current size < minimum size.'''
        return [
            f'[{self.name.upper()}]', 
            f'Mininum: {self.minimum[0]} x {self.minimum[1]} ', 
            f'Current: {self.x} x {self.y}'
        ]
    
    @property
    def notification(self) -> str:
        '''Returns the current notification ready to be displayed.'''
        quantity = len(self.notification_queue)
        message = self.current_notification if self.current_notification else 'Nothing new.'
        return f'({quantity}): {message}'
    
    #------------------------ INIT AND EXIT --------------------------#
    def run(self, config: ConfigManager, dispatcher: Dispatcher, profile: Profile, scheduler: Scheduler, 
            threads: list[Thread]) -> None:
        '''Starts a new instance of the self.run function and starts the notifications thread (server).'''
        #Setup class pointers.
        self.config = config
        self.dispatcher = dispatcher
        self.profile = profile
        self.sch = scheduler
        
        notifications_server = Thread(target=self.notifications_thread, daemon=True, name='Notifications server')
        notifications_server.start()

        try:
            curses.wrapper(self.__run__, threads)
        except curses.error as e:
            exit(f'[E] {self.name} err: {e}')
    
    def kill(self) -> None:
        '''Kills the menu activity.'''
        self.is_alive = False
        
    #------------------------ DIMENTIONS --------------------------# 
    def check_dimentions(self) -> bool:
        '''Checks screen dimentions, if current size < minimum size, returns True'''
        if self.x < self.minimum[0] or self.y < self.minimum[1]:
            #print('deus?')
            return True
        return False

    def get_max_size(self, stdscr: curses.window) -> tuple:
        '''Get current terminal size, set class variables and return tuple(x,y)'''
        self.y, self.x = stdscr.getmaxyx()
        return (self.y, self.x)
      
    #------------------------ NOTIFICATIONS --------------------------#
    def notify(self, message: str, display_time: float = NotificationPriority.NORMAL, delimiter: str = '...') -> None:
        '''Adds a new notification to the notifications queue.'''
        #Todo: refactor this function
        message = str(message)
        fixed_x = self.x - 5 #4 char -> (0):
        if len(message) >= fixed_x:
            message = f'{message[0:(fixed_x - len(delimiter) - 1)]}{delimiter}'
        
        #If high prio, put the notification at the beginning
        if display_time in [NotificationPriority.HIGH, NotificationPriority.VERY_HIGH]:
            self.notification_queue = [(message, display_time)] + self.notification_queue
        else:
            self.notification_queue.append((message, display_time))
        
    def _err_notification(self, e: str) -> None:
        '''Schedules an notification containing an error message, it automatically checks 
        if the notification isn't already in the queue.'''
        for notification, _ in self.notification_queue:
            if message == notification:
                return None
        
        err_message = f'[E] {self.name} error: {e}'
        debugger.log(e, f'{self.name} - run')
        self.notify(err_message, NotificationPriority.NORMAL)

        return None
    
    def notifications_thread(self) -> None:
        '''Controls the notification queue and manage its display time.'''
        #Todo: use queue library instead
        while True:
            if self.notification_queue != []:
                message, display_time = self.notification_queue.pop(0)
                self.current_notification = message

                sleep(display_time)
                self.current_notification = ''

            else:
                sleep(self.config.refresh_rate)
    
    #------------------------ FEATURES --------------------------#
    def check_keybinds(self, pressed_key: int, stdscr: curses.window) -> None:
        '''Checks pressed key and trigger its action (if it matches).'''
        if not pressed_key:
            return None
        
        for key, action in self.keybinds.list:
            if ord(key) == pressed_key:
                match action:
                    case 'Pause':
                        self.dispatcher.pause
                    case 'Quit':
                        self.kill()
                    case 'Sell Inventory':
                        self.sch.schedule(self.sch.commands.sell)
                    case 'Update Inventory':
                        if self.name == 'CompactMenu':
                            self.popup(
                                stdscr=stdscr,
                                command=self.sch.commands.profile,
                                title='Inventory', 
                                items=self.profile, 
                            )
                        else:
                            self.sch.schedule(self.sch.commands.profile)
                    case 'Update Leaderboards':
                        if self.name == 'CompactMenu':
                            self.popup(
                                stdscr=stdscr,
                                command=self.sch.commands.pos,
                                title='Leaderboards', 
                                items=self.profile.leaderboard, 
                            )
                        else:
                            self.sch.schedule(self.sch.commands.pos)
                    case 'Update Cosmetics':
                        raise Exception('Feature not implemented.')
                    case 'Buy Morefish':
                        self.sch.schedule(self.sch.commands.morefish)
                    case 'Buy Moretreasures':
                        self.sch.schedule(self.sch.commands.moretreausre)
                    case 'Claim Daily':
                        self.sch.schedule(self.sch.commands.daily)
                    case 'Show Quests':
                        self.popup(
                            stdscr=stdscr,
                            command=self.sch.commands.quests,
                            title='Quests', 
                            items=self.profile.quests, 
                        )
                    case 'Show Current Inv':
                        self.popup(
                            stdscr=stdscr,
                            command=self.sch.commands.profile,
                            title='Current Inventory',
                            items=self.profile.inventory,
                        )
                    case 'Show Charms':
                        self.popup(
                            stdscr=stdscr, 
                            command=self.sch.commands.charms,
                            title='Charms', 
                            items=self.profile.charms, 
                        )
                    case 'Show Buffs':
                        self.popup(
                            stdscr=stdscr,
                            command=self.sch.commands.buffs,
                            title='Buffs', 
                            items=self.profile.buffs, 
                        )
                    case 'Show Exotic Fishes':
                        self.popup(
                            stdscr=stdscr,
                            command=self.sch.commands.profile,
                            title='Exotic Fish', 
                            items=self.profile.exotic_fish, 
                        )
                    case _:
                        return None
                    
    def popup(self, stdscr: curses.window, command: Commands, title: str = 'Popup', items: object = []) -> None:    
        '''Show a popup window in the middle of the screen. Used to display quick info.
        The `element: object` argument expects to be a Profile variable containing:
        - `list -> list[tuple]` property
        - `last_update: float` attribute'''

        pressed_key = None
        processed_list = []
        last_update = items.last_update
        choice = '[press \'q\' to return...]'
        update = 'press \'u\' to update...'

        if items.list == []:
            #Auto schedule item if list is empty
            self.sch.schedule(command)

        def construct_lists(_tmp = []) -> list:
            '''Constructs the tupled object list to a string format and returns a tuple
            with (list, objectlast_update)'''
            match title:
                case 'Quests':
                    _tmp = [f'{a} ({b})' for _, a, b in items.list]
                case 'Charms':
                    _tmp = [f'{b} {a}' for a, b in items.list]
                case 'Buffs' | 'Inventory':
                    _tmp = [f'{a}: {b}' for a, b in items.list]
                case 'Current Inventory' | 'Exotic Fish':    
                    _tmp = [f'{a} x {b}' for a, b in items.list]
                case 'Leaderboards':
                    _tmp = [f'{a}: #{b}' for a, b in items.list]
                case _:
                    _tmp = []

            return (_tmp, items.last_update)

        while True:
            try:
                #Check keybinds
                if pressed_key == ord('q'):
                    break
                elif pressed_key == ord('u'):
                    self.sch.schedule(command)
                    
                stdscr.erase()
                
                #Update lists
                if processed_list == [] or (items.last_update != last_update):
                    processed_list, last_update = construct_lists()
                    update_msg = f'[Last update: {convert_time(last_update)} | {update}] '
                
                #Calculations
                #Todo: rework these (prob something realted to odd list length)
                self.get_max_size(stdscr)
                box_size_x = (max(len(line) for line in processed_list)) + 8 if processed_list != [] else 32
                box_size_y = len(processed_list) + 4 if processed_list != [] else 12
                x = (self.x // 2) - (box_size_x // 2)
                y = (self.y // 2) - (box_size_y // 2)
                middle_x = self.x // 2
                middle_y = self.y // 2
                rel_x = (self.x - x) #+ (1 if self.x % 2 == 0 else 2)
                rel_y = (self.y - y) + (0 if self.y % 2 == 0 else -1)

                if self.check_dimentions():
                    for k, data in enumerate(self.minimum_info):
                        stdscr.addstr(middle_y + k - 3, middle_x - ceil(len(data) / 2), data)
                else:
                    #Box
                    stdscr.hline(y - 1, x - 1, curses.ACS_HLINE, box_size_x + 2)
                    stdscr.hline(rel_y, x, curses.ACS_HLINE, box_size_x + 1)
                    stdscr.vline(y, x - 1, curses.ACS_VLINE, box_size_y)
                    stdscr.vline(y, rel_x + 1, curses.ACS_VLINE, box_size_y)
                    
                    #Notification bar
                    stdscr.hline(1, 0, curses.ACS_HLINE, self.x) #Top
                    stdscr.addstr(0, 0, self.notification)
                    
                    #Object list
                    stdscr.addstr(y - 1, middle_x - (len(title) // 2), title)
                    for k, data in enumerate(processed_list):
                        popup_x = middle_x - (len(data) // 2)
                        stdscr.addstr(y + k + 1, popup_x, data)

                    #Exit message
                    stdscr.addstr(rel_y, middle_x - (len(choice) // 2) + 1, choice)

                    #Last update message
                    stdscr.addstr(self.y - 3, middle_x - (len(update_msg) // 2) + 1, update_msg)
                
                stdscr.refresh()
                sleep(self.config.refresh_rate)
                pressed_key = stdscr.getch()
            
            except KeyboardInterrupt:
                break
            except curses.error as e:
                self._err_notification(e)
                sleep(self.config.refresh_rate)
            
        stdscr.erase()
        return None

    #------------------------ MAIN --------------------------#
    def __run__(self, stdscr: curses.window, threads: list[Thread]) -> None:
        '''[Boilerplate function]: Starts the menu main loop, display info on screen 
        and manages user input.

        Quick notes:
        - stdscr.addstr(y, x, string)
        - stdscr.vline/hline(starting_y, starting_x, line_character, line_length)
        (for line_character use curses constants)
        Full documentation: https://docs.python.org/3/library/curses.html
        '''
        
        curses.curs_set(0)
        curses.noecho()
        stdscr.nodelay(True)
        
        self.is_alive = True

        while self.is_alive:
            #Checks for essential threads activitys
            for thread in threads:
                if not thread.is_alive():
                    self.kill()
                    curses.endwin()
                    exit(f'[E] "{thread.name}" thread exited.')
            try:
                stdscr.refresh()
                stdscr.erase()
                
                #Calculations
                self.get_max_size(stdscr)
                middle_x, middle_y = (self.x // 2),  (self.y // 2)
                #...

                if self.check_dimentions():
                    for k, data in enumerate(self.minimum_info):
                        stdscr.addstr(middle_y + k - 3, middle_x - ceil(len(data) / 2), data)
                else:
                    #------------------------ LINES --------------------------#
                    #...
                    
                    #------------------------ ASCII --------------------------#
                    #...
                    
                    #------------------------ TEXTS --------------------------#
                    #...
                    pass
                
                sleep(self.config.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch(), stdscr)

            except KeyboardInterrupt:
                self.kill()
            except Exception as e:
                self._err_notification(e)
                sleep(self.config.refresh_rate)
        

    
@dataclass(slots=True)
class MainMenu(BaseMenu):
    minimum: tuple = (100, 30)
    
    def __run__(self, stdscr: curses.window, threads: list[Thread]) -> None:
        '''Starts the menu main loop, display info on screen and manages user input.
        In order to save memory and processing time optimization were made, so readibility
        is compromised, for future updates and forks note that:
        - stdscr.addstr(y, x, string)
        - stdscr.vline/hline(starting_y, starting_x, line_character, line_length)
        (for line_character use curses constants)'''
        
        ascii_middle: int = (max(len(x) for x in MENUART) // 2)
        
        #Titles
        lea_title = 'LEADERBOARDS'
        key_title = 'KEYBINDS'
        cfg_title = 'CONFIG STATUS'
        inv_title = 'INVENTORY'
        app_title = 'APP INFO'
        
        curses.curs_set(0)
        curses.noecho()
        stdscr.nodelay(True)
        
        self.is_alive = True

        while self.is_alive:
            #Checks for essential threads activitys
            for thread in threads:
                if not thread.is_alive():
                    self.kill()
                    curses.endwin()
                    exit(f'[E] "{thread.name}" thread exited.')
            try:
                stdscr.refresh()
                stdscr.erase()
                
                #Calculations
                self.get_max_size(stdscr)
                column = self.x - ((75 * self.x) // 100)
                row = (35 * self.y) // 100
                middle_x, middle_y, m_column = (self.x // 2),  (self.y // 2), (column // 2)
                middle_message_panel_y = (self.y - (row) + 4) // 2
                middle_message_panel_x = (self.x - (2 * column)) - 2
                bottom_panels_y = (self.y - row) + 2
                left_bottom_panels_x = (self.x - column) + 2
                x_ascii = (middle_x + 1) - ascii_middle

                if self.check_dimentions():
                    for k, data in enumerate(self.minimum_info):
                        stdscr.addstr(middle_y + k - 3, middle_x - ceil(len(data) / 2), data)
                else:
                    #------------------------ LINES --------------------------#
                    #Notification bar
                    stdscr.hline(1, 0, curses.ACS_HLINE, self.x) #Top
                    
                    #Columns
                    stdscr.vline(2, column, curses.ACS_VLINE, self.y) #Left
                    stdscr.vline(2, (self.x - column), curses.ACS_VLINE, self.y) #Right
                    
                    #Rows
                    stdscr.hline((self.y - row), 0, curses.ACS_HLINE, self.x) #Bottom 
                    stdscr.hline(len(MENUART), column, curses.ACS_HLINE, middle_message_panel_x + 3) #Logo bottom 
                    
                    #------------------------ ASCII --------------------------#
                    #Render Logo
                    for k, line in enumerate(MENUART):
                        stdscr.addstr(k, x_ascii, f'{line}')
                        if line == MENUART[-1]:
                            title = 'You caught:'
                            stdscr.addstr(k + 1, middle_x - (len(title) // 2), title)
                
                    #------------------------ TEXTS --------------------------#
                    #Render notification
                    stdscr.addstr(0, 0, self.notification)
                    
                    #Leaderboards Panel - Profile
                    stdscr.addstr(2, m_column - (len(lea_title) // 2) + 1, lea_title)
                    for k, data in enumerate(self.profile.leaderboard.list):
                        stdscr.addstr(k + 5, 1, f'{data[0]}:')
                        stdscr.addstr(k + 5, m_column - (len(data[1]) // 2) - 1, f'#{data[1]}')
                    
                    #Keybinds Panel - Keybinder
                    stdscr.addstr(2, ((self.x - column) + m_column) - (len(key_title) // 2) + 1, key_title)
                    for k, data in enumerate(self.keybinds.list):
                        stdscr.addstr(k + 5, left_bottom_panels_x, f'{data[0]} - {data[1]}')
                    
                    #Config status panel - Self
                    stdscr.addstr(bottom_panels_y - 2, (left_bottom_panels_x + m_column) - (len(cfg_title) // 2) - 1, cfg_title)
                    for k, data in enumerate(self.config_list):
                        stdscr.addstr(bottom_panels_y + k, left_bottom_panels_x, f'{data[0]}: {data[1]}')
                    
                    #Inventory Panel - Profile
                    stdscr.addstr(bottom_panels_y - 2, middle_x - (len(inv_title) // 2) + 1, inv_title)
                    for k, data in enumerate(self.profile.list):
                        stdscr.addstr(bottom_panels_y + k, column + 2, f'{data[0]}: {data[1]}')
                    
                    #App info panel - Self
                    stdscr.addstr(bottom_panels_y - 2, m_column - (len(app_title) // 2), app_title)
                    for k, data in enumerate(self.app_list):
                        stdscr.addstr(bottom_panels_y + k, 1, f'{data[0]}: {data[1]}')

                    #Messages panel - Self (from receiver)
                    if len(self.items) >= middle_message_panel_y:
                        _y = middle_message_panel_y // 2
                    else:
                        _y = (middle_message_panel_y - (len(self.items) // 2)) 
                    for k, data in enumerate(self.items):
                        line = f'{data}'
                        
                        #Trim long messages
                        if len(line) >= middle_message_panel_x:
                            #Limits message size to fit on panel 
                            line = f'{line[0:(middle_message_panel_x - 3)]} +'

                        #Limits item list size to fit on pannel
                        if k >= middle_message_panel_y:
                            line = f'+ {len(self.items) - middle_message_panel_y} ...'
                            stdscr.addstr(_y + k + 1, middle_x - (len(line) // 2), line)
                            break
                        
                        stdscr.addstr(_y + k, middle_x - ceil(len(line) / 2) + 1, line)

                sleep(self.config.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch(), stdscr)

            except KeyboardInterrupt:
                self.kill()
            except Exception as e:
                self._err_notification(e)
                sleep(self.config.refresh_rate)
                  

@dataclass(slots=True)
class CompactMenu(BaseMenu):
    minimum: tuple = (70, 22)
    
    def __run__(self, stdscr: curses.window, threads: list[Thread]) -> None:
        '''Starts the menu main loop, display info on screen and manages user input.
        In order to save memory and processing time optimization were made, so readibility
        is compromised, for future updates and forks note that:
        - stdscr.addstr(y, x, string)
        - stdscr.vline/hline(starting_y, starting_x, line_character, line_length)
        (for line_character use curses constants)'''
        
        art_len_x: int = max(len(x) for x in C_MENUART)
        art_len_y: int = len(C_MENUART)
        al_len: int = len(self.app_list)
        
        #Titles
        cfg_title = 'CONFIG STATUS'
        app_title = 'APP INFO'
        
        curses.curs_set(0)
        curses.noecho()
        stdscr.nodelay(True)
        
        self.is_alive = True

        while self.is_alive:
            #Checks for essential threads activitys
            for thread in threads:
                if not thread.is_alive():
                    self.kill()
                    curses.endwin()
                    exit(f'[E] "{thread.name}" thread exited.')
            try:
                stdscr.refresh()
                stdscr.erase()
                
                #Calculations
                self.get_max_size(stdscr)
                column = art_len_x + 1
                row = art_len_y + 2
                sec_row = row + al_len + 2
                middle_x, middle_y, m_column = (self.x // 2),  (self.y // 2), (column // 2)
                items_x = (self.x - column) - 6
                items_y = self.y - 2
                middle_message_panel_x = (items_x // 2)

                if self.check_dimentions():
                    for k, data in enumerate(self.minimum_info):
                        stdscr.addstr(middle_y + k - 3, middle_x - ceil(len(data) / 2), data)
                else:
                    #------------------------ LINES --------------------------#
                    #Notification bar
                    stdscr.hline(1, 0, curses.ACS_HLINE, self.x)

                    stdscr.vline(2, column, curses.ACS_VLINE, self.y) #division
                    stdscr.hline(row, 0, curses.ACS_HLINE, column) #logo frame
                    stdscr.hline(sec_row, 0, curses.ACS_HLINE, column) #logo frame
                    
                    #------------------------ ASCII --------------------------#
                    #Render Logo
                    for k, data in enumerate(C_MENUART):
                        stdscr.addstr(k + 2, 0, data)
                
                    #------------------------ TEXTS --------------------------#
                    #Render notification
                    stdscr.addstr(0, 0, self.notification)
                    
                    #App info panel - Self
                    stdscr.addstr(row, m_column - (len(app_title) // 2), app_title)
                    for k, data in enumerate(self.app_list):
                        stdscr.addstr(row + k + 1, 1, f'{data[0]}: {data[1]}')
                    
                    #Config status panel - Self
                    stdscr.addstr(sec_row, m_column - (len(cfg_title) // 2), cfg_title)
                    for k, data in enumerate(self.config_list):
                        stdscr.addstr(sec_row + k + 1, 1, f'{data[0]}: {data[1]}')

                    #Messages panel - Self (from receiver)
                    if len(self.items) >= items_y:
                        _y = 2
                    else:
                        _y = (items_y // 2) - (len(self.items) // 2) #- (len(self.items))) 
                    for k, data in enumerate(self.items):
                        line = f'{data}'
                        
                        #Trim long messages
                        if len(line) >= items_x:
                            #Limits message size to fit on panel 
                            line = f'{line[0:(items_x - 1)]} +'

                        #Limits item list size to fit on pannel
                        if k >= (items_y - 1):
                            line = f'+ {len(self.items) - items_y} ...'
                            stdscr.addstr(_y + k, self.x - (middle_message_panel_x + len(line)), line)
                            break
                        
                        stdscr.addstr(_y + k, self.x - (middle_message_panel_x + ceil(len(line) / 2)) - 2, line)

                sleep(self.config.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch(), stdscr)

            except KeyboardInterrupt:
                self.kill()
            except Exception as e:
                self._err_notification(e)
                sleep(self.config.refresh_rate)

# --------- INIT ---------#
if __name__ == "__main__":
    pass