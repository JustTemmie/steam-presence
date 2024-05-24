import os
import sys
import json
import time


import src.platforms.steam as steam_service

import src.file_system.cache as cache

import src.services.steam_grid_db as sgdb_service

from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))


class Core():
    def __init__(self, APIKeys):
        self.steam =  steam_service.Steam(APIKeys["steam"])
        self.SGDB =  sgdb_service.SGDB(APIKeys["sgdb"])

    def get_current_game(self, SteamUserIDs = []):
        results = {}
        
        config = getConfigFile()
        large_image_sources = config["LARGE_IMAGE_SOURCES"]
        
        steamGame = self.steam.get_game(SteamUserIDs)
        if steamGame:
            if steamGame["gameID"] == 0:
                log("no game is being played")
                return {}
            
            gameID = steamGame["gameID"]
            userID = steamGame["userID"]
            
            data = {}
            data["gameName"] = steamGame["name"]
            data["gameID"] = steamGame["gameID"]
            data["userID"] = steamGame["userID"]

            # semi cached
            data["price"] = self.steam.get_game_price(gameID)
            data["reviews"] = self.steam.get_game_reviews(gameID)
            data["playtime"] = self.steam.get_playtime(userID, gameID)
            data["achievement_count"] = self.steam.get_achievement_progress(userID, gameID)
            
            # not cached
            data["rich_presence"] = self.steam.get_rich_presence(SteamUserIDs, data["gameName"])
            
            image_fetchers = {
                "file_cache": lambda: cache.get_image_from_cache(data["gameName"]),
                "steam_grid_db": lambda: self.SGDB.get_icon_url_from_steam_id(gameID),
                "discord_cdn": lambda: 0,
                "steam_store_page": lambda: self.steam.get_image_url_from_store_page(gameID)
            }
            
            
            data["image"] = self.get_image(image_fetchers, large_image_sources)
            
            
            results["steam"] = data

        return results

    
    def get_image(self, image_fetchers, image_preferences):
        for service in image_preferences:
            service = service.lower()
            if service in image_fetchers:
                print(f"trying to fetch image using {service}")
                image = image_fetchers[service]()
                if image:
                    return image