#! /usr/bin/env python3
#------------------------ IMPORTS --------------------------#
from __future__ import annotations
from app import *
from websocket import WebSocketConnectionClosedException
from threading import Thread
from time import sleep, time
from random import random, uniform


@dataclass(slots=True)
class Receiver:
    #Pointers
    session: DiscordWrapper
    config: ConfigManager 
    menu: MainMenu
    
    #Objects
    captcha: Captcha = field(init=False)
    profile: Profile = field(default_factory=Profile)
    message: Message = field(default_factory=Message)
    category: MessageCategory = field(default_factory=MessageCategory)
    event: dict = None

    #Flags
    is_ready: bool = False
    
    def __post_init__(self) -> None:
        '''Setups captcha.'''
        self.captcha = Captcha(api_key=self.config.ocr_api_key, menu=self.menu)
    
    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'
    
    def check_event(self, response: dict) -> bool:
        '''Checks if event is targeted to the user (sent by the application to the selected channel),
        also defines the self.event.'''
        if not response:
            return False
        
        try:
            e = response['d']
            e_name = response['t']
            e_channel = e['channel_id']
            e_author = e['author']['id']
        except (KeyError, TypeError):
            return False
        
        if e_name in TARGET_EVENT_NAMES:
            if e_channel == self.config.channel_id:
                if e_author == APPLICATION_ID:
                    self.event = e
                    return True
        return False

    
    def run(self) -> None:
        '''Main loop, continuously checks for new gateway events and properly handles it.'''
        self.is_ready = True
        while True:
            try:
                response = self.session.receive_event()
            except WebSocketConnectionClosedException as e:
                debugger.log(e, f'{self.name} - run - reconnection')
                #Connection lost
                self.is_ready = False
                self.menu.notify('[!] Connection lost, attempting to reconnect...', NotificationPriority.HIGH)
                if self.session.reconnect():
                    self.is_ready = True
                    self.menu.notify('[*] Reconnection succeeded.')
                    continue
                else:
                    self.menu.kill()
                    print(f'[E] Reconnection failed. Exception: {e}')
                    break
            except Exception as e:
                debugger.log(e, f'{self.name} - run - reconnection')
                break
            
            if not self.check_event(response):
                #Invalid/Irrelevant gateway event
                continue
            
            self.message.make(self.event)
            
            if self.captcha.detected and not self.captcha.regenerating:
                if self.message.content == 'You may now continue.':
                    #Captcha bypassed
                    self.menu.rcv_bypasses += 1
                    self.captcha.reset()
                    self.menu.notify('[*] Captcha bypassed !')
                else:
                    if self.message.content.find('Incorrect code') > -1:
                        self.menu.notify('[*] Incorrect code.', NotificationPriority.LOW)
                        continue
                    else:
                        #Message sent by the bot while captcha is detected
                        debugger.log(self, f'{self.name} - run (Message sent by the AFB while captcha is detected)')
                        break
            elif self.captcha.regenerating:
                if self.captcha.detect(self.event):
                    self.captcha.solve()
                    continue
                else:
                    #No detection while regenerating
                    debugger.log(self, f'{self.name} - run (No detection while regenerating)')
                    exit()
            else:
                if self.captcha.detect(self.event):
                    self.menu.notify('[!] Captcha detected !', NotificationPriority.NORMAL)
                    self.captcha.solve()
                    continue
                else:
                    if self.message.title:
                        #Normal messages
                        if self.message.title == self.category.fish:
                            #Fish (/fish or button) messages
                            self.menu.items = self.message.build()
                            self.menu.rcv_streak += 1
                        elif self.message.title.find(self.category.profile) > -1:
                            #Profile (/profile) messages
                            self.profile.update(self.message.description)
                            self.menu.notify('[*] Profile updated.')
                        elif self.message.title.find(self.category.charms) > -1:
                            #Charms (/charms) messages
                            self.profile.charms.update(self.message.description)
                            self.menu.notify('[*] Charms updated.')
                        elif self.message.title.find(self.category.buffs) > -1:
                            #Buffs/multipliers (/buffs) messages
                            self.profile.buffs.update(self.message.description)
                            self.menu.notify('[*] Buffs updated.')
                        elif self.message.title.find(self.category.quests) > -1:
                            #Quest list (/quests) messages
                            self.profile.quests.update(self.message.description)
                            self.menu.notify('[*] Quests updated.')
                        elif self.message.title.find(self.category.leaderboard) > -1:
                            #Leaderboard (/pos) messages
                            self.profile.leaderboard.update(self.message.description)
                            self.menu.notify('[*] Leaderboards updated.')
                        #Todo: read '... boost ended' message and inform scheduler (?)
                        #Your fishing boost ended!
                        #Your treasure boost ended!
                        else:
                            #Unhandled titled message
                            self.menu.notify(f'{sanitize(self.message.title)}: {sanitize(self.message.description)}')
                            pass
                    else:
                        #Untitled messages
                        if self.message.content:
                            if self.message.content.find('You must wait') > -1:
                                #Intentional short cooldown
                                self.menu.notify(
                                    '[*] If automatic, this short cooldown is intentional to ensure non-bot behavior.', 
                                    NotificationPriority.VERY_LOW
                                    )
                                pass
                            else:
                                #Untitled message
                                self.menu.notify(f'[*] {self.message.untitled}')
                        else:
                            #Untitled with empty content  - probably embeded only with description
                            if menu.is_alive:
                                self.menu.notify(f'[*] {self.message.untitled}')
                            else:
                                if self.message.untitled.find('You hired a worker for the next') > -1 \
                                    or self.message.untitled.find('You already have a worker working') > -1:
                                    print(f'[*] {self.message.untitled}')
                            pass

        self.is_ready = False
        exit()
        
