import configparser
import json
import sys

config = configparser.ConfigParser()
config.read(sys.argv[1])

with open(sys.argv[2]) as file:
    game = json.loads(file.read())
