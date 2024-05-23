import os
import sys
import json
import time

import re

from functools import cache

if __name__ == "__main__":
    # change the path to match the root directory when testing it
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    
from src.helpers import *


# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

# a regex used when fetching the discord app ID of a game
ignoredCharsInName = "[" + re.escape("®©™'℠ :,.-") + "]"

def remove_ignored_chars(string):
    return re.sub(ignoredCharsInName, "", string.casefold())

@cache
def get_app_list():
    r = make_web_request("https://discordapp.com/api/v8/applications/detectable")
    if r == "error":
        return
    
    if r.status_code != 200:
        error(f"status code {r.status_code} returned whilst trying to find the game's ID from discord")
        return
    
    return r.json()
    
# requests a list of all games recognized internally by discord, if any of the names matches
# the detected game, save the discord game ID associated with said title to RAM, this is used to report to discord as that game
@cache
def get_game_ID(gameName):
    discordApps = get_app_list()
    if not discordApps:
        return
    
    # check if the "customGameIDs.json" file exists, if so, open it
    if os.path.exists(f"{project_root}/data/customGameIDs.json"):
        with open(f"{project_root}/data/customGameIDs.json", "r") as f:
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
    gameName.replace("demo", "")
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
            log(f"found the discord game ID: {app['id']} for {gameName}")
            return app["id"]
    
    return 0


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    print(get_game_ID("visual boy advance"))
    runtimes = []
    for i in range(100):
        start = time.time()
        get_game_ID("visual boy advance")
        end = time.time()
        
        runtimes.append(end-start)
    
    print(sum(runtimes) / 100)