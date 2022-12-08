#------------------------ IMPORTS --------------------------#
from __future__ import annotations

from . import *
from .utils import debugger
from .menu import NotificationPriority
from time import time, sleep
from websocket import WebSocket
from requests import get, post, exceptions
from random import choice, randint, random

from string import digits, ascii_letters
from json import loads, dumps
from threading import Thread
from platform import uname


#------------------------ CONSTANTS --------------------------#
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

GATEWAY_CLOSE = [
{'code': 4000 , 'name': 'Unknown error', 'description': 'We\'re not sure what went wrong. Try reconnecting?', 'reconnect': True},
{'code': 4001 , 'name': 'Unknown opcode', 'description': 'You sent an invalid Gateway opcode or an invalid payload for an opcode.', 'reconnect': True},
{'code': 4002 , 'name': 'Decode error', 'description': 'You sent an invalid payload to us.', 'reconnect': True},
{'code': 4003 , 'name': 'Not authenticated', 'description': 'You sent us a payload prior to identifying.', 'reconnect': True},
{'code': 4004 , 'name': 'Authentication failed', 'description': 'The account token sent with your identify payload is incorrect.', 'reconnect': False},
{'code': 4005 , 'name': 'Already authenticated', 'description': 'You sent more than one identify payload.', 'reconnect': True},
{'code': 4007 , 'name': 'Invalid seq', 'description': 'The sequence sent when resuming the session was invalid. Reconnect and start a new session.', 'reconnect': True},
{'code': 4008 , 'name': 'Rate limited', 'description': 'Woah nelly! You\'re sending payloads to us too quickly. Slow it down! You will be disconnected on receiving this.', 'reconnect': True},
{'code': 4009 , 'name': 'Session timed out', 'description': 'Your session timed out. Reconnect and start a new one.', 'reconnect': True},
{'code': 4010 , 'name': 'Invalid shard', 'description': 'You sent us an invalid shard when identifying.', 'reconnect': False},
{'code': 4011 , 'name': 'Sharding required', 'description': 'The session would have handled too many guilds - you are required to shard your connection in order to connect.', 'reconnect': False},
{'code': 4012 , 'name': 'Invalid API version', 'description': 'You sent an invalid version for the gateway.', 'reconnect': False},
{'code': 4013 , 'name': 'Invalid intent(s)', 'description': 'You sent an invalid intent for a Gateway Intent. You may have incorrectly calculated the bitwise value.', 'reconnect': False},
{'code': 4014 , 'name': 'Disallowed intent(s)', 'description': 'You sent a disallowed intent for a Gateway Intent. You may have tried to specify an intent that you have not enabled or are not approved for.', 'reconnect': False},
]

HTTP_CODES = [
{'code': 200, 'name': 'OK', 'description': 'The request completed successfully.' },
{'code': 201, 'name': 'CREATED', 'description': 'The entity was created successfully.' },
{'code': 204, 'name': 'NO CONTENT', 'description': 'The request completed successfully but returned no content.' },
{'code': 304, 'name': 'NOT MODIFIED', 'description': 'The entity was not modified (no action was taken).' },
{'code': 400, 'name': 'BAD REQUEST', 'description': 'The request was improperly formatted, or the server couldn\'t understand it.' },
{'code': 401, 'name': 'UNAUTHORIZED', 'description': 'The Authorization header was missing or invalid.' },
{'code': 403, 'name': 'FORBIDDEN', 'description': 'The Authorization token you passed did not have permission to the resource.' },
{'code': 404, 'name': 'NOT FOUND', 'description': 'The resource at the location specified doesn\'t exist.' },
{'code': 405, 'name': 'METHOD NOT ALLOWED', 'description': 'The HTTP method used is not valid for the location specified.' },
{'code': 429, 'name': 'TOO MANY REQUESTS', 'description': 'You are being rate limited, see Rate Limits.' },
{'code': 502, 'name': 'GATEWAY UNAVAILABLE', 'description': 'There was not a gateway available to process your request. Wait a bit and retry.' },
{'code': '5xx', 'name': 'SERVER ERROR', 'description': 'The server had an error processing your request (these are rare).' },
]

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
NON_CRITICAL_CODES = [400, 429, 502]
TARGET_EVENT_NAMES = ['MESSAGE_CREATE', 'MESSAGE_UPDATE']
INVALID_FORM_BODY = 50035
APPLICATION_ID = '574652751745777665'
COMMAND = 'slash-command-interaction'
BUTTON = 'button-interaction'


