import requests, websocket, threading
import time, random, json
import re, sys, os, datetime
from distutils import util
from configparser import ConfigParser

class StdoutRedirection:
    '''Standard output redirection context manager'''
    def __init__(self, path):
        self._path = path

    def __enter__(self):
        sys.stdout = open(self._path, mode="a")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = sys.__stdout__


#-------------------- CONFIG LOADER --------------------#

def configLoader(param = 'default') -> bool:
    '''Generate and load configuration files'''
    global channelId, token, bait, buffSwitch, cd, boostCd, logMode, logCaptcha, auto30m

    configPath = os.getcwd()+'/autofish.config'

    if(os.path.isfile(configPath) and param == 'default'):
        #Load config
        try:
            config = ConfigParser()
            config.read(configPath)
            cfg = config['PREFERENCES']
            #Config values
            channelId = str(int(cfg['ChannelId'])) #yes, int() first
            token = str(cfg['Token'])
            bait = str(cfg['Bait'])
            cd = float(cfg['Cooldown'])
            buffSwitch = util.strtobool(cfg['BuffSwitch'])
            boostCd = int(cfg['BoostCd']) 
            logCaptcha = util.strtobool(cfg['LogCaptcha'])
            logMode = str(cfg['LogMode'])
            auto30m = util.strtobool(cfg['autofish_on_exit'])
            return True
        except:
            #Call config loader in "create new config" mode 
            configLoader('force')
    else:
        if param == 'force':
            print('\nConfiguration information doesn\'t follow the expected format.')
        
        #Create new config
        newConfig = ConfigParser()
        newConfig['PREFERENCES'] = {
                'ChannelId' : 'Your channel id here',
                'Token' : 'Your authorization token here',
                'Bait' : 'Your bait preference',
                'BuffSwitch' : 'true',
                'Cooldown' : 'Your cooldown',
                'BoostCd' : 5,
                'LogMode' : 'n',
                'LogCaptcha': 'false',
                'autofish_on_exit': 'false'
        }
        try:
            with open(configPath, 'w') as f:
                newConfig.write(f)
            print("\nConfig created ! You need to set your channel and token to continue.")
            wasntCreated = True
            if sys.platform == 'linux':
                os.system('gedit autofish.config')
            elif sys.platform == 'darwin':
                os.system('open -a TextEdit autofish.config')
            elif sys.platform == 'win32':
                os.system('notepad.exe autofish.config')
            else:
                print(f"\nPlease, edit it here: {configPath}")
        except:
            if wasntCreated:
                print("\nUnable to create new config, try again.")
        finally:
            sys.exit(1)



#-------------------- AUX FUNCTIONS --------------------#

def send_json_request(ws, request):
    ws.send(json.dumps(request))

def recieve_json_response(ws):
    response = ws.recv()
    if response:
        return json.loads(response)

def heartbeat(interval, ws):
    while True:
        time.sleep(interval)
        heartbeatJSON = {
            "op": 1,
            "d": "null"
        }
        send_json_request(ws, heartbeatJSON)
        #print("Debug >> Heartbeat sent")

def logRaw(event, mode):
    if mode == 'e' or mode == 'f' or mode == 'ee':
        if not event['embeds'] == []:
            if event['embeds'][0]['description'].find("fb_") > -1:
                with StdoutRedirection("emotes.txt"):
                    print(re.sub('[\n]',' , ',event['embeds'][0]['description']))
                    return True
    if mode == 'f':
        with StdoutRedirection("logs.txt"):
            print(event)
    if mode == 'em' or mode == 'f':
        with StdoutRedirection("embeds.txt"):
            print(event['embeds'][0])
    if mode == 'c' or mode == 'f':
        with StdoutRedirection("captchas.txt"):
            print(event)

def makeMessageTimestamp() -> str:
    '''Simple datetime function'''
    return datetime.datetime.now().strftime('%H:%M:%S')

def messagePrettify(message, param) -> str:
    text = ""
    
    if param == 'enough':
        tmp = message.split(' ')
        # :x: You don't have enough :fb_emeraldfish:.
        for x in range(1, len(tmp)):
            if tmp[x].find('fb_') < 0:
                text += tmp[x] + " "
            else:
                if tmp[x].find('emerald') > -1:
                    text += 'Emerald Fish.'
                else:
                    text += 'Gold Fish.'
        return text
    
    if param == 'already':
        # You are already boosting that! Time left: 16m 3s
        return message
    
    if param == 'minutes':
        #:white_check_mark: You will now catch more fish for the next 5 minutes.
        tmp = message.split(' ')
        tmp.remove(tmp[0])
        text = ' '.join(tmp)
        return text
    
    if param == 'sold':
        # :white_check_mark: You sold your entire inventory for $92.\nYou now have $23,426!
        values = []
        tmp = message.split('\n')
        for x in range(len(tmp)):
            values.append(re.sub(r'[^0-9$,]', '', tmp[x]))
        text = f'You sold your inventory for {values[0]}. Account balance: {values[1]}.'
        return text
        



