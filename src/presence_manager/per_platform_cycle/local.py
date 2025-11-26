import logging

import src.presence_manager.misc as presence_manager
from src.presence_manager.interfaces import Platforms

import src.apis.steamGridDB as steamGridDB
from src.getters.LocalGetter import LocalGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config

LOCAL_GETTER_REFERENCE: list[LocalGetter] = []

def run_local_cycle(RPC_connections, config: Config):
    if not config.local.enabled:
        return

    if presence_manager.blocked_by_presedence(
        Platforms.LOCAL,
        RPC_connections.values(),
        config
    ):
        return
    
    if len(LOCAL_GETTER_REFERENCE) == 0:
        logging.info("Instancing Local getter")
        LOCAL_GETTER_REFERENCE.append(LocalGetter(config))

    processes = LOCAL_GETTER_REFERENCE[0].fetch()
    
    for process in processes:
        rpc_id = process.process_name

        if not RPC_connections.get(rpc_id):
            if process.display_name:

                logging.info("Found process %s locally, creating new local RPC", process.process_exe)

                rpc_session = DiscordRPC(config, Platforms.LOCAL)

                if config.steam_grid_db.enabled:
                    rpc_session.steam_grid_db_payload = steamGridDB.fetch_steam_grid_db(
                        config = config,
                        app_name = process.display_name
                    )

                if config.local.inject_discord_status_data:
                    rpc_session.inject_bonus_status_data(config.local.discord_status_data)

                rpc_session.instanciate(
                    process.display_name,
                    presence_manager.get_unused_discord_id([rpc.discord_app_id for rpc in RPC_connections.values()], config)
                )
                
                rpc_session.start_time = process.start_time

                RPC_connections[rpc_id] = rpc_session
            else:
                break
            
        game = RPC_connections[rpc_id]

        game.local_payload = process

        game.update()