# creating rich presences for discord
from time import sleep, time

# for errors
from datetime import datetime

# for loading the config file
import json
from os.path import exists, dirname

# for restarting the script on a failed run
import sys 
import os

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

except:
    answer = input("looks like either requests, pypresence, steamgrid, psutil, or beautifulSoup is not installed, do you want to install them? (y/n) ")
    if answer.lower() == "y":
        from os import system
        print("installing req packages...")
        system(f"python3 -m pip install -r {dirname(__file__)}/requirements.txt")
        
        from pypresence import Presence
        from steamgrid import SteamGridDB
        from bs4 import BeautifulSoup
        import psutil
        import requests
        
        print("\npackages installed and imported successfully!")

# just shorthand for logs and errors - easier to write in script
def log(log):
    print(f"[{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {log}")

def error(error):
    print(f"    ERROR: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {error}")


# opens the config file and loads the data
def getConfigFile():
    if exists(f"{dirname(__file__)}/config.json"):
        with open(f"{dirname(__file__)}/config.json", "r") as f:
            return json.load(f)
    
    if exists(f"{dirname(__file__)}/exampleconfig.json"):
        with open(f"{dirname(__file__)}/exampleconfig.json", "r") as f:
            return json.load(f)
    
    else:
        error("Config file not found. Please read the readme and create a config file.")
        exit()

def getImageFromSGDB():
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
                    with open(f'{dirname(__file__)}/icons.txt', 'a') as icons:
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
                page = requests.get(URL)
                
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
                with open(f'{dirname(__file__)}/icons.txt', 'a') as icons:
                    icons.write(f"{gameName.lower()}={coverImage}||{coverImageText}\n")
                    icons.close()
                return
        
        log("failed to fetch icon from SGDB")
    
    else:
        log(f"SGDB doesn't seem to have any entries for {gameName}")


def getImageFromStorepage():
    global coverImage
    global coverImageText
    
    log("getting icon from the steam store")
    try:
        # fetches a list of ALL games on steam
        r = requests.get(f"https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={steamAPIKey}&format=json")
        
        if r.status_code == 403:
            error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
            exit()
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
            return

        respone = r.json()
        
        steamAppID = 0
        # loops thru every game until it finds one matching your game's name
        for i in respone["applist"]["apps"]:
            if gameName.lower() == i["name"].lower():
                steamAppID = i["appid"]
                
                log(f"steam app ID {steamAppID} found for {gameName}")
                break
        
        # if we didn't find the game at all on steam, 
        if steamAppID == 0:
            log(f"could not find the steam app ID for {gameName}")
            coverImage = None
            coverImageText = None
            return

        # then load the store page, and find the icon thru it
        URL = f"https://store.steampowered.com/app/{steamAppID}/"
        page = requests.get(URL, allow_redirects=True)
        
        # if it was redirected to the main page (steam does this whenever it recieves an invalid URL), exit
        if page.url == "https://store.steampowered.com/":
            log(f"the app ID found for {gameName} ({steamAppID}) does not seem to be valid, ignoring")
            return
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when trying to load store page for {gameName}, ignoring")
            return
        
        soup = BeautifulSoup(page.content, "html.parser")
        img = soup.find("div", {"class": "game_header_image_ctn"}).find("img")
        # save it to variable
        coverImage = img["src"]
        coverImageText = f"{gameName} on steam"
        # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
        
        log(f"successfully found steam's icon for {gameName}")

    except Exception as e:
        error(f"Exception {e} raised when trying to fetch {gameName}'s icon thru steam, ignoring")
        coverImage = None
        coverImageText = None


# searches the steam grid DB or the official steam store to get cover images for games
def getGameImage():
    global coverImage
    global coverImageText
    
    log(f"fetching icon for {gameName}")
    
    # checks if there's already an existing icon saved to disk for the game 
    with open(f'{dirname(__file__)}/icons.txt', 'r') as icons:
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
    
    
    if gridEnabled:
        getImageFromSGDB()
        
    if steamStoreCoverartBackup:
        getImageFromStorepage()

# checks what game the user is currently playing
def getSteamPresence(userIDs):
    r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steamAPIKey}&format=json&steamids={userIDs}")
    if r.status_code == 403:
        error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
        exit()

    if r.status_code != 200:
        error(f"error code {r.status_code} met when trying to fetch game, ignoring")
        return ""
    
    global isPlayingLocalGame
    
    response = r.json()
    
    if len(response["response"]["players"]) == 0:
        error("No account found, please verify that all your user IDs are correct")
        exit()

    for i in range(0, len(response["response"]["players"])):
        if "gameextrainfo" in response["response"]["players"][0]:
            game_title = response["response"]["players"][0]["gameextrainfo"]
            isPlayingLocalGame = False
            return game_title

    return ""

# requests a list of all games recognized internally by discord, if any of the names matches
# the detected game, save the discord game ID associated with said title to RAM, this is used to report to discord as that game 
def getGameDiscordID():
    log(f"fetching the Discord game ID for {gameName}")
    r = requests.get("https://discordapp.com/api/v8/applications/detectable")
    
    if r.status_code != 200:
        error(f"status code {r.status_code} returned whilst trying to find the game's ID from discord")
    
    
    response = r.json()
    
    # check if the "customGameIDs.json" file exists, if so, open it
    if exists(f"{dirname(__file__)}/customGameIDs.json"):
        with open(f"{dirname(__file__)}/customGameIDs.json", "r") as f:
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
        gameNames.append(i["name"].lower())
        
        # make a list containing all the names of said game
        if "aliases" in i:
            aliases = i["aliases"]
            for alias in aliases:
                gameNames.append(alias.lower())

        # if it's the same, we successfully found the discord game ID
        if gameName.lower() in gameNames:
            log(f"found the discord game ID for {gameName}")
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

