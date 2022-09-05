# FAQ 

### Table of contents:
<!-- no toc -->
- [CONFIG RELATED](#config-related)
  - [How do I get my CHANNEL_ID ?](#how-do-i-get-my-channel_id-)
  - [How do I get my USER_TOKEN ?](#how-do-i-get-my-user_token-)
  - [How do I get my OCR_API_KEY ?](#how-do-i-get-my-ocr_api_key-)
  - [How do I get my USER_COOLDOWN ?](#how-do-i-get-my-user_cooldown-)
  - [How do I get my BAIT ?](#how-do-i-get-my-bait-)
  - [What is AUTO_BUFF ?](#what-is-auto_buff-)
  - [What is BUFF_LENGTH ?](#what-is-buff_length-)
  - [What is FISH_ON_EXIT ?](#what-is-fish_on_exit-)
  - [What is COMPACT_MODE ?](#what-is-compact_mode-)
  - [What is DEBUG ?](#what-is-debug-)
<!-- - [SYSTEM RELATED](#system-related) -->
  

## <p align='center'>CONFIG RELATED</p>

## HOW DO I GET MY CHANNEL_ID ?
The **CHANNEL_ID** parameter stands for the **integer** identifier value of a channel on Discord, it's used for filtering which events should be analysed in order to compose the messages displayed on your screen.

To get it, you will need to:
- Enable "*Developer Mode*" option on Discord ([*User Settings -> Advanced -> Enable Developer Mode*](https://img001.prntscr.com/file/img001/NzQmu739QQe5E6UmetJadA.png)).
- [Right click on the channel of your preference, then click on the "**Copy ID**" button](https://img001.prntscr.com/file/img001/dcwjC6w9TzuTv4sMmyfbzw.png).

## HOW DO I GET MY USER_TOKEN ?
The **USER_TOKEN** parameter stands for the **string** value used to properly authenticate you on Discord's servers and correctly send/receive new events assigned to that token.

To get it, you will need to:
1. Log in the desired Discord account on any **browser**
2. With your account open, in the Discord's page, **press F12** (to open *Developer Tools*)
3. On the top middle, click on the "**Storage**" button (or press SHIFT + F9 on the developer menu)
4. On right the side bar, click on the "**Local Storage**" option, then click on the **Discord's URL** option.
5. After that, on the top middle, **type** "*token*" on the filter search bar.
6. Look for the exact key name matching the keyword "*token*", then copy that key's value **without quotation marks** *("mykey123&18jh" -> mykey123&18jh)* and paste it on the **USER_TOKEN** parameter.

Image guide:
- [Steps 1, 2, 3](https://img001.prntscr.com/file/img001/2Xfy-1NYSRmXAnBr3dLgjw.png)
- [Step 4](https://img001.prntscr.com/file/img001/NiJm1v9TRB6zIOT4Nf1ZCA.png)
- [Step 5, 6](https://img001.prntscr.com/file/img001/TDpMd3c0Te2U6qo8LLDTLQ.png)

**The user token is a very sensitive information and should not be shared with anyone. This program does NOT collect any kind of data, all information is stored locally on your computer. All the requests made to Discord's API and Webgate use HTTPS by default.**

## HOW DO I GET MY OCR_API_KEY ?
The **OCR_API_KEY** parameter stands for the **string** value used to authorize your request to the [OCR.SPACE](https://ocr.space/) API (see the documentation [here](https://ocr.space/OCRAPI)).

To get it, you will need to:
- Go to the free registration page: *https://ocr.space/ocrapi/freekey*
- Fill in the requested information *(you don't need to answer anything truthfully, **except** your email address - as you will be receiving a confirmation email there)* then click on the "**Subscribe**" button.
- After that, check your email for a subscription confirmation, then click on the "**YES, SUBSCRIBE ME TO THE FREE OCR API LIST.**" button. Once you confirmed your email address, you will receive a second email with your personal API key.
- Finally, refresh your inbox and find the API KEY email. 

For any remaining questions see their [FAQ](https://ocr.space/faq) and [FORUM](https://forum.ui.vision/c/ocr-api/10).

## HOW DO I GET MY USER_COOLDOWN ?
The **USER_COOLDOWN** parameter stands for the **float** value used to delay the commands sending rate, for deeper information see the discussion [here](https://github.com/thejoabo/virtualfisher-bot/discussions/12).

To get it, you will need to:
- Go to the desired channel (on a server that the Virtual Fisher is and have proper permissions).
- [Trigger the cooldown alert event by manually sending two consecutive messages containing "*%f*"](https://img001.prntscr.com/file/img001/QLZR2fifRReKyK_SOiG-4A.png).
- After that copy the number that stands for '*Your cooldown:*'.

## HOW DO I GET MY BAIT ?
The **BAIT** parameter stands for the **string** value used to re-suply your baits (so you won't run out of it mid-session).

To get it, you will need to:
- Go to the desired channel (on a server that the Virtual Fisher is in and have permission to see this channel).
- [Send the command "*%shop bait*" and check for your avaible baits, then choose one and use it as the **BAIT** value](https://img001.prntscr.com/file/img001/4g2tz06eTQ6YGBek7AwW6w.png).

## WHAT IS AUTO_BUFF ?
The **AUTO_BUFF** parameter stands for the **boolean** value used to enable the "*%buy fish*{**BUFF_LENGTH**}*m*" and "*%buy treasure*{**BUFF_LENGTH**}*m*" commands in the "*autoBuff()*" function, the frequency at which this routine is invoked is also set by the **BUFF_LENGTH** parameter.

## WHAT IS BUFF_LENGTH ?
The **BUFF_LENGTH** parameter stands for the **literal (5, 20)** value used to correctly compose the command "*%buy fish*{**BUFF_LENGTH**}*m*" and "*%buy treasure*{**BUFF_LENGTH**}*m*" by defining their length. 

Even if **AUTO_BUFF** is set to "**FALSE**", this value will be used to define the frequency (in seconds) at which the "*autoBuff()*" routine is executed. This routine also includes the queries for selling all fish as well as restocking the bait *(the quantity is computed based on the selected value)*.


## WHAT IS FISH_ON_EXIT ?
The **FISH_ON_EXIT** parameter stands for the **boolean** value which enables the functionality to send the "*%buy auto30m*" command when you close the program, thus fishing for 30 minutes while you are offline. *Keep in mind that you must meet the requirements to use the command.*

## WHAT IS COMPACT_MODE ?
The **COMPACT_MODE** parameter stands for the **boolean** value that changes menu operation, the "*compact mode*" is a reduced version of the default menu, contains only strictly necessary information and has a more minimalistic aesthetic, ideal for small displays. See [#15](https://github.com/thejoabo/virtualfisher-bot/issues/15) and [#23](https://github.com/thejoabo/virtualfisher-bot/discussions/23).

## WHAT IS DEBUG ?
The **DEBUG** parameter stands for the **boolean** value used to display back-end information about exceptions and errors. The purpose of this setting is to help users draw up an [issue](https://github.com/thejoabo/virtualfisher-bot/issues/new) report by including debugging information to determine where and why the error occurred.

## WHAT IS NUMBER_FORMATTING ?
### **Not implemented yet.**
The **NUMBER_FORMATTING** parameter stands for the **literal ('default', 'e')** value that switches between the '[*Decimal notation*](https://en.wikipedia.org/wiki/Decimal#Decimal_notation)' (1000000) and '[*E notation*](https://en.wikipedia.org/wiki/Scientific_notation#E_notation)' (1.00e+06) modes for denoting numbers on the screen. 

<!-- ## <p align='center'>SYSTEM RELATED</p>
### ... -->

 
