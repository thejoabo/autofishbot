#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from configparser import ConfigParser
from webbrowser import Error as wbError, open as wbOpen
from datetime import date
from random import randbytes
from os import listdir, getcwd
from re import sub 
from sys import argv


#------------------------ CONSTANTS --------------------------#
REPO_CONFIG = 'https://github.com/thejoabo/virtualfisher-bot/blob/main/assets/template.config'


#------------------------- CLASSES ---------------------------#
class GenericException(Exception): pass

class MissingRequiredFieldError(Exception): 
    def __init__(self, field_name: str) -> None:
        super().__init__(f"The field '{field_name}' is required.")
        
class OutsideBoundariesError(Exception):
    def __init__(self, limits: tuple, value: any, field: str = 'Unk') -> None:
        super().__init__(f"{field}: Value outside boundaries ({limits[0]}, {limits[1]}), '{value}' given.") 
        
@dataclass(slots=True)
class ConfigManager:
    '''The configuration file manager to autofisherbot.'''
    #Todo: use argparse library instead of sys.argv for better (and more featured) argument parsing
    #Todo: ^^ https://docs.python.org/3/library/argparse.html#module-argparse
    
    
    #System
    user_token: str = ''
    user_cooldown: float = 3.5
    channel_id: str = ''
    debug: bool = False
    config_path: str = './configs/'
    
    #Captcha
    ocr_api_key: str = ''
    #manual_mode: bool = False
    
    #Network
    user_agent: str = ''
    proxy_ip: str = ''
    proxy_port: str = ''
    proxy_auth_user: str = ''
    proxy_auth_password: str = ''
    
    #Automation
    boosts_length: int = 5
    more_fish: bool = False
    more_treasures: bool = False
    fish_on_exit: bool = False
    auto_daily: bool = False
    auto_buy_baits: bool = False
    auto_sell: bool = False
    auto_update_inventory: bool = False
    
    #Menu
    compact_mode: bool = False
    refresh_rate: float = 0.3
    #number_formatting: str = 'default'
    
    #Cosmetic
    pet: str = ''
    bait: str = ''
    biome: str = ''
    
    _path: str = field(init=False, repr=False) 
    _configs: list[str] = field(init=False, repr=False)
    
    def __post_init__(self) -> None:
        self._path = f'{getcwd()}/{self.config_path}'
        self._configs = self.list_configs()
        
        
        if len(argv) >= 2:
            if argv[1] == '--create':
                self.create_config()
                exit()
        if self._configs != []:
            if len(self._configs) > 1:
                selected = self.choice_dialog()
                self.load_config(selected)
            else:
                self.load_config(self._configs[0])
        else:
            self.create_config()  
    
    def load_config(self, selected_config: str) -> None:
        '''Loads a config file.'''
        print(f'[*] Loading "{selected_config}" ...')
        
        cfg = ConfigParser()
        cfg.read(f'{self._path}/{selected_config}')
        
        try:
            system = cfg['SYSTEM']
            captcha = cfg['CAPTCHA']
            network = cfg['NETWORK']
            automation = cfg['AUTOMATION']
            menu = cfg['MENU']
            cosmetics = cfg['COSMETIC']
        except KeyError as e:
            self.err_dialog(f'[E] Outdated config file.\nTIP: You can use "python autofishbot.py --create" to create a new one at any time.')
            exit(1)
            
        try:
            #System
            self.user_token = self.to_str(system['user_token'], field='USER_TOKEN')
            self.user_cooldown = self.to_float(system['user_cooldown'], field='USER_COOLDOWN')
            self.channel_id = self.to_str(system['channel_id'], field='CHANNEL_ID')
            self.debug = self.to_bool(system['debug'])
            
            #Captcha
            self.ocr_api_key = self.to_str(captcha['ocr_api_key'], field='OCR_API_KEY')
            
            #Network
            self.user_agent = self.to_str(network['user_agent'], required=False)
            self.proxy_ip = self.to_str(network['proxy_ip'], required=False)
            self.proxy_port = self.to_str(network['proxy_port'], required=False)
            self.proxy_auth_user = self.to_str(network['proxy_auth_user'], required=False)
            self.proxy_auth_password = self.to_str(network['proxy_auth_password'], required=False)
            
            #Automation
            self.boosts_length = self.to_int(automation['boosts_length'], field='BOOSTS_LENGTH')
            self.more_fish = self.to_bool(automation['more_fish'])
            self.more_treasures = self.to_bool(automation['more_treasures'])
            self.fish_on_exit = self.to_bool(automation['fish_on_exit'])
            self.auto_daily = self.to_bool(automation['auto_daily'])
            self.auto_buy_baits = self.to_bool(automation['auto_buy_baits'])
            self.auto_sell = self.to_bool(automation['auto_sell'])
            self.auto_update_inventory = self.to_bool(automation['auto_update_inventory'])
            
            #Menu
            self.compact_mode = self.to_bool(menu['compact_mode'])
            self.refresh_rate = self.to_float(menu['refresh_rate'], field='REFRESH_RATE', bd=(0.1, 1))
            
            #Cosmetic
            self.pet = self.to_str(cosmetics['pet'], False)
            self.bait = self.to_str(cosmetics['bait'], False)
            self.biome = self.to_str(cosmetics['biome'], False)
        except KeyError as e:
            self.err_dialog(f'[E] Err -> {e} key missing | Outdated config file.')
        except (MissingRequiredFieldError, 
                OutsideBoundariesError, 
                GenericException, 
                ValueError) as e:
            exit(f'[E] Err -> {e}')
            
    def create_config(self) -> None:
        '''Creates a new config file.'''
        print(f'[*] Generating new config...')
        
        cfg = ConfigParser()
        cfg['SYSTEM'] = {
            'user_token': self.user_token,
            'user_cooldown': self.user_cooldown,
            'channel_id': self.channel_id,
            'debug': self.debug
        }
        
        cfg['CAPTCHA'] = {
            'ocr_api_key': self.ocr_api_key
        }
        
        cfg['NETWORK'] = {
            'user_agent': self.user_agent,
            'proxy_ip': self.proxy_ip,
            'proxy_port': self.proxy_port,
            'proxy_auth_user': self.proxy_auth_user,
            'proxy_auth_password': self.proxy_auth_password
        }
        
        cfg['AUTOMATION'] = {
            'boosts_length': self.boosts_length,
            'more_fish': self.more_fish,
            'more_treasures': self.more_treasures,
            'fish_on_exit': self.fish_on_exit,
            'auto_daily': self.auto_daily,
            'auto_buy_baits': self.auto_buy_baits,
            'auto_sell': self.auto_sell,
            'auto_update_inventory': self.auto_update_inventory
        }
        
        cfg['MENU'] = {
            'compact_mode': self.compact_mode,
            'refresh_rate': self.refresh_rate
        }
        
        cfg['COSMETIC'] = {
            'pet': self.pet,
            'bait': self.bait,
            'biome': self.biome
        }

        try:
            cfg_name = input(f'[?] Please insert a name for this config: ')
            if not cfg_name or len(sub('[a-zA-Z0-9 ]', '', cfg_name)) > 0:
                print('[!] Invalid name, a new name will be used instead.')
                cfg_name = self.make_name()
        except KeyboardInterrupt:
            exit(f'\n[!] User exited.')

        try:
            cfg_name += '.config'
            with open(f'{self._path}/{cfg_name}' , 'w') as f:
                cfg.write(f)
            exit_message = f'\n[!] Config "{cfg_name}" successfully created at "{self._path}".\n[!] Please fill in the configuration information...'
            wbOpen(f'{self._path}/{cfg_name}' )
        except wbError as e:
            exit_message = f'\n[E] Unable to open default text editor, please edit it manually. Details: {e}'
        except Exception as e:
            exit_message =f'\n[E] Unable to create new config -> {e}\n[!] NOTE: You can download a sample config file at: {REPO_CONFIG}'
        finally:
            print(exit_message)
        
    def list_configs(self, arr: list = []) -> list:
        '''List all .config files from a directory.'''
        for file in listdir(self._path):
            if file.find('.config') > -1:
                arr.append(file)
        return arr

    def to_str(self, value: any, required: bool = True, field: str = None) -> str:
        '''Validate string values.'''
        value = sub('["\']', '', value)
        if value:
            return str(value)
        else: 
            if required:
                raise MissingRequiredFieldError(field)
            else:
                return None
            
    def to_bool(self, value: any) -> bool:
        '''Converts and evaluates string values to boolean.'''
        if value:
            return True if str(value).lower() in ['1', 'true', 'on'] else False
        else:
            return False

    def to_int(self, value: any, field: str = None) -> int:
        '''Converts and evaluates string values to integer.'''
        if value:
            try:
                if int(value) > 12.5:
                    return 20
            except ValueError as e:
                raise GenericException(f'{field}: {e}')
        return 5

    def to_float(self, value: any, field: str = None, bd: tuple = (2, 3.5)) -> float:
        '''Converts and evaluates string values to float.'''
        if value:
            try:
                value = float(value)
            except ValueError as e:
                raise GenericException(f'{field}: {e}.')
            
            if self.compare(value, bd):
                return float(value)
            else:
                raise OutsideBoundariesError((2, 3.5), value, field)
        else:
            if field == 'REFRESH_RATE':
                return 0.3
            else:
                raise MissingRequiredFieldError(field)

    def compare(self, value: float, bd: tuple) -> bool:
        '''Compares if value is between boundaries.'''
        l_min, l_max = bd
        if value >= l_min and value <= l_max:
            return True
        return False
    
    def err_dialog(self, message: str) -> None:
        '''Error dialog to create a new config.'''
        print(f'{message}')
        try:
            if input(f'[?] Do you want to create a new config ? (y/n) ').lower() == 'y':
                self.create_config()
            else: 
                exit(f'[!] User exited.')
        except KeyboardInterrupt: 
            exit(f'\n[!] User exited.')
        except Exception as e: 
            #debugger.debug(e, 'Exception')
            exit(f'\n[!] User exited ({e}).')
    
    def choice_dialog(self) -> str:
        '''Choosing dialog to select one config.'''
        if len(argv) >= 2:
            try: 
                index = int(argv[1])
                if index > 0 and index <= len(self._configs):
                    return self._configs[index - 1]
                else:
                    print(f'Invalid choice. {index} is outside the scope.')
            except ValueError:
                for name in self._configs:
                    if name.lower() == f'{argv[1].lower()}.config'or name.lower() == argv[1].lower():
                        return name
                print(f'Invalid choice. "{argv[1]}" is outside the scope.')
        
        print(f'[!] Multiple configs detected in {self._path} folder.\nPlease choose:')
        for k, config in enumerate(self._configs):
            print(f'\t{k + 1} - "{config}"')
        while True:
            try:
                index = int(input(f'[?] Insert the config number: '))
                if index > 0 and index <= len(self._configs):
                    return self._configs[index - 1]
                else: 
                    raise GenericException(f'Invalid choice. {index} is outside the scope.')
            except KeyboardInterrupt:
                exit('\n[!] User exited.')
            except Exception as e:
                print(f'[E] Try again. Err -> {e}')
    
    def make_name(self) -> str:
        return f'{date.today().strftime("%d-%m-%y")}-{randbytes(5).hex()}' 
    


# --------- INIT ---------#
if __name__ == "__main__":
    config = ConfigManager()
    print(config)