#------------------------- CLASSES ---------------------------#
@dataclass(slots=True)
class Proxy:
    '''Proxy class, responsible for validating and constructing proper - ready-to-use - arguments
    for the request post/get methods.'''
    ip: str = None
    port: str = None
    user: str = None
    password: str = None
    validator_urls: list = field(default_factory=list, repr=False)
    _max_timeout: int = field(default=10, repr=False)
    is_valid: bool = False
    
    def __post_init__(self) -> None:
        self.validator_urls = ['https://ident.me', 'https://api.my-ip.io/ip']
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    def setup(self, ip: str, port: str, user: str = None, password: str = None) -> None:
        '''Assigns the class variables and calls the validate method.'''
        if ip and port:
            self.ip = ip
            self.port = port
            self.user = user
            self.password = password

            if self.validate():
                return None
            else:
                #Invalid proxy, using real ip.
                self.ip = None
                self.port = None
                self.user = None
                self.password = None
    
    def proxies(self) -> dict:
        '''Returns a dictionary containing the proxies argument for the 'requests' package.'''
        if self.ip and self.port:
            return {
                'http': f'{self.ip}:{self.port}',
                'https': f'{self.ip}:{self.port}'
            }
        else:
            return None
        
    def auth(self) -> tuple:
        '''Returns a tuple containing the auth information argument for the 'requests' package.'''
        if self.user and self.password:
            return (self.user, self.password)
        else: 
            return None
    
    def validate(self) -> bool:
        '''Validates the proxy and returns True if valid (uses real ip if validation failed).'''
        for url in self.validator_urls:
            print(f'[*] Validating proxy at {url}...')
            try:
                request = get(url, proxies=self.proxies(), auth=self.auth(), timeout=self._max_timeout)
                if request.status_code == 200:
                    print(f'[*] Using proxy: {request.content.decode()}')
                    self.is_valid = True
                    return True
            except exceptions.ProxyError as e:
                print(f'[!] Proxy validation Failed -> {e}')
            except exceptions.ReadTimeout:
                print(f'[!] Attempt timed out ({self._max_timeout}. Consider using a faster proxy.')
            except KeyboardInterrupt:
                exit(f'\n[!] User exited during proxy validation.')
            except Exception as e:
                debugger.log(e, f'{self.name} - validate')
                print(f'[E] Proxy validation unknown error -> {e}')
        print('\n\n[WARNING] PROXY VALIDATION FAILED, USING REAL IP.\n\n')
        return False


@dataclass(frozen=True, slots=True)
class ApiEndpoints:
    #Todo: refactor/remove this class
    channel_id: str = field(repr=False)
    version: int = 10
    interactions: str = None
    application_commands: str = None
    gateway: str = None
    
    def __post_init__(self) -> None:
        object.__setattr__(self, 'interactions', f'https://discord.com/api/v{self.version}/interactions')
        object.__setattr__(self, 'application_commands', f'https://discord.com/api/v{self.version}/channels/{self.channel_id}/application-commands/search?type=1&application_id={APPLICATION_ID}')
        object.__setattr__(self, 'gateway', f'wss://gateway.discord.gg/?v={self.version}&encoding=json')



