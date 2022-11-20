#------------------------ IMPORTS --------------------------#
from __future__ import annotations
from dataclasses import dataclass, field
from time import time
from typing import Callable, Any
from inspect import stack, trace
from datetime import datetime
from re import sub

#------------------------- FUNCTIONS ---------------------------#
def convert_time(epoch_time: float) -> str:
    '''Converts a given epoch time to readable format.'''
    if not epoch_time:
        return '-'
    date: datetime = datetime.fromtimestamp(epoch_time)
    return date.strftime('%H:%M - %D')

def sanitize(raw_string: str) -> str:
    '''Sanitizes a given string to a safe-to-use format.'''
    emojiless = sub(r':.+?:', '', sub(r'<.+?> ', '', raw_string)) #Removes emotes
    return sub(r'[*_`]', '', sub('[\n\b\t]', ' ', emojiless)) #Removes markdown

def dumper(fn: str, content: Any, path: str = './dumps', mode: str = 'w'):
    '''Writes content to the disk.'''
    with open(f'{path}/{fn}', mode) as f:
        f.write(content)

def make_command(cmd: str, name: str, value: str, type: int = 3) -> tuple:
    '''Builds a tuple containing the command (str) and the 'options' parameter (dict).'''
    parameters = {
        "type": type,
        "name": name,
        "value": value
    }
    return (cmd, parameters)

#------------------------- CLASSES ---------------------------#
@dataclass
class Debugger:
    '''Logs errors and exceptions.'''
    enabled: bool = False
    errors: int = 0
    
    def setup(self, switch : bool) -> None:
        self.enabled = switch
    
    def log(self, event : any = None, id : str = 'Unk') -> None:
        self.errors += 1
        if self.enabled:
            log_data = f'\n[{convert_time(time())}] {id} | [Traceback] {trace()} | [Event] {event} | [Stack] {stack()}\n'
            dumper('debug.log', log_data, './app', 'a')

#------------------------- INIT ---------------------------#
debugger = Debugger()