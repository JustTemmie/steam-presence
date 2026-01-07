import logging

from enum import Enum
from typing import Union, Optional

from src.steam_presence.config import Config, SGDBLookupTable
from src.steam_presence.interfaces import SteamGridDBFetchPayload
from src.steam_presence.fetch import fetch


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
        cache_ttl = 7200
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
    r = _api_fetch(f"search/autocomplete/{app_name}", api_key)

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
        r = _api_fetch(f"icons/{platform}/{app_id}", api_key, data=data)

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
    config: Config,
    app_id: Optional[Union[str, int]] = None,
    platform: Optional[SteamGridPlatforms] = None,
    app_name: Optional[str] = None
) -> SteamGridDBFetchPayload:
    if app_name:
        lookup_table: SGDBLookupTable = config.steam_grid_db.lookup_table
        if lookup_table:
            for entry in lookup_table:
                if app_name == entry.get("name"):
                    app_id = entry.get("id")
                    platform = SteamGridPlatforms.INTERNAL
                    break

        if not app_id:
            app_id = get_id_with_name(
                config.steam_grid_db.api_key,
                app_name
            )
            platform = SteamGridPlatforms.INTERNAL

    if app_id:
        return SteamGridDBFetchPayload(get_icon_with_id(
            config.steam_grid_db.api_key,
            app_id,
            platform
        ))

    return SteamGridDBFetchPayload()
