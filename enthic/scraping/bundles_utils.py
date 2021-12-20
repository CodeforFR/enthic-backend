import os
import shutil
from enum import Enum, auto
from glob import glob
from json import load
from os.path import dirname, join
from pathlib import Path

import numpy as np
from deprecated import deprecated

IMPORT_HISTORIC = []

with open(
    join(dirname(__file__), "../", "configuration.json")
) as json_configuration_file:
    CONFIG = load(json_configuration_file)


class ModifiedData(Enum):
    """Enum used to replace or insert data in CSV"""

    ABSENT = auto()
    WRONG_FORMAT = auto()


@deprecated(reason="use clean_raw_data_directory")
def clean_after_importing(file_path, date_processed):
    """
    Add data contained in the given file into MySQL database
    then delete temporary files if it's a success
    :param file_path: daily INPI file to add to database
    """

    try:
        shutil.rmtree(CONFIG["inputPath"] + "/comptes")
    except FileNotFoundError:
        pass
    files = glob(CONFIG["inputPath"] + "/PUB_CA*")
    for f in files:
        os.remove(f)

    os.remove(file_path)
    IMPORT_HISTORIC.append(date_processed)
    with open(
        join(CONFIG["inputPath"], CONFIG["importHistoricFile"]), "a"
    ) as import_historic_file:
        import_historic_file.write(date_processed + "\n")


def bundle_history(savedir):
    fn = savedir / "bundle_history.txt"
    return np.loadtxt(fn, dtype=str, ndmin=1)


def clean_raw_data_directory(bundle_name: str, savedir: Path):
    """
    Remove raw files and save the information into store

    :param bundle_name:
    Name of the bundle to clean

    :param savedir:
    Directory where raw data are stored
    """
    _save_to_history(bundle_name, savedir)
    os.remove(savedir / bundle_name)

    dirname = savedir / Path(bundle_name).stem
    shutil.rmtree(dirname)


def _save_to_history(bundle_name: str, savedir: Path):
    """
    Keep track of the bundle_name in the store.
    """
    store_fn = savedir / "bundle_history.txt"
    with store_fn.open("a") as f:
        f.write(Path(bundle_name).name + "\n")
