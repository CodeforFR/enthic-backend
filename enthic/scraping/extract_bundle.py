import datetime
import json
import logging
from csv import reader
from io import BytesIO
from logging import debug, info
from os import listdir
from os.path import dirname, join
from pathlib import Path
from re import compile, sub
from zipfile import BadZipFile, ZipFile

from enthic.scraping.insee import (
    get_siren_data_from_insee_api,
    get_siret_data_from_insee_api,
)
from enthic.scraping.liasse import Liasse, parse_xml_liasse, read_address_data
from enthic.utils.ape_utils import APE_CONVERSION
from enthic.utils.bundle_utils import ACCOUNTING_TYPE_CONVERSION, BUNDLE_CONVERSION
from enthic.utils.INPI_data_enhancer import decrypt_code_motif

from .accountability_metadata import AccountabilityMetadata, MetadataCase
from .database_requests_utils import (
    get_metadata,
    replace_bundle_into_database,
    replace_metadata_ORM,
    save_bundle_to_database,
    save_company_to_database,
    save_metadata_ORM,
    sum_bundle_into_database,
)

RE_DENOMINATION = compile(r"\s+|[\t\n]|\xEF")  # NOT AN OBVIOUS PERFORMANCE GAIN...
LOGGER = logging.getLogger(__name__)

with open(
    join(dirname(__file__), "../", "configuration.json")
) as json_configuration_file:
    CONFIG = json.load(json_configuration_file)

ACC_ONT = {}  # EMPTY OBJECT STORING DATA TO EXTRACT
with open(Path(__file__).parents[2] / "references" / "account-ontology.csv") as infile:
    _reader = reader(infile, delimiter=";")
    next(_reader, None)  # SKIP FIRST LINE, HEADER OF THE CSV
    for rows in _reader:  # ITERATES ALL THE LINES
        try:
            ACC_ONT[rows[3]]["bundleCodeAtt"].append({rows[1]: rows[2].split(",")})
        except KeyError:
            ACC_ONT[rows[3]] = {"bundleCodeAtt": []}


KNOWN_ADDRESS_ERRORS = ["0 | Durée de L'exercice précédentI"]


# Dict for conversion of APE code from NAF rév. 1 to NAF rév. 2 (source from https://www.insee.fr/fr/information/2579599)
with open(Path(__file__).parents[2] / "references" / "naf_transition.json") as f:
    old_naf_to_new_naf = json.load(f)


def read_identity_data(identity_xml_item, xml_file_name):
    """
    Read the xml's identity item, to extract useful data from it

       :param identity_xml_item: the identity XMl object
       :return: extracted data as a tuple
    """
    (
        acc_type,
        siren,
        denomination,
        year,
        ape,
        postal_code,
        town,
        code_motif,
        info_traitement,
        code_confidentialite,
        duree_exercice,
        date_cloture_exercice,
    ) = (None,) * 12

    unknown_ape_codes = ["00.00Z", "00.0Z", "00.000", "00.097"]
    for identity in identity_xml_item:  # identite LEVEL
        if identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}siren":
            siren = int(identity.text)
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}code_type_bilan":
            acc_type = identity.text
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}denomination":
            # If denomination contain weird character, get denomination from INSEE's API
            if (
                "�" in identity.text
                or "�" in identity.text
                or "�" in identity.text
                or "" in identity.text
                or "�" in identity.text
                or "µ" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
                or "" in identity.text
            ):
                identity.text, dummy = get_siren_data_from_insee_api(siren)
            # REMOVE MULTIPLE WHITESPACES, TABULATION, NEW LINE, THEN SWITCH TO UPPER CASE
            denomination = sub(RE_DENOMINATION, " ", identity.text).strip(" ").upper()
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}code_motif":
            code_motif = decrypt_code_motif(identity.text)
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}code_confidentialite":
            code_confidentialite = int(identity.text)
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}info_traitement":
            info_traitement = identity.text.replace(" ", "") if identity.text else None
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}date_cloture_exercice":
            date_cloture_exercice = datetime.datetime.strptime(
                identity.text, "%Y%m%d"
            ).date()
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}adresse":
            postal_code, town = read_address_data(identity.text)
            if len(str(postal_code)) > 5:
                result = get_siret_data_from_insee_api(siren)
                if result:
                    postal_code, town = result
                else:
                    postal_code = postal_code[:5]
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}duree_exercice_n":
            duree_exercice = int(identity.text)
        elif identity.tag == "{fr:inpi:odrncs:bilansSaisisXML}code_activite":
            ape_with_dot = identity.text[:2] + "." + identity.text[2:]
            if (
                ape_with_dot in APE_CONVERSION
            ):  # Find enthic integer from given ape code
                ape = str(APE_CONVERSION[ape_with_dot])
            elif (
                ape_with_dot in old_naf_to_new_naf
            ):  # Try to convert given apecode from old naf to new naf
                ape = str(APE_CONVERSION[old_naf_to_new_naf[ape_with_dot]])
            else:  # Try to fetch ape code from INSEE's API
                ape_from_insee = None
                try:
                    dummy, ape_from_insee = get_siren_data_from_insee_api(siren)
                except TypeError:
                    print(
                        "Le numéro siren", siren, "n'est pas dispo via l'API de l'INSEE"
                    )
                if ape_from_insee in APE_CONVERSION:
                    ape = str(APE_CONVERSION[ape_from_insee])
                elif ape_from_insee in old_naf_to_new_naf:
                    ape = str(APE_CONVERSION[old_naf_to_new_naf[ape_from_insee]])
                elif (
                    ape_from_insee in unknown_ape_codes
                    or ape_with_dot in unknown_ape_codes
                ):
                    ape = str(APE_CONVERSION["00.00"])
                else:
                    print(
                        "N'a pas pu trouvé le code APE correspondant à celui du XML (",
                        ape_with_dot,
                        ") ou de l'INSEE (",
                        ape_from_insee,
                        ") from xmlfile",
                        xml_file_name,
                    )
                    exit()

    if (
        duree_exercice <= date_cloture_exercice.month
        or duree_exercice - date_cloture_exercice.month <= date_cloture_exercice.month
    ):
        year = date_cloture_exercice.year
    else:
        year = date_cloture_exercice.year - 1

    return (
        acc_type,
        siren,
        denomination,
        year,
        ape,
        postal_code,
        town,
        code_motif,
        code_confidentialite,
        info_traitement,
        duree_exercice,
        date_cloture_exercice,
    )


