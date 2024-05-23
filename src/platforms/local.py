import os
import sys
import json
import time

import psutil

from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))


# checks if any local games are running
def getLocalPresence():
    config = getConfigFile()
    # load the custom games, all lower case
    config["LOCAL_GAMES"]["GAMES"] = list(map(str.lower, config["LOCAL_GAMES"]["GAMES"]))

    
    gameFound = False
    # process = None
    
    try:
        # get a list of all open applications, make a list of their creation times, and their names
        processCreationTimes = [i.create_time() for i in psutil.process_iter()]
        processNames = [i.name().lower() for i in psutil.process_iter()]
    except:
        return

    # loop thru all games we're supposed to look for
    for game in config["LOCAL_GAMES"]["GAMES"]:
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