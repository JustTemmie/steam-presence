from src.steam_presence.config import Config, SteamUser
from src.steam_presence.DataClasses import SteamFetchPayload
from dataclasses import dataclass
from bs4 import BeautifulSoup
from typing import Union

import requests
import logging
import json


@dataclass
class getCurrentStateResponse:
    app_name: str
    app_id: int
    avatar_url: str | None = None
    display_name: str | None = None
    profile_url: str | None = None

@dataclass
class fetchMiniProfileDataResponse:
    rich_presence: str | None = None
    background_url: str | None = None
    profile_level: str | None = None
    profile_badge_url: str | None = None
    profile_badge_name: str | None = None

@dataclass
class fetchAppDetailsResponse:
    required_age: int | None = None
    header_image: str | None = None
    capsule_image: str | None = None
    website: str | None = None
    developers: str | None = None
    publishers: str | None = None
    price_currency: str | None = None
    price_initial: int | None = None
    price_current: int | None = None
    price_discount_percent: int | None = None
    price_formatted: str | None = None
    platform_windows: bool | None = None
    platform_mac: bool | None = None
    platform_linux: bool | None = None
    achievement_count: int | None = None
    release_date: str | None = None

@dataclass
class fetchAppReviewsResponse:
    total_positive_reviews: int | None = None
    total_negative_reviews: int | None = None
    total_reviews: int | None = None
    review_percent: int | None = None
    review_description: str | None = None

class SteamAPI:
    def __init__(self, config: Config, user: SteamUser):
        self.config = config
        self.user = user
        
        self.api_key = user.api_key

    def getCurrentState(self) -> getCurrentStateResponse | None:
        URL = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={self.api_key}&steamids={self.user.user_id}"
        # URL = f"https://steamcommunity.com/miniprofile/{self.user.user_id - 76561197960265728}"
        r = requests.get(URL)

        if r.status_code != 200:
            logging.error(f"failed to fetch mini profile, status code {r.status_code} met")
            return fetchMiniProfileDataResponse()
        
        player_summaries = r.json()
        print(player_summaries)

        if not player_summaries: return None
        players = player_summaries.get("response", {}).get("players", [])
        if len(players) == 0: return None

        player_summary = players[0]
        if not player_summary.get("gameid"): return None

        return getCurrentStateResponse(
            app_name=player_summary.get("gameextrainfo"),
            app_id=player_summary.get("gameid"),
            avatar_url=player_summary.get("avatarfull"),
            display_name=player_summary.get("personaname"),
            profile_url=player_summary.get("profileurl")
        )
    
    # returns html data or None
    def fetchMiniProfileData(self) -> fetchMiniProfileDataResponse:
        # convert steam ID 64 to steam ID 3, yes, really
        URL = f"https://steamcommunity.com/miniprofile/{self.user.user_id - 76561197960265728}"
        r = requests.get(URL)

        if r.status_code != 200:
            logging.error(f"failed to fetch mini profile, status code {r.status_code} met")
            return fetchMiniProfileDataResponse()

        mini_profile = r.content

        soup = BeautifulSoup(mini_profile, "html.parser")
        
        rich_presence_span = soup.find("span", class_="rich_presence")
        rich_presence = rich_presence_span.text.strip() if rich_presence_span else None

        profile_level_span = soup.find("span", class_="friendPlayerLevelNum")
        profile_level = profile_level_span.text.strip() if profile_level_span else None

        profile_badge_url = soup.find("img", class_="badge_icon").get("src")

        video = soup.find('video', class_='miniprofile_nameplate')
        background_source = video.find('source', type='video/webm')
        background_url = background_source.get("src")

        badge_container = soup.find('div', class_='miniprofile_featuredcontainer')
        badge_name = badge_container.find('div', class_='name').text.strip() if badge_container else None
        
        return fetchMiniProfileDataResponse(
            rich_presence = rich_presence,
            background_url = background_url,
            profile_level = profile_level,
            profile_badge_url = profile_badge_url,
            profile_badge_name = badge_name,
        )
    
    def fetchAppDetails(self, app_ID: Union[str, int], currency: str = "us") -> fetchAppDetailsResponse:
        URL = f"https://store.steampowered.com/api/appdetails?json=1&appids={app_ID}&cc={currency}"
        r = requests.get(URL)

        if r.status_code != 200:
            logging.error(f"failed to fetch app details for {app_ID}, status code {r.status_code} met")
            return fetchAppDetailsResponse()

        data = r.json()
        if not data:
            return fetchAppDetailsResponse()

        data = data.get(f"{app_ID}", {}).get("data", {})

        required_age: int = data.get("required_age")
        header_image: str = data.get("header_image")
        capsule_image: str = data.get("capsule_image")
        website: str = data.get("website")
        developers: str = ", ".join(data.get("developers", []))
        publishers: str = ", ".join(data.get("publishers", []))

        price_currency: str = data.get("price_overview", {}).get("currency")
        # do note a price of $4.99 would have an initial price of 499
        price_initial: int = data.get("price_overview", {}).get("initial")
        price_current: int = data.get("price_overview", {}).get("final")
        price_discount_percent: int = data.get("price_overview", {}).get("discount_percent")
        price_formatted: str = data.get("price_overview", {}).get("final_formatted")

        platform_windows: bool = data.get("platforms", {}).get("windows")
        platform_mac: bool = data.get("platforms", {}).get("mac")
        platform_linux: bool = data.get("platforms", {}).get("linux")

        achievement_count: int = data.get("achievements", {}).get("total")
        release_date: str = data.get("release_date", {}).get("date")

        return fetchAppDetailsResponse(
            required_age,
            header_image,
            capsule_image,
            website,
            developers,
            publishers,
            price_currency,
            price_initial,
            price_current,
            price_discount_percent,
            price_formatted,
            platform_windows,
            platform_mac,
            platform_linux,
            achievement_count,
            release_date,
        )
    
    def fetchAppReviews(self, app_ID: Union[str, int]) -> fetchAppReviewsResponse:
        URL = f"https://store.steampowered.com/appreviews/{app_ID}?json=1"

        r = requests.get(URL)

        if r.status_code != 200:
            logging.error(f"failed to fetch app details for {app_ID}, status code {r.status_code} met")
            return fetchAppReviewsResponse()

        data = r.json()
        if not data:
            return fetchAppReviewsResponse()

        data = data.get("query_summary", {})

        total_positive_reviews = data.get("total_positive", None)
        total_negative_reviews = data.get("total_negative", None)
        total_reviews = data.get("total_reviews", None)
        review_percent = None
        review_description = data.get("review_score_desc", None)

        if total_reviews and total_positive_reviews:
            review_percent = round((total_positive_reviews / total_reviews) * 100)
        
        return fetchAppReviewsResponse(
            total_positive_reviews,
            total_negative_reviews,
            total_reviews,
            review_percent,
            review_description,
        )


