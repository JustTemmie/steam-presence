# steam presence on discord

a simple script to check a Steam user's current game, and display that as a Discord rich presence

![ExampleImage1](readmeimages/example1.png)

playing "BTD6" with the script running 

![ExampleImage2](readmeimages/example2.png)

playing "Everything" with the script running (more niece game so Discord doesn't have it saved)

### Why??
well, why did i make this? Discord already detects the games you're playing so isn't this just pointless??

see, no.

Discord has severe limitations when it comes to Linux as most games running thru a compatability layer (like 90% of them) are displayed as pr-wrap or something similar.

in addition to this, there's the Steam Deck, a handheld linux game "console".

having discord constantly run in the background is a terrible idea considering how that's gonna lose you at least half an hour of battery life, in addition to the previous issues with linux.

so this script is a way of circumventing these issues by instead having this run on something like a server 24/7.

also yes this is very dumb you're right lmao

if you're interested in something similar for nintendo switch, check out <a href="https://github.com/MCMi460/NSO-RPC">this repo</a>

## Setup
create a file named `config.json` in the same directory as this file and fill it in accordingly.
 
```json
{
    "STEAM_API_KEY": "STEAM_API_KEY",
    "USER_ID": "USER_ID",

    "DISCORD_APPLICATION_ID": "DISCORD_APPLICATION_ID",

    "COVER_ART": {
        "ENABLED": false,
        "STEAM_GRID_API_KEY": "STEAM_GRID_API_KEY"
    },

    "CUSTOM_GAME_OVERWRITE": {
        "ENABLED": false,
        "NAME": "NAME"
    },

    "CUSTOM_STATUS_STATE": {
        "ENABLED": false,
        "STATUS": "https://github.com/JustTemmie/steam-presence-on-discord"
    },

    "CUSTOM_ICON": {
        "ENABLED": false,
        "URL": "https://raw.githubusercontent.com/JustTemmie/steam-presence-on-discord/main/readmeimages/defaulticon.png",
        "TEXT": "Steam Presence on Discord"
    }
}
```
# Steam web API
the `STEAM_API_KEY` in this case is regarding to the Steam web API.

this you can obtain by registering here https://steamcommunity.com/dev/apikey while logged in

# User ID
the `USER_ID` is the steam user id of the user you want to track.

**NOTE** this is not the same as the display URL of the user.

the easiest way i've found to get the ID is by throwing your url into the steamDB calculator https://steamdb.info/calculator/

and then taking the ID from that url

![ExampleImage](readmeimages/steamDB.png)

# Discord Application ID
the `DISCORD_APPLICATION_ID` is the discord application ID of the app you want to use.

please generate one here https://discordapp.com/developers/applications/ or use mine "869994714093465680"

the only thing you need to fill out on their site is the application name itself.

for example i named mine "a game on steam" as shown in the screenshot above.

# Cover Art
and then we have the `COVER_ART` section.

this will download an icon from steamGridDB and use it as the cover art for the discord presence.

change the ENABLED field to true and fill in the api key enable this.

**NOTE** this is optional and the script functions perfectly without it, you'll just be missing the cover art.

you can get your API key here https://www.steamgriddb.com/profile/preferences/api

additionally, this caches the url to a file named icons.txt, so if you don't like an icon it found you can replace the url in that file for whatever game.

# Non Steam Games
ahh... the non steam games

so for a bit of background of why this might seem a bit weird at first Steam's actual API does not report non steam games in ANY capacity

so the solution for this, web scraping - loading a website in the background, reading the data off it, and closing it - redoing this every minute

performance wise it's actually fine, being reasonably light weight and on anything reasonably modern this should be fine, due note though - on battery powered devices this will shorten the battery life by i would GUESS around 5-30 minutes, depending on it's configuration

change the enabled field to true

download your cookies for steam, i'm unsure how long these stay valid for as i'm writing this so this might be a non issue or this might be pain - not sure

download the addon that matches your browser

https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en (COMPLETELY UNTESTED, might not work, create an issue if needed)

navigate to your profile on steam, and download the cookie file, naming it "cookies.txt" and save it in the same folder as main.py

Note: due to the names of non steam games being set by yourself, steam grid DB might have problems finding icons for the game, but if it's in their database, this script will fetch it

# Custom Game Overwrite
if you want to display a game that isn't on steam, you can use the `CUSTOM_GAME_OVERWRITE` section.

set enabled to true and fill in the name of the game you want to display.

this will still try to grab an icon from steamGridDB, but if it can't find one you can try giving it one yourself.

# Custom Status State
if you want to display a custom status alongside the game, you can use the `CUSTOM_STATUS_STATE` section.

set enabled to true and fill in the status you want to display.

# Custom Icon
this is a small icon that appears in the bottom right, enable it or disable it.

set an URL to the image you want to use, and a text that will appear when hovering over the icon.

# Python
python3.8 or higher is required.

run `pip install -r requirements.txt` to install all the dependencies

then run `python3 main.py`

(these are linux commands, if you're on windows you might need to change them into something, idk search it up)
