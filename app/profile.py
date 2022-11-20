#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from .utils import debugger
from time import time
from re import sub

#Todo: make functions/classes docstrings

def remove_markdown(data: str) -> str:
    '''Removes any markdown notations from string.'''
    return sub(r'[\*\+\_]', '', data)

@dataclass(slots=True)
class QuestType:
    '''Quest (singular entry) data type.'''
    objective: str
    current_progress: int
    total_progress: int
    category: str
    
    #Flags
    is_completed: bool = False
    
    @property
    def progress(self) -> str:
        if not self.is_completed:
            return f'{self.current_progress}/{self.total_progress}'
        else:
            return f'completed'
    
    def __post_init__(self) -> None:
        if self.current_progress == -1:
            self.conclude()
    
    def update(self, objective: str, current: int, total: int) -> None:
        self.objective = objective
        self.current_progress = current
        self.total_progress = total
        return None
    
    def conclude(self) -> None:
        self.is_completed = True
        return None

@dataclass(slots=True)
class QuestList:
    '''Quest list data type.'''
    quest_list: list[QuestType] = field(default_factory=list)
    
    remaining_time: str = None
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list, repr=False)
    
    @property
    def list(self) -> list[tuple]:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list
        
        for quest in self.quest_list:
            self._cached_list.append(
                (quest.category, quest.objective, quest.progress)
            )
        return self._cached_list
    
    def make_quest(self, data: list[str]) -> QuestType:
        '''Creates a new QuestType object containg the category, objective and progress.
        data: list[category, objective, progress]
        '''
        if len(data) == 3:
            category = data[0]
            objective = data[1]
            current, total = data[2].split('/')
        else:
            #Quest completed
            category = data[0]
            objective = sub(' COMPLETED', '', data[1])
            current, total = -1, -1
        
        return QuestType(
            category=category, objective=objective, 
            current_progress=current, total_progress=total
        )
    
    def update_quest(self, data: list[str], quest: QuestType) -> bool:
        '''Updates a given QuestType object to the new progress and objective.
        data: list[category, objective, progress]
        '''
        objective = data[1]
        current, total = -1, -1

        if len(data) == 3:
            current, total = data[2].split('/')
            if quest.is_completed:
                #New quest
                quest.is_completed = False
            quest.update(objective, current, total)
        else:
            #Quest completed
            objective = sub(' COMPLETED', '', data[1])
            quest.update(objective, current=current, total=total)
            quest.conclude()
        return True
    
    def update(self, raw_data: str) -> None:
        '''Scrapes quest information from raw event data and
        add each quest to the quest_list. If the list is not empty
        update progress values.'''

        data = remove_markdown(raw_data).split('\n')
        for line in data:
            if line.find('Quests have multiple tiers') > -1 or line == '':
                continue
            if line.find('Quests reset') > -1:
                start = line.find('in') + 3
                self.remaining_time = line[start:]
                continue
            
            #Quests content
            if line.startswith('Daily'):
                inner_data = line.split(' - ')
                if self.last_update == None:
                    self.quest_list.append(self.make_quest(inner_data))
                else:
                    for quest in self.quest_list:
                        if quest.category == inner_data[0]:
                            self.update_quest(inner_data, quest)

        self.last_update = time()
        self._cached_list = []
        return True

@dataclass(slots=True)
class ExoticFish:
    '''Exotic Fish data type.'''
    gold: int = 0
    emerald: int = 0
    lava: int = 0
    diamond: int = 0
    
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list)
    
    @property
    def list(self) -> list:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list
        
        self._cached_list = [
            (self.gold, 'Gold Fish'),
            (self.emerald, 'Emerald Fish'),
            (self.lava, 'Lava Fish'),
            (self.diamond, 'Diamond Fish')
        ]
        return self._cached_list

    def update(self) -> None:
        self.last_update = time()
        self._cached_list = []
        return None

