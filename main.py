from src.config import Config
import src.log

from src.services.Discord import DiscordActivity, DiscordActivityUpdatePayload
from src.services.LocalGames import LocalGames
from src.services.Steam import Steam
from src.services.SteamGridDB import SteamGridDB

config = Config()
config.load()

steam = Steam(config.steam.api_key)
steam.add_user(config.steam.user_ids[0])

activities: list[DiscordActivity] = []

activity = DiscordActivity(869994714093465680)

data = DiscordActivityUpdatePayload()
data.new_details = "testing frfr"
data.new_state = "mrp mrp nya"
data.new_large_image_url = "https://cdn.discordapp.com/avatars/338627190956490753/34ba5b83644f719b9c0558a5e8ba51bd.webp?size=1024&format=webp"

activity.update_activity(data)

activities.append(activity)

import time

a = 2
while True:
    a += 1
    # time.sleep(0.2)

    # data = DiscordActivityUpdatePayload()
    # data.new_state = f"loop {a}"

    # activity.update_activity(data)
