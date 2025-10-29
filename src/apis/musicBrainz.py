import logging
import requests

def fetch_cover_art_url(artist: str | None, recording: str | None, release: str | None) -> str | None:
    parts = []
    if artist:
        parts.append(f'artist:"{artist}"')
    if recording:
        parts.append(f'recording:"{recording}"')
    if release:
        parts.append(f'release:"{release}"')
    query = " AND ".join(parts)

    search_resp = requests.get(
        f'https://musicbrainz.org/ws/2/recording/?query={query} AND primarytype:album&inc=releases&fmt=json',
        timeout=10,
    )

    if search_resp.status_code != 200:
        logging.info("MusicBrainz search failed: %s", search_resp.status_code)
        return None
    
    recordings = search_resp.json().get("recordings", [])

    if not recordings:
        logging.info("no matching release found for %s %s", artist, recording)
        return None

    mbid = recordings[0].get("releases", [])[0].get("id")
    cover_art_resp = requests.get(
        f"https://coverartarchive.org/release/{mbid}",
        timeout=10
    )

    if cover_art_resp.status_code != 200:
        logging.info("Cover Art Archive request failed: %s", cover_art_resp.status_code)
        return None
    
    data = cover_art_resp.json()

    for img in data.get("images", []):
        print(img.get("thumbnails", {}).get("small"))
        if img.get("front"):
            return img.get("thumbnails", {}).get("small")
    if data.get("images"):
        return data["images"][0]["image"]
    
    return None