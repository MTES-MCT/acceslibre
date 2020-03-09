module Page.Home exposing (Model, Msg(..), init, update, view)

import Data.Commune as Commune exposing (Commune)
import Data.Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Http
import Markdown
import Route exposing (Route)


type alias Model =
    { commune : Maybe Commune }


type Msg
    = NoOp


init : Session -> Maybe Commune -> ( Model, Session, Cmd Msg )
init session maybeCommune =
    ( { commune = maybeCommune }
    , { session | commune = maybeCommune }
    , Cmd.none
    )


update : Session -> Msg -> Model -> ( Model, Session, Cmd Msg )
update session msg model =
    case msg of
        NoOp ->
            ( model
            , session
            , Cmd.none
            )


view : Session -> Model -> ( String, List (Html Msg) )
view _ model =
    ( "Home"
    , [ div [ class "container-fluid p-0 m-0 a4a-app-content" ]
            [ header [ class "a4a-app-title row p-0 m-0" ]
                [ div [ class "col pt-2 pb-1" ]
                    [ h2 [ class "display-4", id "content", attribute "style" "font-size:32px" ]
                        (case model.commune of
                            Just commune ->
                                [ text "Commune de ", a [ Route.href (Route.CommuneHome commune) ] [ text commune.nom ] ]

                            Nothing ->
                                [ text "Toutes les communes" ]
                        )
                    ]
                ]
            , div [ class "row p-0 m-0" ]
                [ nav
                    [ class "a4a-app-nav col-lg-2 col-md-3 col-sm-4 d-none d-sm-block bg-light activites-list p-0 m-0 border-top overflow-auto"
                    , attribute "role" "navigation"
                    ]
                    [ h3 [ class "sr-only" ]
                        [ text "Liste des domaines d'activité" ]
                    , div [ class "list-group list-group-flush border-right" ]
                        [ a
                            [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                            , href "/56-lorient/a/non-categorises/"
                            ]
                            [ text "Activité indéterminée          " ]
                        , a
                            [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                            , href "/56-lorient/a/administration-publique/"
                            ]
                            [ text "Administration publique            "
                            , span [ class "badge badge-primary badge-pill" ]
                                [ text "1" ]
                            ]
                        ]
                    ]
                , main_ [ class "a4a-app-main col-lg-5 col-md-5 col-sm-8 erp-list p-0 m-0 border-top overflow-auto" ]
                    [ div [ class "list-group list-group-flush" ]
                        [ a
                            [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center a4a-erp-list-item"
                            , href "/56-lorient/a/musee/erp/cite-de-la-voile-eric-tabarly/"
                            ]
                            [ span [ class "flex-fill" ]
                                [ text "Cité de la voile Eric Tabarly"
                                , br [] []
                                , small [ class "text-muted" ]
                                    [ strong [] [ text "Musée" ]
                                    , text "» 7 Honoré d'Estienne d'Orves"
                                    ]
                                ]
                            , button [ class "btn btn-sm btn-outline-success mr-2 a4a-icon-btn", title "Les informations d'accessibilités sont disponibles" ]
                                [ i [ class "icon icon-checklist" ] []
                                , span [ class "sr-only" ]
                                    [ text "Les informations d'accessibilités sont disponibles" ]
                                ]
                            , button
                                [ class "btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link"
                                , attribute "data-erp-id" "11571"
                                , title "Localiser sur la carte"
                                ]
                                [ i [ class "icon icon-target" ] []
                                ]
                            ]
                        , a
                            [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center a4a-erp-list-item"
                            , href "/56-lorient/a/location-vehicules/erp/avis-budget-group-lorient-apt-cabine/"
                            ]
                            [ span [ class "flex-fill" ]
                                [ text "AVIS BUDGET  GROUP -  LORIENT APT CABINE"
                                , br [] []
                                , small [ class "text-muted" ]
                                    [ strong [] [ text "Location véhicules" ]
                                    , text "» Impasse de Beg-Er-Lann"
                                    ]
                                ]
                            , button
                                [ class "btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link"
                                , attribute "data-erp-id" "10259"
                                , title "Localiser sur la carte"
                                ]
                                [ i [ class "icon icon-target" ] []
                                ]
                            ]
                        ]
                    ]
                , div [ class "a4a-app-map col-lg-5 col-md-4 d-none d-md-block map-area p-0 m-0" ]
                    [ div [ class "a4a-map", id "map" ]
                        []
                    ]
                ]
            ]
      ]
    )
