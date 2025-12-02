import logging
import json
from typing import Optional
from pypresence import ActivityType, StatusDisplayType

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
    activity_type: Optional[ActivityType]
    status_display_type: Optional[StatusDisplayType]
    status_lines: list[str]
    small_images: dict[str, str]
    large_images: dict[str, str]
    buttons: dict[str, str]

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
class LastFmUser:
    api_key: str = ""
    username: str = ""

@dataclass
class LocalProcess:
    process_name: str
    display_name: str

@dataclass
class SGDBLookupTable:
    name: str
    id: int

class ConfigApp(GenericConfig):
    def __init__(self):
        self.timeout: int = 55
        self.cycle_interval: int = 5
        self.blacklist: list[str] = []
        self.presedence_rules: dict[str: str] = {
            # "mpd": "last_fm" # in this example, mpd takes presedence over last.fm
        }

class ConfigDiscord(GenericConfig):
    def __init__(self):
        self.enabled: bool = True
        # discord only displays 1 app ID on your profile at a time, so we're just using 20 hard coded app IDs
        # these are *NOT* user IDs, do *NOT* change these unless you actively use the discord developer portal
        # i will make fun of you in public discussions if you run into problems due to changing these
        self.app_ids: list[int] = [
            1433256589011321014,
            1433256631692693645,
            1433256671072882829,
            1433256701313945630,
            1433256734390227114,
            1433256768414421032,
            1433256801830436974,
            1433256843169497148,
            1433256891588542634,
            1433283419613171763,
            1433283473157656657,
            1433283516803584071,
            1433283551494930624,
            1433283600035479704,
            1445382457271652474,
            1445382571591602217,
            1445382681411063840,
            1445382780002238545,
            1445382923900686418,
            1445383025365094422
        ]

        self.status_data: DiscordData = {
            "activity_type": ActivityType.PLAYING,
            "status_display_type": StatusDisplayType.NAME,
            "status_lines": [
            ],
            "small_images": {
            },
            "large_images": {
                "{steam_grid_db.icon}": None,
                "{steam.capsule_header_image}": None, # these are still here, due to injected status lines being prioritized above all else
                "{steam.capsule_vertical_image}": None,
                "{steam.hero_capsule}": None,
            },
            "buttons": {

            }
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
        self.lookup_table: list[SGDBLookupTable] = [
            {
                "name": "Blender",
                "id": 5247796
            }
        ]

class ConfigSteam(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.cooldown: int = 25
        self.users: list[SteamUser] = []
        # self.steam_store_button: bool = True

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "status_lines": [
                "{steam.rich_presence}",
                "{steam.review_description} reviews ({steam.review_percent}%)",
            ],
            "buttons": {
                "on steam! – {steam.price_formatted}": "https://store.steampowered.com/app/{steam.app_id}"
            }
        }

# TODO, not implemented
class ConfigEpicGamesStore(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.cooldown: int = 20

class ConfigJellyfin(GenericConfig):
    def __init__(self):
        # warning: if you enable jellyfin images, your IP will be visible via inspect element
        # it will also require your instance to be accessible by the wider internet
        # so an instance URL of http://192.168.1.20:8096 won't work if you want images
        self.enabled: bool = False
        self.cooldown: int = 0
        self.instances: list[JellyfinInstance] = []

        self.app_name: str = "Jellyfin"
        self.inject_discord_status_data: bool = True
        self.default_discord_status_data: DiscordData = {
            "activity_type": ActivityType.WATCHING,
            "status_display_type": StatusDisplayType.DETAILS,
            "large_images": {
                # after playing around with the numbers, this seems to be close the best resolution for discord
                # anything higher and it just looks "oversharpened"
                "{jellyfin.public_url}/Items/{jellyfin.series_id}/Images/Primary?fillHeight=128&fillWidth=128&quality=100": None,
                "{jellyfin.public_url}/Items/{jellyfin.id}/Images/Primary?fillHeight=128&fillWidth=128&quality=100": None,
                "https://avatars.githubusercontent.com/u/45698031?s=512.png": None
            }
        }
        self.per_media_type_discord_status_data: dict[str, DiscordData] = {
            "episode": {
                "status_lines": [
                    "{jellyfin.series_name}",
                    "S{jellyfin.season_number}E{jellyfin.episode_number} – {jellyfin.name}",
                    "{jellyfin.name}"
                ]
            },
            "movie": {
                "status_lines": [
                    "{jellyfin.name}"
                ]
            },
            "audio": {
                "activity_type": ActivityType.LISTENING,
                "status_lines": [
                    "{jellyfin.name}"
                ]
            }
        }

class ConfigLocal(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.cooldown: int = 0
        self.processes: list[LocalProcess] = []

        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {}

class ConfigMpd(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.cooldown: int = 0
        self.server_url: str = "localhost:6600"
        self.password: Optional[str] = None
        self.music_brainz: bool = False

        self.app_name: str = "MPD"
        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "activity_type": ActivityType.LISTENING,
            "status_display_type": StatusDisplayType.DETAILS,
            "status_lines": [
                "{mpd.title}",
                "{mpd.artist} / {mpd.album}",
                "{mpd.artist}",
            ],
            "large_images": {
                "{mpd.music_brainz_cover_art}": None
            }
        }

class ConfigLastFm(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.cooldown: int = 15
        self.users: list[LastFmUser] = []

        self.app_name: str = "Last.fm"
        self.inject_discord_status_data: bool = True
        self.discord_status_data: DiscordData = {
            "activity_type": ActivityType.LISTENING,
            "status_display_type": StatusDisplayType.DETAILS,
            "status_lines": [
                "{last_fm.track_name}",
                "{last_fm.artist_name} / {last_fm.album_name}",
                "{last_fm.album_name}",
            ],
            "large_images": {
                "{last_fm.album_art}": None
            },
            "buttons": {
                "{last_fm.track_name} on Last.fm": "{last_fm.track_url}"
            }
        }

class ConfigDefaultGame(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
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
        self.last_fm = ConfigLastFm()
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
        self.last_fm.load(config.get("last_fm", {}))
        self.default_game.load(config.get("default_game", {}))

        # ensure the app name checks are case-insensitive
        case_insensitive_per_app = {}
        for key, value in self.discord.per_app_status_data.items():
            case_insensitive_per_app[key.casefold()] = value
        
        self.discord.per_app_status_data = case_insensitive_per_app