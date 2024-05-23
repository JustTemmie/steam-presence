import os
import sys
import json
import time

import copy
from bs4 import BeautifulSoup
import http.cookiejar as cookielib
import functools

from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))

class Steam():
    def __init__(self, APIKey):
        self.APIKey = APIKey
    
    # cache the data for an hour
    @time_cache(3600)
    def get_game_reviews(self, gameID):
        # get the review data for the steam game
        r = make_web_request(f"https://store.steampowered.com/appreviews/{gameID}?json=1")
        if r == "error":
            return
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when requesting the review score from steam, ignoring")
            return

        # convert it to a dictionary
        respone = r.json()
        
        # sometimes instead of returning the desired dicationary, steam just decides to be quirky
        # and it returns the dictionary `{'success': 2}` - something which isn't really useful. If this happens we try again :)
        if respone["success"] != 1:
            self.get_game_reviews(gameID)
            return
        
        response = respone["query_summary"]
        
        # if there aren't any reviews, just return early
        if 0 in [response["total_positive"], response["total_reviews"]]:
            return
        
        scorePercentage = (response["total_positive"] / response["total_reviews"]) * 100
        
        return {
            "score_percentage": f"{round(scorePercentage, 2)}%",
            "score_description": response["review_score_desc"]
        }


    @time_cache(3600)
    def get_game_price(self, gameID, countryCode = "us"):
        r = make_web_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}&cc={countryCode}")
        if r == "error":
            return
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when requesting price data from stam, ignoring")
            return
        
        respone = r.json()
        
        if "price_overview" not in respone[str(gameID)]["data"]:
            return "unknown price"
        
        return respone[str(gameID)]["data"]["price_overview"]["final_formatted"]
        
        
    # web scrapes the user's web page, sending the needed cookies along with the request
    def get_web_scrape_presence(self, userIDs):
        if not os.path.exists(f"{project_root}/cookies.txt"):
            error("cookie.txt not found, this is because `WEB_SCRAPE` is enabled in the config")
            return
        
        cj = cookielib.MozillaCookieJar(f"{project_root}/cookies.txt")
        cj.load()
        
        # split on ',' in case of multiple userIDs
        for userID in userIDs:
            URL = f"https://steamcommunity.com/profiles/{userID}/"
            
            # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
            time.sleep(0.2)
            
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
                        return result

    @time_cache(600)
    def get_playtime(self, userID, gameID):
        r = make_web_request(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={self.APIKey}&steamid={userID}")
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r == "error":
            return
        
        if r.status_code == 403:
            error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
            exit()

        if r.status_code != 200:
            error(f"error code {r.status_code} met when trying to fetch game stats for user: {userID}, ignoring")
            return
        
        response = r.json()
        
        playtime = None
        for i in response["response"]["games"]:
            if i["appid"] == gameID:
                playtime = i["playtime_forever"]
        
        # incase the user doesn't actually own the game, for example if they got it thru family sharing
        if playtime == None:
            recentGamesRequest = make_web_request(f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={self.APIKey}&steamid={userID}")
            if recentGamesRequest == "error":
                return
            
            if recentGamesRequest.status_code == 403:
                error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
                exit()

            if recentGamesRequest.status_code != 200:
                error(f"error code {recentGamesRequest.status_code} met when trying to fetch game stats for user: {userID}, ignoring")
                return
        
            recentGames = recentGamesRequest.json()

            if r == "error":
                return
            
            if r.status_code == 200:
                for i in recentGames["response"]["games"]:
                    if i["appid"] == gameID:
                        playtime = i["playtime_forever"]
        
        if playtime == None:
            return "0"

        if playtime > 0:
            return f"{round(playtime / 60, 1)}"

    @time_cache(180)
    def get_achievement_progress(self, userID, gameID):
        r = make_web_request(f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={gameID}&key={self.APIKey}&steamid={userID}")

        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r == "error":
            return
        
        if r.status_code == 403:
            error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
            exit()
        
        if r.status_code == 400:
            return "0/0"

        elif r.status_code != 200:
            error(f"error code {r.status_code} met when trying to fetch achievements for user: {userID}, ignoring")
            return
        
        
        response = r.json()
        
        unlocked_achievements = 0
        total_achievements = 0
        
        for i in response["playerstats"]["achievements"]:
            total_achievements += 1
            # i love how the `true` boolean in python is just 1 
            unlocked_achievements += i["achieved"]
            
        return f"{unlocked_achievements}/{total_achievements}"

    # checks what game the user is currently playing
    def get_game(self, userIDs):
        r = make_web_request(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.APIKey}&format=json&steamids={','.join((map(str, userIDs)))}")
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r == "error":
            return
        
            
        if r.status_code == 403:
            error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
            exit()

        if r.status_code != 200:
            error(f"error code {r.status_code} met when trying to fetch game, ignoring")
            return
        
        
        response = r.json()
        
        # counts how many users you're supposed to get back, and checks if you got that many back
        if len(response["response"]["players"]) != len(userIDs):
            error("There seems to be an incorrect account IDs given, please verify that your user ID(s) are correct")

        # sort the players based on position in the config file
        sortedResponse = []
        for userID in userIDs:
            for player in response["response"]["players"]:
                if player["steamid"] == userID:
                    sortedResponse.append(player)
                    break


        # loop thru every user in the response, if they're playing a game, save it
        for player in range(0, len(sortedResponse)):
            if "gameextrainfo" in sortedResponse[player]:
                playerData = sortedResponse[player]
                return {
                    "name": playerData["gameextrainfo"],
                    "gameID": int(playerData["gameid"]),
                    "userID": int(playerData["steamid"])
                }


        # if the user isn't playing anything
        return {"name": "", "gameID": 0, "userID": 0}

    # webscrape the "enhanced" rich presence information for your profile
    # if you're confused this uses your <id3>, it's your <id64> (which is what you put into the config file) minus 76561197960265728
    # aka <id3> = <id64> - 76561197960265728
    # why steam does this is beyond me but it's fine
    # thank you so much to `wuddih` in this post for being the reason i found out about this https://steamcommunity.com/discussions/forum/1/5940851794736009972/ lmao 
    def get_rich_presence(self, userIDs, gameName):
        for userID in userIDs:
            # userID type 3. <id3> = <id64> - 76561197960265728
            URL = f"https://steamcommunity.com/miniprofile/{int(userID) - 76561197960265728}"
            try:
                pageRequest = make_web_request(URL)
            except requests.exceptions.RetryError as e:
                log(f"failed connecting to {URL}, perhaps steam is down for maintenance?\n    error:{e}")
                return
            except Exception as e:
                error(f"error caught while fetching enhanced RPC data from {URL}, ignoring\n    error:{e}")
                return
            
            if pageRequest == "error":
                return
            
            # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
            time.sleep(0.2)
            
            if pageRequest.status_code != 200:
                error(f"status code {pageRequest.status_code} returned whilst trying to fetch the enhanced rich presence info for steam user ID `{userID}`, ignoring function")
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
                return rich_presence.contents[0]
            
            # set the "enhanced rich presence" information back to nothing
            if rich_presence == None:
                return ""


    @functools.cache
    def get_game_steam_ID(self, gameName, APIKey):
        # fetches a list of ALL games on steam
        r = make_web_request(f"https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={APIKey}&format=json")
        if r == "error":
            return
        
        # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
        time.sleep(0.2)
        
        if r.status_code == 403:
            error("Forbidden, Access to the steam API has been denied, please verify your steam API key")
            exit()
        
        if r.status_code != 200:
            error(f"error code {r.status_code} met when requesting list of games in order to obtain an icon for {gameName}, ignoring")
            return

        respone = r.json()
        
        # loops thru every game until it finds one matching your game's name
        for game in respone["applist"]["apps"]:
            if gameName.lower() == game["name"].lower():
                return game["appid"]
        
        
        # for handling game demos
        if " demo" in gameName.lower():
            tempGameName = copy(gameName.lower())
            tempGameName.replace(" demo", "")
            for game in respone["applist"]["apps"]:
                if tempGameName.lower() == game["name"].lower():
                    return  game["appid"]
        
        
        
        # if we didn't find the game at all on steam, 
        log(f"could not find the steam app ID for {gameName}")
        return 0


    # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
    @functools.cache
    def get_image_url_from_store_page(self, gameID) -> str:
        # if the steam game ID is known to be invalid, just return immediately
        if gameID == 0:
            return None
        
        log("getting icon from the steam store")
        try: 
            r = make_web_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}")
            if r == "error":
                return
            
            # sleep for 0.2 seconds, this is done after every steam request, to avoid getting perma banned (yes steam is scuffed)
            time.sleep(0.2)
            
            if r.status_code != 200:
                error(f"error code {r.status_code} met when requesting an image from the steam store page, ignoring")
                return
            
            respone = r.json()
            
            log(f"successfully fetched image from steam")
            return respone[str(gameID)]["data"]["header_image"]
            

        except Exception as e:
            error(f"Exception {e} raised when trying to fetch image thru steam, gameID: {gameID}, ignoring")
            return None
