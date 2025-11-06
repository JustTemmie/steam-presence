import os
import logging
import random
from typing import Optional


from src.presence_manager.config import Config


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
