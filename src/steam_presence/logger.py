# this file should only be imported once, preferably in main.py or smth

from src.steam_presence.command_line_args import args

import logging
import os
import datetime

log_level = logging.WARN

if args.log_level:
    log_level = args.log_level

# enable logging to file if in debug mode
if log_level <= logging.DEBUG:
    if not os.path.isdir("logs"):
        os.mkdir("logs")

    logging.basicConfig(
        level=log_level,
        format="%(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/{datetime.datetime.now()}.log")
        ]
    )

else:
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )

logging.info("Info logging enabled")
logging.debug("Debug logging enabled")
