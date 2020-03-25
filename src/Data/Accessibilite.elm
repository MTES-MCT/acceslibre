module Data.Accessibilite exposing
    ( Accessibilite
    , Accueil
    , CheminementExt
    , Entree
    , Labels
    , Sanitaires
    , Stationnement
    , decode
    )

import Json.Decode as Decode exposing (Decoder)
import Json.Decode.Pipeline as Pipe


type alias Accessibilite =
    { stationnement : Stationnement
    , cheminementExt : CheminementExt
    , entree : Entree
    , accueil : Accueil
    , sanitaires : Sanitaires
    , labels : Labels
    , commentaire : Maybe String
    }


type alias Stationnement =
    { stationnement_presence : Maybe Bool
    , stationnement_pmr : Maybe Bool
    , stationnement_ext_presence : Maybe Bool
    , stationnement_ext_pmr : Maybe Bool
    }


type alias CheminementExt =
    { cheminement_ext_plain_pied : Maybe Bool
    , cheminement_ext_nombre_marches : Maybe Int
    , cheminement_ext_reperage_marches : Maybe Bool
    , cheminement_ext_main_courante : Maybe Bool
    , cheminement_ext_rampe : Maybe Bool
    , cheminement_ext_ascenseur : Maybe Bool
    , cheminement_ext_pente : Maybe String -- TODO: enum
    , cheminement_ext_devers : Maybe String -- TODO: enum
    , cheminement_ext_bande_guidage : Maybe Bool
    , cheminement_ext_guidage_sonore : Maybe Bool
    , cheminement_ext_retrecissement : Maybe Int
    }


type alias Entree =
    { entree_reperage : Maybe Bool
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
    }


type alias Accueil =
    { accueil_visibilite : Maybe Bool
    , accueil_personnels : Maybe String -- TODO: enum
    , accueil_cheminement_plain_pied : Maybe Bool
    , accueil_cheminement_nombre_marches : Maybe Int
    , accueil_cheminement_reperage_marches : Maybe Bool
    , accueil_cheminement_main_courante : Maybe Bool
    , accueil_cheminement_rampe : Maybe String --TODO: enum
    , accueil_cheminement_ascenseur : Maybe Bool
    , accueil_retrecissement : Maybe Bool
    , accueil_prestations : Maybe String
    , accueil_equipements_malentendants : List String
    }


type alias Sanitaires =
    { sanitaires_presence : Maybe Bool
    , sanitaires_adaptes : Maybe Int
    }


type alias Labels =
    { labels : List String
    , labels_familles_handicap : List String
    , labels_autre : Maybe String
    }


decode : Decoder Accessibilite
decode =
    Decode.succeed Accessibilite
        |> Pipe.required "stationnement" decodeStationnement
        |> Pipe.required "cheminement_ext" decodeCheminementExt
        |> Pipe.required "entree" decodeEntree
        |> Pipe.required "accueil" decodeAccueil
        |> Pipe.required "sanitaires" decodeSanitaires
        |> Pipe.required "labels" decodeLabels
        |> Pipe.requiredAt [ "commentaire", "commentaire" ] (Decode.maybe Decode.string)


decodeStationnement : Decoder Stationnement
decodeStationnement =
    Decode.succeed Stationnement
        |> Pipe.required "stationnement_presence" (Decode.maybe Decode.bool)
        |> Pipe.required "stationnement_pmr" (Decode.maybe Decode.bool)
        |> Pipe.required "stationnement_ext_presence" (Decode.maybe Decode.bool)
        |> Pipe.required "stationnement_ext_pmr" (Decode.maybe Decode.bool)


decodeCheminementExt : Decoder CheminementExt
decodeCheminementExt =
    Decode.succeed CheminementExt
        |> Pipe.required "cheminement_ext_plain_pied" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_nombre_marches" (Decode.maybe Decode.int)
        |> Pipe.required "cheminement_ext_reperage_marches" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_main_courante" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_rampe" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_ascenseur" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_pente" (Decode.maybe Decode.string)
        |> Pipe.required "cheminement_ext_devers" (Decode.maybe Decode.string)
        |> Pipe.required "cheminement_ext_bande_guidage" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_guidage_sonore" (Decode.maybe Decode.bool)
        |> Pipe.required "cheminement_ext_retrecissement" (Decode.maybe Decode.int)


decodeEntree : Decoder Entree
decodeEntree =
    Decode.succeed Entree
        |> Pipe.required "entree_reperage" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_vitree" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_vitree_vitrophanie" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_plain_pied" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_marches" (Decode.maybe Decode.int)
        |> Pipe.required "entree_marches_reperage" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_marches_main_courante" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_marches_rampe" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_dispositif_appel" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_aide_humaine" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_ascenseur" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_largeur_mini" (Decode.maybe Decode.int)
        |> Pipe.required "entree_pmr" (Decode.maybe Decode.bool)
        |> Pipe.required "entree_pmr_informations" (Decode.maybe Decode.string)


decodeAccueil : Decoder Accueil
decodeAccueil =
    Decode.succeed Accueil
        |> Pipe.required "accueil_visibilite" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_personnels" (Decode.maybe Decode.string)
        |> Pipe.required "accueil_cheminement_plain_pied" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_cheminement_nombre_marches" (Decode.maybe Decode.int)
        |> Pipe.required "accueil_cheminement_reperage_marches" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_cheminement_main_courante" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_cheminement_rampe" (Decode.maybe Decode.string)
        |> Pipe.required "accueil_cheminement_ascenseur" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_retrecissement" (Decode.maybe Decode.bool)
        |> Pipe.required "accueil_prestations" (Decode.maybe Decode.string)
        |> Pipe.required "accueil_equipements_malentendants" (Decode.list Decode.string)


decodeSanitaires : Decoder Sanitaires
decodeSanitaires =
    Decode.succeed Sanitaires
        |> Pipe.required "sanitaires_presence" (Decode.maybe Decode.bool)
        |> Pipe.required "sanitaires_adaptes" (Decode.maybe Decode.int)


decodeLabels : Decoder Labels
decodeLabels =
    Decode.succeed Labels
        |> Pipe.required "labels" (Decode.list Decode.string)
        |> Pipe.required "labels_familles_handicap" (Decode.list Decode.string)
        |> Pipe.required "labels_autre" (Decode.maybe Decode.string)
