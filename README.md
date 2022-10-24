# steam presence

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

DO NOTE that if you do intend to run this on a steam deck itself, discord will have to be open in the background

but what this script CAN do is run on as mentioned, a server, or another form of desktop computer (with discord open in the background on that device)

I.E with this setup, Discord is able to be updated. Let's say I launch Deep Rock Galactic (rock & stone) on my Steam Deck. Here's what happens:

1) Steam (on my Steam Deck) lets Steam HQ know that I'm running DRG.

2) Steam HQ updates, so my Steam Friends can see that I'm playing DRG.

3) Within a minute, steam-presence (running on my Mac) queries Steam HQ and sees that I'm playing DRG.

4) steam-presence (still on my Mac) pushes the rich presence information to the Discord client (also running on my Mac).

5) The Discord client will now display your current game to your friends (and others)

if you're interested in something similar for nintendo switch, check out <a href="https://github.com/MCMi460/NSO-RPC">this repo</a>

## Setup
create a file named `config.json` in the same directory as this file and fill it in accordingly.
 
```json
{
    "STEAM_API_KEY": "STEAM_API_KEY",
    "USER_ID": "USER_ID",

    "DISCORD_APPLICATION_ID": "869994714093465680",

    "DO_GAME_TITLE_AS_DESCRIPTION": true,

    "COVER_ART": {
        "ENABLED": false,
        "STEAM_GRID_API_KEY": "STEAM_GRID_API_KEY"
    },

    "NON_STEAM_GAMES": {
        "ENABLED": false,
        "NON_STEAM_DISCORD_APP_ID": "939292559765803018"
    },

    "CUSTOM_GAME_OVERWRITE": {
        "ENABLED": false,
        "NAME": "NAME"
    },

    "CUSTOM_STATUS_STATE": {
        "ENABLED": false,
        "STATUS": "https://github.com/JustTemmie/steam-presence"
    },

    "CUSTOM_ICON": {
        "ENABLED": false,
        "URL": "https://raw.githubusercontent.com/JustTemmie/steam-presence/main/readmeimages/defaulticon.png",
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

# Do Game Title As Description
the `DO_GAME_TITLE_AS_DESCRIPTION` field is used for games that aren't found to be cached on discord's end,

thus they will appear as the Discord Application ID.

with this field set to true, it will display the current game as a description.

![WithItEnabled](readmeimages/doGameTitleAsDescription-true.png)

setting it to false will lead to it not showing up at all.

![WithItEnabled](readmeimages/doGameTitleAsDescription-false.png)

this setting will not have any effect on more popular games in any capacity.

# Cover Art
and then we have the `COVER_ART` section.

this will download an icon from steamGridDB and use it as the cover art for the discord presence.

change the ENABLED field to true and fill in the api key enable this.

**NOTE** this is optional and the script functions perfectly without it, you'll just be missing the cover art.

you can get your API key here https://www.steamgriddb.com/profile/preferences/api

additionally, this caches the url to a file named icons.txt, so if you don't like an icon it found you can replace the url in that file for whatever game.

# Non Steam Games
ahh... the non steam games

so for a bit of background of why this might seem a bit weird at first Steam's actual API does not report non steam games in ANY capacity.

so the solution for this, web scraping - loading a website in the background, reading the data off it, and closing it - redoing this every minute.

performance wise it's actually fine, being reasonably light weight and on anything reasonably modern this should be fine, due note though - on battery powered devices this will shorten the battery life by i would GUESS around 5-30 minutes, depending on it's configuration.

change the enabled field to true

download your cookies for steam, i'm unsure how long these stay valid for as i'm writing this so this might be a non issue or this might be pain - not sure.

download the addon that matches your browser.

https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en

navigate to your profile on steam, and download the cookie file, naming it "cookies.txt" and save it in the same folder as main.py

the NON_STEAM_DISCORD_APP_ID field is a seprate discord app ID which displays when the game isn't found in discord's cached game list, but is being played as a non steam game. The default app id "939292559765803018" is simply called "a game not on steam"

**NOTE** the NON_STEAM_DISCORD_APP_ID and the DISCORD_APPLICATION_ID from earlier in the config file **CANNOT** be the same, because of how this script is coded, they can have the same name but if you want both to be called the same you must create two applications, with the same name

**Note2**: due to the names of non steam games being set by yourself, steam grid DB might have problems finding icons for the game, but if it's in their database, this script will fetch it

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
only tested on python3.8 and higher.

run `python3 -m pip install -r requirements.txt` to install all the dependencies

then run `python3 main.py`

(these should hopefully be platform independent, if they're not please open an issue or pull request)

# Run On Startup
this script doesn't have any inherent way to run when your device starts up.

if you're running either Windows or MacOS i cannot really give you any help with this.

(if you do know a way to run this on startup on any of the mentioned systems, please create a pull request with an updated readme)

## Steam Deck / Linux with Systemd

If you have a Steam Deck, it is possible to have steam-presence start automatically when your Steam Deck boots.  This method may also work on other Linux distributions that use per-used Systemd instances.  If you (as a regular user) can run the command `systemctl --user status` successfully, then this should work.

The file `steam-presence.service` has more information and instructions.

## Linux (not using Systemd)

If you're running linux i do have a way to start the script on bootup.

create a file named `startup.sh` and paste in the code below, changing the path so it finds the main.py file.

```
sleep 120
screen -dmS steamPresence bash -c 'python3 /home/USER/steam-presence/main.py'
```

make this script executable using `chmod +x startup.sh`

then run `crontab -e` and add `@reboot  /home/USER/startup.sh` to the end of the crontab file.

if you've done these steps the script should launch itself 120 seconds after your computer turns on, giving time enough to open discord.

(this ends up using about 30MB of ram)
