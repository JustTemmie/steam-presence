import logging

import src.presence_manager.misc as presence_manager

from src.getters.LocalGetter import LocalGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config

inital_config = Config()
inital_config.load()

LOCAL_GETTER = LocalGetter(inital_config) if inital_config.local.enabled else None

del inital_config

def run_local_cycle(RPC_connections, config: Config):
    if not config.local.enabled:
        return

    processes = LOCAL_GETTER.fetch()
    
    for process in processes:
        rpc_id = process.process_name

        if not RPC_connections.get(rpc_id):
            if process.display_name:

                logging.info("Found process %s locally, creating new local RPC", process.process_exe)


                rpc_session = DiscordRPC(config)

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