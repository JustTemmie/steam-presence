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

# from src.platforms.steam import *
# from platforms.local import *

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
        

from src.platforms.setters.discord import Discord
from src.helperFunctions import *

class SteamPresence():
    def __init__(self):
        self.files = {}
        self.platforms = {
            "discord": Discord(self)
        }
        self.debugMode = True
        print("hi")
            
    def startLoop(self):
        self.platforms["discord"].test()


if __name__ == "__main__":
    steamPresence = SteamPresence()
    steamPresence.startLoop()
    
    pass
    # print("----------------------------------------------------------")
    # global debugMode
    # debugMode = False

    # log("loading config file")
    # config = getConfigFile()
    # loadConfigFile()
    
    # # this always has to match the newest release tag
    # global currentVersion
    # currentVersion = "v1.13"
    
    # # check if there's any updates for the program
    # checkForUpdate()
    # # does various things, such as verifying that certain files are in certain locations
    # # well it does 1 thing at the time of writing, but i'll probably forget to update this comment when i add more lol 
    # verifyProjectVersion()
    

    # global startTime
    # global gameName
    # global gameRichPresence
    # global activeRichPresence
    # global userID
    # global gameSteamID
    # global isPlaying
    # global isPlayingLocalGame
    # global isPlayingSteamGame
    
    # global coverImage
    # global coverImageText
    
    # global RPC
    # global sgdb
    
    # global gridEnabled
    # global steamStoreCoverartBackup
    # global customIconURL
    # global customIconText
    
        
    # # load these later on
    # customIconURL = None
    # customIconText = None
    
    
    # # loads the steam user id
    # userID = ""
    # if type(config["USER_IDS"]) == str:
    #     userID = config["USER_IDS"]
    # elif type(config["USER_IDS"]) == list:
    #     for i in config["USER_IDS"]:
    #         userID += f"{i},"
    #     # remove the last comma
    #     userID = userID[:-1]
    # else:
    #     error(
    #         "type error whilst reading the USER_IDS field, please make sure the formating is correct\n",
    #         "it should be something like `\"USER_IDS\": \"76561198845672697\",`",
    #     )
    
    # # declare variables
    # isPlaying = False
    # isPlayingLocalGame = False
    # isPlayingSteamGame = False
    # startTime = 0
    # coverImage = None
    # coverImageText = None
    # gameSteamID = 0
    # global gameReviewScore
    # gameReviewScore = 0
    # global gameReviewString
    # gameReviewString = ""
    # gameName = ""
    # previousGameName = ""
    # gameRichPresence = ""
    # # the rich presence text that's actually in the current discord presence, set to beaver cause it can't start empty
    # activeRichPresence = "beaver"


    # if doCustomIcon:
    #     log("loading custom icon")
    #     customIconURL = config["CUSTOM_ICON"]["URL"]
    #     customIconText = config["CUSTOM_ICON"]["TEXT"]

    # # initialize the steam grid database object
    # if gridEnabled:
    #     log("intializing the SteamGrid database...")
    #     sgdb = SteamGridDB(gridKey)

    # # everything ready! 
    # log("everything is ready!")
    # print("----------------------------------------------------------")
    
    # while True:
    #     # these values are taken from the config file every cycle, so the user can change these whilst the script is running
    #     loadConfigFile()


    #     # set the custom game
    #     if doCustomGame:
    #         gameName = customGameName
        
    #     else:
    #         if enabledPlatforms["steam"]["enabled"]:
    #             gameName = getSteamPresence()
            
    #         if gameName == "" and enabledPlatforms["localGames"]["enabled"]:
    #             getLocalPresence()
            
    #         if gameName == "" and enabledPlatforms["steam"]["webscraping"]["enabled"]:
    #             getWebScrapePresence()
        
    #         if isPlayingSteamGame and enabledPlatforms["steam"]["enchanedPresence"]["enabled"]:
    #             getSteamRichPresence()        
            
            
    #     # if the game has changed
    #     if previousGameName != gameName:
    #         # try finding the game on steam, and saving it's ID to `gameSteamID` 
    #         getGameSteamID()
            
    #         # fetch the steam reviews if enabled
    #         if enabledPlatforms["steam"]["gameReviews"]:
    #             if gameName != "" and gameSteamID != 0:
    #                 getGameReviews()
    #             else:
    #                 gameReviewScore = 0
                
    #         # if the game has been closed
    #         if gameName == "":
    #             # only close once
    #             if isPlaying:
    #                 log(f"closing previous rich presence object, no longer playing {previousGameName}")
    #                 print("----------------------------------------------------------")
    #                 RPC.close()
                    
    #                 # set previous game name to "", this is used to check if the game has changed
    #                 # if we don't use this and the user opens a game, closes it, and then relaunches it - the script won't detect that
    #                 previousGameName = ""
    #                 startTime = 0
    #                 isPlaying = False
            
    #         # if the game has changed or a new game has been opened
    #         else:
    #             # save the time as the time we started playing
    #             # if we're playing a localgame the time has already been set
    #             if not isPlayingLocalGame:
    #                 startTime = round(time())
                
    #             if doCustomGame:
    #                 log(f"using custom game '{customGameName}'")
    #                 # set the start time to the custom game start time
    #                 if customGameStartOffset != 0:
    #                     startTime = round(time() - customGameStartOffset)
    
    #             log(f"game changed, updating to '{gameName}'")

    #             # fetch the new app ID
    #             getGameDiscordID()
                
    #             # get cover image
    #             getGameImage()
                
    #             # checks to make sure the old RPC has been closed
    #             if isPlaying:
    #                 log(f"RPC for {previousGameName} still open, closing it")
    #                 RPC.close()
                    
    #             # redefine and reconnect to the RPC object
    #             log(f"creating new rich presence object for {gameName}")
    #             RPC = Presence(client_id=appID)
    #             RPC.connect()

    #             # push info to RPC
    #             setPresenceDetails()
                
    #             isPlaying = True
    #             previousGameName = gameName
                
    #             print("----------------------------------------------------------")
        
    #     if activeRichPresence != gameRichPresence and isPlaying:
    #         setPresenceDetails()
    #         print("----------------------------------------------------------")
        
    #     if debugMode:
    #         print("----------------------------------------------------------")
            

    #     # sleep for a 20 seconds for every user we query, to avoid getting banned from the steam API
    #     sleep(20 * (userID.count(",") + 1))