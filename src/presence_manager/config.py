import logging
import json
from typing import Optional

from dataclasses import dataclass

def _deep_merge(original, update):
    for key, value in update.items():
        if (
            key in original
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(original[key], value)
        else:
            original[key] = value
    
    return original

class GenericConfig:
    def load(self, update: dict):
        data = _deep_merge(self.__dict__, update)
        
        for key, value in data.items():
            setattr(self, key, value)

@dataclass
class DiscordData:
    status_lines: list[str]
    small_images: dict[str, str]
    large_images: dict[str, str]

@dataclass
class SteamUser:
    api_key: str = ""
    user_id: int = 0
    # web_scrape: bool = False
    # auto_fetch_cookies: bool = False
    # cookie_browser: str = ""

@dataclass
class JellyfinInstance:
    api_key: str = ""
    username: str = ""
    server_url: str = ""
    public_url: Optional[str] = None


@dataclass
class LocalProcess:
    process_name: str
    display_name: str

class ConfigApp(GenericConfig):
    def __init__(self):
        self.timeout: int = 30
        self.cycle_interval: int = 20
        self.blacklist: list[str] = []

class ConfigDiscord(GenericConfig):
    def __init__(self):
        self.enabled: bool = True
        self.fallback_app_id: int = 1400019956321620069
        self.custom_app_ids: dict[str, int] = {
            "App name here": 141471589572411256163
        }
        self.presence_manager_app_ids: dict[str, int] = {
            # "official" custom app IDs, overwrite custom_app_ids instead
            # i will _NOT_ merge a PR adding more of these
            # as the creator could delete them in the future, sorry :p
            "The Legend of Zelda: Majora's Mask": 1403714141734309980,
            "Rift Riff": 1403716067821490206,
        }
        self.status_data: DiscordData = {
            "status_lines": [
            ],
            "small_images": {
            },
            "large_images": {
                "{discord.image_url}": None,
                "{steam_grid_db.icon}": None,
                "{steam.capsule_header_image}": None, # these are still here, due to injected status lines being prioritized above all else
                "{steam.capsule_vertical_image}": None,
            },
        }
        # the discord trackmania icon SUCKS due to being super blurry
        # so it's a good example of a per app config
        self.per_app_status_data: dict[str, DiscordData] = {
            "Trackmania": { # case-insensitive name
                "large_images": {
                    "https://img.icons8.com/?size=256&id=LJEz2yMtDm2f": None,
                },
            },
        }

class ConfigSteamGridDB(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.api_key: str = "NONE"

class ConfigSteam(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.users: list[SteamUser] = []
        self.discord_fallback_app_id: int = 1400020030565122139
        # self.steam_store_button: bool = True

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "status_lines": [
                "{steam.rich_presence}",
                "{steam.review_description} reviews ({steam.review_percent}%)",
            ]
        }

# TODO, not implemented
class ConfigEpicGamesStore(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_fallback_app_id: int = 1400020128699256914

class ConfigJellyfin(GenericConfig):
    def __init__(self):
        # warning: if you enable jellyfin images, your IP will be visible via inspect element
        # it will also require your instance to be accessible by the wider internet
        # so an instance URL of http://192.168.1.20:8096 won't work if you want images
        self.enabled: bool = False
        self.instances: list[JellyfinInstance] = []
        self.discord_app_id: int = 1408546253008146472

        self.inject_discord_status_data: bool = True
        self.default_discord_status_data: DiscordData = {
            "large_images": {
                "{jellyfin.public_url}/Items/{jellyfin.id}/Images/Primary": None,
                "https://avatars.githubusercontent.com/u/45698031?s=512.png": None
            }
        }
        self.per_media_type_discord_status_data: dict[str, DiscordData] = {
            "episode": {
                "status_lines": [
                    "S{jellyfin.season_number}E{jellyfin.episode_number} - {jellyfin.name}",
                    "{jellyfin.name}",
                ]
            },
            "movie": {

            }
        }

class ConfigLocal(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_fallback_app_id: int = 1400019956321620069
        self.processes: list[LocalProcess] = []

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {}

class ConfigMpd(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_app_id: int = 1397363004676509729
        self.server_url: str = "localhost:6600"
        self.password: Optional[str] = None

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "status_lines": [
                "{mpd.title}",
                "{mpd.artist} / {mpd.album}",
                "{mpd.artist}",
            ],
            "large_images": {
                "{mpd.music_brainz_cover_art}": None
            }
        }

class ConfigDefaultGame(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_app_id: Optional[int] = None
        self.name: str = "Breath of the Wild"
        self.details: str = "Fighting a Stalnox."
        self.state: str = None

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "status_lines": [
                "{default.details}",
                "{default.state}",
            ]
        }

class Config:
    def __init__(self):
        self.app = ConfigApp()
        self.discord = ConfigDiscord()
        self.steam_grid_db = ConfigSteamGridDB()
        self.steam = ConfigSteam()
        self.epic_games_store = ConfigEpicGamesStore()
        self.jellyfin = ConfigJellyfin()
        self.local = ConfigLocal()
        self.mpd = ConfigMpd()
        self.default_game = ConfigDefaultGame()
    
    def load(self, config_path="config.json"):
        logging.info("Loading config file")

        try:
            with open(config_path, "r", encoding="utf-8", errors="replace") as f:
                config = json.load(f)
        except FileNotFoundError as e:
            if self.app:
                logging.warning("couldn't find config, skipping reload")
                return
            else:
                logging.error("could not find a config path at '%s' - exiting\n%s", config_path, e)
                exit()
        
        self.app.load(config.get("app", {}))
        self.discord.load(config.get("discord", {}))
        self.steam_grid_db.load(config.get("steam_grid_db", {}))
        self.steam.load(config.get("steam", {}))
        self.epic_games_store.load(config.get("epic_games_store", {}))
        self.jellyfin.load(config.get("jellyfin", {}))
        self.local.load(config.get("local", {}))
        self.mpd.load(config.get("mpd", {}))
        self.default_game.load(config.get("default_game", {}))

        # ensure the app name checks are case-insensitive
        case_insensitive_per_app = {}
        for key, value in self.discord.per_app_status_data.items():
            case_insensitive_per_app[key.casefold()] = value
        
        self.discord.per_app_status_data = case_insensitive_per_app