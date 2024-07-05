# creating rich presences for discord
from time import sleep, time

# for errors
from datetime import datetime

# for loading the config file
import json
from os.path import exists, dirname, abspath

# for restarting the script on a failed run
import sys 
import os

# for general programing
import copy

try:
    # requesting data from steam's API
    import requests

    # creating rich presences for discord
    from pypresence import Presence

    # used to get the game's cover art
    from steamgrid import SteamGridDB
    
    # used as a backup when cover art
    from bs4 import BeautifulSoup
    
    # used to check applications that are open locally
    import psutil
    
    # used to load cookies for non-steam games
    import http.cookiejar as cookielib

except:
    answer = input("looks like either requests, pypresence, steamgrid, psutil, or beautifulSoup is not installed, do you want to install them? (y/n) ")
    if answer.lower() == "y":
        from os import system
        print("installing required packages...")
        system(f"python3 -m pip install -r {dirname(abspath(__file__))}/requirements.txt")
        
        from pypresence import Presence
        from steamgrid import SteamGridDB
        from bs4 import BeautifulSoup
        import psutil
        import requests
        import http.cookiejar as cookielib
        
        print("\npackages installed and imported successfully!")

# just shorthand for logs and errors - easier to write in script
def log(log):
    print(f"[{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {log}")

def error(error):
    print(f"    ERROR: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {error}")

# i've gotten the error `requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))` a lot;
# this just seems to sometimes happens if your network conection is a bit wack, this function is a replacement for requests.get() and basically just does error handling and stuff
def makeWebRequest(URL, loops=0):
    try:
        r = requests.get(URL)
        return r
    except Exception as e:
        if loops > 10:
            error(f"falling back... the script got caught in a loop while fetching data from `{URL}`")
            return "error"
        elif "104 'Connection reset by peer'" in str(e):
            return makeWebRequest(URL, loops+1)
        else:
            # error(f"falling back... exception met whilst trying to fetch data from `{URL}`\nfull error: {e}")
            return "error"

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
    
    
    
# opens the config file and loads the data
def getConfigFile():
    # the default settings, don't use exampleConfig.json as people might change that
    defaultSettings = {
        "STEAM_API_KEY": "STEAM_API_KEY",
        "USER_IDS": "USER_ID",

        "DISCORD_APPLICATION_ID": "869994714093465680",

        "FETCH_STEAM_RICH_PRESENCE": True,
        "FETCH_STEAM_REVIEWS": False,
        "ADD_STEAM_STORE_BUTTON": False,
        
        "WEB_SCRAPE": False,
        
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
        },
  
        "BLACKLIST" : [
            "game1",
            "game2",
            "game3"
        ]
    }

    if exists(f"{dirname(abspath(__file__))}/config.json"):
        with open(f"{dirname(abspath(__file__))}/config.json", "r") as f:
            userSettings = json.load(f)
    
    elif exists(f"{dirname(abspath(__file__))}/exampleconfig.json"):
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

def removeChars(inputString: str, ignoredChars: str) -> str:
    # removes all characters in the ingoredChars string from the inputString
    for ignoredChar in ignoredChars:
        if ignoredChar in inputString:
            for j in range(len(inputString) - 1, 0, -1):
                if inputString[j] in ignoredChar:
                    inputString = inputString[:j] + inputString[j+1:]

    return inputString


