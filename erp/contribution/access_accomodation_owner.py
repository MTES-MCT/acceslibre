from django.utils.translation import gettext_lazy as translate_lazy

from .access_utils import no_answer, not_sure_answer, yes_answer
from .conditions import accommodation_and_owner
from .dataclasses import MUTIPLE_ANSWERS, UNIQUE_ANSWER, Answer, Question

shower = Answer(
    label=translate_lazy("Un bac extra plat (douche à l'italienne)"),
    picture="2-9-a-bac.jpg",
    modelisations=[{"field": "accueil_chambre_douche_plain_pied", "value": True}],
)

shower_seat = Answer(
    label=translate_lazy("Un siège de douche"),
    picture="2-9-a-siege.jpg",
    modelisations=[{"field": "accueil_chambre_douche_siege", "value": True}],
)
shower_grab_bar = Answer(
    label=translate_lazy("D'une barre d'appui horizontale"),
    picture="2-9-a-barre.jpg",
    modelisations=[{"field": "accueil_chambre_douche_barre_appui", "value": True}],
)


SHOWER_QUESTION = Question(
    label=translate_lazy("Dans la chambre accessible, la douche est-elle équipée de :"),
    type=MUTIPLE_ANSWERS,
    answers=[shower, shower_seat, shower_grab_bar],
    display_conditions=[accommodation_and_owner],
)


toilet_grab_bar = Answer(
    label=translate_lazy("D'une barre d'appui horizontale"),
    picture="2-9-b-barre - .jpg",
    modelisations=[{"field": "accueil_chambre_sanitaires_barre_appui", "value": True}],
)

toilet_space = Answer(
    label=translate_lazy("Un espace d'usage à côté des toilettes"),
    picture="2-9-b-espace-usage.jpg",
    modelisations=[{"field": "accueil_chambre_sanitaires_espace_usage", "value": True}],
)

ROOM_TOILET_QUESTION = Question(
    label=translate_lazy("Dans la chambre accessible, les toilettes sont-elles équipées de :"),
    type=MUTIPLE_ANSWERS,
    answers=[toilet_grab_bar, toilet_space],
    display_conditions=[accommodation_and_owner],
)


SPECIFIC_SUPPORT_QUESTION = Question(
    label=translate_lazy(
        "Votre établissement propose-t-il un accompagnement personnalisé pour les personnes malvoyantes ou aveugles ?"
    ),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_chambre_accompagnement"]),
        no_answer(["accueil_chambre_accompagnement"]),
        not_sure_answer(["accueil_chambre_accompagnement"]),
    ],
    display_conditions=[accommodation_and_owner],
)


SPECIFIC_ALERT_QUESTION = Question(
    label=translate_lazy("Votre établissement dispose-t-il d'une alerte par flash lumineux ou vibration ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_chambre_equipement_alerte"]),
        no_answer(["accueil_chambre_equipement_alerte"]),
        not_sure_answer(["accueil_chambre_equipement_alerte"]),
    ],
    display_conditions=[accommodation_and_owner],
)


ROOM_NUMBER_QUESTION = Question(
    label=translate_lazy("Les numéros de chambre sont-il très repérable et en relief ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_chambre_numero_visible"]),
        no_answer(["accueil_chambre_numero_visible"]),
        not_sure_answer(["accueil_chambre_numero_visible"]),
    ],
    display_conditions=[accommodation_and_owner],
)
