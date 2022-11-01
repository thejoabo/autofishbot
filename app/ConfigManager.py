#------------------------ IMPORTS --------------------------#
from webbrowser import Error as wbError, open as wbOpen
from configparser import ConfigParser
from os import getcwd, listdir
from app.Util import debugger
from re import sub
from sys import argv


#------------------------ CONSTANTS --------------------------#
CONFIG_PATH = './configs/'
REPO_CONFIG = 'https://github.com/thejoabo/virtualfisher-bot/blob/main/assets/template.config'


#------------------------- CLASSES ---------------------------#
class CustomError(Exception): pass

class ConfigManager:
    def __init__(self, auto_load = True, generate_new = False) -> None:
        self.channel_id = None
        self.user_token = None
        self.ocr_api_key = None
        self.user_cooldown = None
        self.bait = None
        self.auto_buff = None
        self.buff_length = None
        self.fish_on_exit = None
        self.compact_mode = None
        self.debug = None
        self.number_formatting = None
        self.path = f'{getcwd()}/{CONFIG_PATH}' 
        self.configs = self.__list_configs__()
        self.cdlimits = {'min': 2, 'max': 4}
        self.bflimits = {'min': 0, 'max': 20}
        if auto_load:
            self.loadConfig()
        elif generate_new:
            self.generateConfig()
        else: pass
    
    def loadConfig(self) -> None:
        if self.configs != []:
            if len(self.configs) > 1:
                selected = self.choiceDialog()
            else: selected = self.configs[0]
            try:
                cfg = ConfigParser()
                cfg.read(f'{self.path}/{selected}')
                config = cfg['PREFERENCES']
                #?--------------------   PARAMETERS    --------------------#
                self.channel_id    = str(int(config['CHANNEL_ID']))
                self.user_token    = self.to_string(config['USER_TOKEN'])
                self.ocr_api_key   = self.to_string(config['OCR_API_KEY'])
                self.bait          = self.to_string(config['BAIT'])
                self.auto_buff     = self.to_bool(config['AUTO_BUFF'])
                self.buff_length   = self.round_bf(int(config['BUFF_LENGTH']))
                self.fish_on_exit  = self.to_bool(config['FISH_ON_EXIT']) 
                self.debug         = self.to_bool(config['DEBUG'])
                
                #COMPACT_MODE
                _cm = self.to_bool(config['COMPACT_MODE'])
                if _cm: 
                    self.compact_mode = 'compact'
                else: 
                    self.compact_mode = 'full'
                
                #NUMBER_FORMATTING - not implemented yet
                _nf = self.to_string(config['NUMBER_FORMATTING']).lower()
                if _nf in ['e','scientific']: 
                    self.number_formatting = 'e'
                elif _nf in [None,'default']: 
                    self.number_formatting = 'default'
                else: 
                    raise CustomError(f'NUMBER_FORMATTING outside ["e", "default"] -> "{_nf}" given.')
                
                #USER_COOLDOWN
                _cd = float(config['USER_COOLDOWN'])
                if self.between(_cd, self.cdlimits['min'], self.cdlimits['max']):
                    self.user_cooldown = _cd
                else: 
                    raise CustomError(f'USER_COOLDOWN outside {self.cdlimits} -> "{_cd}" given.')
                #?---------------------------------------------------------#
                
                print(f'[*] Successfully loaded \'{selected}\' config. ')
                cfg.clear()
                return
            except KeyError as e:
                self.errDialog(f'[E] Your config doesn\'t have the {e} parameter. This might occur due to a outdated config file.')
            except Exception as e:
                debugger.debug(e, 'Exception')
                self.errDialog(f'[E] Something went wrong trying to import your config. Err -> {e}') 
        else:
            self.generateConfig()
    
    def between(self, value: float, min: float, max: float) -> bool:
        '''Check if given value is between two numbers'''
        if min <= value and value <= max: 
            return True 
        return False

    def to_string(self, value: str) -> str:
        return sub(r'[\'\"]', '', value)

    def round_bf(self, value: int, m = 12.5) -> int:
        if value > -1:
            if self.between(value, self.bflimits['min'], m): 
                return 5
            elif self.between(value, m, self.bflimits['max']): 
                return 20
            else: 
                raise CustomError(f'BUFF_LENGTH outside {self.bflimits} -> "{value}" given.')
        else: 
            raise CustomError(f'BUFF_LENGTH: {value} < 0.')
    
    def to_bool(self, param: str) -> bool:
        '''Convert string to bool'''
        param = str(param).lower()
        if param in ['1', 'true']: 
            return True
        elif param in ['0', 'false']: 
            return False
        else: 
            raise CustomError(f'[E] Expected: true or false, "{param}" given. Check your config file.')
    
    def errDialog(self, message: str) -> None:
        print(f'{message}')
        try:
            if input(f'[?] Do you want to generate a new config ? (y/n) ').lower() == 'y':
                self.generateConfig()
            else: 
                exit(f'[!] User exited.')
        except KeyboardInterrupt: 
            exit(f'\n[!] User exited.')
        except Exception as e: 
            debugger.debug(e, 'Exception')
            exit(f'\n[!] User exited ({e}).')
    
    def choiceDialog(self) -> str:
        if len(argv) >= 2:
            index = int(argv[1])
            if index > 0 and index <= len(self.configs):
                return self.configs[index - 1]
            else:
                print(f'Invalid choice. {index} is outside the scope.')
        print(f'[!] Multiple configs detected in {CONFIG_PATH} folder.\nPlease choose:')
        for k, config in enumerate(self.configs):
            print(f'\t{k + 1} - "{config}"')
        while True:
            try:
                index = int(input(f'[?] Insert the config number: '))
                if index > 0 and index <= len(self.configs):
                    return self.configs[index - 1]
                else: 
                    raise CustomError(f'Invalid choice. {index} is outside the scope.')
            except KeyboardInterrupt:
                exit('\n[!] User exited.')
            except Exception as e:
                print(f'[E] Try again. Err -> {e}')

    def generateConfig(self) -> None:
        print(f'[*] Generating new config...')
        newConfig = ConfigParser()
        newConfig['PREFERENCES'] = {
            'CHANNEL_ID'    : 'YOUR CHANNEL ID',
            'USER_TOKEN'    : 'YOUR TOKEN',
            'OCR_API_KEY'   : 'YOUR API KEY',
            'USER_COOLDOWN' : 'YOUR COOLDOWN',
            'BAIT'          : 'YOUR BAIT HERE',
            'AUTO_BUFF'     : 'FALSE',
            'BUFF_LENGTH'   : '5',
            'FISH_ON_EXIT'  : 'FALSE',
            'COMPACT_MODE'  : 'FALSE',
            'DEBUG'         : 'TRUE',
            'NUMBER_FORMATTING': 'DEFAULT'
        }
        #Config name
        while True:
            _name = input(f'[?] Please insert a name for this config: ')
            if _name: break
            else: print(f'[!] The name can\'t be null.')
        
        #Writes config
        try:
            with open(f'{self.path}/{_name}.config' , 'w') as f:
                newConfig.write(f)
            exit_message = f'\n[!] Config successfully created at "{self.path}".\n[!] Please fill in the configuration information...'
            wbOpen(f'{self.path}/{_name}.config' )
        except wbError as e:
            exit_message = f'\n[E] Unable to open default text editor, please edit it manually. Details: {e}'
        except Exception as e:
            exit_message =f'\n[E] Unable to create new config -> {e}\n[!] NOTE: You can download a sample config file at: {REPO_CONFIG}'
        finally:
            exit(exit_message)
    
    def __list_configs__(self, arr = []) -> list:
        '''List all .config files from a directory'''
        for file in listdir(self.path):
            if file.find('.config') > -1:
                arr.append(file)
        return arr

# --------- INIT ---------#
if __name__ == "__main__":
    config = ConfigManager()
