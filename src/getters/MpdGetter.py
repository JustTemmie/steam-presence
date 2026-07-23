import logging
import socket
import time

from src.apis.musicBrainz import fetch_cover_art_url

from src.steam_presence.config import Config
from src.steam_presence.interfaces import MpdFetchPayload

class MpdGetter:
    def __init__(self, config: Config):
        self.server_url = config.mpd.server_url
        self.password = config.mpd.password
        self.music_brainz = config.mpd.music_brainz

        self.host, self.port = self.server_url.split(":", 1)

    def fetch(self) -> MpdFetchPayload:
        logging.debug("Fetching MPD information at %s %s", self.host, self.port)
        info = {}

        def parse_data(source_data):
            """
                Converts a string of MPD data into a dictionary object
            """
            parsed_data = {}
            for line in source_data.splitlines():
                if ": " in line:
                    key, val = line.split(": ", 1)
                    parsed_data[key.lower()] = val
            
            return parsed_data

        with socket.create_connection((self.host, self.port)) as conn:
            conn.recv(1024)
            current_song_data = b""
            next_song_data = b""

            if self.password:
                conn.sendall(f"password {self.password}\n".encode())
                response = conn.recv(1024)
                if not response.startswith(b"OK"):
                    logging.critical("MPD password was rejected, don't set a password if the server doesn't need one")
                    exit()

            conn.sendall(b"currentsong\n")
            conn.sendall(b"status\n")

            while current_song_data.count(b"OK\n") < 2:
                current_song_data += conn.recv(4096)
            
            info = parse_data(current_song_data.decode())
            if info.get("nextsongid"):
                payload = f"playlistid {info.get('nextsongid')}\n"
                conn.sendall(payload.encode())

                while next_song_data.count(b"OK\n") < 1:
                    next_song_data += conn.recv(4096)

                info["next_song_data"] = parse_data(next_song_data.decode())

        def generate_mpd_fetch_payload(info) -> MpdFetchPayload:
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
                file = folder = None

                pathes = info.get("file", "").rsplit("/", 2)
                if len(pathes) >= 1:
                    file = pathes[-1]
                if len(pathes) >= 2:
                    folder = pathes[-2]
            except ValueError as _e:
                return MpdFetchPayload()

            return MpdFetchPayload(
                file = file,
                folder = folder,
                file_path = info.get("file"),
                last_modified = info.get("last-modified"),
                added = info.get("added"),
                format = info.get("format"),
                title = info.get("title") or file,
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
        
        payload: MpdFetchPayload = generate_mpd_fetch_payload(info)

        if info.get("next_song_data"):
            payload.next_song_data = generate_mpd_fetch_payload(info.get("next_song_data"))

        return payload