def getImageFromSGDB(loops=0):
    global coverImage
    global coverImageText
    
    log("searching for an icon using the SGDB")
    # searches SGDB for the game you're playing
    results = sgdb.search_game(gameName)
    
    if len(results) == 0:
        log(f"could not find anything on SGDB")
        return

    
    log(f"found the game {results[0]} on SGDB")
    gridAppID = results[0].id
    
    # searches for icons
    gridIcons = sgdb.get_icons_by_gameid(game_ids=[gridAppID])
    
    # makes sure anything was returned at all
    if gridIcons != None:
    
        # throws the icons into a dictionary with the required information, then sorts them using the icon height
        gridIconsDict = {}
        for i, gridIcon in enumerate(gridIcons):
            gridIconsDict[i] = [gridIcon.height, gridIcon._nsfw, gridIcon.url, gridIcon.mime, gridIcon.author.name, gridIcon.id]
        
        gridIconsDict = (sorted(gridIconsDict.items(), key=lambda x:x[1], reverse=True))
        
        
        # does a couple checks before making it the cover image
        for i in range(0, len(gridIconsDict)):
            entry = gridIconsDict[i][1]
            # makes sure image is not NSFW
            if entry[1] == False:
                # makes sure it's not an .ico file - discord cannot display these
                if entry[3] == "image/png":
                    # sets the link, and gives credit to the artist if anyone hovers over the icon
                    coverImage = entry[2]
                    coverImageText = f"Art by {entry[4]} on SteamGrid DB"
                    log("successfully retrived icon from SGDB")
                    # saves this data to disk
                    with open(f'{dirname(abspath(__file__))}/data/icons.txt', 'a') as icons:
                        icons.write(f"{gameName.lower()}={coverImage}||{coverImageText}\n")
                        icons.close()
                    return
        
        log("failed, trying to load from the website directly")
        # if the game doesn't have any .png files for the game, try to web scrape them from the site
        for i in range(0, len(gridIconsDict)):
            entry = gridIconsDict[i][1]
            # makes sure image is not NSFW
            if entry[1] == False:
                URL = f"https://www.steamgriddb.com/icon/{entry[5]}"
                page = makeWebRequest(URL)
                if page == "error":
                    return
                
                if page.status_code != 200:
                    error(f"status code {page.status_code} recieved when trying to web scrape SGDB, ignoring")
                    return

                # web scraping, this code is messy
                soup = BeautifulSoup(page.content, "html.parser")

                img = soup.find("meta", property="og:image")
                
                coverImage = img["content"]
                coverImageText = f"Art by {entry[4]} on SteamGrid DB"

                log("successfully retrived icon from SGDB")

                # saves data to disk
                with open(f'{dirname(abspath(__file__))}/data/icons.txt', 'a') as icons:
                    icons.write(f"{gameName.lower()}={coverImage}||{coverImageText}\n")
                    icons.close()
                return
        
        log("failed to fetch icon from SGDB")
    
    else:
        log(f"SGDB doesn't seem to have any entries for {gameName}")

def getGameSteamID():
    # fetches a list of ALL games on steam
    r = makeWebRequest(f"https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={steamAPIKey}&format=json")
    if r == "error":
        return
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    if r.status_code == 403:
        error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
        exit()
    
    if r.status_code != 200:
        error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
        return

    respone = r.json()
    
    global gameSteamID
        
    # loops thru every game until it finds one matching your game's name
    for i in respone["applist"]["apps"]:
        if gameName.lower() == i["name"].lower():

            if gameSteamID == 0:
                log(f"steam app ID {i['appid']} found for {gameName}")
            
            gameSteamID = i["appid"]
            return
    
    
    # for handling game demos
    if " demo" in gameName.lower():
        tempGameName = copy(gameName.lower())
        tempGameName.replace(" demo", "")
        for i in respone["applist"]["apps"]:
            if tempGameName.lower() == i["name"].lower():

                if gameSteamID == 0:
                    log(f"steam app ID {i['appid']} found for {gameName}")
                
                gameSteamID = i["appid"]
                return
    
    
    
    # if we didn't find the game at all on steam, 
    log(f"could not find the steam app ID for {gameName}")
    gameSteamID = 0


def getImageFromStorepage():    
    global coverImage
    global coverImageText
    
    # if the steam game ID is known to be invalid, just return immediately
    if gameSteamID == 0:
        coverImage = None
        coverImageText = None
        return
    
    log("getting icon from the steam store")
    try: 
        r = makeWebRequest(f"https://store.steampowered.com/api/appdetails?appids={gameSteamID}")
        if r == "error":
            return
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        sleep(0.2)
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
            coverImage = None
            coverImageText = None
            return
        
        respone = r.json()
        
        coverImage = respone[str(gameSteamID)]["data"]["header_image"]
        coverImageText = f"{gameName} on Steam"
        # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
        
        log(f"successfully found steam's icon for {gameName}")

    except Exception as e:
        error(f"Exception {e} raised when trying to fetch {gameName}'s icon thru steam, ignoring")
        coverImage = None
        coverImageText = None


