from src.steam_presence.config import Config
from src.steam_presence.DataClasses import DiscordDataPayload

import requests
import json

from typing import Union
from dataclasses import dataclass


def getAppId(app_name: str) -> int | None:
    r = requests.get("https://discordapp.com/api/v8/applications/detectable")

    if r.status_code != 200:
        logging.error(f"failed to fetch discord app ID, status code {r.status_code} met")
        return None

    games = json.loads(r.content)

    # these chars will be ignored in comparisons
    trans_table = str.maketrans('', '', "®©™℠")

    app_name = app_name.translate(trans_table).casefold()

    for game in games:
        game_name = game.get("name", "").translate(trans_table).casefold()
        
        if game_name == app_name:
            app_ID = game.get("id", None)
            if app_ID: return int(app_ID)

@dataclass
class getAppInfoPayload:
    image_url: str | None = None
    steam_app_id: str | None = None
    name: str | None = None

def getAppInfo(app_id: Union[str | int]) -> getAppInfoPayload | None:
    r = requests.get(f"https://discordapp.com/api/v8/applications/{app_id}/rpc")
    
    if r.status_code != 200:
        logging.error(f"failed to fetch image from discord, status code {r.status_code} met")
        return None
    
    response = r.json()

    if response.get("icon"):
        image_url = f"https://cdn.discordapp.com/app-icons/{app_id}/{response.get('icon')}.webp"
    else:
        image_url = None
    steam_app_id = None
    
    for sku in response.get("third_party_skus", []):
        if sku.get("distributor") == "steam":
            steam_app_id = sku.get("id")

    return getAppInfoPayload(
        image_url=image_url,
        steam_app_id=steam_app_id,
        name=response.get("name")
    )

def fetchData(app_name: str) -> DiscordDataPayload | None:
    app_id = getAppId(app_name)

    if not app_id:
        return None

    app_info = getAppInfo(app_id)

    return DiscordDataPayload(
        app_id,

        app_info.image_url,
        app_info.steam_app_id,
        app_info.name,
    )