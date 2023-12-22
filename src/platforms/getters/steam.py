import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import log, logDebug, error, makeWebRequest, gameName


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

from platforms.steam import *
from platforms.local import *

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
    pass


def getGameSteamID():
    global gameSteamID
    
    with open(f"{dirname(abspath(__name__))}/data/cache/steamIDs.json", "r") as f:
        cachedGameIDs = json.load(f)
    
    if gameName in cachedGameIDs:
        # if the ID was cached more than 48 hours ago, ignore it at overwrite it later in the code
        if cachedGameIDs[gameName]["cacheTime"] + 172800 < time():
            log(f"steam expired game ID for {gameName} found cached, discarding it")
        else:
            if gameSteamID != cachedGameIDs[gameName]["steamID"]:
                log(f"steam app ID {cachedGameIDs[gameName]['steamID']} found for {gameName} in cache")
                        
            gameSteamID = cachedGameIDs[gameName]["steamID"]
            return
                    
    # fetches a list of ALL games on steam
    logDebug("getting a list of all games on steam, in order to find our current game's steam ID")
    r = makeWebRequest(f"https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={steamAPIKey}&format=json")
    if r == "error":
        return
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    if r.status_code == 403:
        error("Forbidden, Access to the steam API has been denied, please verify your steam API key\n    Steam's website for this stuff: https://steamcommunity.com/dev/apikey")
        exit()
    
    if r.status_code != 200:
        error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
        return

    respone = r.json()
    
    
    def handleSteamGame(name):
        global gameSteamID
        for i in respone["applist"]["apps"]:
            if name.lower() == i["name"].lower():

                if gameSteamID != i["appid"]:
                    log(f"steam app ID {i['appid']} found for {gameName}")
                
                gameSteamID = i["appid"]
                
                with open(f"{dirname(abspath(__file__))}/data/cache/steamIDs.json", "r") as f:
                    cachedGameIDs = json.load(f)
                
                cachedGameIDs[gameName] = {
                    "steamID":gameSteamID,
                    "cacheTime": time()
                }  
                
                with open(f"{dirname(abspath(__file__))}/data/cache/steamIDs.json", "w") as f:
                    json.dump(cachedGameIDs, f)
                
                return True
        
    # loops thru every game until it finds one matching your game's name
    if handleSteamGame(gameName):
        return
    
    # for handling game demos
    if " demo" in gameName.lower():
        tempGameName = copy(gameName.lower())
        tempGameName.replace(" demo", "")
        if handleSteamGame(tempGameName):
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
    
    try: 
        logDebug("getting an icon from the steam store")
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
        coverImageText = f"{gameName} on steam"
        # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
        
        log(f"successfully found Steam's icon for {gameName}")

    except Exception as e:
        error(f"Exception {e} raised when trying to fetch {gameName}'s icon thru steam, ignoring")
        coverImage = None
        coverImageText = None

def getGameReviews():    
    # get the review data for the steam game
    logDebug("checking the reviews for the current game")
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
    
    # sometimes instead of returning the desired dicationary steam just decides to be quirky
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
    
    log(f"found a review score of {gameReviewScore}% for {gameName}")

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
        
    if steamStoreCoverartBackup and coverImage == "":
        getImageFromStorepage()


def getGamePrice():
    logDebug("checking the price of the current game")
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
        print("cookie.txt not found")
        return
    
    cj = cookielib.MozillaCookieJar(f"{dirname(abspath(__file__))}/cookies.txt")
    cj.load()
    
    # split on ',' in case of multiple userIDs
    for i in userID.split(","):
        URL = f"https://steamcommunity.com/profiles/{i}/"
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        sleep(0.2)
        
        page = requests.post(URL, cookies=cj)
        
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
    logDebug("checking what game is being played by any of the added users")
    r = makeWebRequest(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steamAPIKey}&format=json&steamids={userID}")
    
    # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
    sleep(0.2)
    
    # if it errors out, just return the already asigned gamename
    if r == "error":
        return gameName
    
        
    if r.status_code == 403:
        error("Forbidden, Access to the steam API has been denied, please verify your steam API key\n    Steam's website for this stuff: https://steamcommunity.com/dev/apikey")
        exit()

    if r.status_code != 200:
        error(f"error code {r.status_code} met when trying to fetch game, ignoring")
        return ""
    
    
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
                log(f"found game {game_title} played by {sorted_response[i]['personaname']} on Steam")
            isPlayingSteamGame = True
            logDebug(f"steam user {sorted_response[i]['personaname']} is currently playing {game_title}")
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
        logDebug("checking for any potential enhanced rich presence data")
        pageRequest = makeWebRequest(f"https://steamcommunity.com/miniprofile/{int(i) - 76561197960265728}")
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