# checks if any local games are running
def getLocalPresence():
    config = getConfigFile()
    # load the custom games, all lower case
    localGames = list(map(str.lower, config["LOCAL_GAMES"]["GAMES"]))

    
    gameFound = False
    # process = None
    
    # get a list of all open applications, make a list of their creation times, and their names
    processCreationTimes = [i.create_time() for i in psutil.process_iter()]
    processNames = [i.name().lower() for i in psutil.process_iter()]
    
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
    
    
    if exists(f"{dirname(__file__)}/games.txt"):
        with open(f'{dirname(__file__)}/games.txt', 'r+') as gamesFile:
            for i in gamesFile:
                # remove the new line
                game = i.split("\n")
                # split first and second part of the string
                game = game[0].split("=")
                
                # if there's a match
                if game[0].lower() == processName:
                    gameName = game[1]
                    startTime = processCreationTime
                    isPlayingLocalGame = True
                    
                    if not isPlaying:
                        log(f"found name for {gameName} on disk")
                        
                    gamesFile.close()
                    return
            
            # if there wasn't a local entry for the game
            log(f"could not find a name for {processName}, adding an entry to games.txt")
            
            gamesFile.write(f"{processName.lower()}={processName.title()}\n")
            gamesFile.close()
            
            isPlayingLocalGame = True
            gameName = processName.title()
            startTime = processCreationTime


    # if games.txt doesn't exist at all           
    else:
        log("games.txt does not exist, creating one")
        with open(f'{dirname(__file__)}/games.txt', 'a') as gamesFile:
            gamesFile.write(f"{processName}={processName.title()}\n")
            gamesFile.close()
            
            isPlayingLocalGame = True
            gameName = processName.title()
            startTime = processCreationTime

    

def setPresenceDetails():
    log("pushing presence to Discord")
    
    # if the game ID is corresponding to "a game on steam" - set the details field to be the real game name
    if appID == defaultAppID or appID == defaultLocalAppID:
        details = gameName
    else:
        details = None

    RPC.update(
        # state field currently unused
        details = details, state = None,
        start = startTime,
        large_image = coverImage, large_text = coverImageText,
        small_image = customIconURL, small_text = customIconText
    )

def main():
    global steamAPIKey
    global localGames
    global defaultAppID
    global defaultLocalAppID
    
    global appID
    global startTime
    global gameName
    global isPlaying
    global isPlayingLocalGame
    
    global coverImage
    global coverImageText
    
    global RPC
    global sgdb
    
    global gridEnabled
    global steamStoreCoverartBackup
    global customIconURL
    global customIconText
    
    log("loading config file")
    config = getConfigFile()
    
    steamAPIKey = config["STEAM_API_KEY"]
    defaultAppID = config["DISCORD_APPLICATION_ID"]
    defaultLocalAppID = config["LOCAL_GAMES"]["LOCAL_DISCORD_APPLICATION_ID"]
    doLocalGames = config["LOCAL_GAMES"]["ENABLED"]
    localGames = config["LOCAL_GAMES"]["GAMES"]
    
    steamStoreCoverartBackup = config["COVER_ART"]["USE_STEAM_STORE_FALLBACK"]
    gridEnabled = config["COVER_ART"]["STEAM_GRID_DB"]["ENABLED"]
    gridKey = config["COVER_ART"]["STEAM_GRID_DB"]["STEAM_GRID_API_KEY"]
    
    doCustomIcon = config["CUSTOM_ICON"]["ENABLED"]
    # load these later on
    customIconURL = None
    customIconText = None
    
    # loads the user ids and turns them into a string of (for example) user1,user2,user3
    userIDs = ""
    if type(config["USER_IDS"]) == str:
        userIDs = config["USER_IDS"]
    elif type(config["USER_IDS"]) == list:
        for i in config["USER_IDS"]:
            userIDs += f"{i},"
        userIDs = userIDs[:-1]
    else:
        error("type error whilst reading the USER_IDS field, please make sure the formating is correct")
        
    # declare variables
    isPlaying = False
    isPlayingLocalGame = False
    startTime = 0
    coverImage = None
    coverImageText = None
    gameName = ""
    previousGameName = ""

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
        
        doCustomGame = config["GAME_OVERWRITE"]["ENABLED"]
        customGameName = config["GAME_OVERWRITE"]["NAME"]


        # set the custom game
        if doCustomGame:
            gameName = customGameName
        
        else:
            gameName = getSteamPresence(userIDs)
            
            if gameName == "" and doLocalGames:
                getLocalPresence()
            
            
        # if the game has changed
        if previousGameName != gameName:
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
                if doCustomGame:
                    log(f"using custom game '{customGameName}'")
    
                log(f"game changed, updating to '{gameName}'")
                
                if startTime == 0:
                    startTime = round(time())


                # fetch the new app ID
                getGameDiscordID()
                
                # get cover image
                getGameImage()
                
                # checks to make sure the old RPC has been closed
                if isPlaying:
                    log(f"RPC for {previousGameName} still open, closing it")
                    RPC.close()
                    
                    # if the game is fetched thru local tasks, the startTime has already been set
                    if not isPlayingLocalGame:
                        startTime = round(time())
                # redefine and reconnect to the RPC object
                log(f"creating new rich presence object for {gameName}")
                RPC = Presence(client_id=appID)
                RPC.connect()

                # push info to RPC
                setPresenceDetails()
                
                isPlaying = True
                previousGameName = gameName
                
                print("----------------------------------------------------------")

        # wait for a bit in order to not get limited by the steam API
        sleep(20)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error(f"{e}\nautomatically restarting script in 60 seconds\n")
        sleep(60)
        python = sys.executable
        log("restarting...")
        os.execl(python, python, *sys.argv)
