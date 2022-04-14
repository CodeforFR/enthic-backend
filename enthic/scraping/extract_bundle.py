import datetime
import json
import logging
import xml.etree.ElementTree as ElementTree
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
from enthic.scraping.liasse import read_address_data
from enthic.utils.ape_utils import APE_CONVERSION
from enthic.utils.bundle_utils import ACCOUNTING_TYPE_CONVERSION, BUNDLE_CONVERSION
from enthic.utils.INPI_data_enhancer import decrypt_code_motif

from .accountability_metadata import AccountabilityMetadata, MetadataCase
from .database_requests_utils import (
    SESSION,
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


def process_xml_file(xml_stream, xml_name):
    """
    Process an xml file already opened
    """
    ####################################################
    # XML PARSER
    try:
        tree = ElementTree.parse(xml_stream)
    except ElementTree.ParseError as error:
        info("Error processing XML " + xml_name + f" : {error}")
        return False
    root = tree.getroot()
    ####################################################
    # XML RELATED VARIABLES
    acc_type, siren, year = (None,) * 3
    ####################################################
    # ITERATE ALL TAGS
    metadata_case = MetadataCase.IS_NEW
    bundles_added_set = set()
    for child in root[0]:
        ################################################
        # IDENTITY TAGS, SIREN AND TYPE OF ACCOUNTABILITY
        if child.tag == "{fr:inpi:odrncs:bilansSaisisXML}identite":
            (
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
            ) = read_identity_data(child, xml_name)
            ############################################
            # WRITE IDENTITY FILE IF ACCOUNT TYPE IS
            # KNOWN
            if acc_type not in ACC_ONT.keys():
                return False
            existing_metadata_list = get_metadata(siren)
            new_metadata = AccountabilityMetadata(
                siren=siren,
                declaration=year,
                duree_exercice=duree_exercice,
                date_cloture_exercice=date_cloture_exercice,
                code_motif=code_motif,
                code_confidentialite=code_confidentialite,
                info_traitement=info_traitement,
                accountability=acc_type,
            )

            metadata_to_replace = None
            for existing_metadata in existing_metadata_list:
                result = new_metadata.compare(existing_metadata)
                if result == MetadataCase.IGNORE:
                    return False
                if result == MetadataCase.REPLACE:
                    metadata_to_replace = existing_metadata
                    metadata_case = result
                if (
                    result != MetadataCase.IS_NEW
                    and metadata_case != MetadataCase.REPLACE
                ):
                    metadata_case = result

            if len(existing_metadata_list) == 0:
                save_company_to_database(
                    str(siren), str(denomination), str(ape), str(postal_code), str(town)
                )
            else:
                print(
                    "New metadata",
                    new_metadata,
                    "different des metadata déjà en base. Action choisie :",
                    metadata_case,
                )

            if metadata_case == MetadataCase.REPLACE:
                replace_metadata_ORM(new_metadata, metadata_to_replace)
            else:
                save_metadata_ORM(new_metadata)
        ################################################
        # BUNDLE TAGS IN PAGES TO ITERATE WITH BUNDLE CODES
        # AND AMOUNT
        elif child.tag == "{fr:inpi:odrncs:bilansSaisisXML}detail":
            for page in child:
                for bundle in page:
                    try:
                        for bundle_code in ACC_ONT[acc_type]["bundleCodeAtt"]:
                            if bundle.attrib["code"] in bundle_code.keys():
                                for amount_code in bundle_code[bundle.attrib["code"]]:
                                    amount_code = f"m{amount_code}"
                                    if metadata_case == MetadataCase.COMPLEMENTARY:
                                        sum_bundle_into_database(
                                            siren,
                                            str(year),
                                            str(ACCOUNTING_TYPE_CONVERSION[acc_type]),
                                            str(
                                                BUNDLE_CONVERSION[
                                                    ACCOUNTING_TYPE_CONVERSION[acc_type]
                                                ][bundle.attrib["code"]]
                                            ),
                                            str(int(bundle.attrib[amount_code])),
                                        )
                                    elif metadata_case == MetadataCase.REPLACE:
                                        replace_bundle_into_database(
                                            siren,
                                            str(year),
                                            str(ACCOUNTING_TYPE_CONVERSION[acc_type]),
                                            str(
                                                BUNDLE_CONVERSION[
                                                    ACCOUNTING_TYPE_CONVERSION[acc_type]
                                                ][bundle.attrib["code"]]
                                            ),
                                            str(int(bundle.attrib[amount_code])),
                                            False,
                                        )
                                    elif metadata_case == MetadataCase.IS_NEW:
                                        new_bundle = (
                                            siren,
                                            str(year),
                                            str(ACCOUNTING_TYPE_CONVERSION[acc_type]),
                                            str(
                                                BUNDLE_CONVERSION[
                                                    ACCOUNTING_TYPE_CONVERSION[acc_type]
                                                ][bundle.attrib["code"]]
                                            ),
                                            str(int(bundle.attrib[amount_code])),
                                        )
                                        if new_bundle[:4] in bundles_added_set:
                                            print(
                                                "Bundle",
                                                new_bundle,
                                                "en double dans le fichier XML",
                                            )
                                        else:
                                            bundles_added_set.add(new_bundle[:4])
                                            save_bundle_to_database(
                                                new_bundle[0],
                                                new_bundle[1],
                                                new_bundle[2],
                                                new_bundle[3],
                                                new_bundle[4],
                                            )
                    except KeyError as key_error:
                        debug(
                            "{} in account {} bundle {}".format(
                                key_error, acc_type, bundle.attrib["code"]
                            )
                        )
    SESSION.commit()
    return True


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
