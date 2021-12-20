import logging
import re
from datetime import date, datetime

from bs4 import BeautifulSoup

from enthic import ontology
from enthic.scraping.bundles_utils import ModifiedData
from enthic.utils.conversion import CON_APE
from enthic.utils.INPI_data_enhancer import decrypt_code_motif

LOGGER = logging.getLogger(__name__)
RE_POSTAL_CODE_TOWN = re.compile(
    r"([0-9]+)[ -]?¨?([a-zA-Z0-9`ÀéÉèÈîÎ_ \'\"-\.\(\)\-]+)"
)


class Liasse(dict):
    def _to_identity(self):
        properties = ["siren", "denomination", "ape", "postal_code", "town"]
        return {k: self[k] for k in properties}


def parse_xml_liasse(xml: str) -> Liasse:
    soup = BeautifulSoup(xml, "lxml")
    identity = _parse_identity(soup)
    bilan = _parse_bilan(soup, identity["type_bilan"])
    return Liasse({"bilan": bilan, **identity})


def _parse_identity(soup: BeautifulSoup) -> dict:
    id_block = soup.find("identite")
    properties_def = [
        ("siren", None, lambda x: str(x).zfill(9)),
        ("date_cloture_exercice", "cloture", _to_date),
        ("code_greffe", None, int),
        ("num_depot", None, str),
        ("num_gestion", None, str),
        ("code_activite", "naf8", lambda s: s.replace(".", "")),
        ("duree_exercice_n", "duree_exercice", int),
        ("date_depot", None, _to_date),
        ("code_motif", None, decrypt_code_motif),
        ("code_type_bilan", "type_bilan", str),
        ("code_devise", None, str),
        ("code_origine_devise", None, str),
        ("code_confidentialite", None, int),
        ("denomination", None, _extract_cdata),
        ("adresse", None, _extract_cdata),
        ("info_traitement", None, lambda x: x.replace(" ", "") if x else None),
    ]
    properties = {
        rename or name: fct(_element_text(id_block, name))
        for name, rename, fct in properties_def
    }
    properties["ape"] = str(
        CON_APE.get(properties["naf8"][:2] + "." + properties["naf8"][2:], -1)
    )
    properties["year"] = int(properties["cloture"].year)
    properties["postal_code"], properties["town"] = read_address_data(
        properties["adresse"]
    )
    return properties


def _element_text(soup: BeautifulSoup, key: str) -> str:
    element = soup.find(key)
    return element.text if element else None


def _to_date(s: str) -> date:
    return datetime.strptime(s, "%Y%m%d").date()


def _extract_cdata(x):
    matching = re.match(r"<\!\[CDATA\[(.*)\]\]>", x)
    if matching:
        return matching.group(1)
    return x


def read_address_data(address_xml_item: str):
    """
     Extract postal_code and town from xml adresse field

    :param address_xml_item: the identity's address XMl object
    """
    postal_code, town = (ModifiedData.ABSENT.value,) * 2
    try:
        regex_match = RE_POSTAL_CODE_TOWN.match(address_xml_item)
        postal_code = regex_match.group(1)
        town = regex_match.group(2).upper()
        if not town.strip():
            postal_code, town = (ModifiedData.WRONG_FORMAT.value,) * 2
    except TypeError as error:
        debug(f"{str(error)}: {str(address_xml_item)}")
        postal_code, town = (ModifiedData.WRONG_FORMAT.value,) * 2
    except AttributeError as error:
        try:
            debug(f"{str(error)}: {str(address_xml_item)}")
            regex_match = RE_TOWN.match(address_xml_item)
            town = regex_match.group(1).upper()
            postal_code = ModifiedData.WRONG_FORMAT.value
        except AttributeError as error:
            try:
                debug(f"{str(error)}: {str(address_xml_item)}")
                regex_match = RE_POSTAL_CODE.match(address_xml_item)
                town = ModifiedData.WRONG_FORMAT.value
                postal_code = regex_match.group(1)
            except AttributeError as error:
                debug(f"{str(error)}: {str(address_xml_item)}")
                postal_code, town = (ModifiedData.WRONG_FORMAT.value,) * 2

    return postal_code, town


def _parse_bilan(soup: BeautifulSoup, type_bilan: str) -> dict:
    bilan = soup.find("detail")
    if bilan is None:
        return {}

    fields = (
        ontology.read_account()
        .pipe(lambda df: df[df["accountability"] == type_bilan])
        .to_dict(orient="records")
    )

    values = [_get_field_amount(bilan, field) for field in fields]

    return {code: amount for code, amount in values if amount is not None}


def _get_field_amount(bilan: BeautifulSoup, field: dict) -> dict:
    element = bilan.find("liasse", {"code": field["code"]})
    if not element:
        return field["code"], None
    column = field["column"]
    amount = element.get(f"m{column}")
    return field["code"], amount if amount is None else int(amount)
