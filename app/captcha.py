#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from .utils import debugger
from .menu import NotificationPriority
from requests import post, exceptions
from threading import Thread
from time import sleep
from json import loads
from re import sub

#------------------------ CONSTANTS --------------------------#
MAX_CAPTCHA_REGENS = 3

#------------------------- CLASSES ---------------------------#
class UnkownCaptchaError(Exception):
    pass

#Todo: make a captcha status (like scheduler class)


@dataclass
class Captcha:
    '''Catpcha class, detects and solves captchas.'''
    #Todo: split this class in chaptcha "controller" and captcha datatype
    #Pointers
    menu: BaseMenu = field(repr=False)
    
    #Components
    api_key: str = field(repr=False)
    answers: list = field(default_factory=list)
    captcha_image: str = None
    
    #Backend
    _ocr_url: str = field(default='https://api.ocr.space/parse/image', repr=False)
    _word_list: list[str] = field(init=False, repr=False)
    _raw_answers: list[str] = field(default_factory=list)
    _engines: list[int] = field(init=False, repr=False)
    _max_timeout: int = field(default=20, repr=False)
    _captcha_length: int = 6
    
    #Counters
    regens: int = 0
    
    #Flags
    busy: bool = False
    detected: bool = False
    solving: bool = False
    regenerating: bool = False

    #OCR Settings
    is_overlay_required: bool = field(default=False, repr=False)
    detect_orientation: bool = field(default=True, repr=False)
    scale: bool = field(default=False, repr=False)
    language: str = field(default='eng', repr=False)
    
    def __post_init__(self) -> None:
        self._word_list = ['captcha', 'verify']
        self._engines = [2, 1, 3, 5]
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    def filter(self, value: str) -> str:
        '''Filters results form the API. Valid results -> only alphanum and len == 6'''
        if value:
            ans = sub('[^a-zA-Z0-9]', '', value)
            if len(ans) == self._captcha_length:
                return ans
            else: 
                #Invalid result
                return None
        else:
            return None
    
    def request(self, engine: int) -> None:
        #Todo: make this function less complex and better structured
        '''Makes a request to the OCR api and appends the result (if valid) to the answers list.'''
        if not self.detected: 
            return None

        payload = {
            'apikey': self.api_key,
            'url': self.captcha_image,
            'isOverlayRequired': self.is_overlay_required,
            'detectOrientation': self.detect_orientation,
            'scale': self.scale,
            'OCREngine': engine,
            'language': self.language
        }
        
        try:
            request = post(self._ocr_url, data=payload, timeout=self._max_timeout)
            response = loads(request.content.decode())
        except exceptions.ReadTimeout as e:
            #Took too long to respond
            self.menu.notify(f'[!] Engine {engine} took too long to respond.', NotificationPriority.LOW)
            if engine == self._engines[-1]:
                self.solving = False
            debugger.log(e, f'{self.name} - request timeout | {self}')
            return None
        except Exception as e:
            debugger.log(e, f'{self.name} - request')
            raise UnkownCaptchaError(e)
        
        if response['OCRExitCode'] == 1:
            if self.detected:
                answer = self.filter(response['ParsedResults'][0]['ParsedText'])
                if answer:
                    #To avoid conflicts due to multi-threading, it must not be duplicate, 
                    #it must not be solved and must be busy (to garatee that the object it's the same)
                    if answer not in self.answers and self.detected:
                        self.answers.append(answer)
                    else:
                        #Duplicate result
                        pass
            
            if engine == self._engines[-1]:
                if not self.detected: 
                    return None
                self.solving = False
            return None
        else:
            #API error
            if not self.detected: 
                return None
            self.menu.notify(
                f'[!] Engine {engine} OCR API error -> ExitCode: {response["OCRExitCode"]}.', 
                NotificationPriority.HIGH
            )
            if engine == self._engines[-1]:
                self.solving = False
            return None     
            
    def detect(self, event: dict) -> bool:
        '''Attempts to detect any captchas in the event.'''
        self.busy = True

        for target in self._word_list:
            if str(event).find(target) > -1:
                self.detected = True
                break
        
        if self.detected:
            embeds = event['embeds']
            if len(embeds) > 0:
                for embed in embeds:
                    try:
                        self.captcha_image = embed['image']['url']
                        if self.captcha_image:
                            self.busy = False
                            return True
                        else:
                            #No image but field not keyerror
                            #raise UnknownCaptchaError('Image embeded but no image on key: embed["image"]["url"]')
                            debugger.log('UnknownCaptchaError: No image but field not keyerror', f'{self.name} - detect')
                            return True
                    except KeyError:
                        #Manual input needed - no image embeded
                        #raise UnknownCaptchaError('No image embeded')
                        #Their bot is bugged: https://discord.com/channels/565375575930437632/1022248238285336626/threads/1042106536232759446
                        #It should raise an exception but for now, just regen
                        debugger.log('UnknownCaptchaError: No image embeded', f'{self.name} - detect')
                        return True
            else:
                #Captcha detected but no embed.
                debugger.log('UnknownCaptchaError: Captcha detected but no embed', f'{self.name} - detect')
                raise UnkownCaptchaError('Captcha detected but no embed')
        else:
            self.busy = False
            self.reset()
            return False

    def solve(self) -> None:
        '''Start engine threads to solve the captcha.'''
        #Todo: try asyncio instead of threads
        self.busy = True
        self.solving = True
        self.regenerating = False
        self.answers = [] #Reset answers for redundancy
        
        for engine in self._engines:
            async_request = Thread(target=self.request, args=(engine,), daemon=True)
            async_request.start()
            sleep(0.5)
        
        self.busy = False
        return None
    
    def reset(self) -> None:
        '''Reset all attrs to default values.'''
        self.answers = []
        self.busy = False
        self.detected = False
        self.regenerating = False
        self.regens = 0
        return None
        
        
# --------- INIT ---------#
if __name__ == "__main__":
    pass