import os
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.db import connection

from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import geocoder

TEST_PASSWORD = "Abc12345!"


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    assert os.environ.get("DJANGO_SETTINGS_MODULE") == "core.settings_test"

    # Installe les extensions postgres pour la suite de test pytest
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
        cursor.execute("CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french )")
        cursor.execute(
            "ALTER TEXT SEARCH CONFIGURATION french_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem"
        )


@pytest.fixture(autouse=True)
def mock_geocode(request, mocker):
    """
    NOTE: use @pytest.mark.disable_geocode_autouse to skip this autoused fixture
    """

    def _result(*args, **kwargs):
        # naive address splitting, could be enhanced
        numero_voie, commune = args[0].split(", ")
        numero_voie = numero_voie.split(" ")
        numero = numero_voie[0]
        voie = " ".join(numero_voie[1:])

        return {
            "geom": Point((3, 43)),
            "numero": numero,
            "voie": voie.capitalize(),
            "lieu_dit": None,
            "code_postal": kwargs.get("postcode") or "34830",
            "commune": commune,
            "code_insee": kwargs.get("postcode") or "34830",
            "provider": "ban",
        }

    if "disable_geocode_autouse" in request.keywords:
        yield
    else:
        yield mocker.patch.object(geocoder, "geocode", side_effect=_result)


@pytest.fixture(autouse=True)
def mock_send_in_blue(mocker):
    mocker.patch("sib_api_v3_sdk.ContactsApi.get_contact_info", return_value=MagicMock(id=1))
    mocker.patch("sib_api_v3_sdk.ContactsApi.update_contact", return_value=True)


@pytest.fixture
def activite_administration_publique():
    return Activite.objects.create(nom="Administration Publique")


@pytest.fixture
def activite_mairie():
    return Activite.objects.create(nom="Mairie")


@pytest.fixture
def commune_castelnau():
    return Commune.objects.create(
        nom="Castelnau-le-Lez",
        code_postaux=["34170"],
        code_insee="34057",
        departement="93",
        geom=Point(0, 0),
    )


@pytest.fixture
def commune_montpellier():
    return Commune.objects.create(
        nom="Montpellier",
        code_postaux=["34000"],
        code_insee="34172",
        departement="34",
        geom=Point(0, 0),
    )


@pytest.fixture
def commune_montreuil():
    return Commune.objects.create(
        nom="Montreuil",
        code_postaux=["93100"],
        code_insee="93048",
        departement="93",
        geom=Point(0, 0),
    )


