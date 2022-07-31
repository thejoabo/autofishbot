#------------------------ IMPORTS --------------------------#
from websocket import WebSocket
from json import loads, dumps
from threading import Thread
from app.Util import debugger
from requests import post
from time import sleep


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

 
#------------------------- CLASSES ---------------------------#
class DiscordWebgate:
    def __init__(self, token : str, channel_id : int , auto_connect : bool = True) -> None:
        self._ws = WebSocket()
        self.token = token
        self.channel_id = channel_id
        self._keepAlive = True
        self._query = f'https://discord.com/api/v9/channels/{channel_id}/messages'
        self._webgate_api = 'wss://gateway.discord.gg/?v=9&encoding=json'
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        self._payload = {
            'op': 2,
            'd': {
                'token': f'{self.token}',
                'properties': {'$os': 'windows', '$browser': 'chrome', '$device': 'pc'}
        }}
        self.headers = {
            'authorization': self.token,
            'user-agent': self.user_agent
        }
        if auto_connect:
            self.connect()  
        else: pass
     
    def connect(self) -> None:
        try:
            self._ws.connect(self._webgate_api, header={'user-agent': self.user_agent})
            self._interval = self._getInterval()
            self._heartbeathread = Thread(target=self._sendHeartbeat, daemon=True)
            self._heartbeathread.start()
            self.send_request()
            print('[*] Session stablished !')
        except Exception as e:
            debugger.debug(e, 'Exception')
            exit(f'\n[E] Something went wrong while connecting: {e}')
    
    def disconnect(self) -> bool:
        try:
            self._keepAlive = False
            self._ws.close()  
            return True
        except Exception as e:
            debugger.debug(e, 'Exception')
            print(f'\n[E] Something went wrong while disconnecting: {e}')
            return False
        
    def recieve_event(self) -> list:
        _response = self._ws.recv()
        if _response:
            return loads(_response)
        
    def send_query(self, payload) -> None:
        request = post(self._query, data = {'content': payload}, headers = self.headers, verify=True)
        return None
    
    def send_request(self, request : dict = None) -> None:
        _request = request if request else self._payload
        self._ws.send(dumps(_request))
        return None
    
    def _getInterval(self) -> int:
        try:
            tmp = self.recieve_event()
            return int(tmp['d']['heartbeat_interval']) / 1000
        except Exception as e:
            debugger.debug(e, 'Exception')
            return int(41.25)
    
    def _sendHeartbeat(self) -> None:
        while True:
            if self._keepAlive:
                sleep(self._interval)
                self.send_request({ 'op': 1, 'd': 'null' })
            else:
                break