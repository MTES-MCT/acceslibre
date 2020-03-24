module Views.Accessibilite exposing (Tab(..), view)

import Data.Accessibilite as Accessibilite
    exposing
        ( Accessibilite
        , Accueil
        , CheminementExt
        , Entree
        , Labels
        , Sanitaires
        , Stationnement
        )
import Data.Accessibilite.Help exposing (Help)
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)


type alias Model =
    { accessibilite : Accessibilite
    , activeTab : Tab
    }


type alias Config msg =
    { accessibilite : Accessibilite
    , noOp : msg
    , session : Session
    }


type Tab
    = AccueilTab Accueil
    | CheminementExtTab CheminementExt
    | EntreeTab Entree
    | LabelsTab Labels
    | SanitairesTab Sanitaires
    | StationnementTab Stationnement
    | CommentaireTab String


tabLabel : Tab -> String
tabLabel tab =
    case tab of
        AccueilTab _ ->
            "Accueil"

        CheminementExtTab _ ->
            "Cheminement extérieur"

        EntreeTab _ ->
            "Entrée"

        LabelsTab _ ->
            "Labels"

        SanitairesTab _ ->
            "Sanitaires"

        StationnementTab _ ->
            "Stationnement"

        CommentaireTab _ ->
            "Commentaire"


tabStationnement : Stationnement -> Html msg
tabStationnement stationnement =
    div [ attribute "aria-labelledby" "stationnement-tab", class "tab-pane", id "stationnement", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ booleanField
                { name = "Stationnement dans l'ERP"
                , help = "Présence de stationnements au sein de l'ERP"
                , maybeValue = stationnement.stationnement_presence
                }
            , booleanField
                { name = "Stationnements adaptés dans l'ERP"
                , help = "Présence de stationnements PMR au sein de l'ERP"
                , maybeValue = stationnement.stationnement_pmr
                }
            , booleanField
                { name = "Stationnement à proximité"
                , help = "Présence de stationnements à proximité immédiate de l'ERP (200m)"
                , maybeValue = stationnement.stationnement_ext_presence
                }
            , booleanField
                { name = "Stationnement PMR à proximité"
                , help = "Présence de stationnements adaptés à proximité immédiate de l'ERP (200m)"
                , maybeValue = stationnement.stationnement_ext_pmr
                }
            ]
        ]


tabAccueil : Accueil -> Html msg
tabAccueil accueil =
    div [ attribute "aria-labelledby" "entree-tab", class "tab-pane active", id "entree", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ booleanField
                { name = "Visibilité directe de la zone d'accueil depuis l'entrée"
                , help = "La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) est-elle visible depuis l'entrée ?"
                , maybeValue = accueil.accueil_visibilite
                }
            , charField
                { name = "Personnel d'accueil"
                , help = "Présence et sensibilisation du personnel d'accueil"
                , maybeValue = accueil.accueil_personnels
                }
            , stringListField
                { name = "Équipements sourds/malentendants"
                , help = "L'accueil est-il équipé de produits ou prestations dédiés aux personnes sourdes ou malentendantes (boucle à induction magnétique, langue des signes françaises, solution de traduction à distance, etc)"
                , maybeValue = accueil.accueil_equipements_malentendants
                }
            , booleanField
                { name = "Cheminement de plain pied"
                , help = "Le cheminement entre l’entrée et l’accueil est-il de plain-pied ?"
                , maybeValue = accueil.accueil_cheminement_plain_pied
                }
            , intField (marches accueil.accueil_cheminement_nombre_marches)
                { name = "Nombre de marches"
                , help = "Indiquez 0 s’il n’y a ni marche ni escalier"
                , maybeValue = accueil.accueil_cheminement_nombre_marches
                }
            , booleanField
                { name = "Repérage des marches ou de l’escalier"
                , help = "Nez de marche contrasté, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches de l'escalier contrastées"
                , maybeValue = accueil.accueil_cheminement_reperage_marches
                }
            , booleanField
                { name = "Main courante"
                , help = "Présence d'une main courante d'escalier"
                , maybeValue = accueil.accueil_cheminement_main_courante
                }
            , charField
                { name = "Rampe"
                , help = "Présence et type de rampe"
                , maybeValue = accueil.accueil_cheminement_rampe
                }
            , booleanField
                { name = "Ascenseur/élévateur"
                , help = "Présence d'un ascenseur ou d'un élévateur"
                , maybeValue = accueil.accueil_cheminement_ascenseur
                }
            , booleanField
                { name = "Rétrécissement du cheminement"
                , help = "Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) du chemin emprunté par le public pour atteindre la zone d’accueil ?"
                , maybeValue = accueil.accueil_retrecissement
                }
            , textField
                { name = "Prestations d'accueil adapté supplémentaires"
                , help = "Veuillez indiquer ici les prestations spécifiques supplémentaires proposées par l'établissement"
                , maybeValue = accueil.accueil_prestations
                }
            ]
        ]


