import os
import sys
import json
import time

import vdf
import re

from steam.client import SteamClient
from steam import webapi

# for development purposes
if __name__ == "__main__":
    sys.path.append(".")

import src.helpers as steam_presence

anonymous_client = SteamClient()
anonymous_client.anonymous_login()


class SteamPlatform():
    def __init__(self, APIKey):
        self.APIKey = APIKey

    @steam_presence.time_cache(180)
    def get_game_achievement_progress(self, userID, gameID):
        r = webapi.get("ISteamUserStats", "GetPlayerAchievements",  params={
            "appid": gameID,
            "key": self.APIKey,
            "steamid": userID
        })
        
        unlocked_achievements = 0
        total_achievements = 0

        try:
            for i in r["playerstats"]["achievements"]:
                total_achievements += 1
                if i["achieved"]:
                    unlocked_achievements += 1
                
            return f"{unlocked_achievements}/{total_achievements}"
        except KeyError:
            steam_presence.log(f"key error met whilst fetching achievement progress for {gameID}")
            return "0/0"
        except Exception as e:
            steam_presence.error(f"get_game_achievement_progress throwed error {e}")
    
    @steam_presence.time_cache(3600)
    def get_game_review_rating(self, gameID) -> str | None:
        # get the review data for the steam game
        r = webapi.webapi_request(f"https://store.steampowered.com/appreviews/{gameID}?json=1")
        
        if r["success"] != 1:
            self.get_game_review_rating(gameID)
            return
        
        try:
            response = r["query_summary"]
            
            # if there aren't any reviews, just return early
            if 0 in [response["total_positive"], response["total_reviews"]]:
                return
            
            scorePercentage = (response["total_positive"] / response["total_reviews"]) * 100
            
            return {
                "score_percentage": f"{round(scorePercentage, 2)}%",
                "score_description": response["review_score_desc"]
            }
        
        except Exception as e:
            steam_presence.error(f"get_game_review_rating throwed error {e}")
            
    
    def get_current_rich_presence(self, userID, gameID) -> str | None:
        current_game_rpc_tokens = self.get_game_RPC_tokens(gameID)
    
        raw_rich_presence_data = self.get_raw_rich_presence_data(userID)
        
        if None in [current_game_rpc_tokens, raw_rich_presence_data]:
            return

        if "steam_display" not in raw_rich_presence_data:
            return

        steam_display = raw_rich_presence_data["steam_display"].casefold()
        rpc_status_string = current_game_rpc_tokens[steam_display].casefold()
    
        def replace_RPC_tokens(s, data):
            # find all patterns inside curly brackets
            patterns = re.findall(r'\{#.*?\}', s)
            for pattern in patterns:
                # remove the curly brackets to find the key
                key = pattern[1:-1]
                
                # make the key lowercase, because for some reason it might be upper case, even though the
                key = key.casefold()
                
                # replace the pattern with the corresponding value if it exists in the dictionary
                if key in data:
                    s = s.replace(pattern, data[key])
            
            return s

        for _i in range(25):
            # replace the tokens (#StatusWithScore) with the actual value (#Status_%gamestatus%: %score%)
            rpc_status_string = replace_RPC_tokens(rpc_status_string, current_game_rpc_tokens)
            
            # fill in the values with
            for key, value in raw_rich_presence_data.items():
                rpc_status_string = rpc_status_string.replace(f'%{key.casefold()}%', value)
            
            # if there are no more RPC tokens to go thru, exit early
            if "#" not in rpc_status_string:
                break
        
        return rpc_status_string

    @steam_presence.time_cache(7200)
    # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
    def get_image_url_from_store_page(self, gameID) -> str | None:
        steam_presence.log("getting icon from the steam store")
        r = webapi.webapi_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}")
        
        try:
            steam_presence.log(f"successfully fetched image from steam")
            return r[str(gameID)]["data"]["header_image"]
        except KeyError:
            steam_presence.log(f"that was a lie, could not fetch image from steam")
        except Exception as e:
            steam_presence.error(f"get_image_url_from_store_page throwed error {e}")

    
    def get_current_game_ID(self, userID) -> int:
        try:
            link_details = self.get_private_player_link_details(userID)
            return int(link_details["game_id"])
        except KeyError:
            steam_presence.debug(f"user {userID} does not seem to be playing anything")
        except Exception as e:
            steam_presence.error(f"get_current_game_ID throwed error {e}")
        
        return 0

    @steam_presence.time_cache(7200)
    def get_game_name(self, gameID) -> str | None:
        try:
            
            product_info = self.get_product_info(gameID)
            return product_info["apps"][gameID]["common"]["name"]
        except KeyError:
            steam_presence.debug(f"couldn't fetch name for {gameID}")
        except Exception as e:
            steam_presence.error(f"get_current_game_name throwed error {e}")

    @steam_presence.time_cache(1200)
    def get_game_playtime(self, userID, gameID) -> str:
        # loop thru all recently played games to find the playtime of our game
        def get_playtime_thru_recently_played_games(userID, gameID) -> int | None:
            recently_played_games = webapi.get("IPlayerService", "GetRecentlyPlayedGames", params={
                "key": self.APIKey,
                "steamid": userID
            })
            
            playtime = None
            for i in recently_played_games["response"]["games"]:
                if i["appid"] == gameID:
                    playtime = int(i["playtime_forever"])
            
            return playtime
        
        # steam sometimes takes a hot second to update the recently played list, so we can also try looping thru all owned games
        def get_playtime_thru_owned_games(userID, gameID) -> int | None:
            owned_games = webapi.get("IPlayerService", "GetOwnedGames", params={
                "key": self.APIKey,
                "steamid": userID
            })
            
            playtime = None
            for i in owned_games["response"]["games"]:
                if i["appid"] == gameID:
                    playtime = int(i["playtime_forever"])

            return playtime
        
        playtime = get_playtime_thru_recently_played_games(userID, gameID)
        if playtime is None:
            playtime = get_playtime_thru_owned_games(userID, gameID)
        
        if playtime is None or playtime == 0:
            return "0.0"

        if playtime > 0:
            return f"{round(playtime / 60, 1)}"
    
    
    def get_game_price(self, gameID, countryCode = "us") -> str | None:
        r = webapi.webapi_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}&cc={countryCode}")
        
        try:
            return r[str(gameID)]["data"]["price_overview"]["final_formatted"]
        except KeyError:
            steam_presence.debug(f"couldn't find a price for {gameID} using the country code: {countryCode}")
        except Exception as e:
            steam_presence.error(f"get_game_price throwed error {e}")
    
    def get_game_RPC_tokens(self, gameID) -> dict | None:
        language = "english"
        
        product_info = self.get_product_info(gameID)
        try:
            return product_info["apps"][gameID]["localization"]["richpresence"][language]["tokens"]
        except KeyError:
            steam_presence.debug(f"the game {gameID} doesn't have any RPC tokens for {language}")
        except Exception as e:
            steam_presence.error(f"get_current_game_ID throwed error {e}")
    
    def get_raw_rich_presence_data(self, userID) -> dict | None:
        link_details = self.get_private_player_link_details(userID)
        if "rich_presence_kv" in link_details:
            rpc_string = link_details["rich_presence_kv"]
            return vdf.loads(rpc_string)["rp"]

    @steam_presence.time_cache(3600)
    def get_product_info(self, gameID):
        return anonymous_client.get_product_info(apps=[gameID])
    
    @steam_presence.time_cache(15)
    def get_player_link_details(self, userID):
        steam_presence.debug(f"fetching player link, or `connection` details for {userID}")
        return webapi.get("IPlayerService", "GetPlayerLinkDetails", params={
            "key": self.APIKey,
            "steamids[0]": userID
        })
        
    
    def get_private_player_link_details(self, userID):
        """
            should return something like this
            ```
            {
                "persona_state": 1,
                "persona_state_flags": 0,
                "time_created": 1530560564,
                "game_id": "287980",
                "rich_presence_kv": "\"rp\"\n{\n\t\"status\"\t\t\"Menu\"\n\t\"steam_display\"\t\t\"#AtMenu\"\n}\n",
                "broadcast_session_id": "0",
                "last_logoff_time": 1721011674,
                "last_seen_online": 1721086148,
                "game_os_type": -184,
                "game_device_type": 1,
                "game_device_name": "device name here (DESKTOP-917825 pilled)"
            }
            ```
        """
        player_link_details = self.get_player_link_details(userID)
        return player_link_details["response"]["accounts"][0]["private_data"]

