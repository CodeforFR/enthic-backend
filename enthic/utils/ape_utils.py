import re

from enthic.ontology import APE_CODE
from enthic.utils.json_response import JSONGenKey

# CREATE DICTIONARY WHERE keys ARE 'official APE code' AND values ARE 'enthic APE code'
APE_CONVERSION = {}
for key, value in APE_CODE.items():
    APE_CONVERSION[value[0]] = key


def get_corresponding_ape_codes(ape_codes):
    """
    APE codes are not saved in the original format.
    This function returns codes that are in the database
    and corresponds to the given APE code or it's sub-categories
    It returns None if the given APE code does not exist

        :param ape_code : the list of APE for the filter, comma separated

        :return: list of corresponding APE_CODE in database
    """
    result = list()
    for one_code in ape_codes.split(","):
        for i in APE_CODE:
            if re.match(one_code, APE_CODE[i][0]):
                result.append(i)
    if not result:
        return None
    return result


def get_json_ape_description(enthic_ape):
    try:
        return {
            JSONGenKey.VALUE: APE_CODE[enthic_ape][1],
            JSONGenKey.DESCRIPTION: "Code Activité Principale Exercée (NAF)",
            JSONGenKey.CODE: APE_CODE[enthic_ape][0],
        }
    except KeyError:
        return {
            JSONGenKey.VALUE: f"{enthic_ape}, Code APE inconnu",
            JSONGenKey.DESCRIPTION: "Code Activité Principale Exercée (NAF)",
        }
