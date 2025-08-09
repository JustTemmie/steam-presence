import os
import requests

def get_terminal_width() -> int:
    width: int

    try:
        size = os.get_terminal_size()
        width = size.columns
    except:
        width = 10
    
    return width


def fetch(url: str) -> requests.Response | None:
    try:
        r = requests.get(url)

        if r.status_code != 200:
            return
        
        return r
    except requests.exceptions.ConnectTimeout:
        return