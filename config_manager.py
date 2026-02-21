import configparser
import os

CONFIG_FILE = "config.ini"

def init_config():
    config = configparser.ConfigParser()

    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)

    if "SERIAL" not in config:
        config["SERIAL"] = {
            "port": "COM1",
            "baudrate": "9600"
        }

        with open(CONFIG_FILE, "w") as f:
            config.write(f)

def load_config():
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        init_config()

    config.read(CONFIG_FILE)

    if "SERIAL" not in config:
        config["SERIAL"] = {
            "port": "COM1",
            "baudrate": "9600"
        }

    return config

def save_serial(port, baudrate):
    config = load_config()

    if "SERIAL" not in config:
        config["SERIAL"] = {}

    config["SERIAL"]["port"] = port
    config["SERIAL"]["baudrate"] = str(baudrate)

    with open(CONFIG_FILE, "w") as f:
        config.write(f)

