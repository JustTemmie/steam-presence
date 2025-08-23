import src.steam_presence.logger # just need to initialize it
import src.steam_presence.misc as steam_presence

from src.fetchers.SteamGridDB import SteamGridDB
from src.getters.Jellyfin import JellyfinGetter
from src.getters.Local import LocalGetter
from src.getters.Steam import SteamGetter
from src.setters.Discord import DiscordRPC
from src.steam_presence.config import Config, SteamUser, JellyfinInstance

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
jellyfinGetters: list[JellyfinGetter] = []

defaultGame: DiscordRPC = None

# key is just a generic identifier such as process ID or steam ID
RPC_connections: dict[Union[int, str], DiscordRPC] = {}


if config.steam_grid_db.enabled:
    SgdbFetcher = SteamGridDB(config)

if config.local_games.enabled:
    localGetter = LocalGetter(config)

if config.default_game.enabled:
    defaultGame = DiscordRPC(config, SgdbFetcher)

if config.steam.enabled:
    for user in config.steam.users:
        # convert user dict into dataclass
        user = SteamUser(**user)
        steamGetters.append(SteamGetter(config, user))

if config.jellyfin.enabled:
    for instance in config.jellyfin.instances:
        instance = JellyfinInstance(**instance)
        jellyfinGetters.append(JellyfinGetter(config, instance))

logging.info("Setup complete!")
print("–" * steam_presence.get_terminal_width())

while True:
    if localGetter:
        processes = localGetter.fetch()

        for process in processes:
            RPC_ID = process.process_name
            if not RPC_connections.get(RPC_ID):
                if process.display_name:
                    config.load() # reload the config on new RPC connection
                    RPC_connections[RPC_ID] = DiscordRPC(config, SgdbFetcher)
                    if config.local_games.inject_discord_status_data:
                        RPC_connections[RPC_ID].inject_bonus_status_data(config.local_games.discord_status_data)

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
                    config.load() # reload the config
                    RPC_connections[RPC_ID] = DiscordRPC(config, SgdbFetcher)
                    if config.steam.inject_discord_status_data:
                        RPC_connections[RPC_ID].inject_bonus_status_data(config.steam.discord_status_data)

                    RPC_connections[RPC_ID].instanciate(
                        steam_game.app_name,
                        config.steam.discord_fallback_app_id
                    )
                else:
                    break
            
            rpc_ression = RPC_connections[RPC_ID]

            rpc_ression.steam_payload = steam_game

            rpc_ression.update()
            rpc_ression.updateSteamData()
    

    for jellyfin_session in [getter.fetch() for getter in jellyfinGetters]:
        if jellyfin_session and jellyfin_session.media_source_id:
            RPC_ID = jellyfin_session.media_source_id

            if not RPC_connections.get(RPC_ID):
                config.load() # reload the config
                RPC_connections[RPC_ID] = DiscordRPC(config, None)
                RPC_connections[RPC_ID].activity_type = 3

                if config.jellyfin.inject_discord_status_data:
                    logging.info(f"{jellyfin_session.name} is of type {jellyfin_session.media_type}, injecting relevant status data")
                    bonus_status_data: dict = config.jellyfin.per_media_type_discord_status_data.get(jellyfin_session.media_type, {})
                    RPC_connections[RPC_ID].inject_bonus_status_data(bonus_status_data)
                
                RPC_connections[RPC_ID].instanciate(
                    jellyfin_session.series_name or jellyfin_session.name,
                    config.jellyfin.discord_app_id
                )

            
            rpc_ression = RPC_connections[RPC_ID]

            rpc_ression.jellyfin_payload = jellyfin_session

            rpc_ression.start_time = time.time() - jellyfin_session.play_position
            rpc_ression.end_time = time.time() - jellyfin_session.play_position + jellyfin_session.length
            rpc_ression.update()

    logging.debug("Processing complete!")

    if defaultGame and len(RPC_connections) == 0:
        config.load() # reload the config
        logging.info("Switching to displaying the default game.")
        RPC_connections["DEFAULT"] = defaultGame
        RPC_connections["DEFAULT"].default_game_payload = config.default_game
        if config.default_game.inject_discord_status_data:
            RPC_connections[RPC_ID].inject_bonus_status_data(config.default_game.discord_status_data)
        RPC_connections["DEFAULT"].instanciate(config.default_game.name)

    if RPC_connections.get("DEFAULT"):
        if len(RPC_connections) == 1:
            RPC_connections["DEFAULT"].update()
        else:
            RPC_connections.pop("DEFAULT")


    expired_IDs: list[Union[int, str]] = []
    for ID, connection in RPC_connections.items():
        logging.debug(f"Refreshing connection for {ID}")
        if not connection.refresh():
            expired_IDs.append(ID)

    for ID in expired_IDs:
        logging.info(f"Deleting connection to {ID}")
        print("–" * steam_presence.get_terminal_width())
        RPC_connections.pop(ID)
    
    logging.debug("----- Cycle complete -----")
    time.sleep(config.app.cycle_interval)