import os
import sys
import json
import time

import copy
from pypresence import Presence

from src.helpers import *

# get the directory of the file initially opened, a.k.a main.py
project_root = os.path.abspath(os.path.dirname(sys.argv[0]))


class RPC():
    def __init__(self, current_version):        
        self.RPCs = {}
        self.platformSpecific = Platform_Specific(current_version)
    
    def get_discord_ID_for_platform(self, platform):
        config = getConfigFile()
        
        if platform == "steam":
            return config["SERVICES"]["STEAM"]["DISCORD_APPLICATION_ID"]
        
        return config["DEFAULT_DISCORD_APPLICATION_ID"]

    def ensure_presence(self, appID, platform):
        if platform in self.RPCs \
            and "app_ID" in self.RPCs[platform] \
            and self.RPCs[platform]["app_ID"] == appID:
                return

        log(f"creating RPC for {platform}")
        
        if appID == 0:
            presence = Presence(client_id=self.get_discord_ID_for_platform(platform))
        else:
            presence = Presence(client_id=appID)
        
        presence.connect()
        
        data = {
            "presence": presence,
            "start_time": time.time(),
            "app_ID": appID
        }
        
        self.RPCs[platform] = data


    def update_presence_details(self, gameInfo): 
        try:
            for platform in copy.copy(self.RPCs):
                print(f"updating RPC presence details for {platform}")
                if platform in gameInfo:
                    RPCData = self.RPCs[platform]
                    platformData = gameInfo[platform]
                    
                    func = getattr(self.platformSpecific, platform)
                    
                    func(RPCData, platformData)
                    
                else:
                    print(f"deleting RPC for {platform}")
                    self.RPCs[platform]["presence"].close()
                    del self.RPCs[platform]
        
        
        except Exception as e:
            error(f"pushing presence failed...\n    Error encountered: {e}")


class Platform_Specific():
    def __init__(self, current_version):
        self.current_version = current_version
    
    def steam(self, RPCData: Presence, platformData: dict):
        lines = []
        config = getConfigFile()
        
        if RPCData["app_ID"] == 0:
            lines.append(platformData["gameName"])
        
        for i in config["RPC_LINES"]:
            try:
                lines.append(i.format(**platformData))
            except Exception as e:
                log(f"Exception {e} met whilst trying to add the RPC line: {e}, ignoring")

        # only return the lines that actually have data in them, then we append `None` twice in case there's not enough entries
        RPCLines = []
        for i in lines:
            if len(i) >= 2 and i.casefold() != "none":
                if len(i) > 128:
                    error(f"the status `{i}` is over 128 characters, splicing off the padding :p")
                    i = i[:128]
                    print(i)
                    
                RPCLines.append(i)
        
        RPCLines.append(None)
        RPCLines.append(None)
        
        print(RPCLines)
        
        # advertise the steam page if desired
        buttons = []
        if config["SERVICES"]["STEAM"]["STORE_BUTTON"]:
            if platformData["price"] and platformData["gameID"]:
                buttons.append({
                    "label": f'Get it for {platformData["price"]} on Steam',
                    "url": f'https://store.steampowered.com/app/{platformData["gameID"]}'
                })
        
        RPCData["presence"].update(
            details = RPCLines[0], state = RPCLines[1],
            start = RPCData["start_time"],
            large_image = platformData["image"], large_text = f"steam-presence {self.current_version}",
            # small_image = customIconURL, small_text = customIconText,
            buttons=buttons
        )