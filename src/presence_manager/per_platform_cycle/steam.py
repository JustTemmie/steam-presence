import logging

import src.presence_manager.misc as presence_manager
from src.presence_manager.interfaces import Platforms

import src.apis.steamGridDB as steamGridDB
from src.getters.SteamGetter import SteamGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config, SteamUser

intial_config = Config()
intial_config.load()

STEAM_GETTERS: list[SteamGetter] = []

if intial_config.steam.enabled:
    for user in intial_config.steam.users:
        user = SteamUser(**user)
        STEAM_GETTERS.append(SteamGetter(intial_config, user))

del intial_config

def run_steam_cycle(RPC_connections, config: Config, ):
    if not config.steam.enabled and STEAM_GETTERS:
        return
    
    if presence_manager.blocked_by_presedence(
        Platforms.STEAM,
        RPC_connections.values(),
        config
    ):
        return

    for steam_game in [getter.fetch() for getter in STEAM_GETTERS]:
        if steam_game:
            rpc_id = steam_game.app_id

            if not RPC_connections.get(rpc_id):
                if not steam_game.app_name:
                    continue
                
                logging.info("Found %s being played on steam, creating new steam RPC", steam_game.app_name)

                rpc_session = DiscordRPC(config, Platforms.STEAM)

                if config.steam_grid_db.enabled and steam_game.app_id:
                    rpc_session.steam_grid_db_payload = steamGridDB.fetch_steam_grid_db(
                        config = config,
                        app_id = steam_game.app_id,
                        platform = steamGridDB.SteamGridPlatforms.STEAM
                    )

                if config.steam.inject_discord_status_data:
                    rpc_session.inject_bonus_status_data(config.steam.discord_status_data)

                rpc_session.instanciate(
                    steam_game.app_name,
                    presence_manager.get_unused_discord_id([rpc.discord_app_id for rpc in RPC_connections.values()], config)
                )

                RPC_connections[rpc_id] = rpc_session
            
            rpc_session = RPC_connections[rpc_id]

            rpc_session.steam_payload = steam_game

            rpc_session.update()