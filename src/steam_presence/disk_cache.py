import os
import time
import json

from typing import Optional
import threading

DISK_LOCK = threading.RLock()

def cache_fetch(bank: str, key: str) -> Optional[dict]:
    with DISK_LOCK:
        os.makedirs("cache", exist_ok=True)

        bank = f"cache/banks/{bank}.json"
        cache: dict = {}

        if os.path.exists(bank):
            with open(bank, 'r', encoding = "utf-8") as f:
                cache = json.load(f)

        fetched = cache.get(key)
        if not fetched:
            return

        if fetched.get("expire_at", 0) > time.time():
            return fetched.get("value")

        cache.pop(key)
        with open(bank, 'w', encoding="utf-8") as f:
            json.dump(cache, f)

def cache_store(bank: str, key: str, value: dict, ttl: float):
    with DISK_LOCK:
        os.makedirs("cache", exist_ok=True)

        path = "cache/banks"
        bank = f"cache/banks/{bank}.json"
        cache: dict = {}

        os.makedirs(path, exist_ok=True)

        if os.path.exists(bank):
            with open(bank, 'r', encoding="utf-8") as f:
                cache = json.load(f)
    
        cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl
        }

        with open(bank, 'w', encoding="utf-8") as f:
            json.dump(cache, f)
