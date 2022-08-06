from python_steamgriddb.steamgrid import SteamGridDB
import requests

sgdb = SteamGridDB('d8bdff9e0fdadd0dd2658af07882d35d')

from steamgrid import StyleType, PlatformType, MimeType, ImageType

results = sgdb.search_game("deep rock galactic")

# yes this is terrible code but i really couldn't figure out a better way to do this, sorry - pull request anyone?
result = str(results).split(',')[0][1:]
steamGridAppID = result[9:].split(' ')[0]
# Get grids list by filter (Multiple filters are allowed)
#grids = sgdb.get_grids_by_gameid(game_ids=[21202])

resolutions = [
    512,
    256,
    128,
    64,
    32,
    16
]
grids = sgdb.get_icons_by_gameid(game_ids=[steamGridAppID])
i = grids[0]
for res in resolutions:
    i = str(i)
    newURL = i[:-4] + f"/32/{res}x{res}.png"
    
    r = requests.get(newURL)
    if r.status_code == 200:
        break

print(newURL)
    #print(i)