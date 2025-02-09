# adds the project root to the path, this is to allow importing other files in an easier manner
# if you know a better way of doing this, please tell me!
if __name__ == "__main__":
    import sys
    sys.path.append(".")

from steam.client import SteamClient
import vdf
import steam.exceptions as SteamExceptions

import requests
import logging
import math
import browser_cookie3

import src.types.steam as SteamTypes
import src.types.discord_data as DiscordTypes


# used to fetch things not available to the web API
class AnonymousClient:        
    def __init__(self):
        self.anonymous_client = SteamClient()
        self.anonymous_client.anonymous_login()
    
    def get_product_info(self, appID: int) -> SteamTypes.ProductInfo:
        product_info = SteamTypes.ProductInfo()

        try:
            request = self.anonymous_client.get_product_info(apps=[appID])
            if request:
                product_info_dict = request.get("apps", {}).get(appID, {})

                product_info.load_dict(product_info_dict)

                return product_info
            
        except SteamExceptions.SteamError as e:
            logging.error(f"steam error met whilst fetching product info for app {appID} - {e}")
        
        except Exception as e:
            logging.error(f"unhandled error met whilst fetching product info for app {appID} - {e}")
        
        return product_info

class SteamWeb:
    def __init__(self, API_key: str, store_cookies = None, community_cookies = None):
        self.API_key = API_key
        
        self.store_cookies = None
        self.community_cookies = None

        self.config = Config()
        self.config.load

        if self.config.steam.auto_fetch_cookies:
            if self.config.steam.cookie_browser == "auto":
                self.store_cookies = browser_cookie3.load(domain_name="store.steampowered.com")
                self.community_cookies = browser_cookie3.load(domain_name="steamcommunity.com")
            else:
                browser_load_function = None

                # we know this won't return None due to vetting in the config loader
                for function in browser_cookie3.all_browsers:
                    if getattr(function, "__name__") == self.config.steam.cookie_browser:
                        browser_load_function = function
                
                self.store_cookies = browser_load_function(domain_name="store.steampowered.com")
                self.community_cookies = browser_load_function(domain_name="steamcommunity.com")
        
            if not self.store_cookies:
                logging.warning("couldn't find any cookies saved for store.steampowered.com")
            if not self.community_cookies:
                logging.warning("couldn't find any cookies saved for steamcommunity.com")
    
    def get_user_achievement_progress(self, appID: int, userID: int) -> dict:
        pass

    def get_app_playtime(self, appID: int, userID: int) -> str:
        pass
        # make sure it actually returns a string or whatever
    
    def get_app_playtime_2(self, appID: int, userID: int) -> str:
        pass
    
    def get_user_rich_presence(self, userID: int) -> dict:
        
        r = requests.get("https://steamcommunity.com/chat/", cookies=self.community_cookies)

        with open("temp/chat.html", "wb") as f:
            f.write(bytes(r.content))
        
        print(r.raw)
        
        return {}

    def get_player_link_details(self, userID: int) -> SteamTypes.LinkDetails:
        link_details = SteamTypes.LinkDetails()

        r = requests.get(f"https://api.steampowered.com/IPlayerService/GetPlayerLinkDetails/v1/?key={self.API_key}&steamids[0]={userID}")
        
        if r.status_code != 200:
            logging.DEBUG(f"status code {r.status_code} recieved when fetching player link details")
            return link_details
        
        json_request = r.json()

        if isinstance(json_request, dict):
            details_list = json_request.get("response", {}).get("accounts", {})

            if isinstance(details_list, list):
                link_details.private_data.load_dict(details_list[0].get("private_data"))
                link_details.public_data.load_dict(details_list[0].get("public_data"))

        return link_details
    
    def get_app_review_score(self, appID: int) -> DiscordTypes.ReviewScore:
        review_score = DiscordTypes.ReviewScore()

        r = requests.get(f"https://store.steampowered.com/appreviews/{appID}?json=1")

        if r.status_code != 200:
            logging.DEBUG(f"status code {r.status_code} recieved when fetching review scores")
            return review_score
        
        query = r.json().get("query_summary", {})

        if query.get("total_reviews") > 0:
            score_percentage = query.get("total_positive") / query.get("total_reviews")
            review_score.review_score_percentage = math.ceil(score_percentage * 100)
        
        review_score.total_reviews = query.get("total_reviews", 0) + query.get("num_reviews", 0)
        review_score.review_total_positive = query.get("total_positive")
        review_score.review_total_negative = query.get("total_negative")
        review_score.review_score_description = query.get("review_score_desc")

        return review_score

    def get_app_display_name(self, appID: int) -> str:
        pass

    def get_app_price(self, appID: int) -> str:
        pass

    def get_app_hero_capsule_url(self, appID: int) -> str:
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appID}/hero_capsule.jpg"
    
    def get_app_header_url(self, appID: int) -> str:
        return f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appID}/header.jpg"

class SteamUser:
    def __init__(self, userID: int, API_key: str):
        self.userID = userID
        self.API_key = API_key

class Steam:
    def __init__(self, API_key: str):
        self.API_key = API_key

        self.app_information: dict[int: dict] = {}

        self.users: list[SteamUser] = []
        
        self.anonymous_client: AnonymousClient = AnonymousClient()
        self.steam_web: SteamWeb = SteamWeb(API_key)
            
    def update_data(self, appID: int):
        if not self.app_information[appID]:
            self.app_information[appID] = {}
        
        for key, value in self.steam_web.get_app_review_score(appID).items():
            self.app_information[appID][key] = value

    def add_user(self, userID: int):
        user = SteamUser(userID, self.API_key)
        self.users.append(user)
    

if __name__ == "__main__":
    from src.config import Config

    import os
    import json

    if not os.path.exists("temp"):
        os.mkdir("temp")

    config = Config()
    config.load()

    steam: Steam = Steam(config.steam.api_key)
    for userID in config.steam.user_ids:
        steam.add_user(userID)
    
    
    appID = 427520

    steam.steam_web.get_user_rich_presence(steam.users[0])
    quit()

    # print(steam.steam_web.get_app_review_score(appID))
    # print(steam.anonymous_client.get_product_info(960090))

    # rp = steam.steam_web.get_user_rich_presence_raw_data(config.steam.user_ids[0])

    # print(rp)
    # quit()

    with open("temp/packageinfo.vdf", "rb") as f:
        a = f.read()
        # print(str(a))
        # print(vdf.loads(str(a)))
    # quit()


    with open(f"temp/product_info_{appID}.json", "w") as f:
        product_info = steam.anonymous_client.get_product_info(appID)
        json.dump(product_info.to_dict(), f)

    with open(f"temp/link_details_{config.steam.user_ids[0]}.json", "w") as f:
        link_details = steam.steam_web.get_player_link_details(config.steam.user_ids[0])
        json.dump(link_details.to_dict(), f)
 
    with open(f"temp/link_details_{config.steam.user_ids[1]}.json", "w") as f:
        link_details = steam.steam_web.get_player_link_details(config.steam.user_ids[1])
        json.dump(link_details.to_dict(), f)