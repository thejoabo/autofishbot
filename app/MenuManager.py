#------------------------ IMPORTS --------------------------#
try:
    from app.Util import pauser, debugger
except ImportError:
    from Util import pauser, debugger
from math import ceil, floor
from time import sleep
import curses


#------------------------ CONSTANTS --------------------------#
MENUART = [ ' ___        _         ___  _      _     ___       _   ',
            '/   \ _  _ | |_  ___ | __|(_) ___| |_  | _ ) ___ | |_ ',
            '| - || || ||  _|/ _ \| _| | |(_-/|   \ | _ \/ _ \|  _|',
            '|_|_| \_._| \__|\___/|_|  |_|/__/|_||_||___/\___/ \__|']

C_MENUART = [' ___  ___  ___       _   ',
             '/   \| __|| _ ) ___ | |_ ',
             '| - || _| | _ \/ _ \|  _|',
             '|_|_||_|  |___/\___/ \__|']

MENUART2 = [' ▀▄▀ ▄▀▄ █ █   ▄▀▀ ▄▀▄ █ █ ▄▀  █▄█ ▀█▀',
            '  █  ▀▄▀ ▀▄█   ▀▄▄ █▀█ ▀▄█ ▀▄█ █ █  █ ']




KEYBINDS = [{'key': 'KEYBINDS ', 'description': '   INFORMATION   '},
            {'key': '    Q    ', 'description': '   Exit         '},
            {'key': '    p    ', 'description': '   Pause/resume '},
            {'key': '    u    ', 'description': '   Update info  '}]

# KEYBINDS = [{'key': 'KEYBINDS ', 'description': '   INFORMATION   '},
#             {'key': '    Q    ', 'description': '   Exit         '},
#             {'key': '    p    ', 'description': '   Pause/resume '},
#             {'key': '    u    ', 'description': '   Update info  '},
#             {'key': '    H    ', 'description': '   Help Page    '},
#             {'key': '    M    ', 'description': '   Manual mode  '}]


