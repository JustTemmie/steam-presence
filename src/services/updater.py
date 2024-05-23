import os
import sys
import json

from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

def verifyProjectVersion():
    metaFile = getMetaFile()
    if metaFile["structure-version"] == "0":
        print("----------------------------------------------------------")
        log("updating meta.json's structure-version to `1`")
        log("importing libraries for meta update")
        try:
            import shutil
        except ImportError:
            error("import error whilst importing `shutil`, exiting")
            exit()
        
        if not os.path.exists(f"{project_root}/data"):
            log(f"creating {project_root}/data/")
            os.makedirs(f"{project_root}/data")
        
        expectedFiles = {
            "icons.txt": "",
            "games.txt": "",
            "customGameIDs.json": "{}"
        }
        
        for i in expectedFiles:
            if not os.path.exists(i):
                log(f"creating file `{i}` with content `{expectedFiles[i]}`")
                with open(f"{project_root}/{i}", "w") as f:
                    f.write(expectedFiles[i])  
        
        try:
            log(f"moving {project_root}/icons.txt")
            shutil.move(f"{project_root}/icons.txt",           f"{project_root}/data/icons.txt")
            log(f"moving {project_root}/games.txt")
            shutil.move(f"{project_root}/games.txt",           f"{project_root}/data/games.txt")
            log(f"moving {project_root}/customGameIDs.json")
            shutil.move(f"{project_root}/customGameIDs.json",  f"{project_root}/data/customGameIDs.json")
            log(f"moving {project_root}/meta.json")
            shutil.move(f"{project_root}/meta.json",           f"{project_root}/data/meta.json")
            
            writeToMetaFile(["structure-version"], "1")
        except Exception as e:
            error(f"error encountered whilst trying to update the config-version to version 1, exiting\nError encountered: {e}")
            exit()
        print("----------------------------------------------------------")
    elif metaFile["structure-version"] == "1":
        
        cache_files = [
            "temp_cache", "persistent_cache"
        ]
        
        for file in cache_files:
            log(f"creating file: {project_root}/data/{file}.json")
            with open(f"{project_root}/data/{file}.json", "w") as f:
                f.write("{}")
        
        writeToMetaFile(["structure-version"], "2")
        
    elif metaFile["structure-version"] == "2":
        print("----------------------------------------------------------")
        log("progam's current folder structure version is up to date...")
        print("----------------------------------------------------------")
    else:
        error("invalid structure-version found in meta.json, exiting")
        exit()

# checks if the program has any updates
def checkForUpdate(currentVersion):
    URL = f"https://api.github.com/repos/JustTemmie/steam-presence/releases/latest"
    try:
        r = requests.get(URL)
    except Exception as e:
        error(f"failed to check if a newer version is available, falling back...\nfull error: {e}")
        return
    
    if r.status_code != 200:
        error(f"status code {r.status_code} recieved when trying to find latest version of steam presence, ignoring")
        return

    # the newest current release tag name
    newestVersion = r.json()["tag_name"]
    
    # make the version numbers easier to parse
    parsableCurrentVersion = currentVersion.replace("v", "") # the `currentVersion` variable is set in the main() function so i'm less likely to forget, lol
    parsableNewestVersion = newestVersion.replace("v", "")
    
    parsableCurrentVersion = parsableCurrentVersion.split(".")
    parsableNewestVersion = parsableNewestVersion.split(".")
    
    
    # make sure both ot the version lists have 4 entries so that the zip() function below works properly
    for i in [parsableNewestVersion, parsableCurrentVersion]:
        while len(i) < 4:
            i.append(0)
    
    # loop thru both of the version lists,
    for new, old in zip(parsableNewestVersion, parsableCurrentVersion):
        if int(new) > int(old):
            print("----------------------------------------------------------")
            print("there's a newer update available!")
            print(f"if you wish to upload from `{currentVersion}` to `{newestVersion}` simply run `git pull` from the terminal/cmd in the same folder as main.py")
            print(f"commits made in this time frame: https://github.com/JustTemmie/steam-presence/compare/{currentVersion}...{newestVersion}")
            print("----------------------------------------------------------")
            return
        # if the current version is newer than the "newest one", just return to make sure it doesn't falsly report anything
        # this shouldn't ever come up for most people - but it's probably a good idea to include this if statement; just in case 
        if int(old) > int(new):
            return


def getMetaFile():
    if os.path.exists(f"{project_root}/data/meta.json"):
        with open(f"{project_root}/data/meta.json", "r") as f:
            metaFile = json.load(f)
    
    elif os.path.exists(f"{project_root}/meta.json"):
        with open(f"{project_root}/meta.json", "r") as f:
            metaFile = json.load(f)
    
    else:
        # remove in 1.12? maybe 1.13 - whenever i do anything else with the meta file - just make this throw an error instead
        log("couldn't find the the meta file, creating new one")
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
    