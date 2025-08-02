# adds the project root to the path, this is to allow importing other files in an easier manner
# if you know a better way of doing this, please tell me!
if __name__ == "__main__":
    import sys
    sys.path.append(".")

from src.steam_presence.DataClasses import SteamGridDBFetchPayload

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Union

import requests

class SteamGridPlatforms(Enum):
    INTERNAL = None
    STEAM = "steam"
    ORIGIN = "origin"
    EGS = "egs"
    BNET = "bnet"
    UPLAY = "uplay"
    FLASHPOINT = "flashpoint"
    ESHOP = "eshop"

class SteamGridDB:
    def __init__(self, config):
        self.config = config        
        self.api_key = config.steam_grid_db.api_key

        self.base_url = "https://www.steamgriddb.com/api/v2"
    
    def _ApiFetch(self, endpoint: str, data: dict = {}) -> dict | None:
        r = requests.get(
            f"{self.base_url}/{endpoint}",
            data = data,
            headers =  {
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        if r.status_code < 200 or r.status_code >= 300:
            logging.error(f"failed to fetch {endpoint}, status code {r.status_code} met")
            return None
        
        return r.json()
    
    def getIdWithName(
        self,
        app_name: str
    ) -> int | None:
        r = self._ApiFetch(f"search/autocomplete/{app_name}")

        if r and len(r) >= 1:
            games = r.get("data", [])
            if len(games) >= 1:
                return games[0].get("id", None)

    def getIconWithId(
        self,
        app_id: Union[str, int],
        platform: SteamGridPlatforms
    ) -> str | None:
        # try multiple searches until we find a good one
        datas = [
            {
                "styles": "official",
                "types": "static",
                "dimensions": "96,100,114,120,128,144,150,152,160,180,192,194,256,310,512,768,1024"
            },
            {
                "styles": "official,custom",
                "types": "static",
                "dimensions": "96,100,114,120,128,144,150,152,160,180,192,194,256,310,512,768,1024"
            },
            {
                "styles": "official,custom",
                "humor": "any",
                "types": "static",
                "dimensions": "96,100,114,120,128,144,150,152,160,180,192,194,256,310,512,768,1024"
            },
            {
                "styles": "official,custom",
                "humor": "any",
                "types": "static,animated",
                "dimensions": "96,100,114,120,128,144,150,152,160,180,192,194,256,310,512,768,1024"
            },
            {
                "styles": "official,custom",
                "humor": "any",
                "types": "static,animated"
            },
        ]
        
        # why are enums like this?
        if isinstance(platform, SteamGridPlatforms):
            platform = platform.value

        # search using SGDBs IDs if no platform is given
        # "/icons/games/{app_id}" is internal
        # "/icons/{platform}/{app_id}" is external
        if platform == None:
            platform = "game"
        
        for data in datas:
            r = self._ApiFetch(f"icons/{platform}/{app_id}", data=data)
            
            if r and len(data) >= 1:
                icons = r.get("data", [])

                # seems like SGDB always returns a score of 0, oh well
                # icons.sort(key=lambda icon: icon["score"], reverse=True)

                for icon in icons:
                    if icon.get("mime") == "image/png":
                        if icon.get("url"):
                            return icon.get("url")
                    else:
                        if icon.get("thumb"):
                            return icon.get("thumb")
        
        return None
    
    def fetch(
        self,
        app_id: Union[str, int] | None = None,
        platform: SteamGridPlatforms | None = None,
        app_name: str | None = None,
    ) -> SteamGridDBFetchPayload:        
        if app_name:
            app_id = self.getIdWithName(app_name)
            platform = SteamGridPlatforms.INTERNAL
        
        if app_id:
            return SteamGridDBFetchPayload(
                self.getIconWithId(app_id, platform)
            )
        
        else:
            return SteamGridDBFetchPayload()
        

if __name__ == "__main__":
    from src.steam_presence.config import Config, SteamUser

    config = Config()
    config.load()

    sgdb = SteamGridDB(config)

    # icon = sgdb.getIconExternalPlatform(1086940, "steam")

    id = sgdb.getIdWithName("The Legend of Zelda: Majora's Mask")
    print(id)

    icon = sgdb.getIconWithId(id, SteamGridPlatforms.INTERNAL)
    print(icon)

