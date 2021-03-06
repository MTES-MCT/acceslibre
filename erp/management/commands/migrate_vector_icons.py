from django.core.management.base import BaseCommand

from erp.models import Activite

MAP = {
    "Accessoires": "panier",
    "Administration publique": "local-government",
    "Aéroport": "airport",
    "Agence de travail temporaire": "general-contractor",
    "Agence de voyage": "travel-agency",
    "Agence immobilière": "real-estate-agency",
    "Agence postale": "post-office",
    "Aide sociale à l'enfance : action éducative": "enfant",
    "Aménagement maison\xa0: cuisine salle de bain salon": "baignoire",
    "Animalerie": "pet-store",
    "Antiquaire": "vase",
    "Apiculteur": "building",
    "Architecte": "architect",
    "Armurerie coutellerie": "armurerie",
    "Art": "art-gallery",
    "Assurance": "insurance-agency",
    "Athlétisme": "athletisme",
    "Audio prothésiste": "assistive-listening-system",
    "Auditorium et salle de conférence": "theatre",
    "Auto école": "car-learn",
    "Autres établissements pour adultes et familles en difficulté": "building",
    "Avocat": "lawyer",
    "Banques, caisses d'épargne": "bank",
    "Bibliothèque médiathèque": "library",
    "Bijouterie joaillerie": "jewelry-store",
    "Blanchisserie teinturerie": "laundry",
    "Boucherie / commerce de viande": "meat",
    "Boulangerie": "bakery",
    "Boulodrome": "sport",
    "Bowling": "bowling-alley",
    "Bricolage aménagement": "hardware-store",
    "Bureau de poste": "post-office",
    "Café, bar, brasserie": "cafe",
    "Cafés et thés": "coffee",
    "Camping caravaning": "rv-park",
    "Cantine": "restaurant",
    "Cardiologie": "health",
    "Carrosserie": "car-repair",
    "Caviste / commerce de détail de boissons": "liquor-store",
    "Centre commercial": "shopping-mall",
    "Centre culturel": "building",
    "Centre de loisirs": "playground",
    "Centre de vacances": "building",
    "Centre équestre": "horse-riding",
    "Centre religieux": "building",
    "Chapeaux et couvre-chefs": "chapeau",
    "Charcuterie": "meat",
    "Chaussures": "chaussure",
    "Chirurgien dentiste": "dentist",
    "Chocolatier": "bonbon",
    "Cigarette électronique": "building",
    "Cimetière": "cemetery",
    "Cinéma": "cinema",
    "Clinique": "health",
    "Coiffure": "beauty-salon",
    "Collège": "school",
    "Commerce automobile": "car-dealer",
    "Comptable expert-comptable": "accounting",
    "Confiserie": "bonbon",
    "Conservatoire": "musique",
    "Contrôle technique auto": "car-repair",
    "Cordonnerie serrurerie": "locksmith",
    "Crèche": "baby",
    "Crèmerie Fromagerie": "cheese",
    "Cure thermale": "health",
    "Cycle vente et entretien": "bicycle-store",
    "Cyclisme": "bicycling",
    "Débit de boisson": "bottle",
    "Décoration Design": "painter",
    "Dermatologie vénéréologie": "health",
    "Disquaire": "musique",
    "École élémentaire": "school",
    "École maternelle": "school",
    "École primaire (regroupement maternelle et élémentaire)": "school",
    "EHPAD": "building",
    "Électricien": "electrician",
    "Électroménager et matériel audio-vidéo": "electronics-store",
    "Encadreur enlumineur": "building",
    "Épicerie": "convenience-store",
    "Équipements du foyer": "panier",
    "Ergothérapeute": "health",
    "Espace vert": "trees",
    "Établissement de santé": "health",
    "Établissement militaire": "building",
    "Exploitation agricole": "trees",
    "Fleuriste": "florist",
    "Fruits et légumes": "vegetables",
    "Galerie d'art": "art-gallery",
    "Garage automobile": "car-repair",
    "Gare avec desserte train à grande vitesse (TAGV)": "train-station",
    "Gare routière": "bus-station",
    "Gare sans desserte train à grande vitesse (TAGV)": "train-station",
    "Gastro-entérologie hépatologie": "estomac",
    "Glacier": "bonbon",
    "Gymnase": "gym",
    "Gynécologie": "female",
    "Herboristerie naturopathie": "health",
    "Hôpital": "hospital",
    "Horlogerie": "clock",
    "Hôtel": "hotel",
    "Huissier": "general-contractor",
    "Hypermarché": "grocery-or-supermarket",
    "Imprimerie photocopie reliure": "building",
    "Infirmier": "health",
    "Information Touristique": "compass",
    "Informatique": "computer",
    "Instituts de formation": "building",
    "Instruments et matériel de musique": "musique",
    "Jardin botanique et/ou zoologique": "zoo",
    "Jardinerie": "trees",
    "Jeux jouets": "jouet",
    "Laboratoire d'analyse médicale": "labo",
    "Laverie": "laundry",
    "Librairie": "book-store",
    "Lieu de culte": "place-of-worship",
    "Lieu de visite": "natural-feature",
    "Literie": "lodging",
    "Location articles loisirs et sport": "archery",
    "Location de matériels": "building",
    "Location véhicules": "car-rental",
    "Luminaire": "building",
    "Lycée": "school",
    "Mairie": "city-hall",
    "Maison de santé ou centre de santé": "health",
    "Marché": "market",
    "Maroquinerie sellerie articles de voyage": "panier",
    "Massages": "spa",
    "Masseur kinésithérapeute": "spa",
    "Médecin généraliste": "doctor",
    "Menuiserie, ébénisterie": "furniture-store",
    "Mercerie": "clothing-store",
    "Meubles ameublement": "furniture-store",
    "Motocycle vente et entretien": "motobike-trail",
    "Musée": "museum",
    "Notaire": "general-contractor",
    "Office du tourisme": "compass",
    "Ophtalmologie": "optique",
    "Optique": "optique",
    "Organisation patronale, professionnelle, syndicale": "building",
    "Orthopédie": "health",
    "Orthophonie": "health",
    "Orthoptie": "optique",
    "Ostéopathie": "spa",
    "Oto-rhino-laryngologie": "health",
    "Papeterie, presse, journaux": "library",
    "Parc d’attraction": "amusement-park",
    "Parfumerie beauté": "parfum",
    "Parking & stationnement": "parking",
    "Patinoire": "ice-skating",
    "Pâtisserie": "cake",
    "Pédiatrie": "enfant",
    "Pédicure-podologue": "health",
    "Pension, gîte, chambres d'hôtes": "lodging",
    "Personnes âgées : foyer restaurant": "restaurant",
    "Personnes âgées : hébergement": "lodging",
    "Pharmacie": "pharmacy",
    "Photographie": "point-of-interest",
    "Piscine": "swimming",
    "Plateaux et terrains de jeux extérieurs": "playground",
    "Plomberie, chauffage": "plumber",
    "Pneumologie": "health",
    "Poissonnerie / commerce de poissons, crustacés et mollusques": "fish-cleaning",
    "Pompes funèbres": "funeral-home",
    "Port": "marina",
    "Poterie verrerie céramique": "vase",
    "Pressing, nettoyage": "clothing-store",
    "Primeur": "panier",
    "Produits surgelés": "flocon",
    "Psychologie, Psychiatrie": "health",
    "Psychomotricien": "physiotherapist",
    "Radiodiagnostic et imagerie médicale": "labo",
    "Rempailleur chaises fauteuils": "furniture-store",
    "Réparation auto et de matériel agricole": "car-repair",
    "Restaurant": "restaurant",
    "Restaurant scolaire": "restaurant",
    "Restauration rapide": "food",
    "Retouche": "clothing-store",
    "Revêtements murs et sols": "painter",
    "Rhumatologie": "health",
    "Sage-femme": "health",
    "Salle de combat": "building",
    "Salle de danse": "building",
    "Salle de jeux": "building",
    "Salle des fêtes": "building",
    "Salle de spectacle": "theatre",
    "Salle multisports": "sport",
    "Salle non spécialisée": "building",
    "Salles de remise en forme": "gym",
    "Salle spécialisée": "building",
    "Salon de thé": "coffee",
    "Service ou aide à domicile": "building",
    "Sex shop": "building",
    "Skatepark": "skateboarding",
    "Soins de beauté": "makeup",
    "Spa": "spa",
    "Sports et loisirs": "sport",
    "Sports nautiques": "sailing",
    "Stade": "stadium",
    "Station lavage auto": "car-wash",
    "Station service": "gas-station",
    "Stomatologie": "estomac",
    "Supérette": "panier",
    "Supermarché": "grocery-or-supermarket",
    "Tabac": "tabac",
    "Tatouage Piercing": "building",
    "Téléphonie": "telephonie",
    "Tennis": "tennis",
    "Textile hors habillement": "building",
    "Théâtre": "theatre",
    "Toiletteur": "pet-store",
    "Traiteur": "traiteur",
    "Université ou école supérieure": "university",
    "Vente à distance": "location-arrow",
    "Vêtements sous-vêtements lingerie": "clothing-store",
    "Vétérinaire": "veterinary-care",
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        manque = 0
        for activite in Activite.objects.all():
            vector_icon = MAP.get(activite.nom)
            if vector_icon:
                activite.vector_icon = vector_icon
                activite.save()
                # print(f"PASS: {activite}: {vector_icon}")
            else:
                print(f"SKIP: nothing for {activite}")
                manque += 1
        if manque > 0:
            print(f"Il manque {manque} icones !")
