"""
    Responsible for setting up the desired logging behaviour
"""

import logging
import os
import datetime

from src.presence_manager.command_line_args import args

def initialize():
    """
        Only intended to be called once to setup correct logging behaviour
    """

    log_level = logging.INFO

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

    logging.info("Logging enabled")
    logging.debug("Logging enabled")
