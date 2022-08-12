# creating rich presences for discord
from time import sleep, time

# requesting data from steam's API
import requests

# for errors
from datetime import datetime

# for loading the config file
import json
from os.path import exists


try:
    # creating rich presences for discord
    from pypresence import Presence

    # used to get the game's cover art
    # the original library is currently broken at the time of writing this, so i'm using a self made fork
    from steamgrid import SteamGridDB

except ImportError:
    answer = input("pypresence or steamgrid is not installed, do you want to install it? (y/n) ")
    if answer.lower() == "y":
        from os import system
        print("installing req packages...")
        system("pip install -r requirements.txt")
        
        from pypresence import Presence
        from steamgrid import SteamGridDB
        
        print("\npackages installed and imported successfully!")

# opens the config file and loads the data
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


# gets the current game the user is playing
def get_steam_presence(STEAM_API_KEY, USER_ID):
    r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&format=json&steamids={str(USER_ID)}").json()

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


# looks into the discord api and steals the app IDs from it
def get_game_id(gameName):
    r = requests.get("https://discordapp.com/api/v8/applications/detectable")
    
    r = r.json()
    
    for i in r:
        gameNames = []
        gameNames.append(i["name"].lower())
        
        if "aliases" in i:
            aliases = i["aliases"]
            for alias in aliases:
                gameNames.append(alias.lower())

        if gameName.lower() in gameNames:
            print(f"found the discord game ID for {gameName}")
            return i["id"]

    print(f"could not find the discord game ID for {gameName}, defaulting to well, the default game ID")
    return DEFAULT_APP_ID

# brtue forces fetching the icon from steamgrid
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
        icon = str(icon)
        
        if icon[-4:] == ".png":
            return icon
        
        for res in resolutions:
            newURL = icon[:-4] + f"/32/{res}x{res}.png"
            
            r = requests.get(newURL)
            if r.status_code == 200:
                return newURL

    
    if res == 16:
        print(f"could not find icon for {gameName} either ignore this or manually add one to icons.txt")
            

# fetches the icon from steamgrid
def get_steam_grid_icon(gameName):
    try:
        gameName = gameName.lower()

        with open(f'icons.txt', 'r') as icons:
            for i in icons:
                game = i.split("=")[0]
                if gameName == game:
                    URL = i.split("=")[1]
                    return URL

        print(f"fetching icon for {gameName}")
        
        results = sgdb.search_game(gameName)

        # yes this is terrible code but i really couldn't figure out a better way to do this, sorry - pull request anyone?
        result = str(results).split(',')[0][1:]
        steamGridAppID = result[9:].split(' ')[0]
        
        # this function is bad... sorry
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


def set_game(
    game_title = None, game_icon = None,
    start_time = None,
    do_custom_state = False, state = None,
    # custom_icon and co are just the mini icons, not the main icon itself
    do_custom_icon = None, custom_icon_url = None, custom_icon_text = None
    ):
    
    try:
        large_text = None
        
        if game_title != None:
            large_text = game_title
        
        if not do_custom_state:
            state = None
        
        if not do_custom_icon:
            custom_icon_url = None
            custom_icon_text = None
            
        if game_icon != None:
            game_icon = game_icon[:-1]
            
            
        # code used in testing
        # if game_title is not None:
        #     large_text = game_title

        # if game_title is None:
        #     game_title = state
        #     state = None
        #     game_icon = None
            
        # if game_title is None and state is None:
        #     game_title = "In-game"

        # if game_icon is None:
        #     large_text = None
        
        RPC.update(
            details = game_title, state = state,
            start = start_time,
            large_image = game_icon, large_text = large_text,
            small_image = custom_icon_url, small_text = custom_icon_text
        )
                
    except Exception as e:
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] problem while setting game, error: {e}")
        return None

if __name__ == "__main__":
    
    # get data from the config file
    print("fetching config data...")
    config = get_config()
    if config["STEAM_API_KEY"] == "KEY":
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Please set your Steam API key in the config file.")
        exit()

    if config["USER_ID"] == "USER_ID":
        print(f"ERROR: [{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}] Please set your Steam user ID in the config file.\n(note this is not the same as the URL ID - read the readme for more info")
        exit()

    STEAM_API_KEY = config["STEAM_API_KEY"]
    USER_ID = config["USER_ID"]
    DEFAULT_APP_ID = config["DISCORD_APPLICATION_ID"]

    GRID_ENABLED = config["COVER_ART"]["ENABLED"]
    GRID_KEY = config["COVER_ART"]["STEAM_GRID_API_KEY"]

    do_custom_game = config["CUSTOM_GAME_OVERWRITE"]["ENABLED"]
    custom_game_name = config["CUSTOM_GAME_OVERWRITE"]["NAME"]
    
    do_custom_icon = config["CUSTOM_ICON"]["ENABLED"]
    custom_icon_url = config["CUSTOM_ICON"]["URL"]
    custom_icon_text = config["CUSTOM_ICON"]["TEXT"]


    # initialize the steam grid database object
    if GRID_ENABLED:
        print("intializing the SteamGrid database...")
        sgdb = SteamGridDB(GRID_KEY)
    
    
    startTime = 0
    coverImage = None
    app_id = DEFAULT_APP_ID
    
    
    # the old game name early to avoid it thinking the game changed even if it didn't on first loop
    if do_custom_game:
        gameName = custom_game_name

    else:
        gameName = get_steam_presence(STEAM_API_KEY, USER_ID)
        
    oldGameName = gameName
    
    if gameName != None:
        app_id = get_game_id(gameName)
    
    # initialize the discord rich presence object
    print("intializing the rich presence...")
    RPC = Presence(client_id=app_id)
    RPC.connect()

    # everything ready! 
    print("everything is ready!")
    
    
    while True:
        # refetches some data from the config file, so these can be changed without restarting the script
        config = get_config()
        do_custom_game = config["CUSTOM_GAME_OVERWRITE"]["ENABLED"]
        custom_game_name = config["CUSTOM_GAME_OVERWRITE"]["NAME"]
        do_custom_state = config["CUSTOM_STATUS_STATE"]["ENABLED"]
        custom_state = config["CUSTOM_STATUS_STATE"]["STATUS"]
        do_custom_icon = config["CUSTOM_ICON"]["ENABLED"]
        custom_icon_url = config["CUSTOM_ICON"]["URL"]
        custom_icon_text = config["CUSTOM_ICON"]["TEXT"]


        oldGameName = gameName
        
        if do_custom_game:
            gameName = custom_game_name

        else:
            gameName = get_steam_presence(STEAM_API_KEY, USER_ID)
            
            
        
        if gameName is None:
            # note, this completely hides your current rich presence
            RPC.clear()
            startTime = 0
    
        else:
            if startTime == 0:
                startTime = round(time())
    
            if GRID_ENABLED:
                coverImage = get_steam_grid_icon(gameName)
            
            if app_id == DEFAULT_APP_ID:
                set_game(gameName, coverImage, startTime, do_custom_state, custom_state, do_custom_icon, custom_icon_url, custom_icon_text)
            
            else:
                set_game(None, coverImage, startTime, do_custom_state, custom_state, do_custom_icon, custom_icon_url, custom_icon_text)
        
        # if the game has changed, restart the rich presence client with that new app ID
        if oldGameName != gameName and gameName != None:
            startTime = round(time())
            print(f"game changed to \"{gameName}\"")
            
            app_id = get_game_id(gameName)
            startTime = round(time())

            RPC.close()
            RPC = Presence(client_id=app_id)
            RPC.connect()
            # repeat the while loop to refresh it's metadata
            sleep(1)

        else:
            sleep(20)