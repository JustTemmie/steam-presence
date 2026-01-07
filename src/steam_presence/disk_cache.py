import os
import time
import json

from typing import Optional
import threading

DISK_LOCK = threading.RLock()

def cache_fetch(bank: str, key: str, ttl: float) -> Optional[dict]:
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

        if fetched.get("last_update", 0) > time.time() - ttl:
            return fetched.get("value")

        cache.pop(key)
        with open(bank, 'w', encoding="utf-8") as f:
            json.dump(cache, f)

def cache_store(bank: str, key: str, value: dict):
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
            "last_update": time.time()
        }

        with open(bank, 'w', encoding="utf-8") as f:
            json.dump(cache, f)
