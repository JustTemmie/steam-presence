# creating rich presences for discord
from pypresence import Presence
from time import sleep, time

# used to get the game's cover art
# the original library is currently broken at the time of writing this, so i'm using a self made fork
from steamgrid import SteamGridDB

# requesting data from steam's API
import requests

# for errors
from datetime import datetime

# for loading the config file
import json
from os.path import exists


def get_config():
    if exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    
    if exists("exampleconfig.json"):
        with open("exampleconfig.json", "r") as f:
            return json.load(f)
    
    else:
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Config file not found. Please read the readme and create a config file.")
        exit()


config = get_config()
if config["KEY"] == "KEY":
    print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Please set your Steam API key in the config file.")
    exit()

if config["USERID"] == "USERID":
    print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Please set your Steam user ID in the config file.\n(note this is not the same as the URL ID - read the readme for more info")
    exit()

KEY = config["KEY"]
USER = config["USERID"]
APP_ID = config["DISCORD_APPLICATION_ID"]

GRID_ENABLED = config["COVER_ART"]["ENABLED"]
GRID_KEY = config["COVER_ART"]["STEAM_GRID_API_KEY"]

do_custom_game = config["CUSTOM_GAME_OVERWRITE"]["ENABLED"]
custom_game_name = config["CUSTOM_GAME_OVERWRITE"]["NAME"]



def get_steam_presence():
    r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={KEY}&format=json&steamids={str(USER)}").json()

    if len(r["response"]["players"]) == 0:
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Player not found, this is likely because the userID is invalid, the key is invalid, or steam is down. Please try again later or read thru the readme again.")

    try:
        game_title = None
        for i in r["response"]["players"][0]:
            if i == "gameextrainfo":
                game_title = r["response"]["players"][0][i]

        if game_title is not None:
            return game_title

    except:
        pass

def try_fetching_icon(gameName, steamGridAppID):
    resolutions = [
            512,
            256,
            128,
            64,
            32,
            16
        ]
        
    grids = sgdb.get_icons_by_gameid(game_ids=[steamGridAppID])
    
    # basically some of the icons are .ico files, discord cannot display these
    # what this does is basically brute force test a bunch of resolutions and pick the first one that works
    # as steamgriddb actually hosts png versions of all the .ico files, they're just not returned by the API
    for icon in grids:
        for res in resolutions:
            icon = str(icon)
            newURL = icon[:-4] + f"/32/{res}x{res}.png"
            
            r = requests.get(newURL)
            if r.status_code == 200:
                return newURL

    
    if res == 16:
        with open(f'icons.txt', 'a') as icons:
            icons.write(f"\n{gameName}=None")
            icons.close()
        print(f"could not find icon for {gameName} either ignore this or manually add one to icons.txt")
            
        
                
def get_steam_grid_icon(gameName):
    try:
        with open(f'icons.txt', 'r') as icons:
            for i in icons:
                game = i.split("=")[0]
                if gameName == game:
                    URL = i.split("=")[1]
                    return URL

        results = sgdb.search_game(gameName)

        # yes this is terrible code but i really couldn't figure out a better way to do this, sorry - pull request anyone?
        result = str(results).split(',')[0][1:]
        steamGridAppID = result[9:].split(' ')[0]
        
        newURL = try_fetching_icon(gameName, steamGridAppID)
        
        if newURL == "":
            return None
        
        with open(f'icons.txt', 'a') as icons:
            icons.write(f"{gameName}={newURL}\n")
            icons.close()

        return newURL
    
    except Exception as e:
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] problem while fetching icon, this is likely because no icons exist as it's a niece game or something - error: {e}\n(can probably just be ignored lmao)\n")
        return None

def set_game(game_title, game_icon, start_time, do_custom_state, state):
    try:
        # GOD THIS IS BAD I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT I HATE IT 
        if coverImage:
            if do_custom_state:
                RPC.update(details=game_title, state=state, large_image=f"{game_icon[:-1]}", large_text=f"{game_title}", start=start_time)
            else:
                RPC.update(details=game_title, large_image=f"{game_icon[:-1]}", large_text=f"{game_title}", start=start_time)
                
        else:
            if do_custom_state:
                RPC.update(details=game_title, start=start_time)
            else:
                RPC.update(details=game_title, state=state, start=start_time)
                
    except Exception as e:
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] problem while setting game, error: {e}")
        return None

if __name__ == "__main__":
    if GRID_ENABLED:
        sgdb = SteamGridDB(GRID_KEY)
    
    RPC = Presence(client_id=APP_ID)
    RPC.connect()
    startTime = 0
    coverImage = None
    
    while True:
        config = get_config()
        do_custom_game = config["CUSTOM_GAME_OVERWRITE"]["ENABLED"]
        custom_game_name = config["CUSTOM_GAME_OVERWRITE"]["NAME"]
        do_custom_state = config["CUSTOM_STATUS_STATE"]["ENABLED"]
        custom_state = config["CUSTOM_STATUS_STATE"]["STATUS"]

        if not do_custom_game:
            game_title = get_steam_presence()
        
        else:
            game_title = custom_game_name
            
        
        if game_title is None:
            # note, this completely hides your current rich presence
            RPC.clear()
            startTime = 0
    
        else:
            if startTime == 0:
                startTime = round(time())
    
            if GRID_ENABLED:
                coverImage = get_steam_grid_icon(game_title)

            set_game(game_title, coverImage, startTime, do_custom_state, custom_state)
            
            
        sleep(15)

