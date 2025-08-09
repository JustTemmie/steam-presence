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
        self.blacklist: list[str] = []

class ConfigDiscord(GenericConfig):
    def __init__(self):
        self.enabled: bool = True
        self.fallback_app_id: int = 1400019956321620069
        self.playing: DiscordData = {
            "status_lines": [
                "{default.details}", # used by the fallback game
                "{default.state}", # used by the fallback game
                "{steam.rich_presence}",
                "{steam.review_description} reviews ({steam.review_percent}%)",
            ],
            "small_images": {
                "{steam.profile_badge_url}": "{steam.profile_badge_name}",
            },
            "large_images": {
                "{discord.image_url}": "Discord Image",
                "{steam_grid_db.icon}": "SGDB Image",
                "{steam.avatar_url}": "Steam Avatar",
            }
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
        self.state: str = "15 Hearts, 7/10 Stamina Vessels."

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
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError as e:
            logging.error(f"could not find a config path at '{config_path}' - exiting\n{e}")
            exit()
        
        self.app.load(config.get("app", {}))
        self.discord.load(config.get("discord", {}))
        self.steam_grid_db.load(config.get("steam_grid_db", {}))
        self.steam.load(config.get("steam", {}))
        self.epic_games_store.load(config.get("epic_games_store", {}))
        self.local_games.load(config.get("local_games", {}))
        self.default_game.load(config.get("default_game", {}))


if __name__ == "__main__":
    config = Config()
    config.load(args.config)