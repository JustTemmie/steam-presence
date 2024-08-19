import time


import src.services.updater as updater
import src.services.discord as discord

import src.discord_RPC as discord_RPC
import src.core as core

from src.helpers import *

import psutil

# list of ports used by discord RPC, https://github.com/discord/discord-api-docs/blob/main/docs/topics/RPC.md#rpc-server-ports
discord_RPC_ports = [i for i in range(6463, 6473)]

# connections = psutil.net_connections()
# for conn in connections:
#     if conn.laddr and conn.laddr.ip == '127.0.0.1' and conn.laddr.port in discord_RPC_ports:
#         print(f"Local address: {conn.laddr}, Remote address: {conn.raddr}, PID: {conn.pid}")
#     # if conn.laddr.port in discord_RPC_ports:

# exit()


def main():
    # this always has to match the newest release tag
    current_version = "v2.0 dev build"
    
    # check if there's any updates for the program
    updater.checkForUpdate(current_version)
    # does various things, such as verifying that certain files are in certain locations
    updater.verifyProjectVersion()
    
    print("-" * 50)
    print("loading config file")
    config = getConfigFile()
    
    steamUserIDs = config["SERVICES"]["STEAM"]["USER_IDS"]
    if isinstance(steamUserIDs, str):
        steamUserIDs = [steamUserIDs]
    
    APIKeys = {
        "steam": config["SERVICES"]["STEAM"]["API_KEY"],
        "sgdb": config["SERVICES"]["STEAM_GRID_DB"]["API_KEY"]
    }
    
    RPC =  discord_RPC.RPC(current_version)
    CORE = core.Core(APIKeys)

    # everything ready! 
    print("-" * 50)
    print("everything is ready!")
    
    while True:
        print("-" * 50)
        current_game = CORE.get_current_games(steamUserIDs)

        for platform in current_game:
            discord_app_id = discord.get_game_ID(current_game[platform]["gameName"])
            if discord_app_id != None:
                RPC.ensure_presence(discord_app_id, platform)
        
        RPC.update_presence_details(current_game)

        # sleep for a 20 seconds, to avoid getting banned from the steam API
        time.sleep(20)


if __name__ == "__main__":
    main()