def process_xml_file(xml: str, xml_name: str):
    liasse = parse_xml_liasse(xml)
    if not liasse["bilan"]:
        LOGGER.warning(
            "No data extracted",
            extra={"siren": liasse["siren"], "cloture": liasse["cloture"].isoformat()},
        )
        return
    metadata_status = _update_metadata(liasse)
    _save_accountability(metadata_status, liasse)


def _update_metadata(liasse: Liasse):
    # Add order by and get last only
    # add selection on year
    existing_metadata = get_metadata(liasse["siren"])
    if not existing_metadata:
        save_company_to_database(**liasse._to_identity())
        return MetadataCase.IS_NEW

    metadata = AccountabilityMetadata.from_liasse(liasse)
    status = metadata.compare(existing_metadata)

    if status == MetadataCase.IGNORE:
        return status

    if status == MetadataCase.REPLACE:
        replace_metadata_ORM(metadata, existing_metadata)
    else:
        save_metadata_ORM(metadata)
    return status


def _save_accountability(status, liasse):
    opts = dict(
        siren=liasse["siren"],
        declaration=liasse["year"],
        accountability=str(ACCOUNTING_TYPE_CONVERSION[liasse["type_bilan"]]),
    )
    for code, amount in liasse["bilan"].items():
        bundle = str(
            BUNDLE_CONVERSION[ACCOUNTING_TYPE_CONVERSION[liasse["type_bilan"]]][code]
        )
        amount = str(int(amount))
        if status == MetadataCase.COMPLEMENTARY:
            sum_bundle_into_database(bundle=bundle, amount=amount, **opts)
        elif status == MetadataCase.REPLACE:
            replace_bundle_into_database(
                bundle=bundle, amount=amount, add_detail_mode=False, **opts
            )
        elif status == MetadataCase.IS_NEW:
            save_bundle_to_database(bundle=bundle, amount=amount, **opts)


def process_daily_zip_file(daily_zip_file_path):
    try:  # SOME BAD ZIP FILES ARE IN THE DATASET
        input_zip = ZipFile(daily_zip_file_path)
        for zipped_xml_name in input_zip.namelist():  # LIST ARCHIVES IN ZIP
            try:
                zipped_xml = ZipFile(BytesIO(input_zip.read(zipped_xml_name)))
                # SUPPOSED ONLY ONE XML BUT ITERATE TO BE SURE
                for xml in zipped_xml.namelist():
                    process_xml_file(
                        BytesIO(zipped_xml.open(xml).read()), zipped_xml_name
                    )
            except UnicodeDecodeError as error:
                debug(error)
    except BadZipFile as error:  #  TODO REPORT ERROR TO INPI
        info(error)
        exit()


def main():
    """
    Based on the configuration storing the input file path. All the xml are
    read to list the bundle code.
    """
    ############################################################################
    # CREATING A LIST OF THE BUNDLE XML CODES, ZIP ARE READ IN BtesIO, IN ORDER
    # TO BREAK FILE SYSTEM. TOO MUCH ZIP DISTURB THE FS.
    for file in listdir(CONFIG["inputPath"]):  # LIST INPUT FILES
        info("processing INPI daily zip file %s", file)
        if file.endswith(".zip"):  # ONLY PROCESS ZIP FILES
            process_daily_zip_file(join(CONFIG["inputPath"], file))


if __name__ == "__main__":
    main()  # ONLY IF EXECUTED NOT WHEN IMPORTED
