# Changelog
##  v1.1.1 - 7/23/21 (current)
#### **Added**
- [diamond fish information](https://github.com/thejoabo/virtualfisher-bot/pull/11) (@yudhistiraindyka)
#### **Changed**
- regex method to handle emotes
- regex method to display balance
#### **Fixed**
- regex pattern to user level on "Inventory" tab (added support to prestige)
- regex patter to display "Level up" information  

##  v1.1.0 - 7/22/21
#### **Added**
- window size detection function
- proper pause/resume function
#### **Changed**
- captcha detection method
- messages alignment (centered)
#### **Fixed**
- messages desyncs (due to unhandled events)
- profile information scraping 

##  v1.0.0 - 7/21/21 
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