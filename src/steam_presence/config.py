# adds the project root to the path, this is to allow importing other files in an easier manner
# if you know a better way of doing this, please tell me!
if __name__ == "__main__":
    import sys
    sys.path.append(".")

from dataclasses import dataclass

import logging
import json

# to check if the browser we're fetching cookies from is a supported browser
# import browser_cookie3

from src.steam_presence.command_line_args import args


def deep_merge(original, update):
    for key, value in update.items():
        if (
            key in original
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            deep_merge(original[key], value)
        else:
            original[key] = value
    
    return original

class GenericConfig:
    def load(self, update: dict):
        data = deep_merge(self.__dict__, update)
        
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
    web_scrape: bool = False
    auto_fetch_cookies: bool = False
    cookie_browser: str = ""

@dataclass
class LocalProcess:
    process_name: str
    display_name: str

class ConfigApp(GenericConfig):
    def __init__(self):
        self.timeout: int = 60 # seconds required to determine a connection as inactive
        self.cycle_interval: int = 20 # seconds between running checks, setting this too low to low may lead to API bans
        self.blacklist: list[str] = []

class ConfigDiscord(GenericConfig):
    def __init__(self):
        self.enabled: bool = True
        self.fallback_app_id: int = 1400019956321620069
        self.custom_app_ids: dict[str, int] = {
            "App name here": 141471589572411256163
        }
        self.steam_presence_app_ids: dict[str, int] = {
            # "official" custom app IDs, overwrite custom_app_ids instead
            # i will _NOT_ merge a PR adding more of these
            # as the creator could delete them in the future, sorry :p
            "The Legend of Zelda: Majora's Mask": 1403714141734309980,
            "Rift Riff": 1403716067821490206,
        }
        self.playing: DiscordData = {
            "status_lines": [
                "{default.details}", # used by the default game
                "{default.state}", # used by the default game
                "{steam.rich_presence}",
                "{steam.review_description} reviews ({steam.review_percent}%)",
            ],
            "small_images": {
            },
            "large_images": {
                "{discord.image_url}": None,
                "{steam_grid_db.icon}": None,
                "{steam.capsule_header_image}": None,
                "{steam.capsule_vertical_image}": None,
            },
        }
        # the discord trackmania icon SUCKS due to being super blurry
        # so it's a good example of a per app config
        self.per_app: dict[str, DiscordData] = {
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
        self.steam_store_button: bool = True

# TODO, not implemented
class ConfigEpicGamesStore(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_fallback_app_id: int = 1400020128699256914

class ConfigLocalGames(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_fallback_app_id: int = 1400019956321620069
        self.processes: list[LocalProcess] = []

class ConfigDefaultGame(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.discord_app_id: int | None = None
        self.name: str = "Breath of the Wild"
        self.details: str = "Fighting a Stalnox."
        self.state: str = None

class Config:
    def __init__(self):
        self.app = ConfigApp()
        self.discord = ConfigDiscord()
        self.steam_grid_db = ConfigSteamGridDB()
        self.steam = ConfigSteam()
        self.epic_games_store = ConfigEpicGamesStore()
        self.local_games = ConfigLocalGames()
        self.default_game = ConfigDefaultGame()
    
    def load(self, config_path="config.json"):
        logging.info("Loading config file")
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError as e:
            if self.app:
                logging.warn(f"couldn't find config, skipping reload")
                return
            else:
                logging.error(f"could not find a config path at '{config_path}' - exiting\n{e}")
                exit()
        
        self.app.load(config.get("app", {}))
        self.discord.load(config.get("discord", {}))
        self.steam_grid_db.load(config.get("steam_grid_db", {}))
        self.steam.load(config.get("steam", {}))
        self.epic_games_store.load(config.get("epic_games_store", {}))
        self.local_games.load(config.get("local_games", {}))
        self.default_game.load(config.get("default_game", {}))

        # ensure the app name checks are case-insensitive
        case_insensitive_per_app = {}
        for key, value in self.discord.per_app.items():
            case_insensitive_per_app[key.casefold()] = value
        
        self.discord.per_app = case_insensitive_per_app



if __name__ == "__main__":
    config = Config()
    config.load(args.config)