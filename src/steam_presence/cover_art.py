import os
import json
import hashlib
import threading
import logging

from base64 import b64decode
from typing import Optional
from mutagen import File

import src.apis.catbox as catbox
import src.steam_presence.disk_cache as disk_cache

mpd_directory = "cache/mpd/"

def extract_cover_art(file_path: str) -> Optional[str]:
    """
        extracts cover art from mp3, ogg, and flac files
    """
    
    # make sure the file actually exists
    if not os.path.exists(file_path):
        return
    
    lookup_table_path = mpd_directory + "lookup_table.json"

    lookup_table = {}

    os.makedirs(mpd_directory, exist_ok=True)
    if os.path.exists(lookup_table_path):
        with open(lookup_table_path, 'r', encoding='utf-8') as f:
            lookup_table = json.load(f)
    
    with open(file_path, 'rb') as f:
        music_hash = hashlib.file_digest(f, "sha256").hexdigest()
        art_hash = lookup_table.get(music_hash)

        if art_hash:
            return art_hash

    audio = File(file_path)

    if audio is None:
        logging.critical("couldn't load audio file %s", file_path)
        return

    def save_as_file_hash(data):
        art_hash = hashlib.sha256(data).hexdigest()
        lookup_table[music_hash] = art_hash

        with open(lookup_table_path, 'w', encoding='utf-8') as f:
            json.dump(lookup_table, f)

        output_path = mpd_directory + f"{art_hash}.jpg"
        if not os.path.exists(output_path):
            with open(output_path, "wb") as f:
                f.write(data)

        return art_hash

    if hasattr(audio, "pictures") and audio.pictures:
        # FLAC format
        if isinstance(audio.pictures, list) and len(audio.pictures) > 0:
            picture = audio.pictures[0]
            return save_as_file_hash(picture.data)

    elif hasattr(audio, "tags") and audio.tags:
        # MP3 format
        for tag in audio.tags.values():
            if hasattr(tag, 'FrameID') and tag.FrameID == "APIC":
                return save_as_file_hash(tag.data)

        # OGG format
        if "metadata_block_picture" in audio:
            data = b64decode(audio["metadata_block_picture"][0])
            return save_as_file_hash(data)

    logging.info("couldn't find any cover art for %s", file_path)
    return None

def get_catbox_link(art_hash: str) -> Optional[str]:
    # 90 day ttl, they should in theory never be deleted on the catbox servers
    cache_result = disk_cache.cache_fetch(bank="mpd", key=art_hash, ttl=86400*90)
    if cache_result:
        return cache_result.get("url")

    def upload_task():
        file_path = mpd_directory + f"{art_hash}.jpg"
        link = catbox.upload_file(file_path, ttl="72h")
        if link:
            disk_cache.cache_store(bank="mpd", key=art_hash, value={"url": link})

    threading.Thread(target=upload_task, daemon=True).start()
    return None