def getMetaFile():
    if exists(f"{dirname(__file__)}/data/meta.json"):
        with open(f"{dirname(__file__)}/data/meta.json", "r") as f:
            metaFile = json.load(f)
    
    elif exists(f"{dirname(__file__)}/meta.json"):
        with open(f"{dirname(__file__)}/meta.json", "r") as f:
            metaFile = json.load(f)
    
    else:
        # remove in 1.12? maybe 1.13 - whenever i do anything else with the meta file - just make this throw an error instead
        log("couldn't find the the meta file, creating new one")
        with open(f"{dirname(__file__)}/meta.json", "w") as f:
            metaFile = json.dump({"structure-version": "0"}, f)
        
        return getMetaFile()
        
    return metaFile

def writeToMetaFile(keys: list, value):
    metaFile = getMetaFile()
    
    for i in range(len(keys) - 1):
        metaFile = metaFile[keys[i]]
    
    metaFile[keys[-1]] = value
    
    with open(f"{dirname(__file__)}/data/meta.json", "w") as f:
        json.dump(metaFile, f)
    
    log(f"version {value} was successfully written to the metafile")


# opens the config file and loads the data
def getConfigFile():
    # the default settings, don't use exampleConfig.json as people might change that
    defaultSettings = {
        "STEAM_API_KEY": "STEAM_API_KEY",
        "USER_IDS": "USER_ID",

        "DISCORD_APPLICATION_ID": "869994714093465680",
        
        "COVER_ART": {
            "STEAM_GRID_DB": {
                "ENABLED": False,
                "STEAM_GRID_API_KEY": "STEAM_GRID_API_KEY"
            },
            "USE_STEAM_STORE_FALLBACK": True
        },

        "LOCAL_GAMES": {
            "ENABLED": False,
            "LOCAL_DISCORD_APPLICATION_ID": "1062648118375616594",
            "GAMES": [
                "processName1",
                "processName2",
                "processName3"
            ]
        },

        "GAME_OVERWRITE": {
            "ENABLED": False,
            "NAME": "NAME",
            "SECONDS_SINCE_START": 0
        },

        "CUSTOM_ICON": {
            "ENABLED": False,
            "URL": "https://raw.githubusercontent.com/JustTemmie/steam-presence/main/readmeimages/defaulticon.png",
            "TEXT": "Steam Presence on Discord"
        }
    }

    if exists(f"{dirname(abspath(__file__))}/config.json"):
        logDebug("reading config.json")
        with open(f"{dirname(abspath(__file__))}/config.json", "r") as f:
            userSettings = json.load(f)
    
    elif exists(f"{dirname(abspath(__file__))}/exampleconfig.json"):
        logDebug("reading exampleconfig.json")
        with open(f"{dirname(abspath(__file__))}/exampleconfig.json", "r") as f:
            userSettings = json.load(f)
    
    else:
        error("Config file not found. Please read the readme and create a config file.")
        exit()
    
        
    # if something isn't speficied in the user's config file, fill it in with data from the default settings 
    settings = {**defaultSettings, **userSettings}
    for key, value in defaultSettings.items():
        if key in settings and isinstance(value, dict):
            settings[key] = {**value, **settings[key]}
            
    
    return settings


