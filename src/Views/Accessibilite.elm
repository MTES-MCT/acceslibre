module Views.Accessibilite exposing (view)

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
import Html exposing (..)
import Html.Attributes exposing (..)


type alias Config msg =
    { accessibilite : Accessibilite
    , noOp : msg
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
            [ li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                [ span []
                    [ text "Stationnement dans l'ERP "
                    , small [ class "text-muted" ]
                        [ text "Présence de stationnements au sein de l'ERP" ]
                    ]
                , span []
                    [ span []
                        [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ] []
                        , span [ class "sr-only" ]
                            [ text "Non" ]
                        ]
                    ]
                ]
            , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                [ span []
                    [ text "Stationnements PMR dans l'ERP "
                    , small [ class "text-muted" ]
                        [ text "Présence de stationnements PMR au sein de l'ERP" ]
                    ]
                , span []
                    [ span []
                        [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ] []
                        , span [ class "sr-only" ]
                            [ text "Non" ]
                        ]
                    ]
                ]
            , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                [ span []
                    [ text "Stationnement à proximité "
                    , small [ class "text-muted" ]
                        [ text "Présence de stationnements à proximité (200m)" ]
                    ]
                , span []
                    [ span []
                        [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ] []
                        , span [ class "sr-only" ] [ text "Oui" ]
                        ]
                    ]
                ]
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
            , class "btn btn-link nav-link px-2 py-1"
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
    [ AccueilTab accueil
    , CheminementExtTab cheminementExt
    , EntreeTab entree
    , LabelsTab labels
    , SanitairesTab sanitaires
    , StationnementTab stationnement
    ]
        |> List.map (tabMenuEntry False)
        |> ul
            [ attribute "aria-label" "Sections"
            , class "nav nav-tabs nav-fill mb-2"
            , attribute "role" "tablist"
            ]


view : Config msg -> Html msg
view config =
    div [ class "mb-2" ]
        [ tabMenu config
        , div [ class "tab-content" ]
            [ div [ attribute "aria-labelledby" "entree-tab", class "tab-pane active", id "entree", attribute "role" "tabpanel" ]
                [ ul [ class "list-group list-group-flush" ]
                    [ li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Plain-pied "
                            , small [ class "text-muted" ]
                                [ text "L'entrée est-elle de plain-pied ?" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ]
                                    []
                                , span [ class "sr-only" ]
                                    [ text "Non" ]
                                ]
                            ]
                        ]
                    , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Repérage de l'entrée "
                            , small [ class "text-muted" ]
                                [ text "Présence d'éléments de répérage de l'entrée" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ]
                                    []
                                , span [ class "sr-only" ]
                                    [ text "Oui" ]
                                ]
                            ]
                        ]
                    , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Entrée spécifique PMR "
                            , small [ class "text-muted" ]
                                [ text "Présence d'une entrée secondaire spécifique PMR" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ]
                                    []
                                , span [ class "sr-only" ]
                                    [ text "Non" ]
                                ]
                            ]
                        ]
                    , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Dispositif d'appel "
                            , small [ class "text-muted" ]
                                [ text "Présence d'un dispositif d'appel (ex. interphone)" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ]
                                    []
                                , span [ class "sr-only" ]
                                    [ text "Oui" ]
                                ]
                            ]
                        ]
                    ]
                ]
            , div [ attribute "aria-labelledby" "stationnement-tab", class "tab-pane", id "stationnement", attribute "role" "tabpanel" ]
                [ ul [ class "list-group list-group-flush" ]
                    [ li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Stationnement dans l'ERP "
                            , small [ class "text-muted" ]
                                [ text "Présence de stationnements au sein de l'ERP" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ] []
                                , span [ class "sr-only" ]
                                    [ text "Non" ]
                                ]
                            ]
                        ]
                    , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Stationnements PMR dans l'ERP "
                            , small [ class "text-muted" ]
                                [ text "Présence de stationnements PMR au sein de l'ERP" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ] []
                                , span [ class "sr-only" ]
                                    [ text "Non" ]
                                ]
                            ]
                        ]
                    , li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Stationnement à proximité "
                            , small [ class "text-muted" ]
                                [ text "Présence de stationnements à proximité (200m)" ]
                            ]
                        , span []
                            [ span []
                                [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ] []
                                , span [ class "sr-only" ] [ text "Oui" ]
                                ]
                            ]
                        ]
                    ]
                ]
            , div [ attribute "aria-labelledby" "accueil-tab", class "tab-pane", id "accueil", attribute "role" "tabpanel" ]
                [ ul [ class "list-group list-group-flush" ]
                    [ li [ class "list-group-item d-flex justify-content-between align-items-center p-2" ]
                        [ span []
                            [ text "Équipements sourds/malentendants "
                            , small [ class "text-muted" ] []
                            ]
                        , span [] []
                        ]
                    ]
                ]
            , div [ attribute "aria-labelledby" "sanitaires-tab", class "tab-pane", id "sanitaires", attribute "role" "tabpanel" ]
                [ ul [ class "list-group list-group-flush" ] []
                ]
            ]
        ]
