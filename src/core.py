import os
import sys
import json
import time

import requests

from io import BytesIO
from PIL import Image

if __name__ == "__main__":
    sys.path.append(".")
    
import src.platforms.steam_platform as steam_service

import src.disk_operations as disk_operations

import src.services.steam_grid_db as sgdb_service
import src.services.discord as discord_service

import src.helpers as steam_presence

# some constants
minimum_image_resolution = 64

class Core():
    def __init__(self, APIKeys):
        self.steam =  steam_service.SteamPlatform(APIKeys["steam"])
        self.SGDB =  sgdb_service.SGDB(APIKeys["sgdb"])

    def get_current_games(self, SteamUserIDs: list[int]):
        results = {}
        
        config = steam_presence.getConfigFile()
        
        for SteamUserID in SteamUserIDs:
            steamGameID = self.steam.get_current_game_ID(SteamUserID)
            steam_presence.debug(f"currently playing game: {steamGameID}")
            if steamGameID:
                steamResponse = self.get_steam_game_info(config, SteamUserID, steamGameID)
                print(f"gameinfo: {steamResponse}")
                if steamResponse:
                    results["steam"] = steamResponse
                    break

        return results

    def get_image(self, image_fetchers: dict[str, callable], image_preferences: list[str]) -> str | None:
        @steam_presence.time_cache(86400)
        def check_image_size(url: str) -> int:
            """
                returns the size of the smallest resolution within the image, a 96x128 image would return the int 96
            """
            try:
                r = steam_presence.make_web_request(url)
                r.raise_for_status()
                
                image = Image.open(BytesIO(r.content))
                
                return min(image.size)

            except requests.RequestException as e:
                steam_presence.debug(f"error fetching the image: {e}")
                return 0
            except Exception as e:
                steam_presence.debug(f"error processing the image: {e}")
                return 0
        
        for service_name in image_preferences:
            service_name = service_name.lower()
            if service_name in image_fetchers:
                steam_presence.debug(f"trying to fetch image using {service_name}")
                image = image_fetchers[service_name]()
                if image:
                    image_resolution = check_image_size(image)
                    if image_resolution > minimum_image_resolution:
                        steam_presence.log(f"successfully retrieved image using {service_name}")
                        steam_presence.debug(f"image link in question: {image}")
                        return image
                    else:
                        steam_presence.debug(f"successfully retrieved image using {service_name}, but the image was too low res ({image_resolution} pixels)")
    
    def get_steam_game_info(self, config, SteamUserID, steamGameID):
        large_image_sources = config["LARGE_IMAGE_SOURCES"]
        
        data = {}
        data["gameID"] = steamGameID
        data["gameName"] = self.steam.get_game_name(steamGameID)
        
        if not data["gameName"]:
            return

        # semi cached
        data["price"] = self.steam.get_game_price(steamGameID)
        data["reviews"] = self.steam.get_game_review_rating(steamGameID)
        data["playtime"] = self.steam.get_game_playtime(SteamUserID, steamGameID)
        data["achievement_count"] = self.steam.get_game_achievement_progress(SteamUserID, steamGameID)
        
        # not cached
        data["rich_presence"] = self.steam.get_current_rich_presence(SteamUserID, steamGameID)
        
        image_fetchers = {
            "file_cache": lambda: disk_operations.get_image_from_disk(data["gameName"]),
            "discord_cdn": lambda: discord_service.get_image_from_discord(discord_service.get_game_ID(data["gameName"])),
            "steam_grid_db_steam_id": lambda: self.SGDB.get_icon_url_from_steam_id(steamGameID),
            "steam_grid_db_game_name": lambda: self.SGDB.get_icon_url_from_game_name(data["gameName"]),
            "steam_store_page": lambda: self.steam.get_image_url_from_store_page(steamGameID),
            "steam_cdn": lambda: self.steam.get_image_url_from_steam_CDN(steamGameID)
        }
        
        data["image"] = self.get_image(image_fetchers, large_image_sources)
        
        return data