@dataclass(slots=True)
class Charms:
    '''Charms data type.'''
    marketing: int = None
    endurance: int = None
    haste: int = None
    quantity: int = None
    worker: int = None
    treasure: int = None
    quality: int = None
    experience: int = None
    found: int = None
    
    _max_per_charm: int = field(default=10, repr=False)
    _max_total: int = field(default=440, repr=False)
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list, repr=False)
    
    @property
    def list(self) -> list:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list
        
        self._cached_list = [
            ('Marketing Charm', f'{self.marketing}/{self._max_per_charm}'),
            ('Endurance Charm', f'{self.endurance}/{self._max_per_charm}'),
            ('Haste Charm', f'{self.haste}/{self._max_per_charm}'),
            ('Quantity Charm', f'{self.quantity}/{self._max_per_charm}'),
            ('Worker Charm', f'{self.worker}/{self._max_per_charm}'),
            ('Treasure Charm', f'{self.treasure}/{self._max_per_charm}'),
            ('Quality Charm', f'{self.quality}/{self._max_per_charm}'),
            ('Experience Charm', f'{self.experience}/{self._max_per_charm}'),
            ('Total charms found.', f'{self.found}/{self._max_total}'),
        ]
        return self._cached_list
    
    def update(self, raw_data: str) -> None:
        data = remove_markdown(raw_data).split('\n')
        for line in data:
            if line == '': continue
            end = line.find('/')
            if line.find('Marketing') > -1:
                self.marketing = line[:end]
            if line.find('Endurance') > -1:
                self.endurance = line[:end]
            if line.find('Haste') > -1:
                self.haste = line[:end]
            if line.find('Quantity') > -1:
                self.quantity = line[:end]
            if line.find('Worker') > -1:
                self.worker = line[:end]
            if line.find('Treasure') > -1:
                self.treasure = line[:end]
            if line.find('Quality') > -1:
                self.quality = line[:end]
            if line.find('Experience') > -1:
                self.experience = line[:end]
            if line == data[-1]:
                self.found = line[:end]

        self.last_update = time()
        self._cached_list = []
        return True
    
@dataclass(slots=True)
class Buffs:
    '''Buffs (multipliers) data type'''
    sell_price: float = None
    fish_catch: float = None
    fish_quality: float = None
    treasure_chance: float = None
    treasure_quality: float = None
    xp_multiplier: float = None
    fishing_cooldown: float = None
    
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list, repr=False)

    @property
    def list(self) -> list[tuple]:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list
        
        self._cached_list = [
            ('Sell price', self.sell_price),
            ('Fish catch', self.fish_catch),
            ('Fish quality', self.fish_quality),
            ('Treasure chance', self.treasure_chance),
            ('Treasure quality', self.treasure_quality),
            ('XP multiplier', self.xp_multiplier),
            ('Fishing cooldown', self.fishing_cooldown),
        ]
        return self._cached_list
        
    def update(self, raw_data: str) -> bool:
        for line in remove_markdown(raw_data).split('\n'):
            if line == '': continue
            start = line.find(':') + 2
            if line.startswith('Sell'):
                self.sell_price = line[start:]
            if line.find('catch') > -1:
                self.fish_catch = line[start:]
            if line.startswith('Fish quality'):
                self.fish_quality = line[start:]
            if line.find('chance') > -1:
                self.treasure_chance = line[start:]
            if line.startswith('Treasure quality'):
                self.treasure_quality = line[start:]
            if line.startswith('XP'):
                self.xp_multiplier = line[start:]
            if line.find('cooldown'):
                self.fishing_cooldown = line[start:]
        
        self.last_update = time()
        self._cached_list = []
        return True

@dataclass(slots=True)
class Leaderboard:
    '''Leaderboards data type, contains all player classifications and points.'''
    level: str = None
    money: str = None
    fish_caught: str = None
    quests_completed: str = None
    chests_found: str = None
    net: str = None
    daily_streak: str = None
    weekly: str = None
    
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list, repr=False)
    
    @property
    def list(self) -> list[tuple]:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list
        
        self._cached_list = [
            ('Level', self.level),
            ('Money', self.money),
            ('Fish', self.fish_caught),
            ('Quests', self.quests_completed),
            ('Chests', self.chests_found),
            ('Net', self.net),
            ('Daily', self.daily_streak),
            ('Weekly', self.weekly)
        ]
        return self._cached_list
    
    def update(self, raw_data: str) -> bool:
        for line in remove_markdown(raw_data).split('\n'):
            if line == '': continue
            
            start = line.find('#') + 1
            end = line.find(' ', start)
            if line.startswith('Level'):
                self.level = line[start:end]
            elif line.startswith('Money'):
                self.money = line[start:end]
            elif line.startswith('Fish'):
                self.fish_caught = line[start:end]
            elif line.startswith('Quests'):
                self.quests_completed = line[start:end]
            elif line.startswith('Chests'):
                self.chests_found = line[start:end]
            elif line.startswith('Net'):
                self.net = line[start:end]
            elif line.startswith('Daily'):
                self.daily_streak = line[start:end]
            elif line.startswith('Weekly'):
                self.weekly = line[start:end]

        self.last_update = time()
        self._cached_list = []
        return True

