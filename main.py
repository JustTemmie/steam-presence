import time


import src.services.updater as updater
import src.services.discord as discord

import src.discord_RPC as discord_RPC
import src.core as core

from src.helpers import *


def main():
    # this always has to match the newest release tag
    currentVersion = "v1.12.1"
    
    # check if there's any updates for the program
    updater.checkForUpdate(currentVersion)
    # does various things, such as verifying that certain files are in certain locations
    updater.verifyProjectVersion()
    
    log("loading config file")
    config = getConfigFile()
    steamUserIDs = config["SERVICES"]["STEAM"]["USER_IDS"].split(",")
    APIKeys = {
        "steam": config["SERVICES"]["STEAM"]["API_KEY"],
        "sgdb": config["SERVICES"]["STEAM_GRID_DB"]["API_KEY"]
    }
    
    RPC =  discord_RPC.RPC()
    CORE = core.Core(APIKeys)

    # everything ready! 
    log("everything is ready!")
    print("----------------------------------------------------------")
    
    while True:
        current_game = CORE.get_current_game(steamUserIDs)

        for platform in current_game:
            discord_app_id = discord.get_game_ID(current_game[platform]["gameName"])
            if discord_app_id != None:
                RPC.ensure_presence(discord_app_id, platform)
        
        RPC.update_presence_details(current_game)

        # sleep for a 20 seconds for every user we query, to avoid getting banned from the steam API
        time.sleep(20 * len(steamUserIDs))


if __name__ == "__main__":
    main()