def getGameReviews():    
    # get the review data for the steam game
    r = makeWebRequest(f"https://store.steampowered.com/appreviews/{gameSteamID}?json=1")
    if r == "error":
        return
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    if r.status_code != 200:
        error(f"error code {r.status_code} met when requesting the review score for {gameName}, ignoring")
        return

    # convert it to a dictionary
    respone = r.json()
    
    # sometimes instead of returning the disered dicationary steam just decides to be quirky
    # and it returns the dictionary `{'success': 2}` - something which isn't really useful. If this happens we try again :)
    if respone["success"] != 1:
        getGameReviews()
        return
    
    response = respone["query_summary"]
    
    if response["total_positive"] == 0:
        return
    
    global gameReviewScore
    global gameReviewString
    
    gameReviewScore = round(
        (response["total_positive"] / response["total_reviews"]) * 100
        , 2)
    gameReviewString = response["review_score_desc"]

    
# searches the steam grid DB or the official steam store to get cover images for games
def getGameImage():
    global coverImage
    global coverImageText
    
    coverImage = ""
    
    log(f"fetching icon for {gameName}")
    
    # checks if there's already an existing icon saved to disk for the game 
    with open(f'{dirname(abspath(__file__))}/data/icons.txt', 'r') as icons:
        for i in icons:
            # cut off the new line character
            game = i.split("\n")
            game = game[0].split("=")
            if gameName.lower() == game[0]:
                coverData = game[1].split("||")
                coverImage = coverData[0]
                
                # if the script doesn't find text saved for the image, it won't set any  
                if len(coverData) >= 2:
                    coverImageText = coverData[1]
                # write over it and set it to None, just in case
                else:
                    coverImageText = None

                log(f"found icon for {gameName} in cache")
                return
    
    log("no image found in cache")

    if gridEnabled and coverImage == "":
        getImageFromSGDB()

    if appID != defaultAppID and appID != defaultLocalAppID and coverImage == "":
        getImageFromDiscord()
        
    if steamStoreCoverartBackup and coverImage == "":
        getImageFromStorepage()


def getGamePrice():
    r = makeWebRequest(f"https://store.steampowered.com/api/appdetails?appids={gameSteamID}&cc=us")
    if r == "error":
        return
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    if r.status_code != 200:
        error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
        return
    
    respone = r.json()
    
    if "price_overview" not in respone[str(gameSteamID)]["data"]:
        return
    
    return respone[str(gameSteamID)]["data"]["price_overview"]["final_formatted"]
        
        
# web scrapes the user's web page, sending the needed cookies along with the request
def getWebScrapePresence():
    if not exists(f"{dirname(abspath(__file__))}/cookies.txt"):
        print("cookie.txt not found, this is because `WEB_SCRAPE` is enabled in the config")
        return
    
    cj = cookielib.MozillaCookieJar(f"{dirname(abspath(__file__))}/cookies.txt")
    cj.load()
    
    # split on ',' in case of multiple userIDs
    for i in userID.split(","):
        URL = f"https://steamcommunity.com/profiles/{i}/"
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        sleep(0.2)
        
        try:
            page = requests.post(URL, cookies=cj)
        except requests.exceptions.RetryError as e:
            log(f"failed connecting to {URL}, perhaps steam is down for maintenance?\n    error:{e}")
            return
        except Exception as e:
            error(f"error caught while web scraping data from {URL}, ignoring\n    error:{e}")
            return
        
        if page.status_code == 403:
            error("Forbidden, Access to Steam has been denied, please verify that your cookies are up to date")

        elif page.status_code != 200:
            error(f"error code {page.status_code} met when trying to fetch game thru webscraping, ignoring")

        else:
            soup = BeautifulSoup(page.content, "html.parser")

            for element in soup.find_all("div", class_="profile_in_game_name"):
                result = element.text.strip()

                # the "last online x min ago" field is the same div as the game name
                if "Last Online" not in result:
                    
                    global isPlayingSteamGame
                    global gameName
                    
                    isPlayingSteamGame = False
                    gameName = result

