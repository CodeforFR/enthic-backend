import logging
import logging.config
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

logging.config.fileConfig(
    Path(__file__).parents[1] / "logging.ini", disable_existing_loggers=False
)


class Config:
    FTP_MAX_VOLUME = os.environ.get("FTP_MAX_VOLUME", 6 * 1024 * 1024 * 1024)
    BUNDLE_RAW_DIR = Path(
        os.environ.get(
            "BUNDLE_RAW_DIR", Path(__file__).parent / ".." / "data" / "bundles"
        )
    )
    INSEE_KEY = os.environ.get("INSEE_KEY")
    INSEE_SECRET = os.environ.get("INSEE_SECRET")
