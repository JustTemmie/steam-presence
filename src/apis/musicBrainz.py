import logging
import requests
from typing import Optional

from src.presence_manager.fetch import fetch

def fetch_cover_art_url(artist: str, album: str) -> Optional[str]:
    query = f"artist:{artist} AND release:{album}"

    r = fetch(
        f"https://musicbrainz.org/ws/2/release-group/?query={query}&limit=1&fmt=json",
        cache_ttl = 7200
    )

    if r is None:
        logging.info("MusicBrainz search failed")
        return None

    try:
        r.raise_for_status()
        data = r.json()
    except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError) as e:
        logging.info("MusicBrainz search failed: %s", e)
        return None
    
    release_group_list = data.get("release-groups", [])
    release_group = release_group_list[0] if release_group_list else {}

    release_list = release_group.get("releases", [])
    release = release_list[0] if release_list else {}

    mb_id = release.get("id")

    if not id:
        logging.info("failed to find a music brainz ID for %s %s", artist, album)
        return None

    cover_art_resp = fetch(
        f"https://coverartarchive.org/release/{mb_id}",
        cache_ttl = 3600
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
