# Changelog
## v1.2.1 - 9/5/22 (current)
#### **Added**
- implemented "fish on exit" (auto30m)
- autofish using interactions (buttons and slash commands) ([#29](https://github.com/thejoabo/virtualfisher-bot/issues/29))
- trace to debugger class (and better logs overall)
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
##  v1.2.0 - 7/31/22 
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
- project overall structue (features can now be compartmentalized, config folder, app folder)
- config management method (also, new parameters)
- proper async approach (dispatcher and listener)
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

##  v1.1.1 - 7/23/22 
#### **Added**
- [diamond fish information](https://github.com/thejoabo/virtualfisher-bot/pull/11) (@yudhistiraindyka)
#### **Changed**
- regex method to handle emotes
- regex method to display balance
#### **Fixed**
- regex pattern to user level on "Inventory" tab (added support to prestige)
- regex patter to display "Level up" information  

##  v1.1.0 - 7/22/22
#### **Added**
- window size detection function
- proper pause/resume function
#### **Changed**
- captcha detection method
- messages alignment (centered)
#### **Fixed**
- messages desyncs (due to unhandled events)
- profile information scraping 

##  v1.0.0 - 7/21/22 
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