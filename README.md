# Virtual Fisher : Autofish Bot
Auto Fishing Bot made in Python 3 for [Virtual Fisher](https://virtualfisher.com/) Discord bot.

## Features
- Auto Fish 
- CLI UI (Menu)
- [Captcha Bypass](#captcha-information)
- Auto Buff (more treasures + more fish)
- Interactions (buttons and slash commands)

## Notice
Unknown ban detection method has been reported, please see [#38](https://github.com/thejoabo/virtualfisher-bot/issues/38). USE IT AT YOUR OWN RISK !

## Demo
![demo](assets/images/demo.gif)


## Installation and Update
Using the terminal, type:
```bash
git clone https://github.com/thejoabo/virtualfisher-bot.git
cd virtualfisher-bot
pip install -r requirements.txt
```

## Usage
Using the terminal, in the repository folder, type:
```bash
python autofishbot.py
```
**Note:** *On the first start up, the bot will ask you to fill the configuration file name (which will be stored at 'configs/' folder). After setting everything up, run the command again. In case of several config files you will be prompted to choose one. [More help](assets/faq.md) | [Template](assets/template.config).*

## Customization

You can easily customize the options listed below in the automatically generated [config file](assets/template.config):

```config
#Example
[PREFERENCES]
CHANNEL_ID = 123456
USER_TOKEN = M@yToke_n123
OCR_API_KEY = MyK!ey12.3
USER_COOLDOWN = 3.5
BAIT = WORMS
AUTO_BUFF = TRUE
BUFF_LENGTH = 5
FISH_ON_EXIT = FALSE
COMPACT_MODE = FALSE
DEBUG = FALSE
NUMBER_FORMATTING = DEFAULT
```
*Detailed information [here](assets/faq.md).*


## Captcha Information
Virtual Fisher has now removed almost every captcha. The only one left is the image recognition one. They also changed how those images are generated, so **preprocessing is no longer required**. The OCR.SPACE API for image to text recognition seems to work with reasonable consistency in the tests performed. Therefore, to automatically solve captchas you **will need** an [API KEY](#how-do-i-get-my-free-key-).

The metodology is pretty straight forward, when a new captcha is detected:

1. A request is sent to the API for each available OCR engine
2. The results are filtered to assert those with reasonable certainty
3. The filtered result list is tested
If all tests fail, a request to regenerate the captcha will be sent (up to 3 times). If everything goes wrong, the bot will halt util you solve it manually.

Keep in mind that the captcha detection method  is not flawless, unexpected events can cause some unusual behavior that could influence detection accuracy. Therefore, it should not be left alone without monitoring for longer periods of time.
### Demo (normal)
![captcha-demo](assets/images/captcha-demo.gif)
*(the current step is outputed on the top, 1.5x speed)*

### Demo (with wrong code)
![captcha-demo-wrong-code](assets/images/captcha-with-wrong-code.gif)
*(the current step is outputed on the top, 1.5x speed)*

- ### HOW DO I GET MY **FREE** KEY ?
All you need to do is use [any](https://temp-mail.io/en) email to get it here: https://ocr.space/ocrapi/freekey.

- ### THERE IS ANY OTHER WAY TO DO IT **WITHOUT** THE KEY ?
For now this is the only way. But I'm thinking about the possibility of make an API myself to enable users to redirect their requests through a list of keys.

*[Need more help ?](assets/faq.md#how-do-i-get-my-ocrapikey-)*


## Changelog
### v1.2.1 - 9/5/22 (current)
#### **Added**
- implemented "fish on exit" (auto30m)
- autofish using interactions (buttons and slash commands) ([#29](https://github.com/thejoabo/virtualfisher-bot/issues/29))
- trace to debugger class (and better log overall)
#### **Changed**
- discord's API wrapper
  -  requests 
  -  webgate identification
  -  headers and authorization
  -  session and nonce (snowflake) functions
- requests error handling
- message class (support to interactions and compartmentalization)
- autobuff function (command list and stalling conditions)
- dispatcher/receiver functions
#### **Fixed**
- OCR's request timeout (25 seconds) for engines 3 and 5
- config manager (strings are now sanatized)
- minor source code typos
...

[FULL CHANGELOG HERE](assets/changelog.md)


## Contributing
- Pull requests are welcome. For major changes, open an issue first to discuss what you would like to change.
- If you notice any errors, bugs or strange behavior **[PLEASE OPEN AN ISSUE](https://github.com/thejoabo/virtualfisher-bot/issues/new)** containing a screenshot or describing the problem.
- [**Suggestions**](https://github.com/thejoabo/virtualfisher-bot/discussions/new) are welcome.

