import os
import sys
import json
import time

from bs4 import BeautifulSoup
import functools

if __name__ == "__main__":
    # change the path to match the root directory when testing it
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    
from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

class SGDB():
    def __init__(self, SGDB_gridKey):
        self.sgdbKey = SGDB_gridKey
    
    def sgdb_request(self, endpoint):
        r = requests.get(
            f"https://www.steamgriddb.com/api/v2/{endpoint}",
            headers={"Authorization": f"Bearer {self.sgdbKey}"}
        )
        
        return r
    
    @functools.cache
    def get_ID_by_steam_ID(self, steamAppID):
        r = self.sgdb_request(f"games/steam/{steamAppID}")
        
        if r.status_code != 200:
            return
        
        return r.json()["data"]["id"]

    @functools.cache
    def get_ID_by_name(self, gameName):
        r = self.sgdb_request(f"search/autocomplete/{gameName}")
        
        if r.status_code != 200:
            return
        
        return r.json()["data"][0]["id"]
    
    @functools.cache
    def get_icon_url(self, gridAppID):
        r = self.sgdb_request(f"icons/game/{gridAppID}")
        
        if r.status_code != 200:
            return
        
        icons = r.json()["data"]
        
        if len(icons) == 0:
            return
        
        contenders = []
        for icon in icons:
            if icon["style"] == "official":
                contenders.append(icon)
        
        contenders = sorted(contenders, key=lambda i: i["score"])
        
        for icon in contenders:
            if icon["mime"] in ["image/png", "image/jpg", "image/webp"]:
                return icon["url"]
        
        contenders = icons
        contenders = sorted(contenders, key=lambda i: i["score"])
        for icon in contenders:
            if icon["mime"] in ["image/png", "image/jpg", "image/webp"]:
                return icon["url"]
        
        return contenders[0]["thumb"]
        
    
    def get_icon_url_from_steam_id(self, steamAppID) -> str:
        ID = self.get_ID_by_steam_ID(steamAppID)
        return self.get_icon_url(ID)
    
    def get_icon_url_from_game_name(self, gameName) -> str:
        ID = self.get_ID_by_name(gameName)
        return self.get_icon_url(ID)
        


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    with open("config.json") as f:
        config = json.load(f)
    
    sgdb = SGDB(config["SERVICES"]["STEAM_GRID_DB"]["API_KEY"])
    ID = sgdb.get_ID_by_name("helldivers 2")
    print(sgdb.get_icon(ID))