import os
import sys
import json
import time


project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

from src.helpers import *

def get_image_from_cache(gameName) -> str:
    with open(f'{project_root}/data/icons.txt', 'r') as icons:            
        for line in icons:
            line = line.split("\n")
            game = line[0].split("=")
            if gameName.casefold() == game[0].casefold():
                coverData = game[1].split("||")
                coverImage = coverData[0]
                
                log(f"found icon for {gameName} in cache")
                return coverImage