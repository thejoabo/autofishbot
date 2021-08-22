import requests
import time
import random
import websocket
import json
import threading
import re
import os
import sys
#-------------------- CHANGE HERE --------------------#

#-------------------- IMPORTANT --------------------#
#Change here the channel id that you pretend to play (otherwise the autofish won't "listen" the response)
channelId = "Your channel id here"
#Change here to your authorization token
token = "Your authorization token here"

#-------------------- PREFERENCES --------------------#
#Your preference bait -> 'worms' / 'leeches' / 'magnet' / 'wise bait' / 'fish' / 'artifact magnet' / 'magic bait'
bait = "Worms"
#True / False -> Automaticaly buy fish'x'm, treasure'x'm, sell all your inventory and rebuy baits
buffSwitch = True
#Logs
logCaptcha = False
#For now, leave it in 'n' option, otherwise it breaks the script idk why yet
logMode = 'n' # e -> emotes / f -> full / em -> embeds / ee -> embeds + emotes / n -> don't log
#Your %f cooldown time
cd = 3.5 
#Change the buff 'x' variable -> 5 or 20 (this will be used in the buff autobuy)
boostCd = 20 #in minutes
#Your timezone in UTC format (like: -1 , 3 , 0 ...) -> this will be used to properly display message timestamps 
timezone = 0


#-------------------- DO NOT CHANGE THIS --------------------#
#Default bot UID
botUID = "574652751745777665"
#Calculate how many times you can fish based in your cooldown time until you can buff again
boostValue = round((boostCd*60)/cd)-10
#Calculate how many baits is needed to resuply your last fishing session (last 'x' minutes where 'x' == boostCd)
baitValue = round(boostValue*0.55)
#This is important to randomize your fish time (you can change the '0.15' to 0 if you want, but you probably will get more captchas)
margin = cd + 0.15
#Default counters - DO NOT CHANGE
streak, count, bypassCount = 0, 0, 0
sendsA, sendsB, desyncs = 0, 0, 0
#Clear the console
clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')
#Channel API
channel = "https://discord.com/api/v9/channels/"+channelId+"/messages"
#Authorization token
auth = {'authorization': token}
#Emote list - is used to identify which emotes should be removed, you can add more if you want
emoteList = ['<:chest_artifact:708049330921013271>','<:charm_white:702921289907830814>','<:charm_red:702916693264957501>','<:charm_cyan:702921275458453514>','<:charm_green:702918994465652817>','<:charm_yellow:702919046772817950>','<:charm_blue:702918982943899648>','<:charm_pink:702919025365352520>','<:fb_chest:625008684786909224>','<:chest_legendary:708049312919322651>','<:chest_epic:708049321882550364>','<:chest_uncommon:708057306507771954>','<:chest_rare:708049302131441727>','<:fb_goldfish:625461158475726861>','<:fb_emeraldfish:625462358411837441>','<:fb_diamondfish:625461188418994196>','<:fb_lavafish:659067000735137793>','<:charm_lblue:702919008478953483>']
#Captcha string list, is used in the 'stringOrientation' captcha type
stringsDict = ['add','subtract','adding','subtracting']
#Default message to fish
default = { 'content': "%f" }
#Default message to sell
sell = { 'content': "%s all" }
#Default message to buy baits
baits = { 'content': "%buy "+str(baitValue)+" "+str(bait) }
#Default message to buy More Fish buff
morefish = { 'content': "%buy fish"+str(boostCd)+"m" }
#Default message to buy More Treasure Buff
moretreasure = { 'content': "%buy treasure"+str(boostCd)+"m" }
#Default payload
payload = {
    'op': 2,
    'd': {
        "token": token,
        "properties": {
            "$os": "windows",
            "$browser": "chrome",
            "$device": "pc"
        }
    }
}

#-------------------- AUX FUNCTIONS --------------------#

class StdoutRedirection:
    """Standard output redirection context manager"""
    def __init__(self, path):
        self._path = path

    def __enter__(self):
        sys.stdout = open(self._path, mode="a")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = sys.__stdout__

#
def send_json_request(ws, request):
    ws.send(json.dumps(request))

def recieve_json_response(ws):
    response = ws.recv()
    if response:
        return json.loads(response)

def heartbeat(interval, ws):
    print(">> Starting up...")
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

#this is poorly coded, idk maybe i just add a datetime.now() ?
def makeMessageTimestamp(timestamp):
    tmp = []
    time = timestamp.split("T")
    time = time[1].split(".")
    tmp = time[0].split(":")
    tmp1 = int(tmp[0]) + timezone
    if tmp1 < 0:
        tmp1 = 24 + tmp1
        newTime = str(tmp1)+":"+str(tmp[1])+":"+str(tmp[2])
    else:
        newTime = str(tmp1)+":"+str(tmp[1])+":"+str(tmp[2])
    return newTime

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
                        if tempFix.find("enough") > -1:
                            print("\n[ALERT]",tempFix)
                            return True
                        if tempFix.find("You are already") > -1:
                            print("\n[COOLDOWN]",tempFix)
                            return True
                        if tempFix.find("minutes") > -1:
                            print("\n[SUCESS-BOOST]",tempFix)
                            return True
                        if tempFix.find("sold") > -1:
                            print("\n[SUCESS-SALE]",tempFix)
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
            
            #Removing emote -> i know, this is trash coding, i will rewrite it later 
            line = desc[x].split("<")
            part1 = re.sub(' ','',line[0])
            line = line[1].split(">")
            part2 = re.sub(' ','',line[1])
            print(f"   + {part1} {part2}")
        except:
            pass
        
    #Bottom log message
    print(f"\n[LOG] NOISE: {noise} | TIMESTAMP: {makeMessageTimestamp(timestamp)} | STREAK: {streak} | BYPASSES: {bypassCount} | DESYNCS: {desyncs}\n")

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
    if count > boostValue or count == 0:
        if count == 0:
            time.sleep(cd_B)
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

        

def fish():
    global count, sendsA, desyncs
    clearConsole()
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=6&encording=json')
    event = recieve_json_response(ws)
    heartbeat_interval = event['d']['heartbeat_interval'] / 1000
    threading._start_new_thread(heartbeat, (heartbeat_interval, ws))
    send_json_request(ws, payload)
    time.sleep(1)

    while True:   
        sendsA += 1
        r = requests.post(channel, data=default, headers=auth)
        noise = round(random.uniform(cd, margin), 3)
        checkResponse(ws, noise)
        if not sendsA == sendsB:
            print(f"\n[WARNING] Your client was out of sync, the problem was solved ! (avoid using commands while AutoFish is running)\n")
            desyncs += 1
            checkResponse(ws, noise)
        if buffSwitch:
            reBuff(ws)
        time.sleep(noise)

if __name__ == "__main__":
    while True:  
        try:
            fish()
        except:
            print("GO FUCK YOURSELF")
            sys.exit(1)