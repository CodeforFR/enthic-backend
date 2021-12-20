import logging
import os
import re
import urllib
from datetime import date
from io import BytesIO
from itertools import chain
from pathlib import Path
from typing import Union

import requests
import wget
from bs4 import BeautifulSoup
from py7zr import SevenZipFile

from enthic.config import Config

from .bundles_utils import bundle_history, clean_raw_data_directory
from .extract_bundle import process_xml_file

LOGGER = logging.getLogger(__name__)
BASE_URL = "http://data.cquest.org/inpi_rncs/comptes/"


def explore_and_process_CQuest_mirror():
    """
    Function that explore CQuest mirror to download every daily zip files
    """
    bundles = sorted(set(list_bundles()) - set(bundle_history(Config.BUNDLE_RAW_DIR)))
    for bundle in bundles:
        fetch_bundle_xmls(bundle, Config.BUNDLE_RAW_DIR)
        bilans = (Config.BUNDLE_RAW_DIR / Path(bundle).stem / "comptes").glob("*.xml")
        for bilan in bilans:
            process_bilan(bilan)
        clean_raw_data_directory(bundle, Config.BUNDLE_RAW_DIR)


def list_bundles():
    """
    List all the zip files present on the platform since 2017
    """
    return sorted(
        chain(*[_bundles_year(year) for year in range(2017, date.today().year + 1)])
    )


def _bundles_year(year: int):
    """
    List all zip file for a given year.
    """
    r = requests.get(os.path.join(BASE_URL, str(year)))
    assert r.status_code == 200
    page = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
    return [x.text for x in page.find_all("a") if x.text.startswith("bilans_")]


def fetch_bundle_xmls(bundle_name: str, savedir: Path):
    """
    Download and unzip a bundle from the platform.

    :param bundle_name:
    Name of the bundle to download

    :param savedir:
    Name of the directory where data is saved.
    """
    LOGGER.info(bundle_name)
    _download_bundle(bundle_name, savedir)
    _unzip_bundle(bundle_name, savedir)


def _download_bundle(bundle_name: Union[str, Path], savedir: Path):
    try:
        year = re.match("bilans_saisis_([0-9]{8}).*.7z", str(bundle_name)).group(1)[:4]
        wget.download(f"{BASE_URL}{year}/{str(bundle_name)}", str(savedir))
    except urllib.error.HTTPError as error:
        LOGGER.error(
            "failed_bundle_download", {"filename": bundle_name, "error": str(error)}
        )
        raise


def _unzip_bundle(bundle_name: str, savedir: Path):
    fn = savedir / bundle_name

    dirname = fn.parent / fn.stem
    dirname.mkdir(exist_ok=True)

    with SevenZipFile(fn, mode="r") as z:
        z.extractall(path=dirname)


def process_bilan(filename: Path):
    """
    Extract bilans from xml files and save data into database
    """
    with open(filename, "rb") as f:
        bytes_io = BytesIO(f.read())
        process_xml_file(bytes_io, filename)