def checkResponse(ws, noise = 0):
    while True:
        event = recieve_json_response(ws)
        try:
            if event['d']['channel_id'] == channelId:
                if event['d']['author']['id'] == botUID:
                    
                    #Logs the event -> disabled for now
                    #logRaw(event['d'], logMode)
                    
                    #Anti-Bot Bypasser       
                    if antiBotBypass(event, ws):
                        tempFix = event['d']['embeds'][0]['description']
                        tempFix = re.sub('[*`|]', '', tempFix)
                        
                        #Boost messages
                        if tempFix.find('enough') > -1:
                            print("\n[ALERT]", messagePrettify(tempFix, 'enough'))
                            return True

                        if tempFix.find("You are already") > -1:
                            print("\n[COOLDOWN]", messagePrettify(tempFix, 'already'))
                            return True

                        if tempFix.find("minutes") > -1:
                            print("\n[SUCESS-BOOST]", messagePrettify(tempFix, 'minutes'))
                            return True

                        if tempFix.find("sold") > -1:
                            print("\n[SUCESS-SALE]",  messagePrettify(tempFix, 'sold'))
                            return True

                        if event['d']['embeds'][0]['title'] == "Bait purchase":
                            text = tempFix.split('$')
                            text = text[1].split('.')
                            print(f"\n[SUCESS-BAIT] You bought {baitValue} {bait} for ${text[0]}")
                            return True
                        
                        #Assignment
                        title = event['d']['embeds'][0]['title']
                        description = event['d']['embeds'][0]['description']
                        timestamp = event['d']['timestamp']
                        content = event['d']['content']
                        
                        #Default message
                        if title == "You caught:":
                            try:
                                successMessage(description,noise,timestamp)
                                return True
                            except:
                                #print("\n[LEVEL UPGRADED]\n")
                                return True    

                        #Redundant anti-bot checker
                        if content ==  "You may now continue.":
                            return True
                        
                        #Any other message, like inventory or some shit like that - this will change later
                        return True
                    else:
                        print("wrong captcha ?")
                        #You can uncomment the line bellow if you are paranoid, but it will wait until you answer the captcha correctly before continuing to send new messages
                        #Once you have answered the captcha correctly, manually type '%f' into the discord channel and it will automatically start sending new messages again
                        #sys.exit(1) 
        except:
            #print('f')
            pass


#------------------------ IMPORTANT --------------------------#
'''
I'll rewrite some parts of this function when I have more time. 
  The way it is does't' change performance, some messages like 
"Daily quests" or "Level up" are not displayed yet, the problem 
            will be fixed in the next updates
'''
def successMessage(description, noise, timestamp):
    global streak, sendsB
    streak += 1
    sendsB += 1
    desc = description.split("\n")
    
    print("\n[SUCCESS] YOU CAUGHT:\n")
    for x in range(len(desc)):
        alreadyFound = False
        
        #Chests and Crates
        if desc[x].find('chest') > -1 or desc[x].find('crate') > -1 or desc[x].find('charm') > -1:
            tmp = desc[x]
            tmp = tmp.split(" ")
            for k in range(len(tmp)):
                for j in range(len(emoteList)):
                    if str(re.sub('[!.*]','',tmp[k])).find(emoteList[j]) > -1 :
                        text = ""
                        for n in range(len(tmp)):
                            if not tmp[n] == tmp[k]:
                                text += tmp[n]+" "
                        alreadyFound = True
                        break     
                    else:
                        text= desc[x]
                if alreadyFound:
                    break
            text = re.sub('[*!.]', '', text)
            print(f"   + {text}")

        #XP
        if desc[x].startswith('+'):
            text = re.sub("[\+]", '', desc[x])
            print(f"   + {text}")

        #Fishes
        try:
            tmp = desc[x].split(" ")
            tmp = int(tmp[0]) #if it is not a message related to catching fish, it stops here 
            
            #Removing emote -> i will rewrite it later 
            line = desc[x].split("<")
            part1 = re.sub(' ','',line[0])
            line = line[1].split(">")
            part2 = re.sub(' ','',line[1])
            print(f"   + {part1} {part2}")
        except:
            pass
        
    #Bottom log message
    print(f"\n[LOG] NOISE: {noise} | TIMESTAMP: {makeMessageTimestamp()} | STREAK: {streak} | BYPASSES: {bypassCount} | DESYNCS: {desyncs}\n")

