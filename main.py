
import time
import logging

from typing import Union

from pypresence import ActivityType

import src.presence_manager.logger # just need to initialize it
import src.presence_manager.misc as presence_manager

from src.fetchers.SteamGridDB import SteamGridDB
from src.getters.JellyfinGetter import JellyfinGetter
from src.getters.LocalGetter import LocalGetter
from src.getters.SteamGetter import SteamGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config, SteamUser, JellyfinInstance


logging.info("Starting setup!")

config = Config()
config.load()

logging.info("Generating getters...")

SGDB_FETCHER = None
LOCAL_GETTER = None
STEAM_GETTERS: list[SteamGetter] = []
JELLYFIN_GETTERS: list[JellyfinGetter] = []

DEFAULT_GAME: DiscordRPC = None

# key is just a generic identifier such as process ID or steam ID
RPC_connections: dict[Union[int, str], DiscordRPC] = {}


if config.steam_grid_db.enabled:
    SGDB_FETCHER = SteamGridDB(config)

if config.local.enabled:
    LOCAL_GETTER = LocalGetter(config)

if config.default_game.enabled:
    DEFAULT_GAME = DiscordRPC(config, SGDB_FETCHER)

if config.steam.enabled:
    for user in config.steam.users:
        # convert user dict into dataclass
        user = SteamUser(**user)
        STEAM_GETTERS.append(SteamGetter(config, user))

if config.jellyfin.enabled:
    for instance in config.jellyfin.instances:
        instance = JellyfinInstance(**instance)
        JELLYFIN_GETTERS.append(JellyfinGetter(config, instance))

logging.info("Setup complete!")
print("–" * presence_manager.get_terminal_width())

while True:
    if LOCAL_GETTER:
        processes = LOCAL_GETTER.fetch()

        for process in processes:
            RPC_ID = process.process_name
            if not RPC_connections.get(RPC_ID):
                if process.display_name:
                    config.load() # reload the config on new RPC connection
                    RPC_connections[RPC_ID] = DiscordRPC(config, SGDB_FETCHER)

                    if config.local.inject_discord_status_data:
                        RPC_connections[RPC_ID].inject_bonus_status_data(config.local.discord_status_data)

                    RPC_connections[RPC_ID].instanciate(
                        process.display_name,
                        config.local.discord_fallback_app_id
                    )
                    
                    RPC_connections[RPC_ID].start_time = process.start_time
                else:
                    break
                
            game = RPC_connections[RPC_ID]

            game.local_payload = process

            game.update()

    for steam_game in [getter.fetch() for getter in STEAM_GETTERS]:
        if steam_game:
            RPC_ID = steam_game.app_id

            if not RPC_connections.get(RPC_ID):
                if steam_game.app_name:
                    config.load() # reload the config
                    RPC_connections[RPC_ID] = DiscordRPC(config, SGDB_FETCHER)
                    if config.steam.inject_discord_status_data:
                        RPC_connections[RPC_ID].inject_bonus_status_data(config.steam.discord_status_data)

                    RPC_connections[RPC_ID].instanciate(
                        steam_game.app_name,
                        config.steam.discord_fallback_app_id
                    )

                    RPC_connections[RPC_ID].start_time = time.time()
                else:
                    break
            
            rpc_ression = RPC_connections[RPC_ID]

            rpc_ression.steam_payload = steam_game

            rpc_ression.update()
            rpc_ression.update_steam_data()
    

    for jellyfin_session in [getter.fetch() for getter in JELLYFIN_GETTERS]:
        if jellyfin_session and jellyfin_session.media_source_id:
            RPC_ID = jellyfin_session.media_source_id

            if not RPC_connections.get(RPC_ID):
                if jellyfin_session.is_paused:
                    continue
                
                config.load() # reload the config
                RPC_connections[RPC_ID] = DiscordRPC(config, None)
                RPC_connections[RPC_ID].activity_type = ActivityType.WATCHING

                if config.jellyfin.inject_discord_status_data:
                    logging.info("%s is of type %s, injecting relevant status data", jellyfin_session.name, jellyfin_session.media_type)

                    bonus_status_data: dict = config.jellyfin.per_media_type_discord_status_data.get(jellyfin_session.media_type, {})
                    RPC_connections[RPC_ID].inject_bonus_status_data(bonus_status_data | config.jellyfin.default_discord_status_data)
                
                RPC_connections[RPC_ID].instanciate(
                    jellyfin_session.series_name or jellyfin_session.name,
                    config.jellyfin.discord_app_id
                )

            rpc_ression = RPC_connections[RPC_ID]
            rpc_ression.jellyfin_payload = jellyfin_session
            
            if jellyfin_session.is_paused:
                rpc_ression.start_time = None
                rpc_ression.end_time = None
            
            else:
                rpc_ression.start_time = time.time() - jellyfin_session.play_position
                rpc_ression.end_time = time.time() - jellyfin_session.play_position + jellyfin_session.length
                rpc_ression.update()
            

    logging.debug("Processing complete!")

    if DEFAULT_GAME and len(RPC_connections) == 0:
        config.load() # reload the config
        logging.info("Switching to displaying the default game.")
        RPC_connections["DEFAULT"] = DEFAULT_GAME
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
    for identifier, connection in RPC_connections.items():
        logging.debug("Refreshing connection for %s", identifier)
        if not connection.refresh():
            expired_IDs.append(identifier)

    for identifier in expired_IDs:
        logging.info("Deleting connection to %s", identifier)
        print("–" * presence_manager.get_terminal_width())
        RPC_connections.pop(identifier)
    
    logging.debug("----- Cycle complete -----")
    time.sleep(config.app.cycle_interval)