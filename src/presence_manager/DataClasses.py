from dataclasses import dataclass

# ID: "discord"
@dataclass
class DiscordDataPayload:
    app_id: int | None = None
    image_url: str | None = None
    steam_app_id: str | None = None
    name: str | None = None

# ID: "steam_grid_db"
@dataclass
class SteamGridDBFetchPayload:
    icon: str | None = None

# ID: "epic_games_store"
@dataclass
class EpicGamesStoreFetchPayload:
    pass

# ID: "jellyfin"
@dataclass
class JellyfinDataPayload:
    user_name: str | None = None
    client: str | None = None
    device_name: str | None = None

    play_position: float | None = None
    media_source_id: str | None = None
    is_paused: bool | None = None
    
    name: str | None = None
    series_name: str | None = None
    series_studio: str | None = None
    production_year: int | None = None
    overview: str | None = None
    length: float | None = None
    media_type: str | None = None

# ID: "local"
@dataclass
class LocalGameFetchPayload:
    process_name: str
    process_ID: int | None = None
    start_time: int | None = None
    process_exe: str | None = None
    display_name: str | None = None

# ID: "steam"
@dataclass
class SteamFetchPayload:
    capsule_vertical_image: str = None

    # Current account state
    app_name: str | None = None
    app_id: int | None = None
    avatar_url: str | None = None
    display_name: str | None = None
    profile_url: str | None = None

    # Current mini profile data
    rich_presence: str | None = None
    mini_profile_background_url: str | None = None
    profile_level: str | None = None
    profile_badge_url: str | None = None
    profile_badge_name: str | None = None

    # App details
    # example: https://store.steampowered.com/api/appdetails?appids=218620
    required_age: int | None = None
    capsule_header_image: str | None = None
    capsule_main_image: str | None = None
    website: str | None = None
    developers: str = None
    publishers: str = None
    price_currency: str | None = None
    price_initial: int | None = None
    price_current: int | None = None
    price_discount_percent: int | None = None
    price_formatted: str | None = None
    platform_windows: bool | None = None
    platform_mac: bool | None = None
    platform_linux: bool | None = None
    achievement_count: int | None = None
    release_date: str | None = None

    # Review Data
    # example: https://store.steampowered.com/appreviews/218620
    total_positive_reviews: int | None = None
    total_negative_reviews: int | None = None
    total_reviews: int | None = None
    review_percent: int | None = None
    review_description: str | None = None