import logging

import src.presence_manager.misc as presence_manager
import src.presence_manager.cover_art as cover_art
from src.presence_manager.interfaces import Platforms

from src.getters.MpdGetter import MpdGetter
from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config

MPD_GETTER_REFERENCE: list[MpdGetter] = []

def run_mpd_cycle(RPC_connections, config: Config):
    if not config.mpd.enabled:
        return

    if presence_manager.blocked_by_presedence(
        Platforms.MPD,
        RPC_connections.values(),
        config
    ):
        return

    if len(MPD_GETTER_REFERENCE) == 0:
        logging.info("Instancing MPD getter")
        MPD_GETTER_REFERENCE.append(MpdGetter(config))

    data = MPD_GETTER_REFERENCE[0].fetch()

    if not data.title or (data.state and data.state != "play"):
        if RPC_connections.get("MPD"):
            RPC_connections.get("MPD").clear_RPC()

    elif data.state:
        if not RPC_connections.get("MPD"):
            logging.info("Found %s being listened to thru MPD, creating new MPD RPC", data.title)

            rpc_session = DiscordRPC(config, Platforms.MPD)

            if config.mpd.inject_discord_status_data:
                rpc_session.inject_bonus_status_data(config.mpd.discord_status_data)

            rpc_session.instanciate(
                config.mpd.app_name,
                presence_manager.get_unused_discord_id(
                    [rpc.discord_app_id for rpc in RPC_connections.values()],
                    config
                )
            )

            RPC_connections["MPD"] = rpc_session


        rpc_session = RPC_connections.get("MPD")
        # clear any mpd data that may be incorrect for a different song
        if rpc_session.mpd_payload and rpc_session.mpd_payload.title != data.title:
            logging.info("Detected new MPD song %s, updating data", data.title)
            rpc_session.mpd_payload = None
            print("–" * presence_manager.get_terminal_width())

        if data.fetched_at and data.elapsed and data.duration:
            try:
                rpc_session.start_time = data.fetched_at - float(data.elapsed)
                rpc_session.end_time = data.fetched_at - float(data.elapsed) + float(data.duration)
            except ValueError:
                pass

        if isinstance(config.mpd.music_library_base_path, str) and isinstance(data.file_path, str):
            cover_art_hash = cover_art.extract_cover_art(config.mpd.music_library_base_path + data.file_path)
            if cover_art_hash:
                data.catbox_mutagen_art = cover_art.get_catbox_link(cover_art_hash)
        

        rpc_session.mpd_payload = data
        rpc_session.update()