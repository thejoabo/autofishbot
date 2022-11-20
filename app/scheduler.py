#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from .cooldown import CooldownManager
from enum import Enum, auto
from time import sleep, time
from random import random, uniform, randint


ONCE = 24*60*60
DEFAULT = 5*60

#Todo: make classes/functions docstrings

class SchStatus(Enum):
    READY = auto()
    BUSY = auto()
    WAITING = auto()
    BREAK = auto()

@dataclass(slots=True)
class CommandType:
    cmd: str
    default_cd: float = DEFAULT
    field_name: str = field(default=None, repr=False)
    value: str = field(default=None, repr=False)
    event: dict = None
    last_usage: float = 0
    block_requests: bool = False

    def __post_init__(self) -> None:
        if self.default_cd != ONCE:
            #Adds some randomization for each base cooldown
            if self.cmd != 'buy':
                self.default_cd += uniform(-120, 240)
            else:
                self.default_cd += uniform(-120, 360)
        
        if self.field_name and self.value:
            self.event = {
                "type": 3,
                "name": self.field_name,
                "value": self.value
            }
    def __repr__(self) -> str:
        return self.cmd    
     
    @property
    def data(self) -> dict:
        self.last_usage = time()
        return (self.cmd, self.event)


class Commands:
    #Todo: refactor this class later - use cooldown manager to generate base cooldowns dynamically
    def __init__(self, config: ConfigManager) -> None:
        #Builds values strings
        bait_cd, bait_value = self._make_bait(config)
        mf_value, mt_value, boosts_cd = self._make_boosts(config.boosts_length)
        
        #Commands lock (if automated, user is restricted)
        daily_lock, sell_lock = config.auto_daily, config.auto_sell
        mf_lock, mt_lock = config.more_fish, config.more_treasures
        
        #Info
        self.profile: CommandType = CommandType('profile', 10*60)
        self.pos: CommandType = CommandType('pos')
        self.quests: CommandType = CommandType('quests')
        self.charms: CommandType = CommandType('charms')
        self.buffs: CommandType = CommandType('buffs')
        self.show_rods: CommandType = CommandType('rod')
        self.show_biomes: CommandType = CommandType('biome')
        self.daily: CommandType = CommandType('daily', ONCE, block_requests=daily_lock)

        #Buy and sell
        self.sell: CommandType = CommandType('sell', 8*60, 'amount', 'all')#, block_requests=sell_lock)
        self.bait: CommandType = CommandType('buy', bait_cd, 'item', bait_value)
        self.worker: CommandType = CommandType('buy', ONCE, 'item', 'auto30m')
        self.morefish: CommandType = CommandType('buy', boosts_cd, 'item', mf_value, block_requests=mf_lock)
        self.moretreausre: CommandType = CommandType('buy', boosts_cd, 'item', mt_value, block_requests=mt_lock)
        
        #Select
        self.select_pet: CommandType = CommandType('pet', DEFAULT, 'selection', config.pet)
        self.select_biome: CommandType = CommandType('biome', DEFAULT, 'selection', config.biome)
        self.select_bait: CommandType = CommandType('bait', DEFAULT, 'selection', config.pet)
        self.select_rod: CommandType = CommandType('rod', DEFAULT, 'selection', 'config.rod...')
    
    def __iter__(self, command: CommandType = None):
        for key in self.__dict__:
            command = self.__dict__.get(key)
            yield command
    
    def _make_boosts(self, length: int) -> tuple[str]:
        return (f'fish{length}m', f'treasure{length}m', length*60)
    
    def _make_bait(self, config: ConfigManager) -> tuple[float, str]:
        if config.bait:
            bait_cd = randint(15, 30) * 60
            bait_amount = round(((bait_cd / config.user_cooldown) - 10) * 0.30, -1)
            bait_value = f'{config.bait} {int(bait_amount)}'
        else:
            bait_cd, bait_value = ONCE, None
        return (bait_cd, bait_value)

