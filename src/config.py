# adds the project root to the path, this is to allow importing other files in an easier manner
# if you know a better way of doing this, please tell me!
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    
import logging
import json

# to check if the browser we're fetching cookies from is a supported browser
import browser_cookie3

from src.command_line_arguments import args


class GenericConfig:
    def load(self, data: dict):
        for key, value in data.items():
            try:
                getattr(self, key)
            except AttributeError:
                logging.critical(f"{key} is not a real config value")
                quit(-1)
            
            setattr(self, key, value)

class ConfigDiscord(GenericConfig):
    def __init__(self):
        self.global_fallback_discord_app_id: int = 1062648118375616594
        self.rpc_lines: list[str] = [
            "{playtime} Hours | {achievement_count} Achievements",
            "{rich_presence}",
            "{review_score_percentage} positive reviews"
        ]
        self.large_image_source: list[str] = {
            "file_cache",
            "steam_grid_db",
            "steam_store_page"
        }
        self.buttons: list[dict[str: str, str: str]] = [
            {
                "name": "dynamic",
                "url": "dynamic",
            }
        ]

class ConfigSteam(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.web_scrape: bool = True
        self.auto_fetch_cookies: bool = False
        self.cookie_browser: str = ""
        self.api_key: str = ""
        self.user_ids: list[int] = []
        self.fallback_discord_app_id: int = 869994714093465680
        self.blacklist: list[str] = []

class ConfigSteamGridDB(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.api_key: str = ""

class ConfigLocalGames(GenericConfig):
    def __init__(self):
        self.enabled: bool = False
        self.processes: list[str] = []

class Config:
    def __init__(self):
        self.discord = ConfigDiscord()
        self.steam = ConfigSteam()
        self.steam_grid_db = ConfigSteamGridDB()
        self.local_games = ConfigLocalGames()
    
    def load(self, config_path="config.json"):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError as e:
            logging.error(f"could not find a config path at '{config_path}' - exiting\n{e}")
            quit()
        
        self.discord.load(config.get("discord", {}))
        self.steam.load(config.get("steam", {}))
        self.steam_grid_db.load(config.get("steam_grid_db", {}))
        self.local_games.load(config.get("local_games", {}))

        # ensure the browser to fetch cookies from is supported        
        if self.steam.cookie_browser == "":
            self.steam.cookie_browser = "auto"

        supported_browser_strings = ["auto"]
        for function in browser_cookie3.all_browsers:
            supported_browser_strings.append(getattr(function, "__name__"))

        if self.steam.cookie_browser not in supported_browser_strings:
            logging.critical(f"the browser `{self.steam.cookie_browser} is not supported, the list of supported browsers are {supported_browser_strings}, disabling auto fetching...")
            self.steam.auto_fetch_cookies = False


if __name__ == "__main__":
    config = Config()
    config.load(args.config)
    print(config.discord.buttons)