import argparse

parser = argparse.ArgumentParser()

parser.add_argument(
    "--log-level",
    type=int,
    help="Specify a custom log level"
)
parser.add_argument(
    "--config",
    type=str,
    help="Overwrite the path of the config file",
    default="config.json"
)

args = parser.parse_args()
