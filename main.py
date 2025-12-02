import time
import logging

from typing import Union

import src.presence_manager.logger as logger
import src.presence_manager.misc as presence_manager

from src.setters.DiscordRPC import DiscordRPC
from src.presence_manager.config import Config

from src.presence_manager.per_platform_cycle.jellyfin import run_jellyfin_cycle
from src.presence_manager.per_platform_cycle.last_fm import run_last_fm_cycle
from src.presence_manager.per_platform_cycle.local import run_local_cycle
from src.presence_manager.per_platform_cycle.mpd import run_mpd_cycle
from src.presence_manager.per_platform_cycle.steam import run_steam_cycle

logger.initialize()
logging.info("Starting setup!")

config = Config()
config.load()

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

DEFAULT_GAME = DiscordRPC(config, None) if config.default_game.enabled else None

logging.info("Initial setup complete!")
print("–" * presence_manager.get_terminal_width())

while True:
    cycle_start_time = time.time()
    config.load() # reload

    if config.mpd.enabled and service_cooldowns.mpd.is_ready():
        run_mpd_cycle(RPC_connections, config)

    if config.local.enabled and service_cooldowns.local.is_ready():
        run_local_cycle(RPC_connections, config)

    if config.jellyfin.enabled and service_cooldowns.jellyfin.is_ready():
        run_jellyfin_cycle(RPC_connections, config)

    if config.last_fm.enabled and service_cooldowns.last_fm.is_ready():
        run_last_fm_cycle(RPC_connections, config)

    if config.steam.enabled and service_cooldowns.steam.is_ready():
        run_steam_cycle(RPC_connections, config)

    logging.debug("Processing complete!")

    if DEFAULT_GAME:
        if len(RPC_connections) == 0:
            logging.info("Switching to displaying the default game.")
            DEFAULT_GAME.default_game_payload = config.default_game

            if config.default_game.inject_discord_status_data:
                DEFAULT_GAME.inject_bonus_status_data(config.default_game.discord_status_data)

            DEFAULT_GAME.instanciate(
                config.default_game.name,
                presence_manager.get_unused_discord_id(
                    [rpc.discord_app_id for rpc in RPC_connections.values()],
                    config
                )
            )

            RPC_connections["DEFAULT"] = DEFAULT_GAME

        elif len(RPC_connections) == 1 and RPC_connections.get("DEFAULT"):
            RPC_connections["DEFAULT"].update()
        else:
            RPC_connections.pop("DEFAULT")


    expired_IDs: list[Union[int, str]] = []
    for identifier, connection in RPC_connections.items():
        logging.debug("Refreshing connection for %s", identifier)
        connection.refresh()

        if connection.get_time_since_timeout() > 600:
            connection.close_RPC()
            expired_IDs.append(identifier)

            logging.info(
                "Deleting connection to %s after being connected for %s seconds",
                identifier,
                round(time.time() - connection.creation_time, 1)
            )
            print("–" * presence_manager.get_terminal_width())

    for identifier in expired_IDs:
        RPC_connections.pop(identifier)

    logging.debug("----- Cycle completed at %s -----", round(time.time()))

    try:
        time.sleep(max(0, config.app.cycle_interval - (time.time() - cycle_start_time)))
    except KeyboardInterrupt:
        logging.info("Closed by keyboard interrupt")
        exit()
