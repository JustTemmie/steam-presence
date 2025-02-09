# adds the project root to the path, this is to allow importing other files in an easier manner
# if you know a better way of doing this, please tell me!
if __name__ == "__main__":
    import sys
    sys.path.append(".")

import logging
import time

from pypresence import Presence


class DiscordActivityUpdatePayload:
    def __init__(self):
        self.new_details: str = None
        self.new_state: str = None
        
        self.new_large_image_url: str = None
        self.new_small_image_url: str = None

class DiscordActivity:
    def __init__(self, appID):
        self.appID = appID
        self.buttons: list[dict[str: str, str: str]] = []

        self.presence = Presence(client_id=appID)
        self.start_time = time.time()

        self.details: str = None
        self.state: str = None
        
        self.large_image_url: str = None
        self.small_image_url: str = None

        self.presence.connect()
    
    def update_activity(self, data: DiscordActivityUpdatePayload):
        if data.new_details: self.details = data.new_details
        if data.new_state: self.state = data.new_state
        if data.new_large_image_url: self.large_image_url = data.new_large_image_url
        if data.new_small_image_url: self.small_image_url = data.new_small_image_url

        
        logging.debug(f"updating presence for {self.appID} with {self}")

        self.presence.update(
            details=self.details, state=self.state,
            start=self.start_time,
            large_image=self.large_image_url,
            small_image=self.small_image_url,
            buttons=self.buttons
        )
    
    def __str__(self):
        return str({
            "details": self.details, "state": self.state,
            "start_time": self.start_time,
            "large_image_url": self.large_image_url,
            "small_image_url": self.small_image_url,
            "buttons": self.buttons
        })

