import src.steam_presence.logger # just need to initialize it

from src.fetchers.SteamGridDB import SteamGridDB
from src.getters.Local import LocalGetter
from src.getters.Steam import SteamGetter
from src.setters.Discord import DiscordRPC
from src.steam_presence.config import Config, SteamUser

import time
import logging

from typing import Union

logging.info("Starting setup!")

config = Config()
config.load()

logging.info("Generating getters...")

SgdbFetcher = None
localGetter = None
steamGetters: list[SteamGetter] = []

# key is just a generic identifier such as process ID or steam ID
RPC_connections: dict[Union[int, str], DiscordRPC] = {}

if config.steam_grid_db.enabled:
    SgdbFetcher = SteamGridDB(config)

if config.local_games.enabled:
    localGetter = LocalGetter(config)

if config.steam.enabled:
    for user in config.steam.users:
        # convert user dict into dataclass
        user = SteamUser(**user)
        steamGetters.append(SteamGetter(config, user))

logging.info("Setup complete!")

while True:
    if localGetter:
        processes = localGetter.fetch()

        for process in processes:
            RPC_ID = process.process_name
            if not RPC_connections.get(RPC_ID):
                if process.display_name:
                    RPC_connections[RPC_ID] = DiscordRPC(config, SgdbFetcher)
                    RPC_connections[RPC_ID].instanciate(
                        process.display_name,
                        config.local_games.discord_fallback_app_id
                    )
                else:
                    break
                
            game = RPC_connections[RPC_ID]

            game.local_payload = process

            game.update()

    for steam_game in [getter.fetch() for getter in steamGetters]:
        if steam_game:
            RPC_ID = steam_game.app_id

            if not RPC_connections.get(RPC_ID):
                if steam_game.app_name:
                    RPC_connections[RPC_ID] = DiscordRPC(config, SgdbFetcher)
                    RPC_connections[RPC_ID].instanciate(
                        steam_game.app_name,
                        config.steam.discord_fallback_app_id
                    )
                else:
                    break
            
            game = RPC_connections[RPC_ID]

            game.steam_payload = steam_game

            game.update()
            game.updateSteamData()

    logging.debug("Processing complete!")

    expired_IDs: list[Union[int, str]] = []
    for ID, connection in RPC_connections.items():
        logging.debug(f"Refreshing connection for {ID}")
        if not connection.refresh():
            expired_IDs.append(ID)

    for ID in expired_IDs:
        logging.info(f"Deleting connection to {ID}")
        RPC_connections.pop(ID)
    
    logging.debug("----- Cycle complete -----")
    time.sleep(20)