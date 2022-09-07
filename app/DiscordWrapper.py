#------------------------ IMPORTS --------------------------#
from random import choice, randint
from websocket import WebSocket
from json import loads, dumps
from threading import Thread
from app.MenuManager import MainMenu
from app.Util import debugger
from requests import get, post, exceptions
from time import sleep, time
from string import digits, ascii_letters


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


#------------------------- CLASSES ---------------------------#
class DiscordWrapper:
    def __init__(self, token: str, auto_connect: bool = True, ) -> None:
        self.ws = WebSocket(enable_multithread=True)
        self.keep_alive = True
        self.auth = str(token)
        self.session = self.generate_session()
        self.channel_id = None
        self.guild_id = None
        self.application_id = None
        self.commands = None
        self.menu = None
        self.start = round(time() * 1000)
        self.seq = 0
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Authorization': self.auth
        }
        
        if auto_connect:
            self.connect()  
        
        return None
    
    
    #--------------------------- Utils ------------------------#
    def setpointers(self, channel_id: str = None, guild_id: str = None, application_id: str = None, menu: MainMenu = None) -> None:
        #Data
        self.channel_id = str(channel_id) if channel_id else self.channel_id
        self.guild_id = str(guild_id) if guild_id else self.guild_id
        self.application_id = str(application_id) if application_id else self.application_id
        self.menu = menu if menu else self.menu
        
        #Api
        self.api = {
            'interactions': 'https://discord.com/api/v9/interactions',
            'commands': f'https://discord.com/api/v9/channels/{self.channel_id}/application-commands/search?type=1&application_id={self.application_id}',
            'gateway': f'wss://gateway.discord.gg/?v=9&encoding=json'
        }
        return None
    

    def generate_session(self, session: str = ''):
        '''Generates user session'''
        return session.join(choice(ascii_letters + digits) for _ in range(32))
    
    def snowflake(self, incrementer: int) -> int:
        '''Generates Discord's snowflake data type'''
        inc = incrementer if incrementer else randint(0, 10**3)
        return int((time()) * 1000 - 1420070400000) * (1024 * 4096) + inc

    def get_commands(self) -> bool:
        '''Searchs for the application commands in a given channel'''
        r_search = get(self.api['commands'], data = '', headers = self.headers)
        if r_search.status_code == 200:
            content = loads(r_search.content)
            try:
                self.commands = content['application_commands']
                self.menu.notify(f'{len(self.commands)} commands loaded.')
                return True
            except Exception as e:
                debugger.debug(e, 'Exception - Commands Parsing')
                return False
        else:
            print(f'{__name__}() returned status code {r_search.status_code}')
            return False
    
    def make_data(self, 
                  message_id: int, 
                  custom_id: str, 
                  type: str, 
                  command: str,
                  options: dict
                  ) -> dict:
        
        if type == 'interactions':
            if command:
                #Slash
                query = None
                
                #Find command info
                for cmd in self.commands:
                    try:
                        if command.lower() == cmd['name'].lower():
                            query = cmd
                            break
                    except Exception as e:
                        debugger.debug(e, 'Exception - Cmd name parsing')
                if not query:
                    self.menu.notify(f'[!] Unknown command: "{command}".')
                    return {}
                
                data = {
                    "type": 2,
                    "application_id": self.application_id,
                    "guild_id": self.guild_id,
                    "channel_id": self.channel_id,
                    "session_id": self.session,
                    "data": {
                        "version": query['version'],
                        "id": query['id'],
                        "name": query['name'],
                        "type": int(query['type']),
                        "options": [options] if options else [],
                        "application_command": query,
                        "attachments": []
                    },
                    "nonce": self.snowflake(self.seq)
                }
            else:
                #Button
                data = {
                    'type': 3,
                    'nonce': self.snowflake(self.seq),
                    'guild_id': self.guild_id,
                    'channel_id': self.channel_id,
                    'message_flags': 0,
                    'message_id': str(message_id),
                    'application_id': self.application_id,
                    'data': {
                        "component_type": 2, 
                        "custom_id": custom_id
                    },
                    "session_id": self.session
                }
        else:
            #In case I still need to send normal messages in the future.
            data = {}
        
        return data
    
    
    
    
    #--------------------------- Send/Receive ------------------------#
    def request(self, 
                message_id: int = None, 
                custom_id: int = None, 
                type: str = 'interactions', 
                command: str = None,
                options: str = None
                ) -> bool:
        
        data = self.make_data(message_id, custom_id, type, command, options)
        if data == {}:
            return False
        
        try:
            r = post(
                    url = self.api[type],
                    data = dumps(data),
                    headers = self.headers,
                    verify = True,
                    timeout= 15
                )
        except exceptions.ReadTimeout:
            self.menu.notify(f'[E] Request timed out. (15)')
            return False
        except Exception as e:
            self.menu.notify(f'[E] Request error: {e}')
            debugger.debug(e, 'Exception - Request')
            return False
        
        self.code = r.status_code

        if self.code > 204:
            print(f'[E] Request error:\nPayload: {data}\nHeaders: {self.headers}\nUrl: {self.api[type]}')
            for code in HTTP_CODES:
                if code['code'] == self.code:
                    if self.code not in [400, 429, 502]:
                        print(f'\nDetails:\n\tCode: {self.code}({code["name"]})\n\tMeaning: {code["description"]}\n')
                        try:
                            print(f'Response dump: {loads(r.content)}')
                        except: 
                            pass
                        finally:
                            self.menu.kill()
                    elif self.code == 400:
                        response = loads(r.content)
                        if int(response['code']) == 50035:
                            #Invalid Form Body
                            return False
                        else:
                            try:
                                print(f'Response dump: {loads(r.content)}')
                            except Exception as e:
                                debugger.debug(e, f'Exception - 400')
                            finally:
                                self.menu.kill()
                    else:
                        self.menu.notify(f'[E] RCV: {self.code}({code["name"]}) | Sleeping 60 seconds... ')
                        debugger.debug(f'code: {self.code}')
                        sleep(60)
                        return True
                    #break
            try:
                print(f'[E] Unknown code: {self.code}')
                print(f'Response dump: {loads(r.content)}')
            except Exception as e:
                pass
            finally:
                self.menu.kill()
        else:
            #Ok
            return True
    
    def receive_event(self) -> list:
        _response = self.ws.recv()
        if _response:
            return loads(_response)
    
    
    #--------------------------- Connection ------------------------#
    #def connect(self, reconnect=False) -> bool:
    def connect(self) -> bool:
        try:
            self.ws.connect(self.api['gateway'])
            self._heartbeathread = Thread(target=self._send_heartbeat, args=(self._get_interval(),), daemon=True)
            self._heartbeathread.start()
            # if reconnect:
            #     if self.reconnect():
            #         self.menu.notify('[!] Session reconnected.')
            #         return True
            #     else:
            #         print('[E] Unable to reconnect.')
            #         self.menu.kill()
            #         return False
            # else:
            if self.webgate_passport():
                print('[*] Session stablished !')
                return True
            else:
                exit('\n[E] Something went wrong while connecting.')
        except Exception as e:
            debugger.debug(e, 'Exception')
            exit(f'\n[E] Something went wrong while connecting: {e}')
    
    # def reconnect(self) -> None:
    #     resume = {
    #         'op': 6,
    #         'd': {
    #             'token': f'{self.auth}',
    #             'session_id': f'{self.session}',
    #             'seq': f'{self.seq}'
    #         }
    #     }
    #     try:
    #         self.ws.send(dumps(resume))
    #         return True
    #     except Exception as e:
    #         debugger(e, 'Exception - Reconnect')
    #         return False

    def disconnect(self) -> bool:
        try:
            self.keep_alive = False
            self.ws.shutdown()  
            return True
        except Exception as e:
            debugger.debug(e, 'Exception')
            print(f'\n[E] Something went wrong while disconnecting: {e}')
            return False
        
    
        
    #--------------------------- Identification/KeepAlive ------------------------#
    def webgate_passport(self) -> bool:
        passport = {
            'op': 2,
            'd': {
                'token': f'{self.auth}',
                'properties': {
                    'os': 'win32', 
                    'browser': 'chrome', 
                    'device': 'pc'
                },
                'nonce': self.snowflake(self.seq)
            }
        }
        try:
            self.ws.send(dumps(passport))
            return True
        except Exception as e:
            debugger(e, 'Exception - Passport')
            return False
    
    
    def _get_interval(self) -> int:
        try:
            tmp = self.receive_event()
            return int(tmp['d']['heartbeat_interval']) / 1000
        except Exception as e:
            debugger.debug(e, 'Exception')
            return int(41.25)
    
    def _send_heartbeat(self, interval: int) -> None:
        heartbeat = {
            'op': 1, 
            'd': 'null' 
        }
        while self.keep_alive:
            sleep(interval)
            self.ws.send(dumps(heartbeat))