import logging
import copy

from time import time
from typing import Optional
from pypresence import Presence, ActivityType, StatusDisplayType

from src.presence_manager.config import Config, DiscordData
from src.presence_manager.DataClasses import DiscordDataPayload, LocalGameFetchPayload, SteamFetchPayload, JellyfinDataPayload, MpdFetchPayload


class DiscordRPC:
    def __init__(self, config: Config):
        self.config = config

        self.discord_RPC: Presence = None
        self.discord_app_id: int = 0
        self.app_name: str = ""
        self.last_update: float = 0

        self.activity_type: ActivityType = config.discord.status_data.get("activity_type", ActivityType.PLAYING)
        self.status_display_type: StatusDisplayType = config.discord.status_data.get("status_display_type", StatusDisplayType.NAME)
        # all activity types display details and state, in addition to text on image hovers
        # the listening, competing, and streaming activities also displays the large image text for some reason

        self.status_data: DiscordData = copy.deepcopy(config.discord.status_data)

        self.details: str = ""
        self.state: str = ""
        self.start_time: int = None
        self.end_time: int = None

        self.large_image_url: Optional[str] = None
        self.large_image_text: str = ""
        self.small_image_url: Optional[str] = None
        self.small_image_text: str = ""

        self.discord_buttons = []

        self.discord_image_url: Optional[str] = None

        self.steam_payload: SteamFetchPayload = None
        self.local_payload: LocalGameFetchPayload = None
        self.jellyfin_payload: JellyfinDataPayload = None
        self.mpd_payload: MpdFetchPayload = None
        self.steam_grid_db_payload = None
        self.epic_games_store_payload = None
        self.default_game_payload = None
        
    def _get_RPC_data(self) -> dict:
        return {
            # "epic_games_store": self.epic_games_store_payload,
            "jellyfin": self.jellyfin_payload,
            "local": self.local_payload,
            "mpd": self.mpd_payload,
            "steam_grid_db": self.steam_grid_db_payload,
            "steam": self.steam_payload,
            "default": self.default_game_payload,
        }

    def inject_bonus_status_data(self, status_data: DiscordData):
        logging.debug("injecting status data: %s", status_data)
        if status_data.get("activity_type"):
            self.activity_type = status_data.get("activity_type")
        if status_data.get("status_display_type"):
            self.status_display_type = status_data.get("status_display_type")
        
        if status_data.get("status_lines"):
            self.status_data["status_lines"] = status_data.get("status_lines", []) + self.status_data.get("status_lines", [])

        if status_data.get("small_images"):
            self.status_data["small_images"] = status_data.get("small_images", {}) | self.status_data.get("small_images", {})

        if status_data.get("large_images"):
            self.status_data["large_images"] = status_data.get("large_images", {}) | self.status_data.get("large_images", {})
        
    def instanciate(self, name: str, discord_app_id: int) -> bool:
        # skip app if it's found in the blacklist
        if name.casefold() in map(str.casefold, self.config.app.blacklist):
            logging.info("%s is in the blacklist, skipping RPC object creation.", name)
            return False
        
        logging.info("Instanciating Discord RPC connection for %s", name)
        self.app_name = name
        self.discord_app_id = discord_app_id

        self.start_time = time()

        # overwrite config data with per app config data if applicable
        for key, value in self.config.discord.per_app_status_data.get(self.app_name.casefold(), {}).items():
            self.status_data[key] = value
        
        # only connect if discord is enabled
        # this check exists to allow development without having discord running
        if self.config.discord.enabled:
            self.discord_RPC = Presence(client_id=self.discord_app_id)
            self.discord_RPC.connect()
        
        logging.info("Established Discord RPC connection for %s", name)

        return True


    def update(self) -> None:
        logging.debug("Updating data for %s", self.app_name)
        
        self.last_update = time()

        self.details = None
        self.state = None
        self.discord_buttons = []

        status_lines: list[str] = []
        
        def format_rpc_data(line) -> Optional[str]:
            try:
                formatted_line = line.format(**self._get_RPC_data())
                if "None" in formatted_line:
                    return None
                
                return formatted_line
            except Exception:
                return None

        for status_line in self.status_data.get("status_lines", []):
            formatted_line = format_rpc_data(status_line)
            if formatted_line:
                status_lines.append(formatted_line)

        if len(status_lines) >= 1:
            self.details = status_lines[0]
        if len(status_lines) >= 2:
            self.state = status_lines[1]
        
        for large_image_url, large_image_text in self.status_data.get("large_images", {}).items():
            image_url = format_rpc_data(large_image_url)
            image_text = format_rpc_data(large_image_text)
            # Continue if large_image_text was explicitly set to None
            if image_url and (image_text or large_image_text == None):
                self.large_image_url = image_url
                self.large_image_text = image_text
                break
        
        for small_image_url, small_image_text in self.status_data.get("small_images", {}).items():
            image_url = format_rpc_data(small_image_url)
            image_text = format_rpc_data(small_image_text)
            if image_url and (image_text or small_image_text == None):
                self.small_image_url = image_url
                self.small_image_text = image_text
                break
    
    def close_RPC(self):
        if self.config.discord.enabled:
            self.discord_RPC.close()
    
    def refresh(self) -> bool:
        # close the connection if it's been more than a minute since the last update
        if self.last_update + self.config.app.timeout < time():
            self.close_RPC()
            return False
        
        if self.config.discord.enabled:
            self.discord_RPC.update(
                name = self.app_name,
                activity_type = self.activity_type,
                status_display_type = self.status_display_type,
                details = self.details, state = self.state,
                start = self.start_time, end=self.end_time,
                large_image = self.large_image_url, large_text = self.large_image_text,
                small_image = self.small_image_url, small_text = self.small_image_text,
                # buttons=[{"label": "Test Button", "url": "https://github.com/JustTemmie/steam-presence"}]#self.discord_buttons
            )
        
        if not self.config.discord.enabled or logging.root.level < 20:
            print("refreshing rpc with:")
            print(f"name = {self.app_name}")
            print(f"discord_app_id = {self.discord_app_id}")
            print(f"activity_type = {self.activity_type}")
            print(f"status_display_type = {self.status_display_type}")
            print(f"details = {self.details}")
            print(f"state = {self.state}")
            print(f"start_time = {self.start_time}")
            print(f"end_time = {self.end_time}")
            print(f"large_image_text = {self.large_image_text}")
            print(f"large_image_url = {self.large_image_url}")
            print(f"small_image_text = {self.small_image_text}")
            print(f"small_image_url = {self.small_image_url}")
            print(f"buttons = {self.discord_buttons}")

        return True

    def update_steam_data(self) -> None:
        pass
        # buttons are currently broken for some unknown reason
        # if self.config.steam.steam_store_button and self.steam_payload.app_id != 0:
        #     price_string = self.steam_payload.price_current

        #     # we try multiple labels as they're capped to 32 characters
        #     labels = [
        #         f"{self.steam_payload.app_name} on steam - {price_string}",
        #         f"{self.steam_payload.app_name} - {price_string}",
        #         f"get it on steam! - {price_string}",
        #         f"on steam! - {price_string}",
        #         "get it on steam!"
        #     ]

        #     for label in labels:
        #         if len(label) <= 32:
        #             break
                
        #     self.discord_buttons.append({
        #         "label": label,
        #         "url": f"https://store.steampowered.com/app/{self.steam_payload.app_id}"
        #     })