# checks what game the user is currently playing
def getSteamPresence():
    r = makeWebRequest(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steamAPIKey}&format=json&steamids={userID}")
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    # if it errors out, just return the already asigned gamename
    if r == "error":
        return gameName
    
        
    if r.status_code == 403:
        error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
        exit()

    if r.status_code != 200:
        error(f"error code {r.status_code} met when trying to fetch game, ignoring")
        return gameName
    
    
    response = r.json()
    
    # counts how many users you're supposed to get back, and checks if you got that many back
    if len(response["response"]["players"]) != userID.count(",") + 1:
        error("There seems to be an incorrect account ID given, please verify that your user ID(s) are correct")


    global isPlayingSteamGame

    # sort the players based on position in the config file
    sorted_response = []
    for steam_id in userID.split(","):
        for player in response["response"]["players"]:
            if player["steamid"] == steam_id:
                sorted_response.append(player)
                break


    # loop thru every user in the response, if they're playing a game, save it
    for i in range(0, len(sorted_response)):
        if "gameextrainfo" in sorted_response[i]:
            game_title = sorted_response[i]["gameextrainfo"]
            if game_title != gameName:
                log(f"found game {game_title} played by {sorted_response[i]['personaname']}")
            isPlayingSteamGame = True
            return game_title

    return ""

# webscrape the "enhanced" rich presence information for your profile
# if you're confused this uses your <id3>, it's your <id64> (which is what you put into the config file) minus 76561197960265728
# aka <id3> = <id64> - 76561197960265728
# why steam does this is beyond me but it's fine
# thank you so much to `wuddih` in this post for being the reason i found out about this https://steamcommunity.com/discussions/forum/1/5940851794736009972/ lmao 
def getSteamRichPresence():
    for i in userID.split(","):
        # userID type 3. <id3> = <id64> - 76561197960265728
        URL = f"https://steamcommunity.com/miniprofile/{int(i) - 76561197960265728}"
        try:
            pageRequest = makeWebRequest(URL)
        except requests.exceptions.RetryError as e:
            log(f"failed connecting to {URL}, perhaps steam is down for maintenance?\n    error:{e}")
            return
        except Exception as e:
            error(f"error caught while fetching enhanced RPC data from {URL}, ignoring\n    error:{e}")
            return
        
        if pageRequest == "error":
            return
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        sleep(0.2)
        
        if pageRequest.status_code != 200:
            error(f"status code {pageRequest.status_code} returned whilst trying to fetch the enhanced rich presence info for steam user ID `{i}`, ignoring function")
            return

        # turn the page into proper html formating
        soup = BeautifulSoup(pageRequest.content, "html.parser")
        
        global gameRichPresence       
        
        # double check if it's the correct game, yea i know we're basically fetching the game twice
        # once thru here, and once thru the API... BUT OH WELL - the api is used for other things so people would still need a steam api key
        # doesn't really change it that much, might change things around later
        miniGameName = soup.find("span", class_="miniprofile_game_name")
        if miniGameName != None:
            # this usually has a length of 0 when the user is playing a non steam game 
            if len(miniGameName.contents) != 0:
                if gameName != miniGameName.contents[0]:
                    # print(f"{gameName} doesn't match", soup.find("span", class_="miniprofile_game_name").contents[0])
                    break
        
        
        # find the correct entry where the rich presence is located
        rich_presence = soup.find("span", class_="rich_presence")
        
        # save rich presence if it exists
        if rich_presence != None:
            gameRichPresence = rich_presence.contents[0]
        
        # set the "enhanced rich presence" information back to nothing
        if rich_presence == None:
            gameRichPresence = ""
    
    

