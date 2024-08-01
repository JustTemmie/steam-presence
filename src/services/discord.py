import os
import sys
import json
import time

import re

from functools import cache

if __name__ == "__main__":
    sys.path.append(".")

import src.helpers as steam_presence


# a regex used when fetching the discord app ID of a game
ignoredCharsInName = "[" + re.escape("®©™'℠ :,.-") + "]"

def remove_ignored_chars(string):
    return re.sub(ignoredCharsInName, "", string.casefold())

@steam_presence.time_cache(86400)
def get_app_list():
    r = steam_presence.make_web_request("https://discordapp.com/api/v8/applications/detectable")
    if r == "error":
        return
    
    if r.status_code != 200:
        steam_presence.error(f"status code {r.status_code} returned whilst trying to find the game's ID from discord")
        return
    
    return r.json()
    
# requests a list of all games recognized internally by discord, if any of the names matches
# the detected game, save the discord game ID associated with said title to RAM, this is used to report to discord as that game
@steam_presence.time_cache(86400)
def get_game_ID(gameName: str):
    discordApps = get_app_list()
    if not discordApps:
        return
    
    # check if the "customGameIDs.json" file exists, if so, open it
    if os.path.exists(f"data/customGameIDs.json"):
        with open(f"data/customGameIDs.json", "r") as f:
            # load the values of the file
            gameIDsFile = json.load(f)
            
            # add the values from the file directly to the list returned by discord
            for name, ID in gameIDsFile.items():
                discordApps.append({
                    "name": name,
                    "id": ID
                })
    
    
    gameName = gameName.casefold()
    # remove the demo from the name, if applicable
    if gameName.endswith(" demo"):
        gameName.replace(" demo", "")
    # remove a list of characters i've decided to ignore, such as ® and ©
    gameName = remove_ignored_chars(gameName)
    
    # loop thru all games
    for app in discordApps:
        appNames = []
        appNames.append(remove_ignored_chars(app["name"]))
        
        if "aliases" in app:
            for alias in app["aliases"]:
                appNames.append(remove_ignored_chars(alias))
        
        if gameName in appNames:
            steam_presence.log(f"found the discord game ID: {app['id']} for {gameName}")
            return app["id"]
    
    return 0

# get game's icon straight from Discord's CDN
@steam_presence.time_cache(86400)
def get_image_from_discord(appID) -> str:
    try: 
        r = steam_presence.make_web_request(f"https://discordapp.com/api/v8/applications/{appID}/rpc")
        if r == "error":
            return

        if r.status_code != 200:
            steam_presence.error(f"status code {r.status_code} returned when fetching icon from Discord")
            return

        response = r.json()

        return f"https://cdn.discordapp.com/app-icons/{appID}/{response['icon']}.webp"

    except Exception as e:
        steam_presence(f"Exception {e} raised when trying to fetch icon from Discord, ignoring")

if __name__ == "__main__":
    print(get_game_ID("visual boy advance"))
    runtimes = []
    for i in range(100):
        start = time.time()
        get_game_ID("visual boy advance")
        end = time.time()
        
        runtimes.append(end-start)
    
    print(sum(runtimes) / 100)