@pytest.fixture
def activite(db):
    list_activite = [
        "Accessoires",
        "Accrobranche",
        "Achat or",
        "Administration publique",
        "Aéroport",
        "Agence de travail temporaire",
        "Agence de voyage",
        "Agence immobilière",
        "Agence postale",
        "Aide à la personne",
        "Aide sociale à l'enfance : action éducative",
        "Ambulances",
        "Aménagement maison : cuisine salle de bain salon",
        "Animalerie",
        "Antiquaire",
        "Apiculteur",
        "Architecte",
        "Armurerie coutellerie",
        "Art",
        "Artisanat",
        "Assurance",
        "Athlétisme",
        "Audio prothésiste",
        "Auditorium et salle de conférence",
        "Auto école",
        "Autres établissements pour adultes et familles en difficulté",
        "Avocat",
        "Banques, caisses d'épargne",
        "Bar tabac",
        "Barbier",
        "Bâtiment d'accueil",
        "Bazar",
        "Bibliothèque médiathèque",
        "Bien-être",
        "Bijouterie joaillerie",
        "Blanchisserie teinturerie",
        "Boucherie / commerce de viande",
        "Boulangerie",
        "Boulangerie Pâtisserie",
        "Boulodrome",
        "Bowling",
        "Bricolage aménagement",
        "Brocante",
        "Brûlerie",
        "Bureau de poste",
        "Café, bar, brasserie",
        "Cafés et thés",
        "Camping caravaning",
        "Cantine",
        "Cardiologie",
        "Carrosserie",
        "Caviste / commerce de détail de boissons",
        "Centre commercial",
        "Centre culturel",
        "Centre de loisirs",
        "Centre de vacances",
        "Centre de vaccination",
        "Centre équestre",
        "Centre médical",
        "Centre religieux",
        "Chambres d'hôtes, gîte, pension",
        "Chapeaux et couvre-chefs",
        "Charcuterie",
        "Chaussures",
        "Chirurgien dentiste",
        "Chocolatier",
        "Cigarette électronique",
        "Cimetière",
        "Cinéma",
        "Clinique",
        "Coiffure",
        "Collège",
        "Commerce automobile",
        "Commissariat de Police",
        "Comptable expert-comptable",
        "Concessionnaire automobile",
        "Confiserie",
        "Conservatoire",
        "Contrôle technique auto",
        "Cordonnerie serrurerie",
        "Crèche",
        "Crèmerie Fromagerie",
        "Cure thermale",
        "Cycle vente et entretien",
        "Cyclisme",
        "Décoration Design",
        "Dermatologie vénéréologie",
        "Disquaire",
        "Droguerie",
        "EHPAD",
        "École élémentaire",
        "École maternelle",
        "École primaire (regroupement maternelle et élémentaire)",
        "Électricien",
        "Électroménager et matériel audio-vidéo",
        "Encadreur enlumineur",
        "Épicerie",
        "Epicerie fine",
        "Équipements du foyer",
        "Ergothérapeute",
        "Espace vert",
        "Établissement de santé",
        "Établissement militaire",
        "Fleuriste",
        "Friperie",
        "Fruits et légumes",
        "Galerie d'art",
        "Garage automobile",
        "Gare avec desserte train à grande vitesse (TAGV)",
        "Gare routière",
        "Gare sans desserte train à grande vitesse (TAGV)",
        "Gastro-entérologie hépatologie",
        "Gendarmerie",
        "Glacier",
        "Gymnase",
        "Gynécologie",
        "Herboristerie naturopathie",
        "Hôpital",
        "Horlogerie",
        "Hôtel",
        "Hôtel restaurant",
        "Huissier",
        "Hypermarché",
        "Imprimerie photocopie reliure",
        "Infirmier",
        "Information Touristique",
        "Informatique",
        "Instituts de formation",
        "Instruments et matériel de musique",
        "Jardin botanique et/ou zoologique",
        "Jardinerie",
        "Jeux jouets",
        "Laboratoire d'analyse médicale",
        "Laverie",
        "Librairie",
        "Lieu de culte",
        "Lieu de visite",
        "Lingerie sous-vêtements",
        "Literie",
        "Location articles loisirs et sport",
        "Location de matériels",
        "Location véhicules",
        "Loisirs créatifs",
        "Luminaire",
        "Lycée",
        "Magasin de bois de chauffage",
        "Magasin de tissus",
        "Mairie",
        "Maison de santé ou centre de santé",
        "Marché",
        "Maroquinerie sellerie articles de voyage",
        "Massages",
        "Masseur kinésithérapeute",
        "Médecin généraliste",
        "Menuiserie, ébénisterie",
        "Mercerie",
        "Meubles ameublement",
        "Motocycle vente et entretien",
        "Musée",
        "Notaire",
        "Office du tourisme",
        "Ophtalmologie",
        "Opticien",
        "Organisation patronale, professionnelle, syndicale",
        "Organisme de conseil",
        "Orthodontie",
        "Orthopédie",
        "Orthophonie",
        "Orthoptie",
        "Ostéopathie",
        "Oto-rhino-laryngologie",
        "Papeterie, presse, journaux",
        "Parc d’attraction",
        "Parfumerie beauté",
        "Parking & stationnement",
        "Patinoire",
        "Pâtisserie",
        "Pédiatrie",
        "Pédicure-podologue",
        "Pépinière",
        "Personnes âgées : foyer restaurant",
        "Personnes âgées : hébergement",
        "Pharmacie",
        "Photographie",
        "Piscine",
        "Plateaux et terrains de jeux extérieurs",
        "Plomberie, chauffage",
        "Pneumologie",
        "Poissonnerie / commerce de poissons, crustacés et mollusques",
        "Pompes funèbres",
        "Port",
        "Poterie verrerie céramique",
        "Pressing, nettoyage",
        "Primeur",
        "Produits de terroir",
        "Produits surgelés",
        "Psychologie, Psychiatrie",
        "Psychomotricien",
        "Puériculture",
        "Radiodiagnostic et imagerie médicale",
        "Rempailleur tapissier chaises fauteuils",
        "Réparation auto et de matériel agricole",
        "Restaurant",
        "Restaurant scolaire",
        "Restauration rapide",
        "Retouche",
        "Revêtements murs et sols",
        "Rhumatologie",
        "Sage-femme",
        "Salle de combat",
        "Salle de danse",
        "Salle de jeux",
        "Salle de spectacle",
        "Salle des fêtes",
        "Salle multisports",
        "Salle non spécialisée",
        "Salle spécialisée",
        "Salles de remise en forme",
        "Salon de thé",
        "Service ou aide à domicile",
        "Sex shop",
        "Skatepark",
        "Soins de beauté",
        "Spa",
        "Sports et loisirs",
        "Sports nautiques",
        "Stade",
        "Station lavage auto",
        "Station service",
        "Stomatologie",
        "Supérette",
        "Supermarché",
        "Tabac",
        "Tatouage Piercing",
        "Téléphonie",
        "Tennis",
        "Textile hors habillement",
        "Théâtre",
        "Toilettes publiques",
        "Toiletteur",
        "Traiteur",
        "Université ou école supérieure",
        "Urologie",
        "Vente à distance",
        "Vente / location d’articles de sport",
        "Vêtements",
        "Vétérinaire",
        "courtier",
        "hypnothérapeute",
        "plage",
        "syndic, gérance immo",
    ]
    for a in list_activite:
        Activite.objects.get_or_create(nom=a)