# requests a list of all games recognized internally by discord, if any of the names matches
# the detected game, save the discord game ID associated with said title to RAM, this is used to report to discord as that game 
def getGameDiscordID(loops=0):
    log(f"fetching the Discord game ID for {gameName}")
    r = makeWebRequest("https://discordapp.com/api/v8/applications/detectable")
    if r == "error":
        return

    
    if r.status_code != 200:
        error(f"status code {r.status_code} returned whilst trying to find the game's ID from discord")
    
    response = r.json()
    
    ignoredChars = "®©™℠"
    
    # check if the "customGameIDs.json" file exists, if so, open it
    if exists(f"{dirname(abspath(__file__))}/data/customGameIDs.json"):
        with open(f"{dirname(abspath(__file__))}/data/customGameIDs.json", "r") as f:
            # load the values of the file
            gameIDsFile = json.load(f)
            
            # add the values from the file directly to the list returned by discord
            for i in gameIDsFile:
                response.append({
                    "name": i,
                    "id": gameIDsFile[i]
                })
            
    global appID
    
    # loop thru all games
    for i in response:
        gameNames = []                      
        gameNames.append(i["name"])
        # for handling demos of games, adding it as a valid discord name because it's easier
        gameNames.append(i["name"] + " demo")
        
        # make a list containing all the names of said game
        if "aliases" in i:
            aliases = i["aliases"]
            for alias in aliases:
                gameNames.append(alias)

        for j in range(len(gameNames)):
            gameNames[j] = removeChars(
                gameNames[j].lower(),
                ignoredChars)
        
        # if it's the same, we successfully found the discord game ID
        if removeChars(gameName.lower(), ignoredChars) in gameNames:
            log(f"found the discord game ID for {removeChars(gameName.lower(), ignoredChars)}")
            appID = i["id"]
            return

    # if the game was fetched using the local checker, instead of thru steam
    if isPlayingLocalGame:
        log(f"could not find the discord game ID for {gameName}, defaulting to the secondary, local game ID")
        appID = defaultLocalAppID
        return

    log(f"could not find the discord game ID for {gameName}, defaulting to well, the default game ID")
    appID = defaultAppID
    return

# get game's icon straight from Discord's CDN
def getImageFromDiscord():
    global coverImage
    global coverImageText

    log("getting icon from Discord")

    try: 
        r = makeWebRequest(f"https://discordapp.com/api/v8/applications/{appID}/rpc")
        if r == "error":
            return
        
        if r.status_code != 200:
            error(f"status code {r.status_code} returned when requesting more info about {gameName} from Discord, ignoring")
            coverImage = None
            coverImageText = None
            return
        
        respone = r.json()
        
        coverImage = f"https://cdn.discordapp.com/app-icons/{appID}/{respone['icon']}.webp"
        coverImageText = f"{respone['name']}"
        
        log(f"successfully found Discord icon for {gameName}")

    except Exception as e:
        error(f"Exception {e} raised when trying to fetch {gameName}'s icon from Discord, ignoring")
        coverImage = None
        coverImageText = None

