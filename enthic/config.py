import logging
import logging.config
import os
from json import load
from os.path import dirname, join
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

logging.config.fileConfig(
    Path(__file__).parents[1] / "logging.ini", disable_existing_loggers=False
)


with open(join(dirname(__file__), "configuration.json")) as json_configuration_file:
    CONFIG = load(json_configuration_file)


class Config:
    FTP_MAX_VOLUME = os.environ.get("FTP_MAX_VOLUME", 6 * 1024 * 1024 * 1024)
    DATADIR = Path(os.environ.get("DATADIR", Path(__file__).parent / ".."))
    BUNDLE_RAW_DIR = (
        Path(os.environ.get("DATADIR", Path(__file__).parent / "..")) / "bundles"
    )
    INSEE_KEY = CONFIG["INSEE"]["KEY"]
    INSEE_SECRET = CONFIG["INSEE"]["SECRET"]
