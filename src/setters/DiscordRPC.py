import logging
import copy

from time import time
from typing import Dict, Optional
import pypresence
from pypresence import ActivityType, StatusDisplayType

import src.presence_manager.misc as presence_manager
from src.presence_manager.config import Config, DiscordData, DiscordMedia
from src.presence_manager.interfaces import (
    LocalGameFetchPayload, SteamFetchPayload,
    JellyfinFetchPayload, MpdFetchPayload,
    LastFmFetchPayload, Platforms)


class DiscordRPC:
    def __init__(self, config: Config, platform: Platforms):
        self.config = config
        self.platform: Platforms = platform if platform else Platforms.UNKNOWN

        self.discord_RPC: pypresence.Presence = None
        self.discord_app_id: int = 0
        self.app_name: str = ""
        self.last_update: float = 0
        self.creation_time = time()

        self.activity_type: ActivityType = config.discord.status_data.get(
            "activity_type",
            ActivityType.PLAYING
        )
        self.status_display_type: StatusDisplayType = config.discord.status_data.get(
            "status_display_type",
            StatusDisplayType.NAME
        )

        # all activity types display details and state, in addition to text on image hovers
        # for some ungodly reason, listening, competing, and streaming activities
        # also displays the large image text
        self.status_data: DiscordData = copy.deepcopy(config.discord.status_data)

        self.details: str = ""
        self.state: str = ""
        self.discord_buttons: list[Dict[str: str, str: str]] = []

        self.start_time: int = None
        self.end_time: int = None

        self.large_image_url: Optional[str] = None
        self.large_image_text: str = ""
        self.small_image_url: Optional[str] = None
        self.small_image_text: str = ""

        self.discord_image_url: Optional[str] = None

        self.steam_payload: SteamFetchPayload = None
        self.local_payload: LocalGameFetchPayload = None
        self.jellyfin_payload: JellyfinFetchPayload = None
        self.mpd_payload: MpdFetchPayload = None
        self.last_fm_payload: LastFmFetchPayload = None
        self.steam_grid_db_payload = None
        self.epic_games_store_payload = None
        self.default_game_payload = None

    def _get_RPC_data(self) -> dict:
        return {
            # "epic_games_store": self.epic_games_store_payload,
            "jellyfin": self.jellyfin_payload,
            "last_fm": self.last_fm_payload,
            "local": self.local_payload,
            "mpd": self.mpd_payload,
            "steam": self.steam_payload,
            "steam_grid_db": self.steam_grid_db_payload,
            "default": self.default_game_payload,
        }

    def inject_bonus_status_data(self, status_data: DiscordData):
        logging.debug("injecting status data: %s", status_data)
        if status_data.get("activity_type"):
            self.activity_type = status_data.get("activity_type")
        if status_data.get("status_display_type"):
            self.status_display_type = status_data.get("status_display_type")

        if status_data.get("status_lines"):
            self.status_data["status_lines"] = \
                self.status_data.get("status_lines", []) \
                + status_data.get("status_lines", [])

        if status_data.get("small_images"):
            self.status_data["small_images"] = \
                self.status_data.get("small_images", []) \
                + status_data.get("small_images", [])

        if status_data.get("large_images"):
            self.status_data["large_images"] = \
                self.status_data.get("large_images", []) \
                + status_data.get("large_images", [])

        if status_data.get("buttons"):
            self.status_data["buttons"] = \
                self.status_data.get("buttons", []) \
                + status_data.get("buttons", [])

    def instanciate(self, name: str, discord_app_id: int) -> bool:
        # skip app if it's found in the blacklist
        if name.casefold() in map(str.casefold, self.config.app.blacklist):
            logging.info("%s is in the blacklist, skipping RPC object creation.", name)
            return False

        logging.info("Trying to establish Discord RPC connection for %s", name)
        self.app_name = name
        self.discord_app_id = discord_app_id

        self.start_time = time()

        # overwrite config data with per app config data if applicable
        for key, value in self.config.discord.per_app_status_data.get(
            self.app_name.casefold(),
            {}
        ).items():
            self.status_data[key] = value

        # only connect if discord is enabled
        # this check exists to allow development without having discord running
        if self.config.discord.enabled:
            self.discord_RPC = pypresence.Presence(client_id=self.discord_app_id)
            try:
                self.discord_RPC.connect()
            except pypresence.exceptions.DiscordNotFound:
                logging.warning("Failed to connect to discord, is it running?")

        logging.info("Succesfully established Discord RPC connection for %s", name)

        print("–" * presence_manager.get_terminal_width())

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


        small_image_status_data: list[DiscordMedia] = [
            DiscordMedia(**field) for field in self.status_data.get("small_images", [])
        ]
        large_image_status_data: list[DiscordMedia] = [
            DiscordMedia(**field) for field in self.status_data.get("large_images", [])
        ]
        button_status_data: list[DiscordMedia] = [
            DiscordMedia(**field) for field in self.status_data.get("buttons", [])
        ]

        for entry in small_image_status_data:
            image_url = format_rpc_data(entry.url)
            image_text = format_rpc_data(entry.label)
            
            # Continue if the label was explicitly set to None
            if image_url and (image_text or entry.label is None):
                self.small_image_url = image_url
                self.small_image_text = image_text
                break
        
        for entry in large_image_status_data:
            image_url = format_rpc_data(entry.url)
            image_text = format_rpc_data(entry.label)
            
            # Continue if the label was explicitly set to None
            if image_url and (image_text or entry.label is None):
                self.large_image_url = image_url
                self.large_image_text = image_text
                break
        
        for entry in button_status_data:
            button_url = format_rpc_data(entry.url)
            button_label = format_rpc_data(entry.label)
            
            if button_url and button_label:
                if len(button_label) > 32:
                    logging.warning(
                        "discord caps labels at 32, %s was skipped due to having a length of %s",
                        button_label,
                        len(button_label)
                    )
                else:
                    self.discord_buttons.append({
                        "url": button_url,
                        "label": button_label
                    })

    def get_time_since_timeout(self) -> float:
        return max(0, time() - self.last_update - self.config.app.timeout)

    def clear_RPC(self):
        if self.config.discord.enabled:
            self.discord_RPC.clear()

        # this directly changes the last_update to make sure
        # it doesn't try to reconnect before getting an update
        # though this could probably be done in a better way
        new_last_update = time() - self.config.app.timeout
        if self.last_update > new_last_update:
            self.last_update = new_last_update

    def close_RPC(self):
        if self.config.discord.enabled:
            try:
                self.discord_RPC.close()
            except AssertionError:
                pass

    def refresh(self) -> bool:
        # hide the connection if it's been more than a minute since the last update
        if self.get_time_since_timeout() > 0:
            self.clear_RPC()
            return False

        if self.config.discord.enabled:
            try:
                self.discord_RPC.update(
                    name = self.app_name,
                    activity_type = self.activity_type,
                    status_display_type = self.status_display_type,
                    details = self.details, state = self.state,
                    start = self.start_time, end = self.end_time,
                    large_image = self.large_image_url,
                    small_image = self.small_image_url,
                    # pypresence breaks if you hand it an empty string or array.
                    # while this workaround may be scuffed, it works
                    large_text = self.large_image_text if self.large_image_text else None,
                    small_text = self.small_image_text if self.small_image_text else None,
                    buttons = self.discord_buttons if self.discord_buttons else None
                )
            except pypresence.exceptions.PipeClosed:
                logging.warning("discord RPC pipe closed, disonnecting...")
                self.close_RPC()
                return False

        if self.config.discord.enabled is False or logging.root.level < 10:
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
