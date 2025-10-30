import os
import hashlib
import time
import logging
from typing import Dict, Tuple, Optional

import requests

from src.presence_manager.config import Config


def get_terminal_width() -> int:
    width: int

    try:
        size = os.get_terminal_size()
        width = size.columns
    except Exception:
        width = 10
    
    return width

_CACHE: Dict[str, Tuple[requests.Response, float]] = {}
_LOCK = __import__('threading').RLock()

def _cache_key(url: str, data: dict = None, headers: dict = None) -> str:
    data = data or {}
    headers = headers or {}

    # using hashing may be a bit overkill, but it looks neat
    raw = f"{url}|{sorted(data.items())}|{sorted(headers.items())}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str, ttl: float) -> Optional[requests.Response]:
    with _LOCK:
        if key not in _CACHE:
            return None
        
        response, fetched_at = _CACHE[key]
        if time.time() - fetched_at > ttl:
            del _CACHE[key]
            return None
        
        return response


def _store_cached(key: str, response: requests.Response) -> None:
    with _LOCK:
        _CACHE[key] = (response, time.time())

def fetch(
    url: str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    cache_ttl: float = 0) -> Optional[requests.Response]:

    key = _cache_key(url, data, headers)

    if cache_ttl > 0:
        cached = _get_cached(key, cache_ttl)
        if cached:
            return cached

    try:
        r = requests.get(
            url,
            data = data,
            headers = headers,
            timeout = 5
        )

        if r.status_code != 200:
            return
    
        if cache_ttl > 0:
            _store_cached(key, r)

        return r
    
    except (requests.ConnectTimeout, requests.ConnectionError, requests.exceptions.ReadTimeout):
        return None

def get_unused_discord_id(used_ids: list[int], config: Config) -> Optional[int]:
    for discord_id in config.discord.app_ids:
        if discord_id not in used_ids:
            return discord_id
    
    logging.warning("all %s discord IDs have been used up, can't create any more RPC connections", len(config.discord.app_ids))
    return None
