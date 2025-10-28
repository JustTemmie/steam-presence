import logging

from enum import Enum
from typing import Union

from src.presence_manager.DataClasses import SteamGridDBFetchPayload

import src.presence_manager.misc as presence_manager


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
    
    def _api_fetch(self, endpoint: str, data: dict = {}) -> dict | None:
        r = presence_manager.fetch(
            f"{self.base_url}/{endpoint}",
            data = data,
            headers =  {
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        if not r:
            logging.error("failed to fetch %s", endpoint)
            return None
        
        return r.json()
    
    def get_id_with_name(
        self,
        app_name: str
    ) -> int | None:
        # i love undocumented endpoints
        r = self._api_fetch(f"search/autocomplete/{app_name}")

        if r and len(r) >= 1:
            games = r.get("data", [])
            if len(games) >= 1:
                return games[0].get("id", None)

    def get_icon_with_id(
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
        if platform is None:
            platform = "game"
        
        for data in datas:
            r = self._api_fetch(f"icons/{platform}/{app_id}", data=data)
            
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
        app_name: str | None = None
    ) -> SteamGridDBFetchPayload:        
        if app_name:
            app_id = self.get_id_with_name(app_name)
            platform = SteamGridPlatforms.INTERNAL
        
        if app_id:
            return SteamGridDBFetchPayload(
                self.get_icon_with_id(app_id, platform)
            )
        
        else:
            return SteamGridDBFetchPayload()