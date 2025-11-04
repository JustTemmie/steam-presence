
import logging
import json

from src.presence_manager.config import Config, LastFmUser
from src.presence_manager.DataClasses import LastFmFetchPayload

import src.presence_manager.misc as presence_manager


class LastFmGetter:
    def __init__(self, config: Config, user: LastFmUser):
        self.config = config

        self.api_key = user.api_key
        self.username = user.username

    def fetch(self) -> LastFmFetchPayload:
        logging.debug("Fetching last.fm information")
        
        url = f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={self.username}&api_key={self.api_key}&format=json"
        r = presence_manager.fetch(url)

        if not r:
            logging.error("failed to fetch last.fm session for %s", self.username)
            return LastFmFetchPayload()

        data = r.json()
        if not data:
            return LastFmFetchPayload()
        
        # with open("lastfm.json", "w", encoding="utf-8") as f:
        #     json.dump(data, f)

        tracks = data.get("recenttracks", {}).get("track")
        if not (isinstance(tracks, list) and len(tracks) >= 1):
            return LastFmFetchPayload()

        current_track = tracks[0]
        if not isinstance(current_track, dict):
            return LastFmFetchPayload()
        
        # not now playing
        if not current_track.get("@attr", {}).get("nowplaying"):
            return LastFmFetchPayload()
            
        album_art = None
        
        artist_name = current_track.get("artist").get("#text")
        album_name = current_track.get("album", {}).get("#text")
        track_name = current_track.get("name")
        
        track_url = current_track.get("url")

        streamable = current_track.get("streamable")
        
        
        for image in current_track.get("image", []):
            if image.get("size") == "medium":
                album_art = image.get("#text")
                continue
        

        return LastFmFetchPayload(
            username = self.username,

            album_art = album_art,
            artist_name = artist_name,
            album_name = album_name,
            track_name = track_name,
            track_url = track_url,
            streamable = streamable,
        )
