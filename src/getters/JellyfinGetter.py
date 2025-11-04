import logging

from src.presence_manager.config import Config, JellyfinInstance
from src.presence_manager.DataClasses import JellyfinFetchPayload

import src.presence_manager.misc as presence_manager


class JellyfinGetter:
    def __init__(self, config: Config, instance: JellyfinInstance):
        self.config = config

        self.api_key = instance.api_key
        self.username = instance.username
        self.server_url = instance.server_url
        self.public_url = instance.public_url

    def fetch(self) -> JellyfinFetchPayload:
        logging.debug("Fetching jellyfin information")

        url = f"{self.server_url}/Sessions?api_key={self.api_key}"
        r = presence_manager.fetch(url)

        if not r:
            logging.error("failed to fetch jellyfin session for %s", self.username)
            return JellyfinFetchPayload()

        data = r.json()
        if not data:
            return JellyfinFetchPayload()
        
        # with open("test.json", "w", encoding="utf-8") as f:
        #     json.dump(data, f)
        
        for session in data:
            play_state = session.get("PlayState", {})
            now_playing = session.get("NowPlayingItem", {})

            if play_state and now_playing:
                # taglines = now_playing.get("Taglines", [])
                # genres = now_playing.get("Genres", [])
                # studios = now_playing.get("Studios", [])

                return JellyfinFetchPayload(
                    server_url = self.server_url,
                    public_url = self.public_url,

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
                    episode_number = now_playing.get("IndexNumber"),
                    season_number = now_playing.get("ParentIndexNumber"),
                    id = now_playing.get("Id"),
                    series_id = now_playing.get("SeriesId"),
                    parent_backdrop_item_id = now_playing.get("ParentBackdropItemId"),
                    # taglines,
                    # genres,
                    # studios,
                    length = now_playing.get("RunTimeTicks") / 10000 / 1000, # seconds
                    media_type = now_playing.get("Type", "").casefold(),
                )
        
        return JellyfinFetchPayload()