@dataclass(slots=True)
class Dispatcher:
    '''Dispatcher class, responsible for making, sending commands related to
    captcha and fish commands.'''
    #Pointers
    session: DiscordWrapper
    config: ConfigManager
    menu: BaseMenu
    sch: Scheduler
    rcv: Receiver
    captcha: Captcha = field(init=False)
    message: Message = field(init=False)
    
    #Objects
    cooldown: CooldownManager = field(init=False)
    
    #Flags
    in_cooldown: bool = False
    paused: bool = False

    def __post_init__(self) -> None:
        #Setting up pointers to improve organization
        self.captcha = self.rcv.captcha
        self.message = self.rcv.message
        
        #Instantiate cooldown manager
        self.cooldown = CooldownManager(user_cooldown=self.config.user_cooldown)
        
    def make_command(self, cmd: str, name: str, value: str, type: int = 3) -> tuple:
        '''Builds a tuple containing the command (str) and the 'options' parameter (dict).'''
        parameters = {
            "type": type,
            "name": name,
            "value": value
        }
        return (cmd, parameters)

    @property
    def name(self) -> str:
        '''Returns the class name in the correct format.'''
        return f'{self.__class__.__name__}'

    @property
    def pause(self) -> None:
        '''Play/Pause switch.'''
        if self.sch.status == SchStatus.BREAK:
            self.sch.interrupt_break()
        if self.paused:
            self.paused = False
            self.menu.notify('[*] Autofishbot resumed.')
        else:
            self.paused = True
            self.menu.notify('[*] Autofishbot paused.')
    
    @property
    def timeout(self) -> float:
        '''Timeout cooldown for general commands (other than fish commands).'''
        return self.cooldown.custom(
            mu= uniform(3, 5),
            sigma= random()
        )
    
    def run(self) -> None:
        '''Main loop, send commands'''
        _delay = 0.2

        while True:
            if not self.rcv.is_ready:
                sleep(_delay)
                continue
            
            if self.captcha.detected and not self.captcha.regenerating:
                if self.captcha.solving or len(self.captcha.answers) > 0:
                    try:
                        answer = self.captcha.answers.pop()
                        self.menu.notify(f'[!] Attempting code: "{answer}".')
                        cmd, param = self.make_command('verify', 'answer', answer)
                        self.session.request(command=cmd, parameters=param, category=COMMAND)
                        
                        sleep(self.timeout)
                    except IndexError:
                        continue
                else:
                    if self.captcha.regens < MAX_CAPTCHA_REGENS:
                        self.captcha.regens += 1
                        self.menu.notify(f'[!] Regenerating captcha ({self.captcha.regens + 1}/{MAX_CAPTCHA_REGENS})', NotificationPriority.HIGH)

                        #This will force a new event to be analyzed by the 
                        #detect() method but also keep the captcha.regens counter
                        self.captcha.regenerating = True
                        
                        cmd, param = self.make_command('verify', 'answer', 'regen')
                        self.session.request(command=cmd, parameters=param, category=COMMAND)

                        #This sleep timeout might be needed in case of really slow 
                        #connections, it might be caused by a bad proxy or internet
                        #?Further testing needed
                        sleep(1)
                    else:
                        self.menu.notify(f'[!] MAXIMUM CAPTCHA REGENS EXCEEDED, WAITING FOR MANUAL INPUT !', NotificationPriority.VERY_HIGH)
                        #Max regens attempts exceeded, waits for manual input
                        while self.captcha.detected:
                            sleep(1)
            else:
                while  self.captcha.busy \
                    or self.captcha.regenerating \
                    or self.sch.status in [SchStatus.BUSY, SchStatus.BREAK]:
                        sleep(_delay)
                
                if not self.captcha.detected and not self.paused and self.menu.is_alive:
                    _start = time()
                    
                    if self.message.id and self.message.play_id:
                        if self.session.request(message_id=self.message.id, custom_id=self.message.play_id, category=BUTTON):
                            #Successfull interaction with buttons
                            pass
                        else:
                            #Failed interaction, reset ids to trigger ussage of slash commands
                            self.message.reset_ids()
                    else:
                        self.session.request(command='fish', category=COMMAND)

                    self.in_cooldown = True
                    sleep(abs(self.cooldown.new() - (time() - _start)))
                    self.in_cooldown = False
                else:
                    sleep(_delay)

