#------------------------ IMPORTS --------------------------# 
from typing import Callable, Any
from inspect import stack, trace

#------------------------- CLASSES ---------------------------#
class Debugger:
    '''This class will get better in the future.'''
    def __init__(self, switch = False) -> None:
        self.is_active = switch
        pass
    
    def setactive(self, switch : bool) -> None:
        self.is_active = switch
    
    def debug(self, event : any = None, id : str = 'Unk') -> None:
        #tt -> a = 'log', b (debug) = true -> !a || (b && a)
        if id != 'Log' or (self.is_active and id == 'Log'):
            print(f'''
            DEBUG -> {id}\n
            TRACEBACK -> {trace()}\n
            EVENT -> {event}\n
            STACK -> {stack()}\n
            ''')


class PauseControl:
    def __init__(self, starter = True) -> None:
        self.paused = starter
        #self.menu = menu
        #self.status = ''
        pass
    def setmenu(self, menu : object) -> None:
        self.menu = menu
    
    def pause(self, func: Callable[[], Any] = None, args : tuple = (), resume_func : Callable[[], Any] = None, rargs : tuple = ()) -> None:
        if func:
            self.paused = True
            self.menu.notification = f'Autofish paused. Calling function: {func.__name__}{args}.'
            resp = func(*args)
            self.menu.notification = f'Autofish resumed. Call ended returning -> {resp}'
            self.paused = False
            return
        else:
            if self.paused:
                #Unpause
                if resume_func:
                    #With function
                    resp = resume_func(*rargs)
                    self.menu.notification = f'Autofish resumed with a call to {resume_func.__name__}{rargs} returning -> {resp}'
                else:
                    #Without function
                    self.menu.notification = 'Autofish resumed.'
                self.paused = False
            else:
                #Pause
                self.menu.notification = 'Autofish paused.'
                self.paused = True
            return
        
        
#------------------------- INIT ---------------------------#
pauser = PauseControl()
debugger = Debugger()