@dataclass(slots=True)
class Inventory:
    items: list[tuple] = field(default_factory=list)
    last_update: float = None
    
    @property
    def list(self) -> list[tuple]:
        return self.items

    def reset(self) -> None:
        self.items = []
    
    def add(self, content: str) -> None:
        '''Adds a tupled element (fish_amount, fish_name) to the items list.'''
        amount, name = sub(r' <.+?> ', '#', content).split('#')
        self.items.append(
            (amount, name)
        )
        return None
        
@dataclass(slots=True)
class Profile:
    '''Profile manager class, contains player account information.'''
    #Money
    balance: str = None
    
    #Level
    level: str = None
    
    #Cosmetics
    rod: str = None
    biome: str = None
    pet: str = None
    bait: str = None
    
    #Current inventory
    inventory: Inventory = field(default_factory=Inventory)
    inventory_value: int = None
    
    #Exotic fishes
    exotic_fish: ExoticFish = field(default_factory=ExoticFish)
    
    #Extra info
    charms: Charms = field(default_factory=Charms)
    buffs: Buffs = field(default_factory=Buffs)
    quests: QuestList = field(default_factory=QuestList)
    leaderboard: Leaderboard = field(default_factory=Leaderboard)
    
    #Backend
    last_update: float = None
    _cached_list: list[tuple] = field(default_factory=list, repr=False)
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    @property
    def list(self) -> list[tuple]:
        if self.last_update == None:
            return []
        if self._cached_list != []:
            return self._cached_list

        self._cached_list = [
            ('Balance', self.balance),
            ('Level', self.level),
            ('Rod', self.rod),
            ('Biome', self.biome),
            ('Pet', self.pet),
            ('Bait', self.bait),
            ('Inventory value', self.inventory_value)
        ]
        return self._cached_list
    
    def update(self, raw_data: str) -> bool:
        self.inventory.reset()
        
        for line in remove_markdown(raw_data).split('\n'):
            if line == '': continue
            first_char = line[0]
            #Basic info
            if line.startswith('Balance:'):
                balance = sub('[^\d+]', '', line)
                self.balance = '${:,.2f}'.format(int(balance))
            elif line.find('XP to next level') > -1:
                #Level
                level = sub(' ', '', sub('[a-z]', '',  sub(', ', '|', line)))
                if level.startswith('P'):
                    level = sub('L', '|L', level) 
                else: 
                    level = sub('L', '', level)
                self.level = sub('\|', ' | ', level)
            
            #Cosmetics
            elif line.find('Rod') > -1:
                self.rod = sub(rf'{first_char}.+?> ', '', line)
            elif line.startswith('Current biome:'):
                self.biome = sub(rf'{first_char}.+?> ', '', line)
            elif line.startswith('Pet:'):
                self.pet = sub(rf'{first_char}.+?> ', '', line)
            elif line.startswith('Bait: '):
                self.bait = sub(rf'{first_char}.+?> ', '', line)
            
            #Exotic fishes
            elif line.find('Gold Fish') > -1:
                end = line.find('<') - 1
                self.exotic_fish.gold = int(sub(',', '', line[:end]))
            elif line.find('Emerald Fish') > -1:
                end = line.find('<')
                self.exotic_fish.emerald = int(sub(',', '', line[:end]))
            elif line.find('Lava Fish') > -1:
                end = line.find('<')
                self.exotic_fish.lava = int(sub(',', '', line[:end]))
            elif line.find('Diamond Fish') > -1:
                end = line.find('<')
                self.exotic_fish.diamond = int(sub(',', '', line[:end]))
            
            #Current inventory
            elif line.startswith('Fish Value:'):
                value = sub('[^\d+]', '', line)
                self.inventory_value = '${:,.2f}'.format(int(value))
            else:
                try:
                    if int(first_char):
                        self.inventory.add(line)
                except ValueError:
                    pass
        
        self.last_update = time()
        self.inventory.last_update = self.last_update
        self.exotic_fish.last_update = self.last_update
        self._cached_list = []
        return True

# --------- INIT ---------#
if __name__ == "__main__":
    pass

