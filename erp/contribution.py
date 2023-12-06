from .schema import RAMPE_AMOVIBLE, RAMPE_AUCUNE, RAMPE_FIXE, UNKNOWN

# TODO remove me ?
UNIQUE_ANSWER = "unique"

FORM_QUESTION = {
    "question": "Il y a-t-il une rampe d'accès pour entrer dans l'établissement",
    "type": UNIQUE_ANSWER,
    "answers": [
        {
            "label": "Rampe fixe",
            "picture": "ramp.jpg",
            "modelisation": [
                {
                    "field": "cheminement_ext_rampe",
                    "value": RAMPE_FIXE,
                },
            ],
        },
        {
            "label": "Rampe amovible",
            "picture": "ramp_mobile.jpg",
            "modelisation": [
                {
                    "field": "cheminement_ext_rampe",
                    "value": RAMPE_AMOVIBLE,
                },
            ],
        },
        {
            "label": "Pas de rampe",
            "picture": "no.jpg",
            "modelisation": [
                {
                    "field": "cheminement_ext_rampe",
                    "value": RAMPE_AUCUNE,
                },
            ],
        },
        {
            "label": "Je ne suis pas sur",
            "picture": "unknown.jpg",
            "modelisation": [
                {
                    "field": "cheminement_ext_rampe",
                    "value": UNKNOWN,
                },
            ],
        },
    ],
    "display_conditions": [],
}
