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
    benefice_attribue = data["benefice_attribue"]

    # If any values unknown, cannot compute score
    if isnan(impot):
        return -3100
    if impot < 0:
        return -3200
    if isnan(resultat_exploitation):
        return -7100
    if isnan(benefice_attribue):
        benefice_attribue = 0
    if resultat_exploitation + benefice_attribue <= 0:
        return -7200

    if isnan(participation):
        participation = 0
    # Compute score if possible
    shared_part = participation + impot

    total_resultat = resultat_exploitation + benefice_attribue
    result = shared_part / total_resultat

    if result < 0 and participation < 0:
        return -10000

    if result > 10:
        resultat_exceptionnel = data["resultat_exceptionnel"]
        resultat_financier = data["resultat_financier"]
        if isnan(resultat_financier):
            resultat_financier = 0
        if isnan(resultat_exceptionnel):
            resultat_exceptionnel = 0
        if resultat_exceptionnel + resultat_financier > total_resultat:
            return -8000
    if result > 1000:
        return -9999

    return result


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

    if result < 0:
        if charges < 0:
            return -6300
        elif cotisations_sociales < 0:
            return -2300
        elif salaires < 0:
            return -1300

    if result > 2:
        if cotisations_sociales > charges and salaires > charges:
            return -6400
        elif cotisations_sociales > charges:
            return -2500
        elif salaires > charges:
            return -1400
        return -9999

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
    if ratio > 2:
        return -2400
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

    if isnan(benefice_attribue):
        benefice_attribue = 0
    somme_resultats = (
        resultat_financier
        + resultat_exploitation
        + resultat_exceptionnel
        + benefice_attribue
    )

    if somme_resultats <= 0:
        return -9000

    if isnan(participation):
        participation = 0

    result = (participation + impot) / somme_resultats

    if result < 0 and participation < 0:
        return -10000

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

    result = (
        abs(data["produits_exploitation"]) + abs(data["charges_exploitation"])
    ) / (
        abs(data["produits_exploitation"])
        + abs(data["charges_exploitation"])
        + abs(data["produits_exceptionnel"])
        + abs(data["charges_exceptionnel"])
        + abs(data["produits_financier"])
        + abs(data["charges_financier"])
    )

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


# SELECT * FROM `annual_statistics` where stats_type != 4 and value not in (-4300, -6300, -6100, -6200, -5100, -1000, -1100, -1200, -1300, -2000, -2100, -2200, -2300, -2400, -2500, -3100, -3200, -4100, -4200, -4300, -1400, -6400, -7100, -7200, -8000, -9000, -9999, -10000) ORDER BY `annual_statistics`.`value`  ASC;
