# this file should only be imported once, preferably in main.py
import logging

from src.command_line_arguments import args

log_level = logging.INFO

if args.debug:
    log_level = logging.DEBUG

logging.basicConfig(level=log_level, format="%(levelname)s - %(message)s")

logging.debug("Debug logging enabled")