# checks if any local games are running
def getLocalPresence():
    config = getConfigFile()
    # load the custom games, all lower case
    localGames = list(map(str.lower, config["LOCAL_GAMES"]["GAMES"]))

    
    gameFound = False
    # process = None
    
    try:
        # get a list of all open applications, make a list of their creation times, and their names
        processCreationTimes = [i.create_time() for i in psutil.process_iter()]
        processNames = [i.name().lower() for i in psutil.process_iter()]
    except:
        return

    # loop thru all games we're supposed to look for
    for game in localGames:
        # check if that game is running locally
        if game in processNames:
            # write down the process name and it's creation time
            processCreationTime = processCreationTimes[processNames.index(game)]
            processName = game
        
            if not isPlaying:
                log(f"found {processName} running locally")

            gameFound = True
            break
    
    # don't continue if it didn't find a game
    if not gameFound:
        return
    
    global gameName
    global startTime
    global isPlayingLocalGame
    global isPlayingSteamGame
    
    
    if exists(f"{dirname(abspath(__file__))}/data/games.txt"):
        with open(f'{dirname(abspath(__file__))}/data/games.txt', 'r+') as gamesFile:
            for i in gamesFile:
                # remove the new line
                game = i.split("\n")
                # split first and second part of the string
                game = game[0].split("=")
                
                # if there's a match
                if game[0].lower() == processName.lower():
                    gameName = game[1]
                    startTime = processCreationTime
                    isPlayingLocalGame = True
                    isPlayingSteamGame = False
                    
                    if not isPlaying:
                        log(f"found name for {gameName} on disk")
                        
                    gamesFile.close()
                    return
            
            # if there wasn't a local entry for the game
            log(f"could not find a name for {processName}, adding an entry to games.txt")
            gamesFile.write(f"{processName}={processName.title()}\n")
            gamesFile.close()
            
    # if games.txt doesn't exist at all           
    else:
        log("games.txt does not exist, creating one")
        with open(f'{dirname(abspath(__file__))}/data/games.txt', 'a') as gamesFile:
            gamesFile.write(f"{processName}={processName.title()}\n")
            gamesFile.close()
    
    
    isPlayingLocalGame = True
    isPlayingSteamGame = False
    gameName = processName.title()
    startTime = processCreationTime

    

def setPresenceDetails():
    global activeRichPresence
    global startTime
    global currentGameBlacklisted
    
    details = None
    state = None
    buttons = None
    
    # ignore game if it is in blacklist, case insensitive check
    if gameName.casefold() in map(str.casefold, blacklist):
        if not currentGameBlacklisted:
            log(f"{gameName} is in blacklist, not creating RPC object.")
            currentGameBlacklisted = True
        return
    
    currentGameBlacklisted = False
    
    # if the game ID is corresponding to "a game on steam" - set the details field to be the real game name
    if appID == defaultAppID or appID == defaultLocalAppID:
        details = gameName
    
    if activeRichPresence != gameRichPresence:
        if gameRichPresence != "":
            if details == None:
                log(f"setting the details for {gameName} to `{gameRichPresence}`")
                details = gameRichPresence
            elif state == None:
                log(f"setting the state for {gameName} to `{gameRichPresence}`")
                state = gameRichPresence
        
            
        activeRichPresence = gameRichPresence
    
    if state == None and gameReviewScore != 0:
        state = f"{gameReviewString} - {gameReviewScore}%"
    
    
    if addSteamStoreButton and gameSteamID != 0:
        price = getGamePrice()
        if price == None:
            price = "Free"
        else:
            price += " USD"
        label = f"{gameName} on steam - {price}"
        if len(label) > 32:
            label = f"{gameName} - {price}"
        if len(label) > 32:
            label = f"get it on steam! - {price}"
        if len(label) > 32:
            label = f"on steam! - {price}"
            
        buttons = [{"label": label, "url": f"https://store.steampowered.com/app/{gameSteamID}"}]
    
    
    log("pushing presence to Discord")
    
    # sometimes startTime is 0 when it reaches this point, which results in a crash
    # i do *NOT* know how or why it does this, adding these 2 lines of code seems to fix it
    if startTime == 0:
        startTime = round((time()))
    
    try:
        RPC.update(
            details = details, state = state,
            start = startTime,
            large_image = coverImage, large_text = coverImageText,
            small_image = customIconURL, small_text = customIconText,
            buttons=buttons
        )
        
    except Exception as e:
        error(f"pushing presence failed...\nError encountered: {e}")

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
        except Exception as e:
            error(f"error encountered whilst trying to update the config-version to version 1, exiting\nError encountered: {e}")
            exit()
        print("----------------------------------------------------------")
    elif metaFile["structure-version"] == "1":
        print("----------------------------------------------------------")
        log("progam's current folder structure version is up to date...")
        print("----------------------------------------------------------")
    else:
        error("invalid structure-version found in meta.json, exiting")
        exit()

# checks if the program has any updates
def checkForUpdate():
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