marches : Maybe Int -> String
marches maybeInt =
    case maybeInt of
        Just int ->
            " marche"
                ++ (if int > 1 then
                        "s"

                    else
                        ""
                   )

        Nothing ->
            ""


tabEntree : Entree -> Html msg
tabEntree entree =
    div [ attribute "aria-labelledby" "entree-tab", class "tab-pane active", id "entree", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ booleanField
                { name = "Entrée facilement repérable"
                , help = "Y a-t-il des éléments de repérage de l'entrée (numéro de rue à proximité, enseigne, etc)"
                , maybeValue = entree.entree_reperage
                }
            , booleanField
                { name = "Entrée vitrée"
                , help = "La porte d'entrée est-elle vitrée ?"
                , maybeValue = entree.entree_vitree
                }
            , booleanField
                { name = "Plain-pied"
                , help = "L'entrée est-elle de plain-pied ?"
                , maybeValue = entree.entree_plain_pied
                }
            , intField (marches entree.entree_marches)
                { name = "Marches d'escalier"
                , help = "Nombre de marches d'escalier"
                , maybeValue = entree.entree_marches
                }
            , booleanField
                { name = "Repérage de l'escalier"
                , help = "Nez de marche contrasté, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches de l'escalier contrastées"
                , maybeValue = entree.entree_marches_reperage
                }
            , booleanField
                { name = "Main courante"
                , help = "Présence d'une main courante pour franchir les marches"
                , maybeValue = entree.entree_marches_main_courante
                }
            , booleanField
                { name = "Rampe"
                , help = "Présence et type de rampe"
                , maybeValue = entree.entree_marches_rampe
                }
            , booleanField
                { name = "Dispositif d'appel"
                , help = "Existe-t-il un dispositif comme une sonnette pour permettre à quelqu'un ayant besoin de la rampe de signaler sa présence ?"
                , maybeValue = entree.entree_dispositif_appel
                }
            , booleanField
                { name = "Aide humaine"
                , help = "Présence ou possibilité d'une aide humaine au déplacement"
                , maybeValue = entree.entree_aide_humaine
                }
            , booleanField
                { name = "Ascenseur/élévateur"
                , help = "Présence d'un ascenseur ou d'un élévateur"
                , maybeValue = entree.entree_ascenseur
                }
            , intField "cm"
                { name = "Largeur minimale"
                , help = "Si la largeur n’est pas précisément connue, indiquez une valeur minimum. Exemple : ma largeur se situe entre 90 et 100 cm ; indiquez 90."
                , maybeValue = entree.entree_largeur_mini
                }
            , booleanField
                { name = "Entrée spécifique PMR"
                , help = "Présence d'une entrée secondaire spécifique PMR"
                , maybeValue = entree.entree_pmr
                }
            , textField
                { name = "Infos entrée spécifique PMR"
                , help = "Précisions sur les modalités d'accès de l'entrée spécifique PMR"
                , maybeValue = entree.entree_pmr_informations
                }
            ]
        ]


tabCheminementExt : CheminementExt -> Html msg
tabCheminementExt cheminementExt =
    div [ attribute "aria-labelledby" "chemeinement-ext-tab", class "tab-pane", id "cheminementExt", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ text "XXX"
            ]
        ]


tabSanitaires : Sanitaires -> Html msg
tabSanitaires sanitaires =
    div [ attribute "aria-labelledby" "sanitaires-tab", class "tab-pane", id "sanitaires", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ text "XXX"
            ]
        ]