#------------------------- CLASSES ---------------------------#
class MainMenu:
    def __init__(self, autorun: bool = True, mode : str = 'full') -> None:
        self.is_alive = False
        self.refresh_rate = 0.3
        self.leaderboard = []
        self.inventory = []
        self.stats = []
        self.app = []
        self.message = []
        self.notification = '[!] Welcome back.'
        self.streak = 0
        self.cooldown = 0
        self.countdown = 0
        self.bypasses = 0
        self.d = ''
        if autorun:
            self.__call_run__(mode)
        pass
    
    def __call_run__(self, mode : str = 'full', func = None) -> None:
        if mode == 'full':
            curses.wrapper(self.full) 
        elif mode == 'compact':
            curses.wrapper(self.compact)
        else:
            #Custom menu
            try: 
                curses.wrapper(func)
            except Exception as e:
                debugger.debug(e, 'Exception')

    def kill(self) -> None:
        #...
        self.is_alive = False
    
    def check_keybinds(self, key) -> None:
        if key == ord('p'): 
            pauser.pause()
        elif key == ord('u'):
            #Pauses while updating profile
            try: 
                pauser.pause(func=self.profile.update)
            except Exception as e:
                self.notify(f'Error while updating profile: {e}')
                debugger(e, 'Exception')
        elif key == ord('H'): 
            self.notification = 'Help page pressed - not implemented yet.'
        elif key == ord('Q'): 
            self.kill()
        elif key == ord('M'): 
            self.notification = 'Manual mode pressed - not implemented yet.'

    def configure(self, bait: str, autobuff: bool, duration: int, profile : object) -> None:
        self.auto_buff = 'ON' if autobuff else 'OFF'
        self.buff_length = duration
        self.bait = bait.upper()
        self.profile = profile
        return None

    def setstats(self, data: list) -> None:
        self.stats = data
        return None
    
    def setinventory(self, data: list) -> None:
        self.inventory = data
        return None
    
    def setmessage(self, data: list) -> None:
        self.message = data
        return None
        
    def notify(self, notification : any) -> None:
        self.notification = str(notification)
        return None
    

    def resize_str(gc: any, message: str, max_width: int, delimiter: str = '+') -> str:
        '''
        Resize any string to a fixed length
        
        Resize formula (in calc_dimentions for the each menu - except for 
        notification which max_width is self.width):\n
        q = vertical lines amount\n
        z = horizontal lines amount (that crosses the entire screen, or
        at least the portion where the target height is located in).

        full:
        max_width = (width - (2 * column)) - q | max_height = (height - (height - row)) - z ?

        compact:
        max_width = (width - column) - q | max_height = height - z
        '''
        
        if len(message) > max_width:
            end = (max_width - len(delimiter)) - 1 #buffer
            return f'{message[:end]}{delimiter}'
        return message
    
    def full(self, stdscr : any) -> None:
        #Init
        stdscr.nodelay(True)
        stdscr.erase()
        stdscr.refresh()
        self.is_alive = True
        
        #Specific variables for this menu
        self.min_size = {'x': 112, 'y': 37}
        self.ascii_middle = (max(len(x) for x in MENUART) // 2)
        
        #Specific functions for this menu
        def calc_dimentions(scr) -> None:
            self.height, self.width = scr.getmaxyx()
            self.column = self.width - round((75 * self.width) / 100)
            self.row = round((30 * self.height) / 100)
            self.m_height, self.m_width, self.m_column = (self.height // 2), (self.width // 2), (self.column // 2)
            self.mr_w = (self.width - (2 * self.column)) - 2
            self.mr_h = (self.height - (self.height - self.row)) - 3
            return None
        
        #Main
        try:
            while self.is_alive:
                stdscr.erase()
                
                self.app = [
                {'title': 'CONFIG STATUS ', 'content': ' '},
                {'title': 'AUTOBUFF:     ', 'content': f'{self.auto_buff}'   },
                {'title': 'DURATION:     ', 'content': f'{self.buff_length}' },
                {'title': 'BAIT:         ', 'content': f'{self.bait}'        },
                {'title': 'STREAK:       ', 'content': f'{self.streak}'      },
                {'title': 'BYPASSES:     ', 'content': f'{self.bypasses}'    },
                {'title': 'RESUPPLY IN:  ', 'content': f'{self.countdown}'   },
                {'title': 'COOLDOWN:     ', 'content': f'{self.cooldown}'    },
                {'title': ''              , 'content': f'{self.d}'           }]
                
                #Calculations
                calc_dimentions(stdscr)
                
                #Check size
                if self.width < self.min_size['x'] or self.height < self.min_size['y']:
                    info = ['[MENU]', f'Mininum size: {self.min_size["x"]} x {self.min_size["y"]} ', f'Current: {self.width} x {self.height}']
                    for k, line in enumerate(info):
                        stdscr.addstr(self.m_height + k - 1, self.m_width - (len(line) // 2), line)
                else:
                    try:
                        #Start
                        #Render notification 
                        stdscr.addstr(0, 1, self.resize_str(self.notification, self.width, '...'))
                        
                        #------------------------ ASCII --------------------------#
                        #Render Logo
                        x_ascii = (self.m_width - 1) - self.ascii_middle
                        for k, line in enumerate(MENUART):
                            _y = k + 2
                            stdscr.addstr(_y, x_ascii, f'{line}')
                        
                        #Render middle
                        for k, line in enumerate(MENUART2):
                            _content = f'{line}'
                            _x = self.m_width - (len(_content) // 2) - 2 
                            _y = round(self.m_height * 0.45) + k
                            stdscr.addstr(_y, _x, f'{_content}')
                        
                        #------------------------ TEXT --------------------------#
                        #Keybinds Panel
                        for k, line in enumerate(KEYBINDS):
                            _content = f"{line['key']}-{line['description']}"
                            _x = ((self.width - self.column) + self.m_column) - (len(_content) // 2)
                            _y = k + 3
                            if k == 0: _y = k + 2
                            stdscr.addstr(_y, _x, f'{_content}')  
                        
                        #App Panel (ConfigManager)
                        for k, line in enumerate(self.app):
                            _content = f"{line['title']}{line['content']}"
                            _x = self.width - self.column #-(len(_content) // 2)
                            _y = (self.height - self.row) + k + 2 
                            if k == 0:
                                _x = ((self.width - self.column) + self.m_column) - (len(_content) // 2)
                                _y = _y - 1
                            stdscr.addstr(_y, _x, f'{_content}')
                        
                        #Inventory Panel (Profile)
                        for k, line in enumerate(self.inventory):
                            _content = f"{line['title']}{line['content']}"
                            _x = self.m_width - self.column
                            _y = (self.height - self.row) + k + 2
                            if k == 0:
                                _x = self.m_width - (len(_content) // 2)
                                _y = _y - 1
                            stdscr.addstr(_y, _x, f'{_content}')
                            
                        #Stats Panel (Profile)
                        for k, line in enumerate(self.stats):
                            _content = f"{line['title']}{line['content']}"
                            _x = 0
                            _y = (self.height - self.row) + k + 2
                            if k == 0:
                                _x = self.m_column - (len(_content) // 2) - 2 
                                _y = _y - 1
                            stdscr.addstr(_y, _x, f'{_content}')

                        #Information Panel (Messages)
                        if len(self.message) > 1:
                            for k, line in enumerate(self.message):
                                _content = f'{line}'
                                if len(_content) > self.mr_w:
                                    _x = (self.m_width + self.column) - (self.mr_w + 1)
                                else:
                                    _x = self.m_width - ceil(len(_content) / 2)
                                _y = (self.m_height - (len(self.message) // 2)) + k
                                if _content != '': 
                                    stdscr.addstr(_y, _x + 1, self.resize_str(_content, self.mr_w, '...'))
                                else: k -= 1
                        
                        #------------------------ LINES --------------------------#
                        stdscr.vline(1, self.column - 2, curses.ACS_VLINE, self.height) #Left
                        stdscr.vline(1, (self.width - self.column) - 2, curses.ACS_VLINE, self.height) #Right
                        stdscr.hline(1, 0, curses.ACS_HLINE, self.width) #Top
                        stdscr.hline(len(MENUART) + 3, self.column - 1, curses.ACS_HLINE, (self.column * 2) - 1) #Logo bottom 
                        stdscr.hline((self.height - self.row), 0, curses.ACS_HLINE, self.width) #Bottom
                    
                    #End
                    except curses.error as e:
                        self.notification = f'Screen size too small. {e}'
                sleep(self.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch())
        except Exception as e:
            debugger.debug(e, 'Exception')


    def compact(self, stdscr : any) -> None:
        #Init
        stdscr.nodelay(True)
        stdscr.erase()
        stdscr.refresh()
        self.is_alive = True
        
        #Specific variables for this menu
        self.min_size = {'x': 70, 'y': 18}
        self.ascii_max = (max(len(x) for x in C_MENUART))
        self.len_art = len(C_MENUART)

        #Specific functions for this menu
        def calc_compact_dimentions(scr) -> None:
            self.height, self.width = scr.getmaxyx()
            self.m_height, self.m_width = (self.height // 2), (self.width // 2)
            self.column = self.ascii_max + 1
            self.row = len(C_MENUART) + 3
            self.middle_info_panel = (self.column + ((self.width - self.column) // 2))
            self.mr_w = (self.width - self.column) - 1
            self.mr_h = self.height - 1
        
        #Main
        try:
            while self.is_alive:
                stdscr.erase()
                
                self.app = [
                {'title': 'CONFIG', 'content': ''},
                {'title': 'AUTOBUFF:    ', 'content': f'{self.auto_buff}'  },
                {'title': 'DURATION:    ', 'content': f'{self.buff_length}'},
                {'title': 'BAIT:        ', 'content': f'{self.bait}'       },
                {'title': 'STREAK:      ', 'content': f'{self.streak}'     },
                {'title': 'BYPASSES:    ', 'content': f'{self.bypasses}'   },
                {'title': 'RESUPPLY IN: ', 'content': f'{self.countdown}'  },
                {'title': 'COOLDOWN:    ', 'content': f'{self.cooldown}'   },
                {'title': ''             , 'content': f'{self.d}'          }]
                
                #Calculations
                calc_compact_dimentions(stdscr)
                
                #Check size
                if self.width < self.min_size['x'] or self.height < self.min_size['y']:
                    info = ['[MENU]', f'Mininum size: {self.min_size["x"]} x {self.min_size["y"]} ', f'Current: {self.width} x {self.height}']
                    for k, line in enumerate(info):
                        stdscr.addstr(self.m_height + k - 1, self.m_width - (len(line) // 2), line)
                else:
                    try:
                        #Start
                        #Render notification 
                        stdscr.addstr(0, 1, self.resize_str(self.notification, self.width, '...') )
                        
                        #------------------------ ASCII --------------------------#
                        
                        #Compact logo
                        for k, line in enumerate(C_MENUART):
                            stdscr.addstr(k + 2, 0, f'{line}')
                        
                        #------------------------ TEXT --------------------------#

                        #App Panel (ConfigManager)
                        for k, line in enumerate(self.app):
                            _content = f"{line['title']}{line['content']}"
                            _y = self.row + k
                            _x = 0
                            if k == 0:
                                _x = self.row + floor(len(_content) / 2)
                            else:
                                _y = _y + 1 #_y = _y - 1
                            stdscr.addstr(_y + 1, _x, f'{_content}')
                        

                        #Information Panel (Messages)
                        if len(self.message) > 1:
                            for k, line in enumerate(self.message):
                                _content = f'{line}'
                                if len(_content) > self.mr_w:
                                    _x = self.column + 1
                                else:
                                    _x = self.middle_info_panel - ceil(len(_content) / 2)
                                _y = (self.m_height - (len(self.message) // 2)) + k
                                if _content != '':
                                    stdscr.addstr(_y + 1, _x + 1, self.resize_str(_content, self.mr_w, '...'))
                                else: k -= 1
                        
                        
                        #------------------------ LINES --------------------------#
                        
                        stdscr.hline(1, 0, curses.ACS_HLINE, self.width) #Top - notifications
                        stdscr.vline(2, self.column, curses.ACS_VLINE, self.height) #division
                        stdscr.hline(self.row, 0, curses.ACS_HLINE, self.column) #logo frame
                    
                    #End
                    except curses.error as e:
                        self.notification = f'Screen size too small. {e}'
                sleep(self.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch())
        except Exception as e:
            debugger.debug(e, 'Exception')

        
    def custom(self, stdscr : any) -> None:
        '''
        This function is a boilerplate cointaining the basics for you to create a custom
        menu. You can create a new function in this class (or extend this class with your 
        own) and use the dafault methods and variables to attach the information to it.
        This boilerplate also include keybind checks enable by default.
        
        To call it is very simple (there is an example at the bottom):
        1- declare the menu: menu = MainMenu(autorun=False)
        2- call your custom menu: menu.__call_run__(mode='custom', func=menu.custom) 
        #func = menu.my_function_name (without the () )
        Also, you can set "func=" to a function outside the menu class but you won't be able
        to use the built-in methods by default.
        Anyways, you can check for the "curses" documentation to create your menu (or check 
        how I did mine). Feel free to share it on github if you did one =).
        
        NOTE: I plan to elaborate a proper documentation for this later.
        '''
        
        #Init
        stdscr.nodelay(True)
        stdscr.erase()
        stdscr.refresh()
        self.is_alive = True
        
        #Specific variables for this menu
        self.min_size = {'x': 70, 'y': 18}
        # + your variables here...
        
        #Specific functions for this menu
        def calc_custom_dimentions(scr):
            self.height, self.width = scr.getmaxyx()
            self.m_height, self.m_width = self.height // 2 , self.width // 2
            # + your code here...
            pass
        # + your functions here
        
        #Main
        try:
            while self.is_alive:
                stdscr.erase()
                
                #Calculations
                calc_custom_dimentions(stdscr)
                
                #Check size
                if self.width < self.min_size['x'] or self.height < self.min_size['y']:
                    info = ['[MENU]', f'Mininum size: {self.min_size["x"]} x {self.min_size["y"]} ', f'Current: {self.width} x {self.height}']
                    for k, line in enumerate(info):
                        stdscr.addstr(self.m_height + k - 1, self.m_width - (len(line) // 2), line)
                else:
                    try:
                        #Start customization
                        
                        #------------------------ ASCII --------------------------#
                        
                        #your arts here (if any) ... 
                        
                        #------------------------ TEXT --------------------------#

                        #your texts here (if any) ...
                        example = 'MY CUSTOM MENU =)'
                        stdscr.addstr(self.m_height, (self.m_width - len(example) // 2), f'{example}')
                        
                        #------------------------ LINES --------------------------#
                        
                        #your lines and shapes here (if any) ...
                    
                    #End customization
                    except curses.error as e:
                        self.notification = f'Screen size too small. {e}'
                sleep(self.refresh_rate)
                stdscr.refresh()
                self.check_keybinds(stdscr.getch())
        except Exception as e:
            debugger.debug(e, 'Exception')
        

# --------- INIT ---------#
if __name__ == "__main__":
    
    #Custom menu usage example
    menu = MainMenu(autorun=False)
    menu.__call_run__(mode='custom', func=menu.custom)
