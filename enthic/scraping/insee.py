from time import sleep

import requests
from requests.auth import HTTPBasicAuth

from enthic.config import Config

BASE_URL = "https://api.insee.fr/entreprises/sirene/V3/"


class INSEEConnector:
    def __init__(self):
        self.token = None
        self.generate_token()

    def header(self):
        return {"Authorization": f"Bearer {self.token}"}

    def generate_token(self):
        if Config.INSEE_KEY is None or Config.INSEE_SECRET is None:
            raise KeyError("Set environment variables INSEE_KEY and INSEE_SECRET")

        r = requests.post(
            "https://api.insee.fr/token",
            auth=HTTPBasicAuth(Config.INSEE_KEY, Config.INSEE_SECRET),
            data={"grant_type": "client_credentials", "validity_period": 3600 * 24},
            verify=False,
        )
        if r.status_code != 200:
            raise RuntimeError(r.content.decode("utf-8"))
        self.token = r.json()["access_token"]


def request_insee(url: str):
    connector = INSEEConnector()

    response = requests.get(url, headers=connector.header())
    if response.status_code == 401:
        print(f"Erreur 401 for url {url}. Response : {response.text}")
        connector.generate_token()
        response = requests.get(url, headers=connector.header(), verify=True)

    if response.status_code == 429:
        print("Erreur 429 : too many request for INSEE, waiting 1 minutes")
        sleep(61)
        response = requests.get(url, headers=connector.header())

    if response.status_code == 404:
        print(
            f"Erreur 404 de l'INSEE, ça peut être parce que le SIREN n'a pas été trouvé : {response.text}"
        )
        response.status_code = 200

    if response.status_code == 403:
        print(
            "l'erreur 403 de l'INSEE, ça peut être parce que le SIREN n'est pas diffusable"
        )
        response.status_code = 200

    return response


def get_siret_data_from_insee_api(siren):
    """
    Get some data from INSEE API for the given company that sometimes lacks from opendatasoft
        :param siren: the company's siren to search for
    """

    url = BASE_URL + f"siret?q=siren:{siren}"

    response = request_insee(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Error {response.status_code} fetching siret for siren {siren} : {response.text}"
        )

    content = response.json()
    if content["header"]["message"].startswith("Aucun élément trouvé pour") or content[
        "header"
    ]["message"].startswith("Unité légale non diffusable"):
        return None

    etab = content["etablissements"][0]["adresseEtablissement"]
    postal_code = etab["codePostalEtablissement"]
    town = etab["libelleCommuneEtablissement"]
    return postal_code, town


def get_siren_data_from_insee_api(siren):
    """
    Get some data from INSEE  for the given company that sometimes lacks from opendatasoft
    :param siren: the company's siren to search for
    """

    while len(str(siren)) < 9:
        siren = "0" + str(siren)
    url = BASE_URL + f"siren/{siren}"
    response = request_insee(url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Error {response.status_code} fetching siren {siren} : {response.text}"
        )

    content = response.json()
    if "Aucun élément trouvé pour" in content["header"]["message"]:
        return None
    if content["header"]["message"] == f"Unité légale non diffusable ({siren})":
        return None
    code_naf = content["uniteLegale"]["periodesUniteLegale"][0][
        "activitePrincipaleUniteLegale"
    ]
    denomination = content["uniteLegale"]["periodesUniteLegale"][0][
        "denominationUniteLegale"
    ]
    if denomination is None:
        denomination = (
            content["uniteLegale"]["prenomUsuelUniteLegale"]
            + " "
            + content["uniteLegale"]["periodesUniteLegale"][0]["nomUniteLegale"]
        )
    return denomination, code_naf
