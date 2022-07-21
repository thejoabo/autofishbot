# Virtual Fisher : Autofish Bot

Auto Fishing Bot made in Python 3 for [Virtual Fisher](https://virtualfisher.com/) discord bot.

## Features
- Auto Fish 
- Anti-bot Bypass
- Auto Buff (more treasures + more fish)

## Demo
![preview](./assets/demo.gif)


## Installation and Usage
Using the terminal, type:
```bash
git clone https://github.com/thejoabo/virtualfisher-bot.git
cd virtualfisher-bot
pip install -r requirements.txt
python autofishbot.py
```

## Customization

You can easily customize the options listed below in the automatically generated ['autofish.config'](assets/autofish.config) file:

```config
[PREFERENCES]
channel_id = YOUR CHANNEL ID
user_token = YOUR TOKEN
ocr_api_key = YOUR API KEY
user_cooldown = YOUR COOLDOWN
bait = WORMS, LEECHES, ...
auto_buff = TRUE
buff_length = 5 / 20
```

## Captcha Information

Virtual Fisher has now removed almost every captcha. The only one left is the image recognition one. They also changed how those images are generated, so **preprocessing is no longer required**. The OCR.SPACE API for image to text recognition seems to work with reasonable consistency in the tests performed. Therefore, to automatically solve captcha you **will need**  an API KEY.

The metodology is pretty straight forward, when a new captcha is detected:
1. An request is sent to the API for each available OCR engine
2. The results are filtered to assert those with reasonable certainty
3. The filtered result list is tested
If all tests fail, a request to regenerate the captcha will be sent (up to 3 times). If everything goes wrong, the bot will halt util you solve it manually.

***Keep in mind that this captcha version is not fully finished yet. I'll be testing new methods of bypassing it.***
- ### How do I get my **FREE** key ?
All you need to do is use [any](https://temp-mail.io/en) email to get it here: https://ocr.space/ocrapi/freekey.

- ### There is any other way to to it **without** the key ?
For now this is the only way. But I'm thinking about the possibility of making a API myself to enable users to redirect their requests through a list of keys.

## Changelog
###  v1.0.0 - 7/19/21 (current)
#### **Added**
- CLI UI (new menu)
- **image recognition (testing phase)**
- safety measures (random noise, command randomization, halt flags)
- user profile (inventory, stats, leaderboards)
- keybinds (pause/play, exit, manual mode)
- multi-threading 
#### **Changed**
- config structure (parameters names)
- captcha detection method
- message handling method
- autobuff routine
#### **Fixed**
- discord webgate interface (connectivity issues)
- unexpected events are now properly handled
- minor text scraping problems

[full changelog here](assets/changelog.md)

## Contributing
- Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
- If you notice any errors, bugs or strange behavior **[PLEASE OPEN AN ISSUE](https://github.com/thejoabo/virtualfisher-bot/issues/new)** containing a screenshot or describing the issue.

