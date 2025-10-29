
import time
import logging

from typing import Union

from pypresence import ActivityType

import src.presence_manager.logger # just need to initialize it
import src.presence_manager.misc as presence_manager

import src.apis.SteamGridDB as SteamGridDB

from src.getters.JellyfinGetter import JellyfinGetter
from src.getters.LocalGetter import LocalGetter
from src.getters.MpdGetter import MpdGetter
from src.getters.SteamGetter import SteamGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config, SteamUser, JellyfinInstance


logging.info("Starting setup!")

config = Config()
config.load()

logging.info("Generating getters...")

LOCAL_GETTER = None
MPD_GETTER = None
STEAM_GETTERS: list[SteamGetter] = []
JELLYFIN_GETTERS: list[JellyfinGetter] = []

DEFAULT_GAME: DiscordRPC = None

# key is just a generic identifier such as process ID or steam ID
RPC_connections: dict[Union[int, str], DiscordRPC] = {}

if config.local.enabled:
    LOCAL_GETTER = LocalGetter(config)

if config.mpd.enabled:
    MPD_GETTER = MpdGetter(config)

if config.default_game.enabled:
    DEFAULT_GAME = DiscordRPC(config)

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
                    rpc_session = DiscordRPC(config)

                    if config.local.inject_discord_status_data:
                        rpc_session.inject_bonus_status_data(config.local.discord_status_data)

                    rpc_session.instanciate(
                        process.display_name,
                        config.local.discord_fallback_app_id
                    )
                    
                    rpc_session.start_time = process.start_time

                    RPC_connections[RPC_ID] = rpc_session
                else:
                    break
                
            game = RPC_connections[RPC_ID]

            game.local_payload = process

            game.update()
    
    if MPD_GETTER:
        data = MPD_GETTER.fetch()

        if data.title:
            if data.state == "pause":
                if RPC_connections.get("MPD"):
                    logging.info("MPD is paused, closing discord RPC")
                    RPC_connections.get("MPD").close_RPC()
                    RPC_connections.pop("MPD")

            else:
                if not RPC_connections.get("MPD"):
                    config.load()
                    rpc_session = DiscordRPC(config)

                    if config.mpd.inject_discord_status_data:
                        rpc_session.inject_bonus_status_data(config.mpd.discord_status_data)
                    
                    rpc_session.instanciate(
                        "MPD",
                        platform_fallback_app_id = config.mpd.discord_app_id,
                        activity_type = ActivityType.LISTENING
                    )

                    rpc_session.app_id_is_name = True

                    RPC_connections["MPD"] = rpc_session

                rpc_session = RPC_connections.get("MPD")
                
                if data.fetched_at and data.elapsed and data.duration:
                    try:
                        rpc_session.start_time = data.fetched_at - float(data.elapsed)
                        rpc_session.end_time = data.fetched_at - float(data.elapsed) + float(data.duration)
                    except ValueError:
                        pass

                rpc_session.mpd_payload = data
                rpc_session.update()
            


    for steam_game in [getter.fetch() for getter in STEAM_GETTERS]:
        if steam_game:
            RPC_ID = steam_game.app_id

            if not RPC_connections.get(RPC_ID):
                if not steam_game.app_name:
                    continue

                config.load() # reload the config
                rpc_session = DiscordRPC(config)

                if config.steam_grid_db.enabled and steam_game.app_id:
                    rpc_session.steam_grid_db_payload = SteamGridDB.fetch_steam_grid_db(
                        api_key = config.steam_grid_db.api_key,
                        app_id = steam_game.app_id,
                        platform = SteamGridDB.SteamGridPlatforms.STEAM
                    )

                if config.steam.inject_discord_status_data:
                    rpc_session.inject_bonus_status_data(config.steam.discord_status_data)

                rpc_session.instanciate(
                    steam_game.app_name,
                    platform_fallback_app_id = config.steam.discord_fallback_app_id
                )

                RPC_connections[RPC_ID] = rpc_session
            
            rpc_session = RPC_connections[RPC_ID]

            rpc_session.steam_payload = steam_game

            rpc_session.update()
            rpc_session.update_steam_data()
    

    for jellyfin_session in [getter.fetch() for getter in JELLYFIN_GETTERS]:
        if jellyfin_session and jellyfin_session.media_source_id:
            RPC_ID = jellyfin_session.media_source_id

            if not RPC_connections.get(RPC_ID):
                if jellyfin_session.is_paused:
                    continue
                
                config.load() # reload the config
                rpc_session = DiscordRPC(config)

                if config.jellyfin.inject_discord_status_data:
                    logging.info("%s is of type %s, injecting relevant status data", jellyfin_session.name, jellyfin_session.media_type)

                    bonus_status_data: dict = config.jellyfin.per_media_type_discord_status_data.get(jellyfin_session.media_type, {})
                    rpc_session.inject_bonus_status_data(bonus_status_data | config.jellyfin.default_discord_status_data)
                
                rpc_session.instanciate(
                    jellyfin_session.series_name or jellyfin_session.name,
                    platform_fallback_app_id = config.jellyfin.discord_app_id,
                    activity_type = ActivityType.WATCHING
                )

                RPC_connections[RPC_ID] = rpc_session

            rpc_session = RPC_connections[RPC_ID]
            rpc_session.jellyfin_payload = jellyfin_session
            
            if jellyfin_session.is_paused:
                logging.info("jellyfin is paused, closing discord RPC")
                rpc_session.close_RPC()
                RPC_connections.pop(RPC_ID)
            
            else:
                rpc_session.start_time = time.time() - jellyfin_session.play_position
                rpc_session.end_time = time.time() - jellyfin_session.play_position + jellyfin_session.length
                rpc_session.update()
            

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
    
    logging.debug("----- Cycle completed at %s -----", round(time.time()))
    time.sleep(config.app.cycle_interval)