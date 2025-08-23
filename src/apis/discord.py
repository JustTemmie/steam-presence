from src.presence_manager.config import Config
from src.presence_manager.DataClasses import DiscordDataPayload

import src.presence_manager.misc as presence_manager

from typing import Union
from dataclasses import dataclass
from PIL import Image
from io import BytesIO

import requests
import json


def getAppId(app_name: str, config: Config | None = None) -> int | None:
    URL = "https://discordapp.com/api/v8/applications/detectable"
    r = presence_manager.fetch(URL)

    if not r:
        logging.error(f"failed to fetch discord app ID")
        return None

    games = []
    if config:
        for key, value in config.discord.presence_manager_app_ids.items():
            games.append({
                "name": key,
                "id": value
            })
        for key, value in config.discord.custom_app_ids.items():
            games.append({
                "name": key,
                "id": value
            })

    games += json.loads(r.content)

    # these chars will be ignored in comparisons
    trans_table = str.maketrans('', '', "®©™℠")

    app_name = app_name.translate(trans_table).casefold()
    app_ID = None

    for game in games:
        game_name = game.get("name", "").translate(trans_table).casefold()
        
        if game_name == app_name:
            app_ID = game.get("id", None)

        for alias in game.get("aliases", []):
            alias_name = alias.translate(trans_table).casefold()

            if alias_name == app_name:
                app_ID = game.get("id", None)

        if app_ID: return int(app_ID)
        


@dataclass
class getAppInfoPayload:
    image_url: str | None = None
    steam_app_id: str | None = None
    name: str | None = None

def getAppInfo(app_id: Union[str | int]) -> getAppInfoPayload | None:
    r = presence_manager.fetch(f"https://discordapp.com/api/v8/applications/{app_id}/rpc")
    
    if not r:
        logging.error(f"failed to fetch image from discord")
        return None
    
    response = r.json()

    if response.get("icon"):
        image_url = f"https://cdn.discordapp.com/app-icons/{app_id}/{response.get('icon')}.webp"
        r = presence_manager.fetch(image_url)
        if r:
            image = Image.open(BytesIO(r.content))
            # discard images under 64p, they just look super bad
            if image.size[0] < 64:
                image_url = None
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

def fetchData(app_name: str) -> DiscordDataPayload:
    app_id = getAppId(app_name)

    if not app_id:
        return DiscordDataPayload()

    app_info = getAppInfo(app_id)

    return DiscordDataPayload(
        app_id,

        app_info.image_url,
        app_info.steam_app_id,
        app_info.name,
    )