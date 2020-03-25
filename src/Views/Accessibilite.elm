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
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)


type alias Config msg =
    { accessibilite : Accessibilite
    , activeTab : Tab
    , noOp : msg
    , session : Session
    , switchTab : Tab -> msg
    }


type Tab
    = AccueilTab Accueil
    | CheminementExtTab CheminementExt
    | EntreeTab Entree
    | LabelsTab Labels
    | SanitairesTab Sanitaires
    | StationnementTab Stationnement
    | CommentaireTab (Maybe String)


tabInfo : Tab -> ( String, String )
tabInfo tab =
    case tab of
        AccueilTab _ ->
            ( "Accueil", "users" )

        CheminementExtTab _ ->
            ( "Cheminement extérieur", "path" )

        EntreeTab _ ->
            ( "Entrée", "entrance" )

        LabelsTab _ ->
            ( "Labels", "star-o" )

        SanitairesTab _ ->
            ( "Sanitaires", "male-female" )

        StationnementTab _ ->
            ( "Stationnement", "car" )

        CommentaireTab _ ->
            ( "Commentaire", "info-circled" )


tabStationnement : Stationnement -> List (Html msg)
tabStationnement stationnement =
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


tabAccueil : Accueil -> List (Html msg)
tabAccueil accueil =
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


tabEntree : Entree -> List (Html msg)
tabEntree entree =
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


tabCheminementExt : CheminementExt -> List (Html msg)
tabCheminementExt cheminementExt =
    [ booleanField
        { name = "Cheminement de plain-pied"
        , help = "Le cheminement est-il de plain-pied ou existe-t-il une rupture de niveau entraînant la présence de marches ou d'un équipement type ascenseur ?"
        , maybeValue = cheminementExt.cheminement_ext_plain_pied
        }
    , intField (marches cheminementExt.cheminement_ext_nombre_marches)
        { name = "Nombre de marches"
        , help = "Indiquez 0 s’il n’y a ni marche ni escalier"
        , maybeValue = cheminementExt.cheminement_ext_nombre_marches
        }
    , booleanField
        { name = "Repérage des marches ou de l’escalier"
        , help = "Nez de marche contrasté, bande d'éveil à la vigilance en haut de l'escalier, première et dernière contremarches de l'escalier contrastées"
        , maybeValue = cheminementExt.cheminement_ext_reperage_marches
        }
    , booleanField
        { name = "Main courante"
        , help = "Présence d'une main courante d'escalier"
        , maybeValue = cheminementExt.cheminement_ext_main_courante
        }
    , booleanField
        { name = "Rampe"
        , help = "Présence et type de rampe"
        , maybeValue = cheminementExt.cheminement_ext_rampe
        }
    , booleanField
        { name = "Ascenseur/élévateur"
        , help = "Présence d'un ascenseur ou d'un élévateur"
        , maybeValue = cheminementExt.cheminement_ext_ascenseur
        }
    , charField
        { name = "Pente"
        , help = "Présence et type de pente"
        , maybeValue = cheminementExt.cheminement_ext_pente
        }
    , charField
        { name = "Dévers"
        , help = "Inclinaison transversale du cheminement"
        , maybeValue = cheminementExt.cheminement_ext_devers
        }
    ]


tabLabels : Labels -> List (Html msg)
tabLabels labels =
    [ stringListField
        { name = "Labels d'accessibilité"
        , help = "Labels d'accessibilité obtenus par l'ERP"
        , maybeValue = labels.labels
        }
    , stringListField
        { name = "Famille(s) de handicap concernées(s)"
        , help = "Liste des familles de handicaps couverts par l'obtention de ce label"
        , maybeValue = labels.labels_familles_handicap
        }
    , charField
        { name = "Autre label"
        , help = "Si autre, précisez le nom du label"
        , maybeValue = labels.labels_autre
        }
    ]


tabSanitaires : Sanitaires -> List (Html msg)
tabSanitaires sanitaires =
    [ booleanField
        { name = "Sanitaires"
        , help = "Présence de sanitaires dans l'établissement"
        , maybeValue = sanitaires.sanitaires_presence
        }
    , intField " wc"
        { name = "Nombre de sanitaires adaptés"
        , help = "Nombre de sanitaires adaptés dans l'établissement"
        , maybeValue = sanitaires.sanitaires_adaptes
        }
    ]


tabCommentaire : Maybe String -> List (Html msg)
tabCommentaire maybeCommentaire =
    [ textField
        { name = "Commentaire libre"
        , help = "Indiquez tout autre information qui vous semble pertinente pour décrire l’accessibilité du bâtiment"
        , maybeValue = maybeCommentaire
        }
    ]


tabMenuEntry : Config msg -> Tab -> Html msg
tabMenuEntry config tab =
    let
        active =
            config.activeTab == tab
    in
    li [ class "nav-item a4a-accessibilite-tab" ]
        [ button
            [ type_ "button"
            , attribute "aria-selected"
                (if active then
                    "true"

                 else
                    "false"
                )
            , class "btn btn-sm btn-link nav-link px-2 py-1"
            , classList [ ( "active", active ) ]
            , attribute "role" "tab"
            , onClick (config.switchTab tab)
            ]
            [ i [ class <| "icon icon-" ++ (tabInfo tab |> Tuple.second) ++ " mr-2" ] []
            , tabInfo tab |> Tuple.first |> text
            ]
        ]


tabContent : Config msg -> Html msg
tabContent config =
    div
        [ class "tab-pane active"
        , attribute "role" "tabpanel"
        ]
        [ tabContentFields config.activeTab
            |> ul [ class "list-group list-group-flush" ]
        ]


tabContentFields : Tab -> List (Html msg)
tabContentFields tab =
    case tab of
        AccueilTab accueil ->
            tabAccueil accueil

        CheminementExtTab cheminementExt ->
            tabCheminementExt cheminementExt

        EntreeTab entree ->
            tabEntree entree

        LabelsTab labels ->
            tabLabels labels

        SanitairesTab sanitaires ->
            tabSanitaires sanitaires

        StationnementTab stationnement ->
            tabStationnement stationnement

        CommentaireTab commentaire ->
            tabCommentaire commentaire


tabList : Accessibilite -> List Tab
tabList accessibilite =
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
    , CommentaireTab commentaire
    ]


tabMenu : Config msg -> Html msg
tabMenu config =
    tabList config.accessibilite
        |> List.filter (tabContentFields >> List.all ((==) (text "")) >> not)
        |> List.map (tabMenuEntry config)
        |> ul
            [ attribute "aria-label" "Sections"
            , class "nav nav-pills mb-2"
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
    case maybeValue of
        [] ->
            text ""

        strings ->
            strings
                |> List.map (\v -> span [ class "badge badge-info" ] [ text v ])
                |> List.intersperse (text " ")
                |> vFieldWrapper name help


textField : { name : String, help : String, maybeValue : Maybe String } -> Html msg
textField { name, help, maybeValue } =
    case maybeValue of
        Just "" ->
            text ""

        Just value ->
            hFieldWrapper name help [ div [ class "lead mb-0 my-1" ] [ text value ] ]

        Nothing ->
            text ""


view : Config msg -> Html msg
view config =
    div [ class "mb-2" ]
        [ tabMenu config
        , div [ class "tab-content" ]
            [ tabContent config
            ]
        ]