def checkBotConfirmation(ws, awnser, log):
    global bypassCount, sendsB

    #Send captcha awnser
    r = requests.post(channel, data={'content': awnser}, headers=auth)
    
    # if logCaptcha == True: -> DISABLED FOR NOW
    #     logRaw(log, 'c')

    while True:
        event = recieve_json_response(ws)
        try:
            if event['d']['channel_id'] == channelId:
                if event['d']['author']['id'] == botUID:
                    content = event['d']['content']
                    if content == "You may now continue.":
                        print("[ALERT] ANTI-BOT SYSTEM HAS BEEN BYPASSED -> RESULT: "+ awnser)
                        bypassCount += 1
                        sendsB += 1
                        return True
                    return False
        except:
            #print('f')
            pass

def antiBotBypass(event, ws):
    '''Identifies and solves captcha problems'''
    code = ""
    order = []

    if event['d']['embeds'] == []:

        #------------------- CONTENT SEGMENT --------------------------#
        content = event['d']['content']
        
        #Checks for image captcha variant
        if content.find('captcha.php') > -1:
            '''
                                IN DEVELOPMENT
                                    PLEASE
                                     READ
                                    READ.ME
            '''
            print("\n\n[WARNING] IMAGE RECOGNITION CAPTCHA IS REQUIRED\n\n")
            return False

        #Checks for <code> variant
        if content.find('<code>') > -1:
            x = content.split(":")
            code = x[len(x)-1]
            awnser = "%verify "+str(re.sub('[` .*]', '', code))
            if checkBotConfirmation(ws, awnser, event['d']) == True:
                return True
            return False

        #Checks for <result> variant
        if content.find('<result>') > -1:
            expression = ""
            x = content.split(":")
            expression = x[len(x)-1]
            expression = re.sub('[` .*]', '', expression)
            resp = round(eval(expression))
            awnser = "%verify "+str(resp)
            if checkBotConfirmation(ws, awnser, event['d']) == True:
                return True
            return False
      
        #Checks for strings orientations variant
        for x in range(len(stringsDict)):
            if content.find(stringsDict[x]) > -1:
                expression = ""
                x = content.split(" ")
                for k in range(len(x)):
                    for l in range(len(stringsDict)):
                        if x[k] == stringsDict[l]:
                            if stringsDict[l].startswith('a'):
                                order.append('+')
                            else:
                                order.append('-')
                clean = re.sub(r'[^0-9:]+', '', content) 
                cleanNumbers = clean.split(':')
                for x in range(len(cleanNumbers)):
                    k = x + 1
                    if k > len(order):
                        expression += cleanNumbers[k]
                        break
                    expression += cleanNumbers[k] + order[x] 
                resp = round(eval(expression))
                awnser = "%verify "+str(resp)
                if checkBotConfirmation(ws, awnser, event['d']) == True:
                    return True
                return False
            
        #Not a captcha message
        return True
        
    else:
        #------------------- EMBED SEGMENT --------------------------#
        try:
            title = event['d']['embeds'][0]['title']
        except:
            title = "none"
        content = event['d']['embeds'][0]['description']
          
        #Checks for <code> in embed variant
        if title.find("<code>") > -1:
            x = content.split(":")
            code = x[len(x)-1]
            awnser = "%verify "+str(re.sub('[` .*]', '', code))
            if checkBotConfirmation(ws, awnser, event['d']) == True:
                return True
            return False
        
        #Checks for <result> eval embed variant
        if title.find("<result>") > -1:
            expression = ""
            x = content.split(":")
            expression = x[len(x)-1]
            expression = re.sub('[` .*]', '', expression)
            resp = round(eval(expression))
            awnser = "%verify "+str(resp)
            if checkBotConfirmation(ws, awnser, event['d']) == True:
                return True
            return False

        #Checks for string orientation with weird pattern
        if title == "Anti-bot" and content.startswith("Please"):
            expression = ""
            numbers = content.split(":")
            numbers =  re.sub('[ .]', '', numbers[len(numbers)-1])
            for k in range(len(stringsDict)):
                if content.find(stringsDict[k]) > -1:
                    if stringsDict[k].startswith("a"):
                        operator = "+"
                    if stringsDict[k].startswith("s"):
                        operator = "-"
            expression  = re.sub('[,]', operator, numbers)
            resp = round(eval(expression))
            awnser = "%verify "+str(resp)
            if checkBotConfirmation(ws, awnser, event['d']) == True:
                return True
            return False

        #Not a captcha message    
        return True

