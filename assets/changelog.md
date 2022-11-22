# Changelog
<!-- ## v0.0.0 - x/x/22
### **Added**
### **Changed**
### **Fixed** -->
## experimental-2.0.0 - 11/20/22 (current)
#### **Added**
- added **Scheduler** class ([#38]([#38](https://github.com/thejoabo/autofishbot/issues/38))) - experimental
  - Allows slash commands to be sent using keybinds
  - Creates, controls and pseudo-randomizes automation routines (boosts and auto_* features) → attempts to mimic human behavior
  - Sporadically mid-session 'break time'
- **DiscordWrapper** new features
  - added **Proxy** class integration
    - native proxy support (**HTTPS only**)
  - session reconnections
- **Menu** new features
  - **BaseMenu**
    - support for custom keybinds ('*./app/keybinds.json*') by **Keybinder** class
    - CPU and Memory consumption reduced - better logic and structure overall (removed redundant calculations and  function calls, simplification, +)
    - asynchronous notifications 'server' (threaded) → notifications are now queued and have priority and display time
    - 'Config Status' panel split in 'App info' and 'Config Status' (with better choices of information to be displayed)
    - **Popup** widget → extra information (like quests, exotic fishes, current inventory, charms and buffs) can be viewed in a popup format (see example) 
  - **MainMenu(BaseMenu)** - "normal" mode
    - design changes ([see comparison](https://imgur.com/a/tQSEXG3))
    - screen strings are now resized dynamically to fit the terminal size
    - added the Leaderboards panel
    - added more profile information to the Inventory panel
    - better exceptions handling 
  - **CompactMenu(BaseMenu)** - compact mode
    - minor design changes ([see comparison](https://imgur.com/a/tsIcg5O))
    - better exceptions handling 
- **ConfigManager** new features
  - argument support for loading specific configs  (e.g. ```python autofishbot.py some_config_name```) (adaptation of @notvirtio 's solution [#51](https://github.com/thejoabo/autofishbot/pull/51))
  - support for the creation of new (alt) configs using arguments (```python autofishbot.py --create```)
  - new parameters:
    - Network: ```proxy_ip```, ```proxy_port```, ```proxy_auth_user```, ```proxy_auth_password```, ```user_agent```
    - Automation:
      - added ```auto_sell```, ```auto_buy_baits```, ```auto_update_inventory```, ```auto_daily```
      - splitted ```auto_buff``` in ```more_fish``` and ```more_treasures```
      - renamed ```buff_length``` to ```boosts_length```
    - Menu: ```refresh_rate```
    - Cosmetic: ```pet```, ```bait```, ```biome``` (**not yet implemented**)
- **Profile** new features
  - support to charms inventory (*/charms*) + **Charms** datatype class
  - support to user leaderboards (*/pos*) + **Leaderboard** datatype class
  - support to buffs (multipliers list) (*/buffs*) + **Buffs** datatype class
  - support to quests list (*/quests*) + **QuestList** and **Quest** datatype class
#### **Changed**
- refactored **DiscordWrapper** class
  - discord's API (v9 → v10)
  - *connect* function's structure
  - heartbeat routine (adjusting to documentation requirements)
  - *receive_event* function (better error management and pre deserialization)
  - application commands and guild ID are now loaded on start-up
  - *request* function (discord's HTTP API requests):
    - simplification and better data structure
    - better handling of exceptions (and proper returns)
    - better error management to failure requests
    - proper handling of discord's rate limits (429 error) (improvement of @gabeaventh 's solution [#36](https://github.com/thejoabo/autofishbot/pull/36))
- refactored **Captcha** class
  - compartmentalization
  - multi-threading solving (asynchronous ocr-engine requests) → each engine request is made simultaneously, so captcha solving time is significantly faster.
  - captcha detection function (added conditional safeguards)
  - status flags (ensuring transparency of actions for external classes)
- *message_dispatcher* function converted to **Dispatcher** class
  - improvements in conditional gates to send commands (safer method)
  - "**pause**" property, to globally pause the dispatcher (instead of a standalone class)
  - improvements in sending captcha-related commands 
  - improvements in cooldown calculations (to consider for network ping between requests oscillations/processing time, in order to preserve the Gaussian approach of value generation)
- *message_receiver* function converted to **Receiver** class
  - better event checking, parsing and validation
  - simplification (removed unnecessary event validation, improvements in code structure, +)
  - improvements in messages categorization
  - untitled (and unhandled) messages are now properly sanitized and displayed on notifications
  - better logic to detect captchas in raw events
  - incorrect captcha code messages are now treated
  - added of more breakpoints conditionals (in case of abnormal behavior)
- refactored **Profile** class
  - compartmentalization
  - attribute fields (instead of a global fixed list)
  - lists (displayed on menu) are now constructed individually per attribute (datatype classes) using the *list* property
  - *update* function 
  - gold, diamond, emerald and lava fishes are now grouped to **ExoticFish** class
- refactored **CooldownManager** class
  - simplification
  - analysis functions removed
- refactored **Message** class
  - better message parsing and fields categorization
  - untitled and contentless message are now handled
- refactored **ConfigManager** class
  - better loading/saving logic of config files
  - compartmentalization of config parameters (system, captcha, network, automation, menu and cosmetic)
  - better value parsing and validation
- refactored **Debugger** class
  - simplification
  - outputs errors and exceptions to 'debug.log' file instead of displaying them on terminal
- **PauseControl** class removed (integrated in **Dispatcher** class)
-  **MenuManager** class removed (split in **BaseMenu**, **MainMenu(BaseMenu)**, **CompactMenu(BaseMenu)** classes)
- *autoBuff* function removed (integrated in **Scheduler** class)
#### **Fixed**
- fixed a bug in which the *sanitize* function in Message class couldn't parse some characters
- fixed a bug in which  required fields weren't validated in ConfigManager ([#48](https://github.com/thejoabo/autofishbot/issues/48))
- fixed a bug in which captcha.regen counter were redefined after solution failure
- fixed a bug in which the bait name overlaps the border in compact mode - inventory (and related information) can be viewed separately on a popup using their respective keybinds ([#50]([#50](https://github.com/thejoabo/autofishbot/issues/50)))
- fixed a bug in which the curses kept blinking on screen's last update position



## 1.2.1 - 9/5/22
#### **Added**
- implemented "fish on exit" (auto30m)
- autofish using interactions (buttons and slash commands) ([#29](https://github.com/thejoabo/virtualfisher-bot/issues/29))
- trace to debugger class (and better logs overall)
#### **Changed**
- discord's API wrapper
  -  requests 
  -  Webgate identification (passport)
  -  headers and authorization
  -  session and nonce (snowflake) functions
- requests error handling
- message class (support to interactions and compartmentalization)
- autobuff function (command list and stalling conditions)
- dispatcher/receiver functions
#### **Fixed**
- OCR's request timeout (25 seconds) for engines 3 and 5
- config manager (strings are now sanitized)
- minor source code typos
##  1.2.0 - 7/31/22 
#### **Added**
- support to multiple configuration files
- support to third-party (custom) menus - experimental
- debugger class (using inspector package)
- pause/resume class
- compact mode ([#23](https://github.com/thejoabo/virtualfisher-bot/discussions/23), [#15](https://github.com/thejoabo/virtualfisher-bot/issues/15) )
- resize function for messages and notifications (to avoid errors when strings > terminal width)
- FAQ to config parameters
#### **Changed**
- discord webgate (connectivity issues, compartmentalization)
- cooldown method - normal distribution ([#12](https://github.com/thejoabo/virtualfisher-bot/discussions/12))
- project overall structure (features can now be compartmentalized, config folder, app folder)
- config management method (also, new parameters)
- proper asynchronous approach (dispatcher and listener)
- all menus are now parts of a class (MenuManager)
- imports (external packages limitation)
- captcha detection method ([#14](https://github.com/thejoabo/virtualfisher-bot/issues/14))
- calculations for menu dimensions and proportions
#### **Fixed**
- sanitized normal emotes (@yudhistiraindyka [#22](https://github.com/thejoabo/virtualfisher-bot/pull/22), [#20](https://github.com/thejoabo/virtualfisher-bot/issues/20))
- multiple embeds handling for profile functions
- pause function argument handling 
- autobuff/resupply function queries  
- captcha regen when all results fail ([#14](https://github.com/thejoabo/virtualfisher-bot/issues/14))
- captcha timeout limit to check for confirmation messages
- captcha answer duplicates are now ignored
- captcha safe-exit methods when abnormal behavior is found
- config manager class (proper exceptions handling, minor compatibility issues)
- reduced memory consumption while paused
- stalling conditions for the dispatcher (while captcha detected or autofish is paused)
- curses exceptions handling (addwstr() type errors) ([#21](https://github.com/thejoabo/virtualfisher-bot/issues/21))

##  1.1.1 - 7/23/22 
#### **Added**
- [diamond fish information](https://github.com/thejoabo/virtualfisher-bot/pull/11) (@yudhistiraindyka)
#### **Changed**
- regex method to handle emotes
- regex method to display balance
#### **Fixed**
- regex pattern to user level on "Inventory" tab (added support to prestige)
- regex patter to display "Level up" information  

##  1.1.0 - 7/22/22
#### **Added**
- window size detection function
- proper pause/resume function
#### **Changed**
- captcha detection method
- messages alignment (centered)
#### **Fixed**
- messages desyncs (due to unhandled events)
- profile information scraping 

##  1.0.0 - 7/21/22 
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