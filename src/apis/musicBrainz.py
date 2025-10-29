import logging

import src.presence_manager.misc as presence_manager

def fetch_cover_art_url(artist: str | None, recording: str | None, release: str | None) -> str | None:
    parts = []
    if artist:
        parts.append(f'artist:"{artist}"')
    if recording:
        parts.append(f'recording:"{recording}"')
    if release:
        parts.append(f'release:"{release}"')
    query = " AND ".join(parts)

    r = presence_manager.fetch(
        f"https://musicbrainz.org/ws/2/recording/?query={query} AND primarytype:album&inc=releases&fmt=json"
    )

    if not r:
        logging.info("MusicBrainz search failed")
        return None
    
    recordings = r.json().get("recordings", [])

    if not recordings:
        logging.info("no matching release found for %s %s", artist, recording)
        return None

    releases = recordings[0].get("releases", [])
    if not releases:
        logging.info("no releases found for %s %s", artist, recording)
        return None
    
    cover_art_resp = presence_manager.fetch(
        f"https://coverartarchive.org/release/{releases[0].get('id')}",
    )

    if not cover_art_resp:
        logging.info("Cover Art Archive request failed")
        return None
    
    data = cover_art_resp.json()

    for img in data.get("images", []):
        print(img.get("thumbnails", {}).get("small"))
        if img.get("front"):
            return img.get("thumbnails", {}).get("small")
    
    if data.get("images"):
        return data["images"][0]["image"]
    
    return None