if __name__ == "__main__":
    config = steam_presence.getConfigFile()
    steam_API_key = config["SERVICES"]["STEAM"]["API_KEY"]
    steam_user_ID = config["SERVICES"]["STEAM"]["USER_ID"]
    
    steamPlatform = SteamPlatform(steam_API_key)
    
    
    current_game_ID = steamPlatform.get_current_game_ID(steam_user_ID)
    if not current_game_ID:
        print("user is not playing anything, exiting")
        exit()

    print(steamPlatform.get_game_achievement_progress(steam_user_ID, current_game_ID))
    current_game_info = steamPlatform.get_product_info(current_game_ID)
    
    current_game_rpc_tokens = steamPlatform.get_game_RPC_tokens(current_game_ID)
    
    with open("development/current_game_info.json", "w") as f:
        json.dump(current_game_info, f)
    
    with open("development/current_game_rpc_localization_keys_info.json", "w") as f:
        json.dump(current_game_rpc_tokens, f)

    # print(current_game_rpc_tokens)
    # print(rich_presence_info)

    print(steamPlatform.get_current_rich_presence(steam_user_ID, current_game_ID))
    print(steamPlatform.get_game_review_rating(current_game_ID))
    print(steamPlatform.get_game_playtime(steam_user_ID, current_game_ID))
    print(steamPlatform.get_game_price(current_game_ID))