tabCommentaire : Maybe String -> Html msg
tabCommentaire maybeCommentaire =
    div [ attribute "aria-labelledby" "sanitaires-tab", class "tab-pane", id "sanitaires", attribute "role" "tabpanel" ]
        [ ul [ class "list-group list-group-flush" ]
            [ textField
                { name = "Commentaire libre"
                , help = "Indiquez tout autre information qui vous semble pertinente pour décrire l’accessibilité du bâtiment"
                , maybeValue = maybeCommentaire
                }
            ]
        ]


tabMenuEntry : Bool -> Tab -> Html msg
tabMenuEntry active tab =
    li [ class "nav-item" ]
        [ button
            [ type_ "button"
            , attribute "aria-controls" "entree"
            , attribute "aria-selected"
                (if active then
                    "true"

                 else
                    "false"
                )
            , class "btn btn-sm btn-link nav-link px-2 py-1"
            , classList [ ( "active", active ) ]

            -- , href "#entree"
            -- , id "entree-tab"
            , attribute "role" "tab"
            ]
            [ i [ class "icon icon-entrance mr-2" ] []
            , text (tabLabel tab)
            ]
        ]


tabMenu : Config msg -> Html msg
tabMenu { accessibilite } =
    let
        { stationnement, cheminementExt, entree, accueil, sanitaires, labels, commentaire } =
            accessibilite
    in
    [ EntreeTab entree
    , StationnementTab stationnement
    , CheminementExtTab cheminementExt
    , AccueilTab accueil
    , LabelsTab labels
    , SanitairesTab sanitaires
    ]
        |> List.map (tabMenuEntry False)
        |> ul
            [ attribute "aria-label" "Sections"
            , class "nav nav-tabs nav-fill mb-2"
            , attribute "role" "tablist"
            ]


hFieldWrapper : String -> String -> List (Html msg) -> Html msg
hFieldWrapper name help html =
    li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
        [ div []
            [ div []
                [ text name
                , text " "
                , small [ class "text-muted" ] [ text help ]
                ]
            , div [] html
            ]
        ]


vFieldWrapper : String -> String -> List (Html msg) -> Html msg
vFieldWrapper name help html =
    li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
        [ div [ class "pr-3" ]
            [ text name
            , text " "
            , small [ class "text-muted" ] [ text help ]
            ]
        , div [] html
        ]


booleanField : { name : String, help : String, maybeValue : Maybe Bool } -> Html msg
booleanField { name, help, maybeValue } =
    case maybeValue of
        Just value ->
            vFieldWrapper name
                help
                (if value then
                    [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ] []
                    , span [ class "sr-only" ] [ text "Oui" ]
                    ]

                 else
                    [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ] []
                    , span [ class "sr-only" ] [ text "Non" ]
                    ]
                )

        Nothing ->
            text ""


charField : { name : String, help : String, maybeValue : Maybe String } -> Html msg
charField { name, help, maybeValue } =
    case maybeValue of
        Just value ->
            vFieldWrapper name help [ text value ]

        Nothing ->
            text ""


intField : String -> { name : String, help : String, maybeValue : Maybe Int } -> Html msg
intField unit { name, help, maybeValue } =
    case maybeValue of
        Just value ->
            vFieldWrapper name help [ text <| String.fromInt value ++ unit ]

        Nothing ->
            text ""


stringListField : { name : String, help : String, maybeValue : List String } -> Html msg
stringListField { name, help, maybeValue } =
    maybeValue
        |> List.map (\v -> span [ class "label label-info" ] [ text v ])
        |> vFieldWrapper name help


textField : { name : String, help : String, maybeValue : Maybe String } -> Html msg
textField { name, help, maybeValue } =
    case maybeValue of
        Just value ->
            hFieldWrapper name help [ div [ class "lead mb-0 my-1" ] [ text value ] ]

        Nothing ->
            text ""


view : Config msg -> Html msg
view config =
    div [ class "mb-2" ]
        [ tabMenu config
        , div [ class "tab-content" ]
            [ tabEntree config.accessibilite.entree
            , tabStationnement config.accessibilite.stationnement
            , tabCheminementExt config.accessibilite.cheminementExt
            , tabAccueil config.accessibilite.accueil
            , tabSanitaires config.accessibilite.sanitaires
            , tabCommentaire config.accessibilite.commentaire
            ]
        ]
