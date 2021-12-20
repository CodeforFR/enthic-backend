import logging
import sys
from argparse import ArgumentParser
from ftplib import FTP_TLS
from json import load
from os.path import basename, dirname, getsize, join

from ..config import Config
from .bundles_utils import clean_after_importing
from .cquest import explore_and_process_CQuest_mirror
from .extract_bundle import process_daily_zip_file

LOGGER = logging.getLogger(__name__)

with open(
    join(dirname(__file__), "../", "configuration.json")
) as json_configuration_file:
    CONFIG = load(json_configuration_file)

FTP_VOLUME_USED = 0  # Bytes
IMPORT_HISTORIC = []


def explore_and_process_FTP_folder(folderToExplore):
    """
    Recursive function that explore FTP to download every daily zip files

    :param folderToExplore: folder to explore
    """
    global FTP_VOLUME_USED
    LOGGER.LOGGER.info("explore_inpi_ftp_folder", {"filename": folderToExplore})
    ftp = FTP_TLS("opendata-rncs.inpi.fr")
    ftp.login(user=CONFIG["INPI"]["user"], passwd=CONFIG["INPI"]["password"])
    ftp.prot_p()
    connexion = True
    element_list = ftp.nlst(folderToExplore)
    for element in element_list:
        if element.endswith(".zip"):
            daily_zip_date = basename(element)[
                14:
            ]  # remove "bilans_saisis_" filename part.
            daily_zip_date = daily_zip_date[
                : len(daily_zip_date) - 4
            ]  # remove ".zip" filenamepart
            if daily_zip_date in IMPORT_HISTORIC:
                LOGGER.info("Déjà téléchargé en base")
                continue
            if FTP_VOLUME_USED > Config.FTP_MAX_VOLUME:
                LOGGER.info("FTP download volume limit reached, stopping everything")
                sys.exit(3)
            localfile_path = join(CONFIG["inputPath"], basename(element))
            localfile = open(localfile_path, "wb")
            LOGGER.info(
                "Downloading file " + str(element) + " into file " + localfile_path
            )
            ftp.retrbinary("RETR " + element, localfile.write)

            FTP_VOLUME_USED += getsize(localfile_path)
            LOGGER.info("FTP bandwidth used : " + str(FTP_VOLUME_USED))
            print(daily_zip_date)
            # extract data from xml files to csv files
            process_daily_zip_file(localfile_path)
            # add csv to database
            clean_after_importing(localfile_path, daily_zip_date)
        elif element.endswith(".md5"):
            continue
        else:
            if connexion:
                ftp.quit()
                connexion = False
            explore_and_process_FTP_folder(element)

    if connexion:
        ftp.quit()


def parse_args():
    """
    Download INPI's daily file into input folder, as stated in configuration file.
    """
    global IMPORT_HISTORIC

    parser = ArgumentParser(description="Download data and add it to Enthic database")
    parser.add_argument(
        "--source",
        help="get closed etablissement only (default is only opened)",
        choices=["INPI", "CQuest"],
        default="INPI",
        required=True,
    )
    parser.add_argument(
        "--folder", metavar="Folder", help="FTP folder where download should start"
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.source == "INPI":
        if not args.folder:
            raise RuntimeError("Argument 'folder' is mandatory for source 'INPI'")
        explore_and_process_FTP_folder(args.folder)
    elif args.source == "CQuest":
        explore_and_process_CQuest_mirror()


if __name__ == "__main__":
    main()