@pytest.fixture
def data(db):
    obj_admin = User.objects.create_user(
        username="admin",
        password=TEST_PASSWORD,
        email="admin@admin.tld",
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    obj_niko = User.objects.create_user(
        username="niko",
        password=TEST_PASSWORD,
        email="niko@niko.tld",
        is_staff=True,
        is_active=True,
    )
    obj_julia = User.objects.create_user(
        username="julia",
        password=TEST_PASSWORD,
        email="julia@julia.tld",
        is_staff=True,
        is_active=True,
    )
    obj_sophie = User.objects.create_user(
        username="sophie",
        password=TEST_PASSWORD,
        email="sophie@sophie.tld",
        is_staff=True,
        is_active=True,
    )
    obj_samuel = User.objects.create_user(
        username="samuel",
        password=TEST_PASSWORD,
        email="samuel@samuel.tld",
        is_staff=False,
        is_active=True,
    )
    obj_jacou = Commune.objects.create(
        nom="Jacou",
        code_postaux=["34830"],
        code_insee="34120",
        departement="34",
        geom=Point((3.9047933, 43.6648217)),
    )
    obj_boulangerie = Activite.objects.create(nom="Boulangerie")
    obj_erp = Erp.objects.create(
        nom="Aux bons croissants",
        siret="52128577500016",
        numero="4",
        voie="grand rue",
        code_postal="34830",
        commune="Jacou",
        commune_ext=obj_jacou,
        geom=Point((3.9047933, 43.6648217)),
        activite=obj_boulangerie,
        published=True,
        user=obj_niko,
    )
    obj_accessibilite = Accessibilite.objects.create(
        erp=obj_erp,
        sanitaires_presence=True,
        sanitaires_adaptes=False,
        commentaire="foo",
        entree_porte_presence=True,
        entree_reperage=True,
        # 4 access info min to reach the min required completion rate
    )

    class Data:
        admin = obj_admin
        niko = obj_niko
        julia = obj_julia
        sophie = obj_sophie
        samuel = obj_samuel
        jacou = obj_jacou
        boulangerie = obj_boulangerie
        accessibilite = obj_accessibilite
        erp = obj_erp

    return Data()