def reBuff(ws):
    global count
    cd_B = 2 #You can change this if you want, not too low tho

    if count >= boostValue or count == 0:
        count = 1
        
        #More fish for 'x' minutes
        r = requests.post(channel, data=morefish, headers=auth)
        checkResponse(ws)
        time.sleep(cd_B)
        
        #More treasures for 'x' minutes
        r = requests.post(channel, data=moretreasure, headers=auth)
        checkResponse(ws)
        time.sleep(cd_B)
        
        #Sell all itens
        r = requests.post(channel, data=sell, headers=auth)
        checkResponse(ws)
        time.sleep(cd_B)
        
        #Rebuy small amount of baits
        r = requests.post(channel, data=baits, headers=auth)
        checkResponse(ws)
        return True
    else:
        count += 1
        return True

        

def autoFish(param = None):
    global count, sendsA, desyncs
    
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=6&encording=json')
    event = recieve_json_response(ws)
    heartbeat_interval = event['d']['heartbeat_interval'] / 1000
    threading._start_new_thread(heartbeat, (heartbeat_interval, ws))
    send_json_request(ws, payload)
    time.sleep(1)

    #Legit Autofish for 30 minutes
    if param == 'auto30m':
        print("\n[ALERT] You will fish for the next 30 minutes.")
        r = requests.post(channel, data={ 'content': '%buy auto30m' }, headers=auth)
        checkResponse(ws, 0)

    while True:   
        sendsA += 1
        noise = round(random.uniform(cd, margin), 3)
        
        #Default message
        r = requests.post(channel, data=default, headers=auth)
        checkResponse(ws, noise)

        #Checks for unsync messages, important to properly identify captcha messages
        if not sendsA == sendsB:
            print(f"\n[WARNING] Your client was out of sync, the problem was solved ! (avoid using commands while AutoFish is running)\n")
            desyncs += 1
            checkResponse(ws, noise)
        
        #Auto buys temporary boosts
        if buffSwitch:
            reBuff(ws)

        #Cooldown time to prevent flood
        time.sleep(noise)

if __name__ == "__main__":
    if configLoader():
        #Default Bot Id
        botUID = "574652751745777665"
        #Channel API
        channel = "https://discord.com/api/v9/channels/"+channelId+"/messages"
        #Calculate how many times you can fish based in your cooldown time until you can buff again
        boostValue = round((boostCd*60)/cd)-10
        #Calculate how many baits is needed to resuply your last fishing session (last 'x' minutes where 'x' == boostCd)
        baitValue = round(boostValue*0.55)
        #This is important to randomize your fishing time (you can change the '0.25' to 0 if you want, but you probably will get more captchas)
        margin = cd + 0.25
        
        #Default counters
        streak, count, bypassCount = 0, 0, 0
        sendsA, sendsB, desyncs = 0, 0, 0
        
        #Clear the console
        clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')
        
        #Authorization token
        auth = {'authorization': token}
        
        #Emote list - is used to identify which emotes should be removed, you can add more if you want
        emoteList = ['<:chest_artifact:708049330921013271>','<:charm_white:702921289907830814>','<:charm_red:702916693264957501>','<:charm_cyan:702921275458453514>','<:charm_green:702918994465652817>','<:charm_yellow:702919046772817950>','<:charm_blue:702918982943899648>','<:charm_pink:702919025365352520>','<:fb_chest:625008684786909224>','<:chest_legendary:708049312919322651>','<:chest_epic:708049321882550364>','<:chest_uncommon:708057306507771954>','<:chest_rare:708049302131441727>','<:fb_goldfish:625461158475726861>','<:fb_emeraldfish:625462358411837441>','<:fb_diamondfish:625461188418994196>','<:fb_lavafish:659067000735137793>','<:charm_lblue:702919008478953483>']
        
        #Captcha string list, is used in the 'stringOrientation' captcha type
        stringsDict = ['add','subtract','adding','subtracting']
        
        #Default message to fish, sell and buy
        default = { 'content': '%f' }
        sell = { 'content': '%s all' }
        baits = { 'content': f'%buy {str(bait).lower()} {baitValue}' }
        
        #Default message to buy More Fish and More Treasure buffs 
        morefish = { 'content': "%buy fish"+str(boostCd)+"m" }
        moretreasure = { 'content': "%buy treasure"+str(boostCd)+"m" }
        
        #Default payload
        payload = {
            'op': 2,
            'd': { 
                'token': token,
                'properties': { 
                    #No need to change these, but you can if you want
                    '$os': 'windows',
                    "$browser": 'chrome',
                    '$device': 'pc'
                }
            }
        }

        #This loop prevents from raise error when losing connection
        while True:  
            try:
                autoFish()
            except:
                try:
                    #Autofish on exit switch only using 'CTRL + C'
                    if auto30m:
                        autoFish('auto30m')
                except:
                    print("Err")
                print("\nConnection Lost\n")
                sys.exit(1) #Comment this line if you want to continue even after the connection is lost