class SteamGetter:
    def __init__(self, config: Config, user: SteamUser):
        self.config = config
        self.user = user

        self.api = SteamAPI(config, user)

    def fetch(self) -> SteamFetchPayload:
        logging.debug(f"Fetching steam information for {self.user}")

        current_game_info: getCurrentStateResponse | None = self.api.getCurrentState()

        if not current_game_info:
            return SteamFetchPayload()

        current_app_ID = current_game_info.app_id

        mini_profile_data: fetchMiniProfileDataResponse = self.api.fetchMiniProfileData()
        app_details_data: fetchMiniProfileDataResponse = self.api.fetchAppDetails(current_app_ID)
        app_reviews: fetchAppReviewsResponse = self.api.fetchAppReviews(current_app_ID)

        # surely there's a better way to pass this much data
        return SteamFetchPayload(
            app_name = current_game_info.app_name,
            app_id = current_game_info.app_id,
            avatar_url = current_game_info.avatar_url,
            display_name = current_game_info.display_name,
            profile_url = current_game_info.profile_url,

            rich_presence = mini_profile_data.rich_presence,
            mini_profile_background_url = mini_profile_data.background_url,
            profile_level = mini_profile_data.profile_level,
            profile_badge_url = mini_profile_data.profile_badge_url,
            profile_badge_name = mini_profile_data.profile_badge_name,

            required_age = app_details_data.required_age,
            header_image = app_details_data.header_image,
            capsule_image = app_details_data.capsule_image,
            website = app_details_data.website,
            developers = app_details_data.developers,
            publishers = app_details_data.publishers,
            price_currency = app_details_data.price_currency,
            price_initial = app_details_data.price_initial,
            price_current = app_details_data.price_current,
            price_discount_percent = app_details_data.price_discount_percent,
            price_formatted = app_details_data.price_formatted,
            platform_windows = app_details_data.platform_windows,
            platform_mac = app_details_data.platform_mac,
            platform_linux = app_details_data.platform_linux,
            achievement_count = app_details_data.achievement_count,
            release_date = app_details_data.release_date,

            total_positive_reviews = app_reviews.total_positive_reviews,
            total_negative_reviews = app_reviews.total_negative_reviews,
            total_reviews = app_reviews.total_reviews,
            review_percent = app_reviews.review_percent,
            review_description = app_reviews.review_description,
        )