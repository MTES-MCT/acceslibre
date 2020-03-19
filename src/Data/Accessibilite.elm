module Accessibilite exposing (Accessibilite)


type alias Accessibilite =
    { stationnement : Maybe Stationnement
    , cheminementExt : Maybe CheminementExt
    , entree : Maybe Entree
    , accueil : Maybe Accueil
    , sanitaires : Maybe Sanitaires
    , labels : Maybe Labels
    , commentaire : Maybe Commentaire
    }


type alias RawAccessibilite =
    { stationnement_presence : Maybe Bool
    , stationnement_pmr : Maybe Bool
    , stationnement_ext_presence : Maybe Bool
    , stationnement_ext_pmr : Maybe Bool
    , cheminement_ext_plain_pied : Maybe Bool
    , cheminement_ext_nombre_marches : Maybe Int
    , cheminement_ext_reperage_marches : Maybe Bool
    , cheminement_ext_main_courante : Maybe Bool
    , cheminement_ext_rampe : Maybe Bool
    , cheminement_ext_ascenseur : Maybe Bool
    , cheminement_ext_pente : Maybe String --TODO: enum
    , cheminement_ext_devers : Maybe String -- TODO: enum
    , cheminement_ext_bande_guidage : Maybe Bool
    , cheminement_ext_guidage_sonore : Maybe Bool
    , cheminement_ext_retrecissement : Maybe Int
    , entree_reperage : Maybe Bool
    , entree_vitree : Maybe Bool
    , entree_vitree_vitrophanie : Maybe Bool
    , entree_plain_pied : Maybe Bool
    , entree_marches : Maybe Int
    , entree_marches_reperage : Maybe Bool
    , entree_marches_main_courante : Maybe Bool
    , entree_marches_rampe : Maybe Bool
    , entree_dispositif_appel : Maybe Bool
    , entree_aide_humaine : Maybe Bool
    , entree_ascenseur : Maybe Bool
    , entree_largeur_mini : Maybe Int
    , entree_pmr : Maybe Bool
    , entree_pmr_informations : Maybe String
    , accueil_visibilite : Maybe Bool
    , accueil_personnels : Maybe String -- TODO: enum
    , accueil_cheminement_plain_pied : Maybe Bool
    , accueil_cheminement_nombre_marches : Maybe Int
    , accueil_cheminement_reperage_marches : Maybe Bool
    , accueil_cheminement_main_courante : Maybe Bool
    , accueil_cheminement_rampe : String --TODO: enum
    , accueil_cheminement_ascenseur : Maybe Bool
    , accueil_retrecissement : Maybe Bool
    , accueil_prestations : Maybe String
    , accueil_equipements_malentendants : List String
    , sanitaires_presence : Maybe Bool
    , sanitaires_adaptes : Maybe Int
    , labels : List String
    , labels_familles_handicap : List String
    , labels_autre : Maybe String
    , commentaire : Maybe String
    }
