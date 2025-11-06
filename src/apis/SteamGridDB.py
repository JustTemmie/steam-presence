import logging

from enum import Enum
from typing import Union, Optional

from src.presence_manager.DataClasses import SteamGridDBFetchPayload

from src.presence_manager.fetch import fetch


class SteamGridPlatforms(Enum):
    INTERNAL = None
    STEAM = "steam"
    ORIGIN = "origin"
    EGS = "egs"
    BNET = "bnet"
    UPLAY = "uplay"
    FLASHPOINT = "flashpoint"
    ESHOP = "eshop"


BASE_URL = "https://www.steamgriddb.com/api/v2"

def _api_fetch(endpoint: str, api_key: str, data: Optional[dict] = None) -> Optional[dict]:
    r = fetch(
        f"{BASE_URL}/{endpoint}",
        data = data,
        headers =  {
            "Authorization": f"Bearer {api_key}"
        },
        cache_ttl = 1800
    )

    if not r:
        logging.error("failed to fetch %s", endpoint)
        return None
    
    return r.json()

def get_id_with_name(
    api_key: str,
    app_name: str
) -> Optional[int]:
    # i love undocumented endpoints
    r = _api_fetch(api_key, f"search/autocomplete/{app_name}")

    if r and len(r) >= 1:
        games = r.get("data", [])
        if len(games) >= 1:
            return games[0].get("id", None)

def get_icon_with_id(
    api_key: str,
    app_id: Union[str, int],
    platform: SteamGridPlatforms
) -> Optional[str]:
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
        r = _api_fetch(api_key, f"icons/{platform}/{app_id}", data=data)
        
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

def fetch_steam_grid_db(
    api_key: str,
    app_id: Optional[Union[str, int]] = None,
    platform: Optional[SteamGridPlatforms] = None,
    app_name: Optional[str] = None
) -> SteamGridDBFetchPayload:
    if app_name:
        app_id = get_id_with_name(api_key, app_name)
        platform = SteamGridPlatforms.INTERNAL
    
    if app_id:
        return SteamGridDBFetchPayload(get_icon_with_id(api_key, app_id, platform))
    
    return SteamGridDBFetchPayload()