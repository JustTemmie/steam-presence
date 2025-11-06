import os
import logging
import random
from typing import Optional, Union

from src.presence_manager.interfaces import Platforms
from src.presence_manager.config import Config

from src.setters.DiscordRPC import DiscordRPC

def get_terminal_width() -> int:
    width: int

    try:
        size = os.get_terminal_size()
        width = size.columns
    except Exception:
        width = 10
    
    return width

def get_unused_discord_id(used_ids: list[int], config: Config) -> Optional[int]:
    # returning a random ID helps with a form of "rate limiting" from discord
    available_ids = list(set(config.discord.app_ids) - set(used_ids))
    if available_ids:
        return random.choice(available_ids)

    logging.warning("all %s discord IDs have been used up, can't create any more RPC connections", len(config.discord.app_ids))
    return None

def blocked_by_presedence(
    platform: Platforms, 
    existing_connections: list[DiscordRPC],
    config: Config
) -> bool:
    presedence_rules = config.app.presedence_rules
    blocking_platforms: list[str] = []

    for blocking, blocked in presedence_rules.items():
        if blocked == platform:
            blocking_platforms.append(blocking)

    for connection in existing_connections:
        if connection.platform in blocking_platforms:
            return True
    
    return False