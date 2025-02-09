import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--debug", type=int, help="boolean, whether to log debug info or not")
parser.add_argument("--config", type=str, help="overwrite the path of the config file", default="config.json")

args = parser.parse_args()