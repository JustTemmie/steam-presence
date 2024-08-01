import os
import sys
import json
import time

# for development purposes
if __name__ == "__main__":
    sys.path.append(".")

import src.helpers as steam_presence

icons_file = "data/icons.json"


def get_image_from_disk(gameName) -> str | None:
    if not os.path.isfile(icons_file):
        with open(icons_file, "w") as f:
            json.dump({}, f)
    
    with open(icons_file) as f:
        data = json.load(f)
    
    data = steam_presence.ensure_lowercase_dictionary_keys(data)
    
    try:
        return data[gameName.casefold()]["url"]
    except KeyError:
        return None

def write_image_to_disk(gameName: str, url: str, text: str = None) -> None:
    if not os.path.isfile(icons_file):
        with open(icons_file, "w") as f:
            json.dump({}, f)
    
    with open(icons_file) as f:
        data = json.load(f)
    
    data[gameName.casefold()] = {
        "url": url,
        "text": text
    }
    
    with open(icons_file, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    write_image_to_disk("twitter", "https://cdn-icons-png.flaticon.com/512/733/733579.png")
    print(get_image_from_disk("twitter"))