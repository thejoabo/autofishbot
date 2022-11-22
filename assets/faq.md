<h1 align='center'>AFB'S CONFIG GUIDE</h1>

### Table of contents:
<!-- no toc -->
- SYSTEM
  - [USER_TOKEN *](#user_token)
  - [USER_COOLDOWN *](#user_cooldown)
  - [CHANNEL_ID *](#channel_id)
  - [DEBUG](#debug)
- CAPTCHA
  - [OCR_API_KEY *](#ocr_api_key)
- NETWORK
  - [USER_AGENT](#user_agent)
  - [PROXY_IP & PROXY_PORT](#proxy_ip--proxy_port)
  - [PROXY_AUTH_USER & PROXY_AUTH_PASSWORD](#proxy_auth_user--proxy_auth_password)
- AUTOMATION
  - [BOOSTS_LENGTH](#boosts_length)
  - [MORE_FISH & MORE_TREASURES](#more_fish--more_treasures)
  - [FISH_ON_EXIT](#fish_on_exit)
  - [AUTO_DAILY](#auto_daily)
  - [AUTO_BUY_BAITS](#auto_buy_baits)
  - [AUTO_SELL](#auto_sell)
  - [AUTO_UPDATE_INVENTORY](#auto_update_inventory)
- MENU
  - [COMPACT_MODE](#compact_mode)
  - [REFRESH_RATE](#refresh_rate)
- COSMETIC
  - [BAIT](#bait)
  - [PET & BIOME](#pet--biome) 

*required \**
# <h3 align='center'>USER_TOKEN *</h3><br>

The **USER_TOKEN** parameter stands for the **string** value used to properly authenticate you on Discord's servers and correctly send/receive new events assigned to this token.

To get it, you will need to:
1. Log in the desired Discord account on any **browser**
2. With your account open, in the Discord's page, **press F12** (to open *Developer Tools*)
3. On the top middle, click on the "**Storage**" button (or press SHIFT + F9 on the developer menu)
4. On right the sidebar, click on the "**Local Storage**" option, then click on the **Discord's URL** option.
5. After that, on the top middle, **type** "*token*" on the filter search bar.
6. Look for the exact key name matching the keyword "*token*", then copy that key's value and paste it in the **USER_TOKEN** parameter.

Video guide (from 'Gauging Gadgets' channel): https://www.youtube.com/watch?v=YEgFvgg7ZPI

**Note**: the user token is a very sensitive information, therefore should not be shared with anyone. This program does NOT collect any kind of data, all information is stored locally on your computer. All the requests made for Discord's API and gateway uses **HTTPS** by default. 

# <h3 align='center'>USER_COOLDOWN *</h3><br>

The **USER_COOLDOWN** parameter stands for the **float** value (ranging from ```2.0``` to ```3.5```) used to delay the command's sending rate, for deeper information see the discussion [here](https://github.com/thejoabo/virtualfisher-bot/discussions/12).

To find your cooldown, you will need to:
1. Go to a channel in which the Virtual Fisher bot has access to
2. Send the '**/buffs**' command
3. Copy the number that stands for the '[Fishing cooldown](https://i.imgur.com/xpAHap7.png)'

# <h3 align='center'>CHANNEL_ID *</h3><br>

The **CHANNEL_ID** parameter stands for the **integer** identifier value of a channel on Discord, it's used for filtering which events should be analyzed to compose the messages displayed on your screen.

To get it, you will need to:
- Enable "Developer Mode" option on Discord ([*User Settings → Advanced → Enable Developer Mode*](https://img001.prntscr.com/file/img001/NzQmu739QQe5E6UmetJadA.png)).
- Right-click on the channel of your preference, then [click on the '**Copy ID**' button](https://img001.prntscr.com/file/img001/dcwjC6w9TzuTv4sMmyfbzw.png).

**Note**: is strongly recommended that you use a private channel to do so (if you use a public channel in which multiple people are playing at the same time, message track will be lost, leading to eventual captcha misses or detecting other user's captcha events).

# <h3 align='center'>DEBUG</h3><br>

The **DEBUG** parameter stands for the **boolean** value used to log back-end information about exceptions and errors. The purpose of this setting is to help users draw up an [issue](https://github.com/thejoabo/virtualfisher-bot/issues/new) report by including debugging information to determine where and why the error occurred.

**Note**: all debug information is outputted to '```{autofishbot directory}/app/debug.log```' file.

# <h3 align='center'>OCR_API_KEY *</h3><br>

The **OCR_API_KEY** parameter stands for the **string** value used to authorize your request to the [OCR.SPACE](https://ocr.space/) API (see the documentation [here](https://ocr.space/OCRAPI)).

To get it, you will need to:
- Go to the free registration page: https://ocr.space/ocrapi/freekey
- Fill in the requested information (all information except the email is optional), then click on the "**Subscribe**" button.
- After that, check your email for a subscription confirmation, then click on the "**YES, SUBSCRIBE ME TO THE FREE OCR API LIST.**" button. Once you confirmed your email address, you will receive a second email with your personal API key.
- Finally, refresh your inbox and find the email containing your API KEY. 

**Note**: for any remaining questions, see their [FAQ](https://ocr.space/faq) and [forum](https://forum.ui.vision/c/ocr-api/10).

# <h3 align='center'>USER_AGENT</h3><br>

The **USER_AGENT** parameter stands for the **string** value used to compose your request headers. By default, it uses ```'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'```. 

**Note**: for changing this value, you can check for valid user agents [here](https://developers.whatismybrowser.com/useragents/explore/software_type_specific/web-browser/).

# <h3 align='center'>PROXY_IP & PROXY_PORT</h3><br>

The **PROXY_IP** (**string**) and **PROXY_PORT** (**integer**) parameters stands for the values used to set up a proxied connection between the user and Discord's servers. Due to multiple issues about the connection being refused, a native proxy manager was added to bypass Discord's restrictions. Since all connections are made using HTTPS protocol, so **only HTTPS proxies are allowed**.

**Note**: places where you can find lists of HTTPS proxies:
- [hidemy.name](https://hidemy.name/en/proxy-list/?type=s#list)
- [freeproxylists.net](https://www.freeproxylists.net/?c=&pt=&pr=HTTPS&a%5B%5D=0&a%5B%5D=1&a%5B%5D=2&u=0)
- [spys.one](https://spys.one/en/https-ssl-proxy/)

# <h3 align='center'>PROXY_AUTH_USER & PROXY_AUTH_PASSWORD</h3><br>

The **PROXY_AUTH_USER** and **PROXY_AUTH_PASSWORD** stands for the **string** values used to authenticate your connection to the proxy server.

**Note**: if your proxy has no authentication (like most free proxies found online) leave these fields empty.

# <h3 align='center'>BOOSTS_LENGTH</h3><br>

The **BOOSTS_LENGTH** parameter stands for the **literal integer**  value (```5``` or ```20```) used to compose the boosts duration (also used to structure some of the **Scheduler**'s routines).

# <h3 align='center'>MORE_FISH & MORE_TREASURES</h3><br>

The **MORE_FISH** and **MORE_TREASURES** parameters stands for the **boolean** values used to enable the automatic sending of the '```/buy fish{BOOST_LENGTH}m```' and '```/buy treasure{BOOST_LENGTH}m```' command, respectively, every ~{BOOST_LENGTH} minutes (+/- variation). You can also use key binds to buy the More fish (default '**F**') and More treasures (default '**T**') boosts at any given time during your fishing session. However, if those values are set to ```True```, user arbitrary input will be restricted (since they are being controlled by the **Scheduler**).

**Note**: as any other boost, you must meet the requirements for it to be successfully executed (6 Gold Fish for the 5 minutes boost and 6 Emerald Fish for the 20 minutes one).

# <h3 align='center'>FISH_ON_EXIT</h3><br>

The **FISH_ON_EXIT** parameter stands for the **boolean** value used to enable the automatic sending of the '```/buy auto30m```' command (sent when you exit the bot). 

**Note**: as any other boost, you must meet the requirements for it to be successfully executed (requires 8 Emerald Fish).

# <h3 align='center'>AUTO_DAILY</h3><br>

The **AUTO_DAILY** parameter stands for the **boolean** value used to enable the automatic sending of the '```/daily```' command (controlled by the **Scheduler**). This command can also be sent via key binds (default '**D**'), but its usage it's restricted by one use for each fishing session.

# <h3 align='center'>AUTO_BUY_BAITS</h3><br>

The **AUTO_BUY_BAITS** parameter stands for the **boolean** value used to enable the automatic sending of the '```/buy {BAIT} {calculated_amount}```' command (controlled by the **Scheduler**). 

**Note**: if the value is set to '```True```' you will also need to set the [**BAIT**](#pet--bait--biome) parameter accordingly.

# <h3 align='center'>AUTO_SELL</h3><br>

The **AUTO_SELL** parameter stands for the **boolean** value used to enable the automatic sending of the '```/sell all```' command every ~8 minutes (+/- variation). You can also use key binds to sell your current inventory items (default '**s**') at any given time during your fishing session. 

**Note**: if the value is set to ```True```, and you manually sell your inventory (using key binds or via Discord) while the command is scheduled to be sent, the next automatic update will happen in ~8 minutes from the last manual update.

# <h3 align='center'>AUTO_UPDATE_INVENTORY</h3><br>

The **AUTO_UPDATE_INVENTORY** parameter stands for the **boolean** value used to enable the automatic sending of the '```/profile```' command every ~10 minutes (+/- variation). You can also use key binds to update your inventory (default '**I**') at any given time during your fishing session. 

**Note**: if this value is to ```True```,  and you manually update your inventory (using key binds or via Discord) while the command is scheduled to be sent, the next automatic update will happen in ~10 minutes from the last manual update.

# <h3 align='center'>COMPACT_MODE</h3><br>

The **COMPACT_MODE** parameter stands for the **boolean** value which changes the menu layout, the "compact mode" is a reduced version of the default menu, contains only necessary information and has a minimalistic aesthetic, ideal for small displays. 

**Note**: you can still use key binds just as the normal menu to view the requested information in a popup format (also, the default "Inventory Panel" can be viewed by pressing the "**I**" key).

# <h3 align='center'>REFRESH_RATE</h3><br>

The **REFRESH_RATE** parameter stands for the **float** value (ranging from ```0.1``` to ```1.0```)  used to set the refresh rate of your menu. By default,  it's set to ```0.3``` (seconds), which has a great balance between performance and usability.

**Note**: for those who prefer leaving AFB running in the background, it's recommended to set the refresh rate to ```1.0``` seconds (to restrict as much as possible CPU/Memory usage).

# <h3 align='center'>BAIT</h3><br>

The **BAIT** parameter stands for the **string** value used to compose the [**AUTO_BUY_BAITS**](#auto_buy_baits) routine. 

To find your available baits, you will need to:
1. Go to a channel in which the Virtual Fisher bot has access to
2. Send the '**/bait**' command
3. Select and [copy the name of your preferred bait](https://i.imgur.com/Q3FkGiR.png)

# <h3 align='center'>PET & BIOME</h3><br>

**Not yet implemented**. Will be used to automatically select the specified pet and biome.


