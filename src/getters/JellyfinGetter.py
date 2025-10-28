import logging
import json

from src.presence_manager.config import Config, JellyfinInstance
from src.presence_manager.DataClasses import JellyfinDataPayload

import src.presence_manager.misc as presence_manager




class JellyfinGetter:
    def __init__(self, config: Config, instance: JellyfinInstance):
        self.config = config

        self.api_key = instance.api_key
        self.username = instance.username
        self.url = instance.instance_url

    def fetch(self) -> JellyfinDataPayload:
        logging.debug("Fetching jellyfin information")

        url = f"{self.url}/Sessions?api_key={self.api_key}"
        r = presence_manager.fetch(url)

        if not r:
            logging.error("failed to fetch jellyfin session for %s", self.username)
            return JellyfinDataPayload()

        data = r.json()
        if not data:
            return JellyfinDataPayload()
        
        with open("test.json", "w") as f:
            json.dump(data, f)
        
        for session in data:
            play_state = session.get("PlayState", {})
            now_playing = session.get("NowPlayingItem", {})

            if play_state and now_playing:
                # taglines = now_playing.get("Taglines", [])
                # genres = now_playing.get("Genres", [])
                # studios = now_playing.get("Studios", [])

                return JellyfinDataPayload(
                    user_name = session.get("UserName"),
                    client = session.get("Client"),
                    device_name = session.get("DeviceName"),

                    play_position = play_state.get("PositionTicks") / 10000 / 1000, # seconds
                    media_source_id = play_state.get("MediaSourceId"),
                    is_paused = play_state.get("IsPaused"),

                    name = now_playing.get("Name"),
                    series_name = now_playing.get("SeriesName"),
                    series_studio = now_playing.get("SeriesStudio"),
                    production_year = now_playing.get("ProductionYear"),
                    overview = now_playing.get("Overview"),
                    # taglines,
                    # genres,
                    # studios,
                    length = now_playing.get("RunTimeTicks") / 10000 / 1000, # seconds
                    media_type = now_playing.get("Type", "").casefold(),
                )
        
        return JellyfinDataPayload()