def main():
    global currentVersion
    # this always has to match the newest release tag
    currentVersion = "v1.12.1"
    
    # check if there's any updates for the program
    checkForUpdate()
    # does various things, such as verifying that certain files are in certain locations
    # well it does 1 thing at the time of writing, but i'll probably forget to update this comment when i add more lol 
    verifyProjectVersion()
    
    global userID
    global steamAPIKey
    global localGames
    global defaultAppID
    global defaultLocalAppID
    global blacklist
    global currentGameBlacklisted
    currentGameBlacklisted = False
    
    global appID
    global startTime
    global gameName
    global gameRichPresence
    global activeRichPresence
    global gameSteamID
    global gameReviewScore
    global gameReviewString
    global isPlaying
    global isPlayingLocalGame
    global isPlayingSteamGame
    
    global coverImage
    global coverImageText
    
    global RPC
    global sgdb
    
    global gridEnabled
    global steamStoreCoverartBackup
    global customIconURL
    global customIconText
    
    global addSteamStoreButton
    
    
    log("loading config file")
    config = getConfigFile()
    
    steamAPIKey = config["STEAM_API_KEY"]
    defaultAppID = config["DISCORD_APPLICATION_ID"]
    defaultLocalAppID = config["LOCAL_GAMES"]["LOCAL_DISCORD_APPLICATION_ID"]
    doLocalGames = config["LOCAL_GAMES"]["ENABLED"]
    localGames = config["LOCAL_GAMES"]["GAMES"]
    blacklist = config["BLACKLIST"]
    
    steamStoreCoverartBackup = config["COVER_ART"]["USE_STEAM_STORE_FALLBACK"]
    gridEnabled = config["COVER_ART"]["STEAM_GRID_DB"]["ENABLED"]
    gridKey = config["COVER_ART"]["STEAM_GRID_DB"]["STEAM_GRID_API_KEY"]
    
    doCustomIcon = config["CUSTOM_ICON"]["ENABLED"]
    
    doWebScraping = config["WEB_SCRAPE"]
    
    doCustomGame = config["GAME_OVERWRITE"]["ENABLED"]
    customGameName = config["GAME_OVERWRITE"]["NAME"]
    customGameStartOffset = config["GAME_OVERWRITE"]["SECONDS_SINCE_START"]
    
    doSteamRichPresence = config["FETCH_STEAM_RICH_PRESENCE"]
    fetchSteamReviews = config["FETCH_STEAM_REVIEWS"]
    addSteamStoreButton = config["ADD_STEAM_STORE_BUTTON"]
    
    # load these later on
    customIconURL = None
    customIconText = None
    
    
    # loads the steam user id
    userID = ""
    if type(config["USER_IDS"]) == str:
        userID = config["USER_IDS"]
    elif type(config["USER_IDS"]) == list:
        for i in config["USER_IDS"]:
            userID += f"{i},"
        # remove the last comma
        userID = userID[:-1]
    else:
        error(
            "type error whilst reading the USER_IDS field, please make sure the formating is correct\n",
            "it should be something like `\"USER_IDS\": \"76561198845672697\",`",
        )
    
    # declare variables
    isPlaying = False
    isPlayingLocalGame = False
    isPlayingSteamGame = False
    startTime = 0
    coverImage = None
    coverImageText = None
    gameSteamID = 0
    gameReviewScore = 0
    gameReviewString = ""
    gameName = ""
    previousGameName = ""
    gameRichPresence = ""
    # the rich presence text that's actually in the current discord presence, set to beaver cause it can't start empty
    activeRichPresence = "beaver"


    if doCustomIcon:
        log("loading custom icon")
        customIconURL = config["CUSTOM_ICON"]["URL"]
        customIconText = config["CUSTOM_ICON"]["TEXT"]

    # initialize the steam grid database object
    if gridEnabled:
        log("intializing the SteamGrid database...")
        sgdb = SteamGridDB(gridKey)

    # everything ready! 
    log("everything is ready!")
    print("----------------------------------------------------------")
    
    while True:
        # these values are taken from the config file every cycle, so the user can change these whilst the script is running
        config = getConfigFile()
        
        steamAPIKey = config["STEAM_API_KEY"]
        defaultAppID = config["DISCORD_APPLICATION_ID"]
        defaultLocalAppID = config["LOCAL_GAMES"]["LOCAL_DISCORD_APPLICATION_ID"]
        doLocalGames = config["LOCAL_GAMES"]["ENABLED"]
        localGames = config["LOCAL_GAMES"]["GAMES"]
        blacklist = config["BLACKLIST"]
        
        steamStoreCoverartBackup = config["COVER_ART"]["USE_STEAM_STORE_FALLBACK"]
        gridEnabled = config["COVER_ART"]["STEAM_GRID_DB"]["ENABLED"]
        gridKey = config["COVER_ART"]["STEAM_GRID_DB"]["STEAM_GRID_API_KEY"]
        
        doCustomIcon = config["CUSTOM_ICON"]["ENABLED"]
        
        doWebScraping = config["WEB_SCRAPE"]
        
        doCustomGame = config["GAME_OVERWRITE"]["ENABLED"]
        customGameName = config["GAME_OVERWRITE"]["NAME"]
        customGameStartOffset = config["GAME_OVERWRITE"]["SECONDS_SINCE_START"]


        # set the custom game
        if doCustomGame:
            gameName = customGameName
        
        else:
            gameName = getSteamPresence()
            
            if gameName == "" and doLocalGames:
                getLocalPresence()
            
            if gameName == "" and doWebScraping:
                getWebScrapePresence()
        
            if doSteamRichPresence and isPlayingSteamGame:
                getSteamRichPresence()        
            
            
        # if the game has changed
        if previousGameName != gameName:
            # try finding the game on steam, and saving it's ID to `gameSteamID` 
            getGameSteamID()
            
            # fetch the steam reviews if enabled
            if fetchSteamReviews:
                if gameName != "" and gameSteamID != 0:
                    getGameReviews()
                else:
                    gameReviewScore = 0
                
            # if the game has been closed
            if gameName == "":
                # only close once
                if isPlaying:
                    log(f"closing previous rich presence object, no longer playing {previousGameName}")
                    print("----------------------------------------------------------")
                    RPC.close()
                    
                    # set previous game name to "", this is used to check if the game has changed
                    # if we don't use this and the user opens a game, closes it, and then relaunches it - the script won't detect that
                    previousGameName = ""
                    startTime = 0
                    isPlaying = False
            
            # if the game has changed or a new game has been opened
            else:
                # save the time as the time we started playing
                # if we're playing a localgame the time has already been set
                if not isPlayingLocalGame:
                    startTime = round(time())
                
                if doCustomGame:
                    log(f"using custom game '{customGameName}'")
                    # set the start time to the custom game start time
                    if customGameStartOffset != 0:
                        startTime = round(time() - customGameStartOffset)
    
                log(f"game changed, updating to '{gameName}'")

                # fetch the new app ID
                getGameDiscordID()
                
                # get cover image
                getGameImage()
                
                # checks to make sure the old RPC has been closed
                if isPlaying:
                    log(f"RPC for {previousGameName} still open, closing it")
                    RPC.close()
                    
                # redefine and reconnect to the RPC object
                log(f"creating new rich presence object for {gameName}")
                RPC = Presence(client_id=appID)
                RPC.connect()

                # push info to RPC
                setPresenceDetails()
                
                isPlaying = True
                previousGameName = gameName
                
                print("----------------------------------------------------------")
        
        if activeRichPresence != gameRichPresence and isPlaying and not currentGameBlacklisted:
            setPresenceDetails()
            print("----------------------------------------------------------")

        # sleep for a 20 seconds for every user we query, to avoid getting banned from the steam API
        sleep(20 * (userID.count(",") + 1))


if __name__ == "__main__":
    main()
#    try:
#        pass
#    except Exception as e:
#        error(f"{e}\nautomatically restarting script in 60 seconds\n")
#        sleep(60)
#        python = sys.executable
#        log("restarting...")
#        os.execl(python, python, *sys.argv)
