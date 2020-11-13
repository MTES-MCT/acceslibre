import json

DPT_BDR = {"code": "13", "nom": "Bouches-du-Rhône"}
DPT_PARIS = {"code": "75", "nom": "Paris"}
DPT_RHONE = {"code": "69", "nom": "Rhône"}


LYON = [
    {
        "code": "69381",
        "nom": "Lyon 1er arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69383",
        "nom": "Lyon 3ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69382",
        "nom": "Lyon 2ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69384",
        "nom": "Lyon 4ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69385",
        "nom": "Lyon 5ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69386",
        "nom": "Lyon 6ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69387",
        "nom": "Lyon 7ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69388",
        "nom": "Lyon 8ème arr.",
        "departement": DPT_RHONE,
    },
    {
        "code": "69389",
        "nom": "Lyon 9ème arr.",
        "departement": DPT_RHONE,
    },
]

MARSEILLE = [
    {
        "code": "13201",
        "nom": "Marseille 1ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13202",
        "nom": "Marseille 2ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13203",
        "nom": "Marseille 3ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13204",
        "nom": "Marseille 4ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13205",
        "nom": "Marseille 5ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13206",
        "nom": "Marseille 6ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13207",
        "nom": "Marseille 7ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13208",
        "nom": "Marseille 8ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13209",
        "nom": "Marseille 9ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13210",
        "nom": "Marseille 10ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13211",
        "nom": "Marseille 11ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13212",
        "nom": "Marseille 12ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13213",
        "nom": "Marseille 13ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13214",
        "nom": "Marseille 14ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13215",
        "nom": "Marseille 15ème arr.",
        "departement": DPT_BDR,
    },
    {
        "code": "13216",
        "nom": "Marseille 16ème arr.",
        "departement": DPT_BDR,
    },
]

PARIS = [
    {
        "code": "75101",
        "nom": "Paris 1er arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75102",
        "nom": "Paris 2eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75103",
        "nom": "Paris 3eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75104",
        "nom": "Paris 4eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75105",
        "nom": "Paris 5eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75106",
        "nom": "Paris 6eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75107",
        "nom": "Paris 7eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75108",
        "nom": "Paris 8eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75109",
        "nom": "Paris 9eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75110",
        "nom": "Paris 10eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75111",
        "nom": "Paris 11eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75112",
        "nom": "Paris 12eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75113",
        "nom": "Paris 13eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75114",
        "nom": "Paris 14eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75115",
        "nom": "Paris 15eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75116",
        "nom": "Paris 16eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75117",
        "nom": "Paris 17eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75118",
        "nom": "Paris 18eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75119",
        "nom": "Paris 19eme arr.",
        "departement": DPT_PARIS,
    },
    {
        "code": "75120",
        "nom": "Paris 20eme arr.",
        "departement": DPT_PARIS,
    },
]


def get_by_code_insee(code_insee):
    all = LYON + MARSEILLE + PARIS
    return next((x for x in all if x["code"] == str(code_insee)), None)


def to_json():
    return json.dumps({"Paris": PARIS, "Marseille": MARSEILLE, "Lyon": LYON})
