import logging
import socket

from src.presence_manager.config import Config
from src.presence_manager.DataClasses import MpdFetchPayload

class MpdGetter:
    def __init__(self, config: Config):
        self.server_url = config.mpd.server_url
        self.password = config.mpd.password

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

            # this might break under high latency? i'm unsure – sockets are weird
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

        return MpdFetchPayload(
            file = info.get("file"),
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
        )