@dataclass(slots=True)
class Scheduler:
    #Todo: make the cooldown variable global
    session: DiscordWrapper
    config: ConfigManager
    menu: BaseMenu
    captcha: Captcha
    dsp: object = field(init=False) #Dispatcher
    
    cooldown: CooldownManager = field(init=False)
    queue: list[CommandType] = field(default_factory=list)
    commands: Commands = field(init=False)

    last_break: float = time()
    current_break_interval: float = field(init=False) #

    #Break time and break interval (min, max)
    break_interval_values: tuple[float] = (15*60, 90*60) #A break can happen between 15 and 90 minutes
    break_duration_values: tuple[float] = (2*60, 10*60) #Each break takes 2 to 10 minutes
    _break_remaining: float = 0.0
    
    status: SchStatus = SchStatus.BUSY 
    global_cooldown: float = 10.0 #Global commands cooldown (in seconds)

    def __post_init__(self) -> None:
        #Creates a new break interval
        self.new_interval()
        
        #Instantiate commands
        self.commands = Commands(self.config)
        
        #Instantiate cooldown generator
        self.cooldown = CooldownManager(self.global_cooldown, randint(2, 4))
        
        #Setups the automations
        self.setup()

    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    @property
    def waiting_time(self) -> None:
        value = self.cooldown.custom(
            mu=randint(1, 4) + random(), 
            sigma=random()
        )
        return value if value > 0 else 1 + random()
    
    def new_interval(self) -> None:
        #Creates a new break interval
        cd_min, cd_max = self.break_interval_values
        self.current_break_interval = uniform(cd_min, cd_max)

    def check_task(self, cmd: CommandType, manual: bool) -> bool:
        cond1 = cmd.last_usage == 0
        cond2 = (time() - cmd.last_usage) >= cmd.default_cd
        cond3 = manual == True
        cond4 = self.captcha.detected == False
        cond5 = self.dsp.paused == False
        if cond1 or cond2 or cond3 and cond4 and cond5:
            return True
        return False
        
    def interrupt_break(self) -> None:
        '''Interrupts break time (must be called after user input).'''
        self.status = SchStatus.WAITING
    
    def break_check(self) -> None:
        if (time() - self.last_break) >= self.current_break_interval:
            self.status = SchStatus.BREAK
            
            b_min, b_max = self.break_duration_values
            
            length = uniform(b_min, b_max)
            for sec in range(int(length*10)):
                #It's more memory costly but essential for informing users
                #about remainig break time
                if self.status != SchStatus.BREAK:
                    #User unpaused
                    self.menu.notify('[!] User exited scheduled break time.')
                    break
                self._break_remaining = length - (sec/10)
                sleep(0.1)

            self.last_break = time()
            
            #Makes a new cooldown, so things get more random
            self.new_interval()
        return None
    
    def purge_items(self, arr: list, idx: list) -> list:
        '''Removes elements from a list by a list of indexes.
        arr: list -> any list
        idx: list -> indexes to be removed'''
        n_arr: list = []
        if idx == []:
            return arr
        for index, element in enumerate(arr):
            if index not in idx:
                n_arr.append(element)
        return n_arr
    
    def run(self, dispatcher: object) -> None:
        self.dsp = dispatcher
        while True:
            removable = []
            self.break_check()
            self.status = SchStatus.READY
            
            #Waits while paused
            while self.dsp.paused:
                sleep(1)
            
            for index, task in enumerate(self.queue):
                command, persist, manual = None, None, None

                command, persist, manual = task
                if self.check_task(command, manual):
                    self.status = SchStatus.BUSY
                    
                    sleep(self.waiting_time)
                    
                    cmd, data = command.data
                    self.session.request(command=cmd, parameters=data)

                    if not persist:
                        removable.append(index)
                else:
                    pass
                    
            if self.status == SchStatus.BUSY:
                #For loop ended with busy status (meaning that an elemtn was ready to be sent)
                #dispatcher can resume, but any other command must wait to be sent again.
                self.queue = self.purge_items(self.queue, removable)
                    
                sleep(self.waiting_time)
                self.status = SchStatus.WAITING
                sleep(self.cooldown.new())
                continue
            else:
                sleep(2)
    
    def make_delay(self, secs: float, command: CommandType) -> None:
        '''It must be triggered by the setup() function, it randomizes the first execution
        of the command by emulating a last_usage value which is at `secs` seconds to get 
        off cooldown, so multiple command won't be called linearly at once when the bot 
        starts.'''
        command.last_usage = (time() - command.default_cd) + secs
        return None
    
    def add(self, command: CommandType, persist: bool = False, manual: bool = True, pre_delay: float = None) -> None:
        '''Appends the requested command to the queue.
        Structure: ...append(command: CommandType, persist: bool, manual: bool)'''
        if pre_delay:
            self.make_delay(pre_delay, command)
        self.queue.append(
            (command, persist, manual)
        )
    
    def setup(self) -> None:
        def init_delay(mn: float = 0, mx: float = 5*60) -> float:
            return uniform(mn, mx)
        
        if self.config.auto_daily:
            self.add(self.commands.daily, False, False, init_delay())
        
        boosts_delay = init_delay(0, 2*60)
        if self.config.more_fish:
            self.add(self.commands.morefish, True, False, boosts_delay)
        if self.config.more_treasures:
            self.add(self.commands.moretreausre, True, False, boosts_delay)

        if self.config.auto_buy_baits and self.config.bait:
            self.add(self.commands.bait, True, False, init_delay(5*60, 20*60))
        
        if self.config.auto_sell:
            self.add(self.commands.sell, True, False, init_delay(5*60, 15*60))

        if self.config.auto_update_inventory:
            self.add(self.commands.profile, True, False, init_delay(20, 3*60))

    def schedule(self, command: CommandType) -> bool:
        '''Schedules new tasks to the queue, must be called ONLY by user input.
        Since the user make the request for commands, it should be pointless to 
        rate limit it too hard, the command can be sent if the scheduler is ready
        and the command is not already schedule.'''
        for cmd in self.commands:
            if cmd == command:
                
                #Conditions
                sub_cond1 = True
                for k in self.queue:
                    if command == k[0]:
                        sub_cond1 = False
                sub_cond2 = (command.cmd == 'profile') and (self.config.auto_update_inventory == True)
                
                cond1 = sub_cond1 or (not sub_cond1 and sub_cond2)
                cond2 = self.status == SchStatus.READY
                cond3 = command.block_requests == False
                
                sub_cond3 = (command.default_cd == ONCE) and (command.last_usage == 0)
                cond4 = (command.default_cd != ONCE) or sub_cond3
                
                cond5 = self.captcha.detected == False
                
                if cond1 and cond2 and cond3 and cond4 and cond5:
                    self.menu.notify('[*] Command scheduled.')
                    self.add(command, manual=True)
                    return True
                else:
                    #Command in cooldown
                    if not cond1:
                        self.menu.notify('[!] Command already schedule to be executed, please wait.')
                    if not cond2:
                        self.menu.notify('[!] Global commands cooldown, please wait.')
                    if not cond3:
                        self.menu.notify('[!] This command is locked by Scheduler (due to automations).')
                    if not cond4:
                        self.menu.notify('[!] This command is rectricted to one usage.')
                    if not cond5:
                        self.menu.notify('[!] Captcha detected, Scheduler is locked.')
                    return False
        #Unknown command
        return False
