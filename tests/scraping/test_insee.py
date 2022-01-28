from unittest.mock import patch

import pytest

from enthic.scraping.insee import BASE_URL, get_siret_data_from_insee_api


@pytest.fixture(autouse=True)
def token_generation_mock():
    with patch("enthic.scraping.insee.INSEEConnector.generate_token") as api_mock:
        api_mock.return_value = None
        yield api_mock


class TestINSEESiret:
    def test_error_error_api(self, requests_mock):
        requests_mock.get(f"{BASE_URL}siret?q=siren:2", status_code=406)
        with pytest.raises(RuntimeError) as excinfo:
            get_siret_data_from_insee_api(2)
        assert str(excinfo.value).startswith("Error fetching siret for siren 2")

    def test_error_unknown_siren(self, requests_mock):
        requests_mock.get(
            f"{BASE_URL}siret?q=siren:4",
            json={"header": {"message": "Aucun élément trouvé pour le siren "}},
        )
        assert get_siret_data_from_insee_api(4) is None

    def test_error_non_diffusable(self, requests_mock):
        requests_mock.get(
            f"{BASE_URL}siret?q=siren:3",
            json={"header": {"message": "Unité légale non diffusable"}},
        )
        assert get_siret_data_from_insee_api(3) is None

    def test_siret_found(self, requests_mock):
        requests_mock.get(
            f"{BASE_URL}siret?q=siren:1",
            status_code=200,
            json={
                "header": {"message": ""},
                "etablissements": [
                    {
                        "adresseEtablissement": {
                            "codePostalEtablissement": "20132",
                            "libelleCommuneEtablissement": "CITY",
                        }
                    }
                ],
            },
        )

        postcode, town = get_siret_data_from_insee_api(1)
        assert postcode == "20132"
        assert town == "CITY"
