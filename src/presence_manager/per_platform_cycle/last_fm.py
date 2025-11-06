import logging

import src.presence_manager.misc as presence_manager

from src.getters.LastFmGetter import LastFmGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config, LastFmUser

inital_config = Config()
inital_config.load()

LAST_FM_GETTERS: list[LastFmGetter] = []

if inital_config.last_fm.enabled:
    for user in inital_config.last_fm.users:
        user = LastFmUser(**user)
        LAST_FM_GETTERS.append(LastFmGetter(inital_config, user))

del inital_config

def run_last_fm_cycle(RPC_connections, config: Config):
    if not config.last_fm.enabled:
        return
    
    for last_fm_session in [getter.fetch() for getter in LAST_FM_GETTERS]:
        if last_fm_session and last_fm_session.username:
            rpc_id = f"{last_fm_session.username}/Last.fm"

            if not last_fm_session.track_name:
                if RPC_connections.get(rpc_id):
                    logging.info("Last.fm is paused, closing discord RPC")
                    RPC_connections.get(rpc_id).close_RPC()
                    RPC_connections.pop(rpc_id)

            else:
                if not RPC_connections.get(rpc_id):                        
                    logging.info("Found %s listening to music thru last.fm, creating new last.fm RPC", last_fm_session.username)
                    
                    rpc_session = DiscordRPC(config)

                    if config.last_fm.inject_discord_status_data:
                        rpc_session.inject_bonus_status_data(config.last_fm.discord_status_data)

                    rpc_session.instanciate(
                        config.last_fm.app_name,
                        presence_manager.get_unused_discord_id([rpc.discord_app_id for rpc in RPC_connections.values()], config)
                    )

                    rpc_session.start_time = None

                    RPC_connections[rpc_id] = rpc_session
                
                # note that start and end time aren't set for last.fm, as the data is simply not available
                rpc_session = RPC_connections[rpc_id]
                rpc_session.last_fm_payload = last_fm_session
                
                rpc_session.update()