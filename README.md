# Virtual Fisher : Autofish Bot

Auto Fishing Bot made in Python 3 for [Virtual Fisher](https://virtualfisher.com/) discord bot.

## Features
- Auto Fish 
- **Anti-bot Bypass** [[INFORMATION]](https://github.com/thejoabo/virtualfisher-bot#captcha-information)
- Auto Buff (more treasures + more fish)

## Comming soon...
![COMING-SOON](https://media.discordapp.net/attachments/943517334566494219/994439612338536478/unknown.png)

## Demonstration video
[Demo video (CLICK ON THE PIC TO WATCH)](https://www.youtube.com/watch?v=m4MPYnChUJ4): 
[![Demo video](https://i.imgur.com/6sCK3uJ.png)](https://www.youtube.com/watch?v=m4MPYnChUJ4)

## Dependencies
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all required dependencies (you probably already have all of them).

```bash
pip install requests
pip install time
pip install random
pip install websocket-client
pip install json
pip install threading
pip install re
pip install os
pip install sys
pip install datetime
pip install configparser
pip install distutils
```

## Customization
You can easily customize the options listed below in the automatically generated 'autofish.config' file:

```conf
[PREFERENCES]
channelid = Your channel id here
token = Your authorization token here
bait = Your bait preference
buffswitch = true
cooldown = Your cooldown
boostcd = 5
logmode = n
logcaptcha = false
autofish_on_exit = false
```

## Installation and Usage

Using the terminal, type:
```bash
git clone https://github.com/thejoabo/virtualfisher-bot.git
cd /virtualfisher-bot
python release.py
```
## Captcha Information

#### Virtual Fisher has 7 variants (that I know of) of Anti-Bot captchas and currently 6/7 are tested and working:

(btw, ignore 'success' misspelled lol)

#### WORKING:

- #### **[code] in embed** 
- #### **[code] as plain text** 

##### Code: 

```python
codeTest = "Please enter the following code to continue: `Bup9K97c`"
x = codeTest.split(":")
code = x[len(x)-1]
awnser = "%verify "+str(re.sub('[` .*]', '', code))
print(f"\nCode: {awnser}")
#Code: %verify Bup9K97c
```

##### Example:
![POC 1 and 2](https://i.imgur.com/hW1tyu9.png)

##

- #### **[result] in embed** 
- #### **[result] as plain text** 

#### Code:
```python
evalTest = "Please enter the answer to the following problem: `**21 + 9**`."
x = evalTest.split(":")
expression = x[len(x)-1]
expression = re.sub('[` .*]', '', expression)
resp = round(eval(expression))
awnser = "%verify "+str(resp)
print(f"Eval: {awnser}")
#Eval: %verify 30
```
#### Example:
![POC 3 and 4](https://i.imgur.com/OsmO0q2.png)

##

- #### **[stringOrientation] in embed** (E.g.: "User, Please verify by adding the following 2 numbers and subtract the third number: 12 : 8 : 11.")

#### Code:
```python
stringOrientation = "xxxx, Please verify by adding the following 2 numbers and subtract the third number: 12 : 8 : 11."

stringsDict = ['add','subtract','adding','subtracting']
expression = ""
x = stringOrientation.split(" ")
for k in range(len(x)):
    for l in range(len(stringsDict)):
        if x[k] == stringsDict[l]:
            if stringsDict[l].startswith('a'): #add, adding
                order.append('+')
            elif stringsDict[l].startswith('s'): #subtract, subtracting
                order.append('-')
clean = re.sub(r'[^0-9:]+', '', stringOrientation) 
cleanNumbers = clean.split(':')
for x in range(len(cleanNumbers)):
    k = x + 1
    if k > len(order):
        expression += cleanNumbers[k] 
        break
    expression += cleanNumbers[k] + order[x] 
resp = round(eval(expression))
awnser = "%verify "+str(resp)
print(f"StringOrientation: {awnser}")
#StringOrientation: %verify 9
```
#### Example:
![POC 5](https://i.imgur.com/9kV2xvv.png)

##

- #### **[stringOrientation] as plain text** (E.g.: "Please subtract the following 2 numbers: 14, 11.")

#### Code:
```python
content = "Please subtract the following 2 numbers: 14, 11."

stringsDict = ['add','subtract','adding','subtracting']
order = []
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
resp = eval(expression)
awnser = "%verify "+str(resp)
print(f"StringOrientationEmbed: {awnser}")
#StringOrientationEmbed: %verify 3
```
##

## Image Captcha - IN DEVELOPMENT
**The captcha image recognition option is being developed**, I know it would be very easy to just use an API (like Google Vision or Microsoft's Cognitive Services) but the accuracy would still be pretty low for full automation purposes.

So I decided to do a pre-process using an simple AI with weights (like blur, contrast, sharpness, brightness, rotation angle...) on the image and then use [OCR.SPACE](https://ocr.space/) API and [Tesseract](https://pypi.org/project/pytesseract/) for reading the text (it was the best in the tests performed).

#### I'm not releasing the OCR-capable version yet as I don't think it's ready for safe use.

### Below are the pre-processing steps and also the text extracted from the image:
#### - Original file:
![Step 1 - Grayscale](https://i.imgur.com/RehLvf2.png)
#### - Grayscale:
![Step 1 - Grayscale](https://i.imgur.com/Jgth8kT.png)
#### - Rotate + Averaging Blur:
![Step 2 - Rotate + Blur](https://i.imgur.com/iphouUC.png)
#### - Brightness + Sharpness + Contrast:
![Step 3 - Brightness + Sharpness + Contrast](https://i.imgur.com/Jjs001D.png)
#### - OCR.SPACE API ([Matplotlib](https://matplotlib.org/) was used to display rectangle and text on image):
![Step 3 - OCR.API + Matplotlib](https://i.imgur.com/FTPwGh9.png)


## Contributing
- Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
- If you notice any errors, bugs or strange behavior **[PLEASE OPEN AN ISSUE](https://github.com/thejoabo/virtualfisher-bot/issues/new)** containing a screenshot or describing the issue.

