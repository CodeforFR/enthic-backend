from enthic.ontology import ONTOLOGY

# CREATE DICTIONARY FROM ONTOLOGY TO CONVERT str TO int
ACCOUNTING_TYPE_CONVERSION = {}
for key, value in ONTOLOGY["accounting"].items():
    ACCOUNTING_TYPE_CONVERSION[value[0]] = key

BUNDLE_CONVERSION = {}
for key, value in ONTOLOGY["accounting"].items():
    BUNDLE_CONVERSION[key] = {}
    for int_bundle, dict_bun in value["code"].items():
        try:
            BUNDLE_CONVERSION[key][dict_bun[0]] = int_bundle
        except KeyError:
            continue