#------------------------ INIT --------------------------#
if __name__ == "__main__":
    print(f'\n[*] Starting...')
    
    #Loads config
    config = ConfigManager()
    
    #Setup debugger
    debugger.setup(config.debug)
    
    #Instantiate menu
    if config.compact_mode:
        menu = CompactMenu()
    else:
        menu = MainMenu()
    
    #Instantiate session
    session = DiscordWrapper(
        config=config, 
        menu=menu, 
        auto_connect=True)
    
    #Instantiate receiver
    receiver = Receiver(
        session=session, 
        config=config, 
        menu=menu)
    
    #Instantiate Scheduler
    scheduler = Scheduler(
        session=session, 
        config=config, 
        menu=menu,
        captcha=receiver.captcha)

    #Instantiate dispatcher
    dispatcher = Dispatcher(
        session=session,
        config=config,
        menu=menu,
        sch=scheduler,
        rcv=receiver)
    
    #Async flow
    rcv_thread = Thread(target=receiver.run, daemon=True, name='Receiver')
    sch_thread = Thread(target=scheduler.run, args=(dispatcher,), daemon=True, name='Scheduler')
    dsp_thread = Thread(target=dispatcher.run, daemon=True, name='Dispatcher')
    
    rcv_thread.start()
    sch_thread.start()
    dsp_thread.start()

    #Start menu
    menu.run(
        config=config,
        dispatcher=dispatcher,
        profile=receiver.profile,
        scheduler=scheduler,
        threads=[rcv_thread, sch_thread, dsp_thread]
    )
    
    if config.fish_on_exit and menu.rcv_streak > 0:
        cmd, data = scheduler.commands.worker.data
        session.request(command=cmd, parameters=data)
        sleep(3)

    session.disconnect()
    exit(f'\n[!] User exited.')