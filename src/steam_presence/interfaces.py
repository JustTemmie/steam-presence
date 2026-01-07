from dataclasses import dataclass
from typing import Optional
from enum import Enum

class Platforms(Enum):
    UNKNOWN = "unknown" # used as fallback
    EPIC_GAMES_STORE = "epic_games_store"
    JELLYFIN = "jellyfin"
    LAST_FM = "last_fm"
    LOCAL = "local"
    MPD = "mpd"
    STEAM = "steam"

# ID: "steam_grid_db"
@dataclass
class SteamGridDBFetchPayload:
    icon: Optional[str] = None

# ID: "epic_games_store"
@dataclass
class EpicGamesStoreFetchPayload:
    pass

# ID: "jellyfin"
@dataclass
class JellyfinFetchPayload:
    server_url: Optional[str] = None
    public_url: Optional[str] = None

    user_name: Optional[str] = None
    client: Optional[str] = None
    device_name: Optional[str] = None

    play_position: Optional[float] = None
    media_source_id: Optional[str] = None
    is_paused: Optional[bool] = None

    name: Optional[str] = None
    series_name: Optional[str] = None
    series_studio: Optional[str] = None
    production_year: Optional[int] = None
    overview: Optional[str] = None
    episode_number: Optional[str] = None
    season_number: Optional[str] = None
    id: Optional[str] = None
    series_id: Optional[str] = None
    parent_backdrop_item_id: Optional[str] = None
    length: Optional[float] = None
    media_type: Optional[str] = None

# ID: "local"
@dataclass
class LocalGameFetchPayload:
    process_name: str
    process_ID: Optional[int] = None
    start_time: Optional[int] = None
    process_exe: Optional[str] = None
    display_name: Optional[str] = None

# ID: "mpd"
@dataclass
class MpdFetchPayload:
    file: Optional[str] = None
    folder: Optional[str] = None

    file_path: Optional[str] = None
    last_modified: Optional[str] = None
    added: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    date: Optional[str] = None
    album: Optional[str] = None
    track: Optional[str] = None
    album_artist: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[str] = None
    pos: Optional[str] = None

    volume: Optional[str] = None
    repeat: Optional[str] = None
    random: Optional[str] = None
    single: Optional[str] = None
    consume: Optional[str] = None
    playlist_length: Optional[str] = None
    state: Optional[str] = None
    song: Optional[str] = None
    song_id: Optional[str] = None
    elapsed: Optional[str] = None
    bitrate: Optional[str] = None

    fetched_at: Optional[float] = None

    music_brainz_cover_art: Optional[str] = None
    catbox_mutagen_art: Optional[str] = None

# ID: "last_fm"
@dataclass
class LastFmFetchPayload:
    username: Optional[str] = None

    album_art: Optional[str] = None
    artist_name: Optional[str] = None
    album_name: Optional[str] = None
    track_name: Optional[str] = None
    track_url: Optional[str] = None
    streamable: Optional[str] = None

# ID: "steam"
@dataclass
class SteamFetchPayload:
    capsule_vertical_image: str = None
    hero_capsule: str = None
    logo: str = None

    # Current account state
    app_name: Optional[str] = None
    app_id: Optional[int] = None
    avatar_url: Optional[str] = None
    display_name: Optional[str] = None
    profile_url: Optional[str] = None

    # Current mini profile data
    rich_presence: Optional[str] = None
    mini_profile_background_url: Optional[str] = None
    profile_level: Optional[str] = None
    profile_badge_url: Optional[str] = None
    profile_badge_name: Optional[str] = None

    # App details
    # example: https://store.steampowered.com/api/appdetails?appids=218620
    required_age: Optional[int] = None
    capsule_header_image: Optional[str] = None
    capsule_main_image: Optional[str] = None
    website: Optional[str] = None
    developers: Optional[str] = None
    publishers: Optional[str] = None
    price_currency: Optional[str] = None
    price_initial: Optional[int] = None
    price_current: Optional[int] = None
    price_discount_percent: Optional[int] = None
    price_formatted: Optional[str] = None
    platform_windows: Optional[bool] = None
    platform_mac: Optional[bool] = None
    platform_linux: Optional[bool] = None
    achievement_count: Optional[int] = None
    release_date: Optional[str] = None

    # Review Data
    # example: https://store.steampowered.com/appreviews/218620
    total_positive_reviews: Optional[int] = None
    total_negative_reviews: Optional[int] = None
    total_reviews: Optional[int] = None
    review_percent: Optional[int] = None
    review_description: Optional[str] = None
