module Views.Page exposing (ActivePage(..), Config, frame)

import Browser exposing (Document)
import Data.Commune as Commune exposing (Commune)
import Data.Session as Session exposing (Session)
import Dict
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Route


type ActivePage
    = Home (Maybe Commune) -- XXX: remove this
    | Other


type alias Config msg =
    { session : Session
    , autocomplete : String -> msg
    , clearNotif : Session.Notif -> msg
    , activePage : ActivePage
    }


frame : Config msg -> ( String, List (Html msg) ) -> Document msg
frame config ( title, content ) =
    { title = title ++ " · access4all"
    , body =
        [ viewHeader config
        , main_ [] content
        , viewNotifs config
        ]
    }


viewHeader : Config msg -> Html msg
viewHeader { session, autocomplete } =
    -- TODO: revamp header for mobile with search always visible
    nav [ class "navbar navbar-expand-lg navbar-dark a4a-navbar" ]
        [ a
            [ class "navbar-brand", Route.href Route.Home ]
            [ text "access4all" ]
        , button
            [ attribute "aria-controls" "navbarSupportedContent"
            , attribute "aria-expanded" "false"
            , attribute "aria-label" "Toggle navigation"
            , class "navbar-toggler"
            , attribute "data-target" "#navbarSupportedContent"
            , attribute "data-toggle" "collapse"
            , type_ "button"
            ]
            [ span [ class "navbar-toggler-icon" ]
                []
            ]
        , div [ class "collapse navbar-collapse", id "navbarSupportedContent" ]
            [ Dict.values Commune.communes
                |> List.map
                    (\commune ->
                        li
                            [ classList
                                [ ( "nav-item", True )
                                , ( "active"
                                  , session.commune == Just commune
                                  )
                                ]
                            ]
                            [ a
                                [ class "nav-link"
                                , Route.href (Route.CommuneHome commune)
                                ]
                                [ text commune.nom ]
                            ]
                    )
                |> ul [ class "navbar-nav mr-auto" ]
            , Html.form
                [ class "form-inline my-2 my-lg-0 ml-1 flex-fill"
                ]
                [ div [ class "a4a-autocomplete" ]
                    [ input
                        [ type_ "search"
                        , class "form-control mr-sm-2 w-100"
                        , attribute "aria-label" "Rechercher"
                        , attribute "autocomplete" "off"
                        , onInput autocomplete
                        , value session.autocomplete.search
                        , placeholder
                            ("Rue, restaurant, café, poste, pharmacie..."
                                ++ (case session.commune of
                                        Just commune ->
                                            " à " ++ commune.nom

                                        Nothing ->
                                            ""
                                   )
                            )
                        ]
                        []
                    , if List.length session.autocomplete.results > 0 then
                        session.autocomplete.results
                            |> List.map
                                (\entry ->
                                    div []
                                        [ a [ Route.href (Route.forAutocompleteEntry entry) ]
                                            [ text entry.value ]
                                        ]
                                )
                            |> div [ class "a4a-autocomplete-items" ]

                      else
                        text ""
                    ]
                ]
            ]
        ]


viewNotifs : Config msg -> Html msg
viewNotifs { session, clearNotif } =
    session.notifs
        |> List.map
            (\notif ->
                case notif of
                    Session.ErrorNotif message ->
                        div
                            [ class "alert alert-danger a4a-notif"
                            , attribute "role" "alert"
                            ]
                            [ button
                                [ type_ "button"
                                , class "close"
                                , attribute "data-dismiss" "alert"
                                , attribute "aria-label" "Close"
                                , onClick (clearNotif notif)
                                ]
                                [ span [ attribute "aria-hidden" "true" ] [ text "×" ] ]
                            , text message
                            ]
            )
        |> div [ class "a4a-notifs" ]