def verifyProjectVersion():
    metaFile = getMetaFile()
    if metaFile["structure-version"] == "0":
        print("----------------------------------------------------------")
        log("updating meta.json's structure-version to `1`...")
        log("importing libraries for meta update")
        try:
            import shutil
        except ImportError:
            error(f"import error whilst importing `shutil`, exiting\n    error: {e}")
            exit()
        
        if not os.path.exists(f"{dirname(__file__)}/data"):
            log(f"creating {dirname(__file__)}/data/")
            os.makedirs(f"{dirname(__file__)}/data")
        
        expectedFiles = {
            "icons.txt": "",
            "games.txt": "",
            "customGameIDs.json": "{}"
        }
        
        for i in expectedFiles:
            if not os.path.exists(i):
                log(f"creating file `{i}` with content `{expectedFiles[i]}`")
                with open(f"{dirname(__file__)}/{i}", "w") as f:
                    f.write(expectedFiles[i])  
        
        try:
            log(f"moving {dirname(__file__)}/icons.txt")
            shutil.move(f"{dirname(__file__)}/icons.txt",           f"{dirname(__file__)}/data/icons.txt")
            log(f"moving {dirname(__file__)}/games.txt")
            shutil.move(f"{dirname(__file__)}/games.txt",           f"{dirname(__file__)}/data/games.txt")
            log(f"moving {dirname(__file__)}/customGameIDs.json")
            shutil.move(f"{dirname(__file__)}/customGameIDs.json",  f"{dirname(__file__)}/data/customGameIDs.json")
            log(f"moving {dirname(__file__)}/meta.json")
            shutil.move(f"{dirname(__file__)}/meta.json",           f"{dirname(__file__)}/data/meta.json")
            
            writeToMetaFile(["structure-version"], "1")
            return verifyProjectVersion()
        except Exception as e:
            error(f"error encountered whilst trying to update the config-version to version 1, exiting\nError encountered: {e}")
            exit()
        
    elif metaFile["structure-version"] == "1":
        log("updating meta.json's structure-version to `2`...")
        log("importing libraries for meta update")
        try:
            import shutil
        except ImportError as e:
            error(f"import error whilst importing `shutil`, exiting\n    error: {e}")
            exit()
        
        
        if not os.path.exists(f"{dirname(__file__)}/data"):
            error(f"couldn't find {dirname(__file__)}/data/ - exiting...")
            exit()
        
        log("creating cache directory...")
        os.makedirs(f"{dirname(__file__)}/data/cache")
        
        expectedFiles = {
            "discordIDs.json": "{}",
            "steamIDs.json": "{}",
        }
        
        for i in expectedFiles:
            if not os.path.exists(i):
                newFile = f"{dirname(__file__)}/data/cache/{i}"
                log(f"creating file `{newFile}` with content `{expectedFiles[i]}`")
                with open(newFile, "w") as f:
                    f.write(expectedFiles[i])  
        
        writeToMetaFile(["structure-version"], "2")
        return verifyProjectVersion()
        
        
        # TODO IMPORTANT
        # do the fucky shit with config.json and make sure that works
        
        return verifyProjectVersion()
    elif metaFile["structure-version"] == "2":
        print("----------------------------------------------------------")
        log("progam's current folder structure is up to date...")
        print("----------------------------------------------------------")
    else:
        error("invalid structure-version found in data/meta.json, exiting - please open an issue on the github if you're confused")
        exit()

# checks if the program has any updates
def checkForUpdate():
    logDebug("checking if there are any newer versions of steam presence available")
    r = makeWebRequest("https://api.github.com/repos/JustTemmie/steam-presence/releases/latest")
    if r == "error":
        error(f"error recieved when trying to find latest version of steam presence, ignoring")
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

def loadConfigFile():
    config = getConfigFile()
    
    global enabledPlatforms
    
    global steamAPIKey
    
    global steamStoreCoverartBackup
    global gridEnabled
    global gridKey
    
    global doCustomIcon
    
    global doCustomGame
    global customGameName
    global customGameStartOffset
    
    global debugMode
    
    enabledPlatforms = {
        "steam": {
            "enabled":config["STEAM"]["ENABLED"],
            "APIKey": config["STEAM_API_KEY"],
            "appID": config["DISCORD_APPLICATION_ID"],
            "gameReviews": config["STEAM"]["FETCH_STEAM_REVIEWS"],
            "storeButton": config["STEAM"]["ADD_STEAM_STORE_BUTTON"],
            
            "webscraping": {
                "enabled": config["STEAM"]["WEB_SCRAPE"]
            },
            "enchanedPresence": {
                "enabled": config["STEAM"]["FETCH_STEAM_RICH_PRESENCE"]
            }
        },
        "localGames": {
            "enabled": config["LOCAL_GAMES"]["ENABLED"],
            "appID": config["LOCAL_GAMES"]["LOCAL_DISCORD_APPLICATION_ID"],
            "processes": config["LOCAL_GAMES"]["GAMES"]
        }
    }

    
    steamAPIKey = config["STEAM_API_KEY"]
    
    steamStoreCoverartBackup = config["COVER_ART"]["USE_STEAM_STORE_FALLBACK"]
    gridEnabled = config["COVER_ART"]["STEAM_GRID_DB"]["ENABLED"]
    gridKey = config["COVER_ART"]["STEAM_GRID_DB"]["STEAM_GRID_API_KEY"]
    
    doCustomIcon = config["CUSTOM_ICON"]["ENABLED"]
    
    doCustomGame = config["GAME_OVERWRITE"]["ENABLED"]
    customGameName = config["GAME_OVERWRITE"]["NAME"]
    customGameStartOffset = config["GAME_OVERWRITE"]["SECONDS_SINCE_START"]
    
    debugMode = config["DEBUG_MODE"]