from datetime import datetime
import requests
import os
import sys
import json

import time
import functools

# just shorthand for logs and errors - easier to write in script
def debug(data):
    if True:
        print(f"DEBUG: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {data}")

def log(data):
    print(f"[{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {data}")

def error(data):
    print(f"    ERROR: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {data}")


# a wrapper for funcstools.lru_cache() that only holds data for x seconds
def time_cache(maxAgeSeconds, maxSize=128):
    def _decorator(func):
        @functools.lru_cache(maxsize=maxSize)
        def _new(*args, __time_salt, **kwargs):
            return func(*args, **kwargs)

        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            return _new(*args, **kwargs, __time_salt=int(time.time() / maxAgeSeconds))

        return _wrapped

    return _decorator

# i've gotten the error `requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))` a lot;
# this just seems to sometimes happens if your network conection is a bit wack, this function is a replacement for requests.get() and basically just does error handling and stuff
def make_web_request(URL, *args, loops=0):
    print(f"making a web request to {URL}")
    try:
        r = requests.get(URL, *args)
        return r
    except Exception as e:
        if loops > 10:
            error(f"falling back... the script got caught in a loop while fetching data from `{URL}`")
            return "error"
        elif "104 'Connection reset by peer'" in str(e):
            return make_web_request(URL, *args, loogs=loops+1)
        else:
            # error(f"falling back... exception met whilst trying to fetch data from `{URL}`\nfull error: {e}")
            return "error"

# opens the config file and loads the data
def getConfigFile():
    # the default settings, don't use exampleConfig.json as people might change that
    defaultSettings = {
        "DEFAULT_DISCORD_APPLICATION_ID": "1062648118375616594",
        
        "SERVICES": {
            "STEAM": {
                "ENABLED": True,
                "API_KEY": "API_KEY",
                "USER_ID": "USER_ID",
                "DISCORD_APPLICATION_ID": "869994714093465680",
                "STORE_BUTTON": True
            },
            "STEAM_GRID_DB": {
                "ENABLED": True,
                "API_KEY": "API_KEY"
            },
            "LOCAL_GAMES": {
                "ENABLED": True,
                "GAMES": [
                    "animdustry",
                    "godot",
                    "Undertale Yello",
                    "FL64.exe",
                    "Celeste64"
                ]
            }
        },
        
        "LARGE_IMAGE_SOURCES": [
            "file_cache",
            "discord_cdn",
            "steam_grid_db_game_name",
            "steam_grid_db_steam_id",
            "steam_cdn",
            "steam_store_page"
        ],
        
        
        "RPC_LINES": [
            "{playtime} Hours | {achievement_count} Achievements",
            "{rich_presence}",
            "{reviews[score_percentage]} positive reviews"
        ],
        "PREFER_NAME_OVER_RPC_LINES": True,

        "WEB_SCRAPE": False,

        "CUSTOM_ICON": {
            "ENABLED": True,
            "URL": "https://raw.githubusercontent.com/JustTemmie/steam-presence/main/readmeimages/defaulticon.png",
            "TEXT": "Steam Presence on Discord, made by me :3"
        },

        "BLACKLIST": [
            "bobr clicker",
            "game2",
            "game3"
        ]
    }


    if os.path.exists(f"config.json"):
        with open(f"config.json", "r") as f:
            userSettings = json.load(f)
    
    elif os.path.exists(f"exampleconfig.json"):
        with open(f"exampleconfig.json", "r") as f:
            userSettings = json.load(f)
    
    else:
        error("Config file not found. Please read the readme and create a config file.")
        exit()
    
        
    # if something isn't speficied in the user's config file, fill it in with data from the default settings 
    settings = {**defaultSettings, **userSettings}
    for key, value in defaultSettings.items():
        if key in settings and isinstance(value, dict):
            settings[key] = {**value, **settings[key]}
            
    
    return settings

def removeChars(inputString: str, ignoredChars: str) -> str:
    # removes all characters in the ingoredChars string from the inputString
    for ignoredChar in ignoredChars:
        if ignoredChar in inputString:
            for j in range(len(inputString) - 1, 0, -1):
                if inputString[j] in ignoredChar:
                    inputString = inputString[:j] + inputString[j+1:]

    return inputString

def ensure_lowercase_dictionary_keys(input_dict: dict[str, any]) -> dict[str, any]:
    """
        a function that ensures that every key in the icons dict is lowercase
        this is done to reduce confusion by manually entered entries
    """
    new_dict = {}
    for key, value in input_dict.items():
        new_dict[key.casefold()] = value
    return new_dict