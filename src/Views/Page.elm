module Views.Page exposing (ActivePage(..), Config, frame)

import Browser exposing (Document)
import Data.Commune as Commune exposing (Commune)
import Data.Session exposing (Session)
import Dict
import Html exposing (..)
import Html.Attributes exposing (..)
import Route


type ActivePage
    = Home (Maybe Commune)
    | Other


type alias Config =
    { session : Session
    , activePage : ActivePage
    }


frame : Config -> ( String, List (Html msg) ) -> Document msg
frame config ( title, content ) =
    { title = title ++ " | elm-kitchen"
    , body =
        [ viewHeader config
        , main_ [] content
        ]
    }


viewHeader : Config -> Html msg
viewHeader { activePage } =
    nav [ class "navbar navbar-expand-lg navbar-dark a4a-navbar" ]
        [ a
            [ class "navbar-brand"
            , href "/"
            ]
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
            [ Commune.communes
                |> Dict.toList
                |> List.map
                    (\( slug, commune ) ->
                        li
                            [ classList
                                [ ( "nav-item", True )
                                , ( "active"
                                  , case activePage of
                                        Home (Just c) ->
                                            commune == c

                                        _ ->
                                            False
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
                [ action "/app/56-lorient/"
                , class "form-inline my-2 my-lg-0 ml-1 flex-fill"
                , method "get"
                ]
                [ input
                    [ attribute "aria-label" "Rechercher"
                    , attribute "autocomplete" "off"
                    , class "form-control mr-sm-2 w-100"
                    , id "q"
                    , name "q"
                    , placeholder "Rue, restaurant, café, poste, pharmacie... à Lorient"
                    , type_ "search"
                    , value ""
                    ]
                    []
                ]
            ]
        ]
