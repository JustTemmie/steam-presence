import src.apis.discord as discordAPI
import src.steam_presence.misc as steam_presence

from src.fetchers.SteamGridDB import SteamGridDB, SteamGridPlatforms
from src.steam_presence.config import Config, DiscordData
from src.steam_presence.DataClasses import DiscordDataPayload, LocalGameFetchPayload, SteamFetchPayload

from time import time
from pypresence import Presence, ActivityType

import logging
import string

class DiscordRPC:
    def __init__(self, config: Config, SgdbFetcher: SteamGridDB | None):
        self.config = config

        self.SgdbFetcher = SgdbFetcher

        self.discord_RPC: Presence = None
        self.discord_app_id: int = 0
        self.app_name: str = ""
        self.app_id_is_name: bool = False
        self.last_update: float = 0
        self.activity_type: ActivityType = ActivityType.PLAYING
        # all activity types display details and state, in addition to text on image hovers
        # the listening, competing, and streaming activities also displays the large image URL

        self.details: str = ""
        self.state: str = ""
        self.start_time: int = 0
        self.end_time: int = 0

        self.large_image_url: str | None = None
        self.large_image_text: str = ""
        self.small_image_url: str | None = None
        self.small_image_text: str = ""

        self.discord_buttons = []

        self.discord_image_url: str | None = None

        self.steam_payload: SteamFetchPayload = None
        self.local_payload: LocalGameFetchPayload = None
        self.discord_payload: DiscordDataPayload = None
        self.steam_grid_db_payload = None
        self.epic_games_store_payload = None
        self.default_game_payload = None
        
    def _get_RPC_data(self) -> dict:
        return {
            "discord": self.discord_payload,
            # "epic_games_store": self.epic_games_store_payload,
            "local": self.local_payload,
            "steam_grid_db": self.steam_grid_db_payload,
            "steam": self.steam_payload,
            "default": self.default_game_payload,
        }

    def instanciate(self, name: str, platform_fallback_app_id: int = None) -> bool:
        # skip app if it's found in the blacklist
        if name.casefold() in map(str.casefold, self.config.app.blacklist):
            logging.info(f"{gameName} is in the blacklist, skipping RPC object creation.")
            return False
        
        logging.info(f"Instanciating Discord RPC connection for {name}")
        print("–" * steam_presence.get_terminal_width())
        self.app_name = name

        self.discord_payload = discordAPI.fetchData(self.app_name)

        # figure out the correct app ID
        app_ID = discordAPI.getAppId(name, self.config)
        if app_ID:
            self.app_id_is_name = True
        else:
            if platform_fallback_app_id:
                app_ID = platform_fallback_app_id
            else:
                app_ID = self.config.discord.fallback_app_id
        
        self.discord_app_id = app_ID
        self.start_time = round(time())
        
        # only connect if discord is enabled
        # this check exists to allow development without having discord running
        if self.config.discord.enabled:
            self.discord_RPC = Presence(client_id=self.discord_app_id)
            self.discord_RPC.connect()

        return True
    
    def firstUpdate(self) -> None:
        if self.SgdbFetcher:
            if self.steam_payload or self.discord_payload.steam_app_id:
                if self.steam_payload:
                    steam_app_id = self.steam_payload.app_id
                else:
                    steam_app_id = self.discord_payload.steam_app_id
                
                self.steam_grid_db_payload = self.SgdbFetcher.fetch(
                    app_id = steam_app_id,
                    platform = SteamGridPlatforms.STEAM
                )

            else:
                self.steam_grid_db_payload = self.SgdbFetcher.fetch(app_name=self.app_name)


    def update(self) -> None:
        logging.debug(f"Updating data for {self.app_name}")
        
        if self.last_update == 0:
            self.firstUpdate()
        
        self.last_update = time()

        app_config_data: DiscordData = self.config.discord.playing
        # overwrite config data with per app config data if applicable
        for key, value in self.config.discord.per_app.get(self.app_name.casefold(), {}).items():
            app_config_data[key] = value

        self.details = None
        self.state = None
        self.discord_buttons = []

        status_lines: list[str] = []

        # if there is no app ID for this specific app, display the name thru the status 
        if not self.app_id_is_name:
            status_lines.append(self.app_name)
        
        def formatRpcData(line) -> str | None:
            try:
                formatted_line = line.format(**self._get_RPC_data())
                if "None" in formatted_line:
                    return None
                
                return formatted_line
            except:
                return None

        for status_line in app_config_data.get("status_lines", []):
            formatted_line = formatRpcData(status_line)
            if formatted_line:
                status_lines.append(formatted_line)

        if len(status_lines) >= 1:
            self.details = status_lines[0]
        if len(status_lines) >= 2:
            self.state = status_lines[1]
        
        for large_image_url, large_image_text in app_config_data.get("large_images", {}).items():
            image_url = formatRpcData(large_image_url)
            image_text = formatRpcData(large_image_text)
            # Continue if large_image_text was explicitly set to None
            if image_url and (image_text or large_image_text == None):
                self.large_image_url = image_url
                self.large_image_text = image_text
                break
        
        for small_image_url, small_image_text in app_config_data.get("small_images", {}).items():
            image_url = formatRpcData(small_image_url)
            image_text = formatRpcData(small_image_text)
            if image_url and (image_text or small_image_text == None):
                self.small_image_url = image_url
                self.small_image_text = image_text
                break

    
    def refresh(self) -> bool:
        # close the connection if it's been more than a minute since the last update
        if self.last_update + self.config.app.timeout < time():
            if self.config.discord.enabled:
                self.discord_RPC.close()
            
            return False
        
        if self.config.discord.enabled:
            self.discord_RPC.update(
                activity_type = self.activity_type,
                details = self.details, state = self.state,
                start = self.start_time,
                large_image = self.large_image_url, large_text = self.large_image_text,
                small_image = self.small_image_url, small_text = self.small_image_text,
                buttons=[{"label": "My Website", "url": "https://qtqt.cf"}]#self.discord_buttons
            )
        else:
            print(f"refreshing rpc with: ")
            print(f"details = {self.details}")
            print(f"state = {self.state}")
            print(f"start_time = {self.start_time}")
            print(f"large_image_text = {self.large_image_text}")
            print(f"large_image_url = {self.large_image_url}")
            print(f"small_image_text = {self.small_image_text}")
            print(f"small_image_url = {self.small_image_url}")
            print(f"buttons = {self.discord_buttons}")

        return True

    def updateSteamData(self) -> None:
        if self.config.steam.steam_store_button and self.steam_payload.app_id != 0:
            price_string = self.steam_payload.price_current

            # we try multiple labels as they're capped to 32 characters
            labels = [
                f"{self.steam_payload.app_name} on steam - {price_string}",
                f"{self.steam_payload.app_name} - {price_string}",
                f"get it on steam! - {price_string}",
                f"on steam! - {price_string}",
                "get it on steam!"
            ]

            for label in labels:
                if len(label) <= 32:
                    break
                
            self.discord_buttons.append({
                "label": label,
                "url": f"https://store.steampowered.com/app/{self.steam_payload.app_id}"
            })