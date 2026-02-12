import requests
import threading

from typing import Optional, Literal
import logging

# locks to ensure we're not uploading multiple copies of the same file
_uploading_lock = threading.Lock()
_uploading_set = set()

def upload_file(
    file_path: str,
    ttl: Literal['1h', '12h', '24h', '72h', 'indefinite'] = None
) -> Optional[str]:
    with _uploading_lock:
        if file_path in _uploading_set:
            return None
        _uploading_set.add(file_path)

    if ttl == "indefinite":
        url = "https://catbox.moe/user/api.php"
        data = {
            "reqtype": "fileupload"
        }
    else:
        url = "https://litterbox.catbox.moe/resources/internals/api.php"
        data = {
            "reqtype": "fileupload",
            "time": ttl
        }

    try:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": (file_path, f)}
            logging.debug("Uploading %s to catbox", file_path)
            response = requests.post(url, data=data, files=files, timeout=120)
            logging.info("Sucessfully uploaded %s to catbox", file_path)

        response.raise_for_status()
        return response.text

    except requests.exceptions.RequestException:
        logging.error("Catbox upload failed: %s", file_path)
        return None

    finally:
        with _uploading_lock:
            _uploading_set.discard(file_path)