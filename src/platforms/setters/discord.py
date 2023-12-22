from src.helperFunctions import *

class Discord():
    def __init__(self, main):
        self.RPC = None
        self.main = main
    
    def test(self):
        print(self)
        log("hi")
        if self.main.debugMode:
            logDebug('hi')
    
    # requests a list of all games recognized internally by discord, if any of the names matches
    # the detected game, save the discord game ID associated with said title to RAM, this is used to report to discord as that game 
    def getGameDiscordID(loops=0):
        if loops == 0:
            logDebug(f"fetching the Discord game ID for {gameName}")
            
        discordIDs = []
        ignoredChars = "®©™℠"
        
        with open(f"{dirname(abspath(__file__))}/data/cache/discordIDs.json", "r") as f:
            gameIDsFile = json.load(f)
            
            if len(gameIDsFile) == 0:
                if loops == 0:
                    log("no cache found, updating it")
                    return getGameDiscordID(loops + 1)
            
            else:
                for i in gameIDsFile:
                    discordIDs.append({
                        "name": i,
                        "id": gameIDsFile[i],
                        "property": "is-cached-game-ID"
                    })
        
        # check if the "customGameIDs.json" file exists, if so, open it
        if exists(f"{dirname(abspath(__file__))}/data/customGameIDs.json"):
            with open(f"{dirname(abspath(__file__))}/data/customGameIDs.json", "r") as f:
                # load the values of the file
                gameIDsFile = json.load(f)
                
                # add the values from the file directly to the list returned by discord
                for i in gameIDsFile:
                    discordIDs.append({
                        "name": i,
                        "id": gameIDsFile[i],
                        "property": "is-custom-game-ID"
                    })
        
        if loops >= 1:
            logDebug("fetching discord game IDs from Discord's servers")
            r = makeWebRequest("https://discordapp.com/api/v8/applications/detectable")
            if r == "error":
                return

            
            if r.status_code != 200:
                error(f"status code {r.status_code} returned whilst trying to find the game's ID from discord")
                return
        
            for i in r.json():
                discordIDs.append({
                    "name": i["name"],
                    "id": i["id"],
                    "property": "is-server-fetched-game-ID"
                })
            
        
                
        global appID
        
        # loop thru all games
        for i in discordIDs:
            lowercaseGameName = gameName.lower()
            
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
            if removeChars(lowercaseGameName, ignoredChars) in gameNames:
                appID = i["id"]
                
                logDebug(f"discord ID {i['id']} found for {gameName}, property-data: {i['property']}, loop count={loops}")
                
                if i["property"] == "is-custom-game-ID":
                    log(f"using a custom game ID for {gameName}")
                elif i["property"] == "is-cached-game-ID":
                    log(f"found the Discord game ID for {removeChars(lowercaseGameName, ignoredChars)} stored in cache")
                elif i["property"] == "is-server-fetched-game-ID":
                    log(f"found the Discord game ID for {removeChars(lowercaseGameName, ignoredChars)}")
                    with open(f"{dirname(abspath(__file__))}/data/cache/discordIDs.json", "r") as f:
                        cachedGameIDs = json.load(f)
                        
                    log(f"Discord game ID {i['id']} was added to cache for {gameName}")
                    cachedGameIDs[lowercaseGameName] = i["id"]
                    
                    with open(f"{dirname(abspath(__file__))}/data/cache/discordIDs.json", "w") as f:
                        json.dump(cachedGameIDs, f)
                
                    
                return

        if loops >= 1:
            # if the game was fetched using the local checker, instead of thru steam
            if isPlayingLocalGame:
                log(f"could not find the discord game ID for {gameName}, defaulting to the secondary, local game ID")
                appID = enabledPlatforms["localGames"]["appID"]
                return

            log(f"could not find the discord game ID for {gameName}, defaulting to well, the default game ID")
            appID = enabledPlatforms["steam"]["appID"]
            return
        else:
            getGameDiscordID(loops + 1)

    def setPresenceDetails():
        global activeRichPresence
        global startTime
        
        details = None
        state = None
        buttons = None
        
        # if the game ID is corresponding to "a game on steam" - set the details field to be the real game name
        if appID == enabledPlatforms["steam"]["appID"] or appID == enabledPlatforms["localGames"]["appID"]:
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
        
        if state == None and gameReviewScore != 0 and enabledPlatforms["steam"]["gameReviews"]:
            state = f"{gameReviewString} - {gameReviewScore}%"
        
        
        if enabledPlatforms["steam"]["storeButton"] and gameSteamID != 0:
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
                # state field currently unused
                details = details, state = state,
                start = startTime,
                large_image = coverImage, large_text = coverImageText,
                small_image = customIconURL, small_text = customIconText,
                buttons=buttons
            )
            
        except Exception as e:
            error(f"pushing presence failed...\nError encountered: {e}")