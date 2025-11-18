import logging
import time

import src.presence_manager.misc as presence_manager
from src.presence_manager.interfaces import Platforms

from src.getters.JellyfinGetter import JellyfinGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config, JellyfinInstance

intial_config = Config()
intial_config.load()

JELLYFIN_GETTERS: list[JellyfinGetter] = []

if intial_config.jellyfin.enabled:
    for instance in intial_config.jellyfin.instances:
        instance = JellyfinInstance(**instance)
        JELLYFIN_GETTERS.append(JellyfinGetter(intial_config, instance))

del intial_config

def run_jellyfin_cycle(RPC_connections, config: Config):
    if not config.jellyfin.enabled and JELLYFIN_GETTERS:
        return
    
    if presence_manager.blocked_by_presedence(
        Platforms.JELLYFIN,
        RPC_connections.values(),
        config
    ):
        return

    for jellyfin_session in [getter.fetch() for getter in JELLYFIN_GETTERS]:
        if jellyfin_session and jellyfin_session.media_source_id:
            RPC_ID = jellyfin_session.media_source_id

            if not RPC_connections.get(RPC_ID):
                if jellyfin_session.is_paused:
                    continue
                    
                logging.info("Found %s being watched on jellyfin, creating new jellyfin RPC", jellyfin_session.name)
                
                rpc_session = DiscordRPC(config, Platforms.JELLYFIN)

                if config.jellyfin.inject_discord_status_data:
                    logging.info("%s is of type %s, injecting relevant status data", jellyfin_session.name, jellyfin_session.media_type)

                    bonus_status_data: dict = config.jellyfin.per_media_type_discord_status_data.get(jellyfin_session.media_type, {})
                    rpc_session.inject_bonus_status_data(config.jellyfin.default_discord_status_data | bonus_status_data)
                
                rpc_session.instanciate(
                    config.jellyfin.app_name,
                    presence_manager.get_unused_discord_id([rpc.discord_app_id for rpc in RPC_connections.values()], config)
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