import logging
import socket
import time

from src.apis.musicBrainz import fetch_cover_art_url

from src.presence_manager.config import Config
from src.presence_manager.interfaces import MpdFetchPayload

class MpdGetter:
    def __init__(self, config: Config):
        self.server_url = config.mpd.server_url
        self.password = config.mpd.password
        self.music_brainz = config.mpd.music_brainz

        self.host, self.port = self.server_url.split(":", 1)

    def fetch(self) -> MpdFetchPayload:
        logging.debug("Fetching MPD information at %s %s", self.host, self.port)

        with socket.create_connection((self.host, self.port)) as conn:
            conn.recv(1024)
            data = b""

            if self.password:
                conn.sendall(f"password {self.password}\n".encode())
                response = conn.recv(1024)
                if not response.startswith(b"OK"):
                    logging.critical("MPD password was rejected, don't set a password if the server doesn't need one")
                    exit()

            conn.sendall(b"currentsong\n")
            conn.sendall(b"status\n")

            while data.count(b"OK\n") < 2:
                data += conn.recv(4096)

        info = {}

        try:
            for line in data.decode().splitlines():
                if ": " in line:
                    key, val = line.split(": ", 1)
                    info[key.lower()] = val
        except Exception:
            return MpdFetchPayload()

        if (self.music_brainz and
            info.get("artist") and
            (info.get("album") or info.get("title"))
        ):
            music_brainz_cover_art = fetch_cover_art_url(
                info.get("artist"),
                info.get("album") or info.get("title")
            )
        else:
            music_brainz_cover_art = None

        try:
            folder, file = info.get("file", "").rsplit("/", 1)
        except ValueError:
            return MpdFetchPayload()

        return MpdFetchPayload(
            file = file,
            folder = folder,
            file_path = info.get("file"),
            last_modified = info.get("last-modified"),
            added = info.get("added"),
            format = info.get("format"),
            title = info.get("title"),
            artist = info.get("artist"),
            date = info.get("date"),
            album = info.get("album"),
            track = info.get("track"),
            album_artist = info.get("albumartist"),
            time = info.get("time"),
            duration = info.get("duration"),
            pos = info.get("pos"),

            volume = info.get("volume"),
            repeat = info.get("repeat"),
            random = info.get("random"),
            single = info.get("single"),
            consume = info.get("consume"),
            playlist_length = info.get("playlistlength"),
            state = info.get("state"),
            song = info.get("song"),
            song_id = info.get("songid"),
            elapsed = info.get("elapsed"),
            bitrate = info.get("bitrate"),

            fetched_at = time.time(),

            music_brainz_cover_art = music_brainz_cover_art,
        )
