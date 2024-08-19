import os
import sys
import json
import requests

from plyer import notification

import src.helpers as steam_presence

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

def verifyProjectVersion():
    metaFile = getMetaFile()
    if metaFile["structure-version"] == "0":
        print("-" * 50)
        steam_presence.log("updating meta.json's structure-version to `1`")
        steam_presence.log("importing libraries for meta update")
        try:
            import shutil
        except ImportError:
            steam_presence.error("import error whilst importing `shutil`, exiting")
            exit()
        
        if not os.path.exists(f"{project_root}/data"):
            steam_presence.log(f"creating {project_root}/data/")
            os.makedirs(f"{project_root}/data")
        
        expectedFiles = {
            "icons.txt": "",
            "games.txt": "",
            "customGameIDs.json": "{}"
        }
        
        for i in expectedFiles:
            if not os.path.exists(i):
                steam_presence.log(f"creating file `{i}` with content `{expectedFiles[i]}`")
                with open(f"{project_root}/{i}", "w") as f:
                    f.write(expectedFiles[i])  
        
        try:
            steam_presence.log(f"moving {project_root}/icons.txt")
            shutil.move(f"{project_root}/icons.txt",           f"{project_root}/data/icons.txt")
            steam_presence.log(f"moving {project_root}/games.txt")
            shutil.move(f"{project_root}/games.txt",           f"{project_root}/data/games.txt")
            steam_presence.log(f"moving {project_root}/customGameIDs.json")
            shutil.move(f"{project_root}/customGameIDs.json",  f"{project_root}/data/customGameIDs.json")
            steam_presence.log(f"moving {project_root}/meta.json")
            shutil.move(f"{project_root}/meta.json",           f"{project_root}/data/meta.json")
            
            writeToMetaFile(["structure-version"], "1")
        except Exception as e:
            steam_presence.error(f"error encountered whilst trying to update the config-version to version 1, exiting\nError encountered: {e}")
            exit()
        print("-" * 50)
    elif metaFile["structure-version"] == "1":
        
        cache_files = [
            "temp_cache", "persistent_cache"
        ]
        
        for file in cache_files:
            steam_presence.log(f"creating file: {project_root}/data/{file}.json")
            with open(f"{project_root}/data/{file}.json", "w") as f:
                f.write("{}")
        
        writeToMetaFile(["structure-version"], "2")
        
    elif metaFile["structure-version"] == "2":
        print("-" * 50)
        print("program's current folder structure version is up to date")
    else:
        print("-" * 50)
        steam_presence.error("invalid structure-version found in meta.json, exiting")
        exit()

# checks if the program has any updates
def checkForUpdate(currentVersion):
    URL = f"https://api.github.com/repos/JustTemmie/steam-presence/releases/latest"
    try:
        r = requests.get(URL)
    except Exception as e:
        steam_presence.error(f"failed to check if a newer version is available, falling back...\nfull error: {e}")
        return
    
    if r.status_code != 200:
        steam_presence.error(f"status code {r.status_code} recieved when trying to find latest version of steam presence, ignoring")
        return

    # the newest current release tag name
    newestVersion = r.json()["tag_name"]
    
    # make the version numbers easier to parse
    parsableCurrentVersion = currentVersion.replace("v", "") # the `currentVersion` variable is set in the main() function so i'm less likely to forget, lol
    parsableNewestVersion = newestVersion.replace("v", "")
    
    parsableCurrentVersion = parsableCurrentVersion.split(" ")[0]
    
    parsableCurrentVersion = parsableCurrentVersion.split(".")
    parsableNewestVersion = parsableNewestVersion.split(".")
    
    
    # make sure both ot the version lists have 4 entries so that the zip() function below works properly
    for i in [parsableNewestVersion, parsableCurrentVersion]:
        while len(i) < 4:
            i.append(0)
    
    # loop thru both of the version lists,
    for new, old in zip(parsableNewestVersion, parsableCurrentVersion):
        if int(new) > int(old):
            print("-" * 50)
            print("there's a newer update available!")
            print(f"if you wish to upload from `{currentVersion}` to `{newestVersion}` simply run `git pull` from the terminal/cmd in the same folder as main.py")
            print(f"commits made in this time frame: https://github.com/JustTemmie/steam-presence/compare/{currentVersion}...{newestVersion}")
            
            if steam_presence.getConfigFile().get("ENABLE_SYSTEM_NOTIFICATIONS", False):
                notification.notify(
                    title = 'Steam Presence',
                    message = "There's a newer version available - edit the config.json file if you'd like to disable this notification,",
                    app_icon = None,
                    timeout = 7.5,
                )
            
            return
        # if the current version is newer than the "newest one", just return to make sure it doesn't falsly report anything
        # this shouldn't ever come up for most people - but it's probably a good idea to include this if statement; just in case 
        if int(old) > int(new):
            print("-" * 50)
            print("it seems like you're running a pre-relase version of steam-presence - expect bugs!")
            return
    
    print("-" * 50)
    print("running the latest version of steam-presence")



def getMetaFile():
    if os.path.exists(f"{project_root}/data/meta.json"):
        with open(f"{project_root}/data/meta.json", "r") as f:
            metaFile = json.load(f)
    
    elif os.path.exists(f"{project_root}/meta.json"):
        with open(f"{project_root}/meta.json", "r") as f:
            metaFile = json.load(f)
    
    else:
        # remove in 1.12? maybe 1.13 - whenever i do anything else with the meta file - just make this throw an error instead
        steam_presence.steam_presence.log("couldn't find the the meta file, creating new one")
        with open(f"{project_root}/meta.json", "w") as f:
            metaFile = json.dump({"structure-version": "0"}, f)
        
        return getMetaFile()
        
    return metaFile

def writeToMetaFile(keys: list, value):
    metaFile = getMetaFile()
    
    for i in range(len(keys) - 1):
        metaFile = metaFile[keys[i]]
    
    metaFile[keys[-1]] = value
    
    with open(f"{project_root}/data/meta.json", "w") as f:
        json.dump(metaFile, f)
    