import logging
from typing import Optional

import src.presence_manager.misc as presence_manager

def fetch_cover_art_url(artist: str, album: str) -> Optional[str]:
    query = f"artist:{artist} AND release:{album}"

    r = presence_manager.fetch(
        f"https://musicbrainz.org/ws/2/release-group/?query={query}&limit=1&fmt=json",
        cache_ttl = 1800
    )

    if not r:
        logging.info("MusicBrainz search failed")
        return None
    
    data = r.json()
    release_group_list = data.get("release-groups", [])
    release_group = release_group_list[0] if release_group_list else {}

    release_list = release_group.get("releases", [])
    release = release_list[0] if release_list else {}

    mb_id = release.get("id")

    if not id:
        logging.info("failed to find a music brainz ID for %s %s", artist, album)
        return None
    
    cover_art_resp = presence_manager.fetch(
        f"https://coverartarchive.org/release/{mb_id}",
        cache_ttl = 1800
    )

    if not cover_art_resp:
        logging.info("Cover Art Archive request failed")
        return None
    
    data = cover_art_resp.json()

    for img in data.get("images", []):
        if img.get("front"):
            return img.get("thumbnails", {}).get("small")
    
    if data.get("images"):
        return data["images"][0]["image"]
    
    return None