@dataclass(slots=True)
class DiscordWrapper:
    '''Discord's Api wrapper, responsible for connectiong to the gateway and handle its events
    in addition to handling the Discord's HTTP Api (by sending valid commands).'''
    #Todo: function to cache commands and other constant info
    #Todo: exceptions and error handling in request function
    #Todo: split this class in gateway and http_api
    #Todo: use sessions for requests
    #Todo: https://github.com/aaugustin/websockets (maybe migrate ws library ?)
    #Todo: https://github.com/websocket-client/websocket-client#long-lived-connection (use this aproach instead)
    
    
    #Pointers
    config: ConfigManager = field(repr=False)
    menu: BaseMenu = field(repr=False)
    
    #User 
    user_token: str = field(init=False)
    channel_id: str = field(init=False)
    guild_id: str = field(init=False)
    
    #Discord
    session_id: str = field(init=False)
    commands: list[dict] = field(repr=False, default_factory=list)
    seq: int = None
    endpoints: ApiEndpoints = field(init=False, repr=False)

    #Network
    ws: WebSocket = field(init=False)
    user_agent: str = field(default=DEFAULT_USER_AGENT, repr=False)
    proxy: Proxy = field(default_factory=Proxy)
    headers: dict = field(default_factory=dict)
    _request_timeout: int = 15
    _jitter: float = field(default_factory=random)
    _default_heartbeat_interval: int = 41250
    _beating: bool = False
    _rate_limit_safe_guard: int = 3

    #Flags
    is_connected: bool = False
    is_ready: bool = False
    is_reconnecting: bool = False
    auto_connect: bool = False
    
    def __post_init__(self) -> None:
        '''Loads values from config and does some validation.'''
        #User
        self.user_token = self.config.user_token
        self.channel_id = self.config.channel_id
        self.guild_id = None 
        
        #Network
        self.ws = WebSocket()
        if self.config.user_agent:
            self.user_agent = self.config.user_agent
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'Authorization': self.user_token
        }
        
        self.proxy.setup(ip=self.config.proxy_ip, 
                         port=self.config.proxy_port, 
                         user=self.config.proxy_auth_user,
                         password=self.config.proxy_auth_password)
        
        #Discord
        self.session_id = self.make_session()
        self.endpoints = ApiEndpoints(self.channel_id)
        self.commands = self.load_commands()
        
        if self.auto_connect:
            self.connect()
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'    
    
    @property
    def heartbeat(self) -> dict:
        '''Returns the gateway ping event.'''
        return {
            'op': 1,
            'd': self.seq
        }
    
    @property
    def snowflake(self) -> int:
        '''Generates Discord's snowflake data type'''
        inc = self.seq if self.seq else randint(0, 10**3)
        return int((time()) * 1000 - 1420070400000) * (1024 * 4096) + inc
    
    @property
    def passport(self) -> dict:
        '''Returns the gateway identifier payload.'''
        return {
            'op': 2,
            'd': {
                'token': self.user_token,
                'properties': {
                    'os': uname().system,
                    'browser': 'firefox',
                    'device': 'pc'
                },
                'nonce': self.snowflake
            }
        }

    def make_session(self, session: str = ''):
        '''Generates user session'''
        return session.join(choice(ascii_letters + digits) for _ in range(32))

    def make_data(self, message_id: str, custom_id: str, category: str,
                  command: str, parameters: dict = []) -> dict:
        #Todo: refactor this class
        '''Builds data object containing a request for Discord's interactions Api.'''
        if category == COMMAND:
            cmd_data = None
            
            #Validate command
            for cmd in self.commands:
                try:
                    if command.lower() == cmd['name'].lower():
                        cmd_data = cmd
                        break
                except KeyError:
                    #debug
                    print('[!] Failed to parse command data.')
                    return None
            
            if cmd_data:
                return {
                    'type': 2,
                    'application_id': APPLICATION_ID,
                    'guild_id': self.guild_id,
                    'channel_id': self.channel_id,
                    'session_id': self.session_id,
                    'data': {
                        'version': cmd_data['version'],
                        'id': cmd_data['id'],
                        'name': cmd_data['name'],
                        'type': int(cmd_data['type']),
                        'options': [parameters] if parameters else [],
                        'application_command': cmd_data,
                        'attachments': []
                    },
                    'nonce': self.snowflake
                }
            else:
                self.menu.notify(f'[!] Unknown command: {command}', NotificationPriority.NORMAL)
                return None
        elif category == BUTTON:
            return {
                'type': 3,
                'nonce': self.snowflake,
                'guild_id': self.guild_id,
                'channel_id': self.channel_id,
                'message_flags': 0,
                'message_id': message_id,
                'application_id': APPLICATION_ID,
                'data': {
                    'component_type': 2, 
                    'custom_id': custom_id
                },
                'session_id': self.session_id
            }
        else:
            self.menu.notify(f'[!] Invalid category: {category}', NotificationPriority.LOW)
            return None
              
        
    def request(self, message_id: str = None, custom_id: str = None, category: str = None,
                command: str = None, parameters: list[dict] = [], method='post', endpoint: str = None, 
                get_data: any = None) -> bool:
        '''...'''
        if not endpoint:
            endpoint = self.endpoints.interactions
        if not category:
            category = COMMAND

        try:
            match method:
                case 'post':
                    data = self.make_data(message_id, custom_id, category, command, parameters)
                    if not data:
                        return None
                    request = post(
                        url=endpoint, data=dumps(data), headers=self.headers, proxies=self.proxy.proxies(),
                        auth=self.proxy.auth(), verify=True, timeout=self._request_timeout
                    )
                case 'get':
                    request = get(
                        url=endpoint, data=get_data, headers=self.headers, proxies=self.proxy.proxies(),
                        auth=self.proxy.auth(), verify=True, timeout=self._request_timeout
                    )
                case _:
                    return False
        except exceptions.ReadTimeout:
            self.menu.notify(f'[!] Request timed out ({self._request_timeout}).')
            return False
        except exceptions.ProxyError:
            self.menu.notify('[!] Proxy error.')
            return False
        except Exception as e:
            debugger.log(e, f'{self.name} - request')
            self.menu.notify(f'[!] Request - Unknown error: {e}')
            return False
            
        status_code = request.status_code
        headers = request.headers

        #Todo: integrate debugger with this code
        if status_code == 200:
            #Successfull requests that need to return data
            return loads(request.content)
        elif status_code > 204:
            #Request error
            if status_code in NON_CRITICAL_CODES:
                #Bad request
                if status_code == 400:
                    response = loads(request.content)
                    err_message = f'Code: {status_code}\nResponse: {response}\nRequest: {data}\nHeaders: {headers}'
                    
                    if int(response['code']) == INVALID_FORM_BODY:
                        #Non critical, but send slash command instead
                        #debug - ax0
                        print(err_message, '\nax0')
                        debugger.log(err_message, 'ax0')
                        return False
                    else:
                        #Critial, debbug and exit - ax1
                        debugger.log(err_message, 'ax1')
                        exit(err_message + '\nax1')
                
                #Rate limits
                elif status_code == 429:
                    response = loads(request.content)
                    try:
                        if not response['global']:
                            #Local resource limitation (but successfull)
                            message = response['message']

                            waiting_time = self._rate_limit_safe_guard + float(response['retry_after'])
                            self.menu.notify(f'[429] {message.capitalize()} waiting {waiting_time} seconds.', NotificationPriority.HIGH)
                            sleep(waiting_time)
                            return True
                        else:
                            #Global resource limitation (rare)
                            message = response['message']
                            exit('[E] 429 (Global): ', message, data)
                    except (KeyError, TypeError, ValueError) as e:
                        debugger.log(e, f'{self.name} 429')
                        exit('[E] 429: ', e)
                else:
                    #Gateway unavailable
                    self.menu.notify(f'[!] Gateway unavailable: {status_code}. Waiting 30 seconds.')
                    sleep(30)
                    return False
            else:
                #Critical, debug and exit  
                debugger.log(data, f'{self.name} {status_code}')
                exit(status_code)
        else:
            #201 and 204 - Successfull interactions
            return True

    def load_guild_id(self) -> str:
        '''Checks the READY event and returns the guild id (if found).'''
        while not self.guild_id:
            event = self.receive_event()
            if event['t'] == 'READY':
                #Guild Structure
                for guild in event['d']['guilds']:
                    for channel in guild['channels']:
                        if str(channel['id']) == self.channel_id:
                            return str(guild['id'])
                exit('[E] Incorrect channel id.')
            else:
                pass

    def load_commands(self) -> list:
        '''Searchs for the application commands from a given channel.'''
        #Todo: make this class dynamically create commands (currently at scheduler)
        try:
            content = self.request(endpoint=self.endpoints.application_commands, method='get')
            return content['application_commands']
        except Exception as e:
            debugger.log(e, f'{self.name} - load_commands')
            return []
    
    #----------------------------------GATEWAY----------------------------------#
    def receive_event(self) -> dict:
        '''Receives events from the gateway.'''
        event = self.ws.recv()
        if event:
            deserialized = loads(event)
            try: 
                self.seq = deserialized['s']
            except KeyError:
                pass
            return deserialized
        else:
            return None
    
    def connect(self) -> bool:
        '''Attempts to setup user connection to the gateway: connects, starts heartbeat thread
        and send identifier event.'''
        try:
            #Connect to the webgate
            if not self.is_reconnecting:
                print('[*] Connecting to gateway ...')
            self.ws.connect(self.endpoints.gateway, http_proxy_host=self.proxy.ip, 
                            http_proxy_port=self.proxy.port, http_proxy_auth=self.proxy.auth())
            self.is_connected = True
            
            #Start heartbeat thread
            if not self.is_reconnecting:
                print('[*] Starting heartbeat thread ...')
            Thread(target=self.start_heartbeat, daemon=True).start()

            #Send identify event
            if not self.is_reconnecting:
                print('[*] Logging in ...')
            self.ws.send(dumps(self.passport))
            
            #Load the guild id
            if not self.guild_id:
                self.guild_id = self.load_guild_id()
            
            self.is_ready = True
            if not self.is_reconnecting:
                print('[*] Session stablished !')
            return True
        except Exception as e:
            #Failed to connect.
            debugger.log(f'{e} : {self}', f'{self.name} - connect')
            exit(e)
 
    
    def reconnect(self) -> bool:
        '''Disconnects from the previous openned gateway and tries to make a new connection.'''
        self.is_reconnecting = True
        if self.is_connected:
            if not self.disconnect():
                exit("[E] Failed to reconnect.")

        #Wait heartbeat cycle
        if self._beating:
            self.menu.notify('[*] Waiting for previous connection to be completly closed...')
            while self._beating:
                sleep(1)
        
        #Reset data
        self.ws = WebSocket()
        self.session_id = self.make_session()
        self.seq = None
        
        #Connect to the webgate
        if self.connect():
            self.is_reconnecting = False
            return True
        else:
            exit("Failed to reconnect.")

    def disconnect(self) -> bool:
        '''Disconnects completly from the gateway'''
        self.is_connected = False
        self.is_ready = False
        try:
            self.ws.shutdown()
            if not self.is_reconnecting:
                print("[*] Disconnected !")
            return True
        except Exception as e:
            debugger.log(e, f'{self.name} - disconnect')
            return False
        pass
    
    def start_heartbeat(self, startup: bool = True) -> None:
        '''Gets the heartbeat interval and controls its sending to the gateway'''
        try:
            event = self.receive_event()
            interval = int(event['d']['heartbeat_interval']) / 1000
        except (KeyError, ValueError, TypeError):
            interval = self._default_heartbeat_interval / 1000

        #Loop
        while self.is_connected:
            self._beating = True
            #Wait for interval
            sleep((interval + self._jitter) if startup else interval)
            if startup:
                startup = False
            #Send heartbeat
            try:
                if self.is_connected:
                    self.ws.send(dumps(self.heartbeat))
            except Exception as e:
                self.menu.notify(f'[E] Failed to send heartbeat: {e}', NotificationPriority.HIGH)
                debugger.log(e, f'{self.name} - start_heartbeat')
        self._beating = False
        return None 


# --------- INIT ---------#
if __name__ == "__main__":
    pass
