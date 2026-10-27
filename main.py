import time
import logging

from typing import Union

import src.steam_presence.logger as logger
import src.steam_presence.misc as steam_presence

from src.setters.DiscordRPC import DiscordRPC
from src.steam_presence.config import Config
from src.steam_presence.command_line_args import args

from src.steam_presence.per_platform_cycle.jellyfin import run_jellyfin_cycle
from src.steam_presence.per_platform_cycle.last_fm import run_last_fm_cycle
from src.steam_presence.per_platform_cycle.local import run_local_cycle
from src.steam_presence.per_platform_cycle.mpd import run_mpd_cycle
from src.steam_presence.per_platform_cycle.steam import run_steam_cycle

logger.initialize()
logging.info("Starting setup!")

def _load_config():
    config_args = {}
    if getattr(args, "config", None):
        config_args["config_path"] = args.config
    config.load(**config_args)

config = Config()
_load_config()

class ServiceCooldown:
    """
    """

    def __init__(self, cooldown):
        self.cooldown: float = cooldown
        self.next_tick: float = time.time()

    def is_ready(self) -> bool:
        if self.next_tick > time.time():
            return False

        self.next_tick = time.time() + self.cooldown
        return True

class ServiceCooldowns:
    def __init__(self):
        self.epic_games_store = ServiceCooldown(config.epic_games_store.cooldown) # unused
        self.last_fm = ServiceCooldown(config.last_fm.cooldown)
        self.jellyfin = ServiceCooldown(config.jellyfin.cooldown)
        self.local = ServiceCooldown(config.local.cooldown)
        self.mpd = ServiceCooldown(config.mpd.cooldown)
        self.steam = ServiceCooldown(config.steam.cooldown)

service_cooldowns = ServiceCooldowns()
# key is just a generic identifier such as process ID or steam ID
RPC_connections: dict[Union[int, str], DiscordRPC] = {}

logging.info("Initial setup complete!")
print("–" * steam_presence.get_terminal_width())

while True:
    cycle_start_time = time.time()
    _load_config() # reload

    def _run_service(name, function):
        section = getattr(config, name, None)
        cooldown = getattr(service_cooldowns, name, None)
        if section is None or cooldown is None:
            logging.error("Unknown section %s", name)
            return
        if not (section.enabled and cooldown.is_ready()):
            return
        try:
            function(RPC_connections, config)
        except Exception as e:
            logging.warning("Failed to run %s: %s", name, e)

    _run_service("mpd", run_mpd_cycle)
    _run_service("local", run_local_cycle)
    _run_service("jellyfin", run_jellyfin_cycle)
    _run_service("last_fm", run_last_fm_cycle)
    _run_service("steam", run_steam_cycle)

    logging.debug("Processing complete!")

    expired_IDs: list[Union[int, str]] = []
    for identifier, connection in RPC_connections.items():
        logging.debug("Refreshing connection for %s", identifier)
        connection.refresh()

        if connection.get_time_since_timeout() > config.app.lifetime:
            connection.close_RPC() 
            expired_IDs.append(identifier)

            logging.info(
                "Deleting connection to %s after being connected for %s seconds",
                identifier,
                round(time.time() - connection.creation_time, 1)
            )
            print("–" * steam_presence.get_terminal_width())

    for identifier in expired_IDs:
        RPC_connections.pop(identifier)

    logging.debug("----- Cycle completed at %s -----", round(time.time()))

    try:
        time.sleep(max(0, config.app.cycle_interval - (time.time() - cycle_start_time)))
    except KeyboardInterrupt:
        logging.info("Closed by keyboard interrupt")
        exit()
