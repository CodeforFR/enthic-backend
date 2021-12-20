import shutil
import tempfile
from datetime import date
from pathlib import Path

import pytest

from enthic.scraping.bundles_utils import ModifiedData
from enthic.scraping.cquest import _unzip_bundle
from enthic.scraping.liasse import parse_xml_liasse, read_address_data


@pytest.fixture(scope="session")
def standard_xml():
    bundle_fn = Path(__file__).parent / "fixtures" / "bundles.7z"
    with tempfile.TemporaryDirectory() as savedir:
        savedir = Path(savedir)
        shutil.copyfile(bundle_fn, savedir / "bilans_saisis_20210101.7z")
        _unzip_bundle("bilans_saisis_20210101.7z", savedir)

        comptes = (
            savedir
            / "bilans_saisis_20210101"
            / "comptes"
            / "PUB_CA_483935326_1303_2013D00195_2015_1048.donnees.xml"
        )

        with open(comptes) as f:
            return f.read()


def test_parse_bilan_metadata_from_xml(standard_xml):
    liasse = parse_xml_liasse(standard_xml)

    assert liasse["siren"] == "483935326"
    assert liasse["cloture"] == date(2015, 12, 31)
    assert liasse["code_greffe"] == 1303
    assert liasse["num_depot"] == "1048"
    assert liasse["num_gestion"] == "2013D00195"
    assert liasse["naf8"] == "8622C"
    assert liasse["duree_exercice"] == 12
    assert liasse["date_depot"] == date(2017, 2, 18)
    assert liasse["code_motif"] == "0"
    assert liasse["type_bilan"] == "C"
    assert liasse["code_devise"] == "EUR"
    assert liasse["code_origine_devise"] == "O"
    assert liasse["code_confidentialite"] == 0
    assert liasse["denomination"] == "SELARL UCI VISTA"
    assert liasse["adresse"] == "13008 MARSEILLE"
    assert liasse["info_traitement"] is None
    assert liasse["postal_code"] == "13008"
    assert liasse["town"] == "MARSEILLE"
    assert liasse["year"] == 2015


def test_parse_bilan_indicators_from_xml(standard_xml):
    liasse = parse_xml_liasse(standard_xml)
    assert len(liasse["bilan"]) == 27
    assert "ZE" not in liasse["bilan"]
    assert liasse["bilan"]["FJ"] == 4549159


class TestReadAddress:
    def test_read_adresse_with_simple_postcode_town(self):
        inp = "13830 RANDOM CITY"
        postcode, town = read_address_data(inp)
        assert postcode == "13830"
        assert town == "RANDOM CITY"

    def test_read_adresse_with_badly_formatted_string(self):
        inp = "SASU PATRICE MAZET"
        postcode, town = read_address_data(inp)
        print(postcode, town)
        assert (postcode, town) == (ModifiedData.WRONG_FORMAT.value,) * 2
