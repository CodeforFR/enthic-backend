from math import isnan


def compute_exploitation_share(data):
    """
    Computes the share score of given data

        :param data: dictionary containing all needed values
        :return: share score value, or NaN if it cannot be computed
    """
    # Retrieve needed values
    participation = data["participation"]
    impot = data["impot"]
    resultat_exploitation = data["resultat_exploitation"]

    # If any values unknown, cannot compute score
    if isnan(impot):
        return -3100
    if impot < 0:
        return -3200
    if (
        any(isnan(value) for value in [resultat_exploitation])
        or resultat_exploitation < 0
    ):
        return float("nan")

    if isnan(participation):
        participation = 0
    # Compute score if possible
    shared_part = participation + impot
    if resultat_exploitation > 0:
        return shared_part / resultat_exploitation

    return float("nan")


def compute_overall_wages_weight(data):
    """
    Computes part of wages in whole company's costs

        :param data: dictionary containing all needed values
        :return: wages part of company's costs, or NaN if it cannot be computed
    """
    cotisations_sociales = data["cotisations_sociales"]
    salaires = data["salaires"]
    charges = data["charges"]

    if isnan(charges):
        return -6100
    if charges == 0:
        return -6200
    if isnan(salaires) and isnan(cotisations_sociales):
        return float("nan")

    if isnan(salaires):
        salaires = 0
    elif isnan(cotisations_sociales):
        cotisations_sociales = 0

    result = (salaires + cotisations_sociales) / charges

    if result < 0 and charges < 0:
        return -6300

    return result


def compute_wage_quality(data):
    """
    Computes ratio between 'cotisations' and wages

    :param data: dictionary containing all needed values
    :return: the score, or NaN if they cannot be computed
    """
    cotisations_sociales = data["cotisations_sociales"]
    salaires = data["salaires"]

    if isnan(salaires):
        return -1100
    elif isnan(cotisations_sociales):
        return -2100
    elif salaires == 0:
        return -1200
    elif cotisations_sociales == 0:
        return -2200

    ratio = cotisations_sociales / salaires
    if ratio > 1000:
        if cotisations_sociales < data["charges_exploitation"]:
            ratio = -1000
        if cotisations_sociales > data["charges_exploitation"]:
            ratio = -2000

    if ratio < 0:
        if salaires < 0:
            return -1300
        if cotisations_sociales < 0:
            return -2300
    return ratio


def compute_average_wage(data):
    """
    Computes the average wage

    :param data: dictionary containing all needed values
    :return: average wage value, or NaN if it cannot be computed
    """
    salaires = data["salaires"]
    effectifs = data["effectifs"]

    if isnan(effectifs):
        return -4100
    if effectifs == 0:
        return -4200
    if effectifs < 0:
        return -4300
    if isnan(salaires):
        return -1100
    if salaires < 0:
        return -1300

    return salaires / effectifs


def compute_profit_sharing(data):
    """
    Computes profit's part shared with State and employees

    :param data: dictionary containing all needed values
    :return: part of profit shared, or NaN if it cannot be computed
    """
    participation = data["participation"]
    impot = data["impot"]
    resultat_exceptionnel = data["resultat_exceptionnel"]
    resultat_financier = data["resultat_financier"]
    resultat_exploitation = data["resultat_exploitation"]
    benefice_attribue = data["benefice_attribue"]

    if isnan(impot):
        return -3100
    if impot < 0:
        return -3200
    if any(
        isnan(value)
        for value in [
            resultat_financier,
            resultat_exceptionnel,
            resultat_exploitation,
        ]
    ):
        return float("nan")

    somme_resultats = resultat_financier + resultat_exploitation + resultat_exceptionnel
    if somme_resultats == 0:
        return float("nan")

    if isnan(participation):
        participation = 0

    result = (participation + impot) / somme_resultats
    if result < 0 and not isnan(benefice_attribue) and benefice_attribue > 0:
        return -5100

    return result


def compute_exploitation_part(data):
    """
    Computes part for exploitation in company's 'compte de résultat'

    :param data: dictionary containing all needed values
    :return: part of exploitation, or NaN if it cannot be computed
    """

    if any(
        isnan(value)
        for value in [
            data["produits_exploitation"],
            data["charges_exploitation"],
            data["produits_exceptionnel"],
            data["charges_exceptionnel"],
            data["produits_financier"],
            data["charges_financier"],
        ]
    ):
        return float("nan")

    if (
        data["produits_exploitation"]
        + data["charges_exploitation"]
        + data["produits_exceptionnel"]
        + data["charges_exceptionnel"]
        + data["produits_financier"]
        + data["charges_financier"]
    ) == 0:
        return float("nan")

    result = (data["produits_exploitation"] + data["charges_exploitation"]) / (
        data["produits_exploitation"]
        + data["charges_exploitation"]
        + data["produits_exceptionnel"]
        + data["charges_exceptionnel"]
        + data["produits_financier"]
        + data["charges_financier"]
    )
    if result < 0:
        if data["charges_exploitation"] < 0:
            return -6300
    return result


def compute_data_availability(data):
    """
    Computes if data are available

    :param data: dictionary containing all needed values
    :return: data availability
    """

    data_available = 0
    for datum in data:
        if not isnan(data[datum]):
            data_available += 1

    return data_available / len(data)
