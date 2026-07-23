import logging
from typing import Optional
import requests

from src.steam_presence.config import Config
from src.steam_presence.interfaces import DiscordFetchPayload

from src.steam_presence.fetch import fetch
import src.steam_presence.disk_cache as disk_cache

class DiscordGetter:
    def __init__(self, config: Config):
        self.config = config

    def fetch(self, game) -> DiscordFetchPayload:
        data = self._fetch_discord_data(game)
        if not data:
            return DiscordFetchPayload()

        return DiscordFetchPayload(
            application_id = data.get('id'),
            icon = f"https://cdn.discordapp.com/app-icons/{data.get('id')}/{data.get('icon_hash')}.png?size=160&keep_aspect_ratio=false",
            cover_image = f"https://cdn.discordapp.com/app-icons/{data.get('id')}/{data.get('cover_image_hash')}.png?size=160&keep_aspect_ratio=false",
        )

    def _fetch_discord_data(self, game: str) -> Optional[id]:
        game = game.casefold()

        cache_result = disk_cache.cache_fetch(bank="discord", key=game)
        if cache_result:
            return cache_result

        url = "https://discordapp.com/api/v9/games/detectable"

        r = fetch(url, cache_ttl=21600)

        if r is None:
            logging.info("Discord game search failed")
            return None

        try:
            r.raise_for_status()
            detectables = r.json()
        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError) as e:
            logging.info("Discord game search failed: %s", e)
            return None

        for detectable in detectables:
            name = detectable.get("name", "").casefold()
            aliases = [alias.casefold() for alias in detectable.get("aliases", [])]

            if game in [name] + aliases:
                disk_cache.cache_store(bank="discord", key=game, value=detectable, ttl=3600*24*30)
                return detectable

        return None
