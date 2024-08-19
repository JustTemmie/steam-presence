import os
import sys
import json
import time
import requests

import vdf
import re

from steam.client import SteamClient
from steam.guard import SteamAuthenticator
from steam.enums.emsg import EMsg
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
        self.current_game_ID = 0

    @steam_presence.time_cache(180)
    def get_game_achievement_progress(self, userID, gameID):
        try:
            r = webapi.get("ISteamUserStats", "GetPlayerAchievements",  params={
                "appid": gameID,
                "key": self.APIKey,
                "steamid": userID
            })
            
            unlocked_achievements = 0
            total_achievements = 0

            for i in r["playerstats"]["achievements"]:
                total_achievements += 1
                if i["achieved"]:
                    unlocked_achievements += 1
                
            return f"{unlocked_achievements}/{total_achievements}"
        except KeyError:
            steam_presence.log(f"key error met whilst fetching achievement progress for {gameID}")
        except Exception as e:
            steam_presence.error(f"get_game_achievement_progress throwed error {e}")
        
        return "0/0"
    
    @steam_presence.time_cache(3600)
    def get_game_review_rating(self, gameID) -> str | None:
        try:
            r = webapi.webapi_request(f"https://store.steampowered.com/appreviews/{gameID}?json=1")
            
            if r["success"] != 1:
                self.get_game_review_rating(gameID)
                return
        
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

    @steam_presence.time_cache(86400)
    def get_image_url_from_steam_CDN(self, gameID) -> str | None:
        try:
            return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{gameID}/hero_capsule.jpg?t={round(time.time())}"
        except Exception as e:
            steam_presence.error(f"get_image_url_from_steam_CDN throwed error {e}")
    
    
    @steam_presence.time_cache(86400)
    # do note this is NOT saved to disk, just in case someone ever adds an entry to the SGDB later on
    def get_image_url_from_store_page(self, gameID) -> str | None:
        try:
            r = webapi.webapi_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}")
        
            steam_presence.log(f"successfully fetched image from steam")
            return r[str(gameID)]["data"]["header_image"]
        except KeyError:
            steam_presence.log(f"that was a lie, could not fetch image from steam")
        except Exception as e:
            steam_presence.error(f"get_image_url_from_store_page throwed error {e}")
        
        raise Exception('')

    
    def get_current_game_ID(self, userID) -> int:
        try:
            link_details = self.get_private_player_link_details(userID)
            if link_details == False:
                return self.current_game_ID
            
            self.current_game_ID = int(link_details["game_id"])
            return self.current_game_ID
        
        except KeyError:
            steam_presence.debug(f"user {userID} does not seem to be playing anything")
        
        except Exception as e:
            steam_presence.error(f"get_current_game_ID throwed error {e}")
            return self.current_game_ID # this is kind of a scuffed fix but it's the best i can offer you
        
        return 0
    
    @steam_presence.time_cache(3600)
    def get_game_name(self, gameID) -> str | None:
        # game IDs currently only go up to ~3,000,000, this is 1,000,000,000 - this should be okay for a while
        if gameID > 1000000000:
            steam_presence.log(f"tried fetching name for ID {gameID}, this seems to be a custom game - this scenario is currently not handled within the program")
            return
        
        try:
            steamApps = webapi.get("ISteamApps", "GetAppList", version=2)
            if steamApps:
                result = [d for d in steamApps["applist"]["apps"] if d.get("appid") == gameID]
                if result:
                    return result[0]["name"]
                else:
                    raise Exception('')
            else:
                raise Exception('')

        
        except KeyError:
            steam_presence.debug(f"couldn't fetch name for {gameID}")
        except Exception as e:
            steam_presence.error(f"get_current_game_name throwed error {e}")
        
        raise Exception('')

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
    
    @steam_presence.time_cache(3600)
    def get_game_price(self, gameID, countryCode = "us") -> str | None:
        try:
            r = webapi.webapi_request(f"https://store.steampowered.com/api/appdetails?appids={gameID}&cc={countryCode}")
        
            return r[str(gameID)]["data"]["price_overview"]["final_formatted"]
        except KeyError:
            steam_presence.debug(f"couldn't find a price for {gameID} using the country code: {countryCode}")
        except Exception as e:
            steam_presence.error(f"get_game_price throwed error {e}")
        
        raise Exception('')
    
    @steam_presence.time_cache(3600)
    def get_game_RPC_tokens(self, gameID) -> dict | None:
        language = "english"
        
        product_info = self.get_product_info(gameID)
        if not product_info:
            raise Exception('')
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
    def get_product_info(self, gameID) -> dict[str, dict] | Exception:
        try:
            product_info = anonymous_client.get_product_info(apps=[gameID])
            if product_info:
                return product_info
        except TimeoutError as e:
            pass
        except Exception as e:
            steam_presence.error(f"whilst calling `get_product_info`:\n{e}")
        except:
            steam_presence.error(f"timed out whilst trying to fetch product info for {gameID}")
        
        raise Exception('')
    
    @steam_presence.time_cache(15)
    def get_player_link_details(self, userID):
        steam_presence.debug(f"fetching player link, or `connection` details for {userID}")
        return webapi.get("IPlayerService", "GetPlayerLinkDetails", params={
            "key": self.APIKey,
            "steamids[0]": userID
        })
        
    
    def get_private_player_link_details(self, userID) -> dict[str, any]:
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
    steam_user_ID = config["SERVICES"]["STEAM"]["USER_IDS"]
    
    steamPlatform = SteamPlatform(steam_API_key)
    
    
    current_game_ID = steamPlatform.get_current_game_ID(steam_user_ID)
    if not current_game_ID:
        print("user is not playing anything, exiting")
        exit()

    # print(steamPlatform.get_game_achievement_progress(steam_user_ID, current_game_ID))
    current_game_info = steamPlatform.get_product_info(current_game_ID)
    
    current_game_rpc_tokens = steamPlatform.get_game_RPC_tokens(current_game_ID)
    print(current_game_ID)
    # print(logged_in_client.get_user(steam_user_ID).get_ps("game_name")) # this adds support for non-steam games, but requires a logged in account
    print(steamPlatform.get_game_name(current_game_ID))
    