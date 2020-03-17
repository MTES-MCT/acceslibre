module Page.Home exposing (Model, Msg(..), init, update, view)

import Browser.Dom as Dom
import Data.Activite as Activite exposing (Activite)
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import InfiniteScroll
import Json.Decode as Decode
import Ports
import RemoteData exposing (WebData)
import Request.Activite
import Request.Erp
import Request.Pager as Pager exposing (Pager)
import Route exposing (Route)
import Task exposing (Task)
import Views.Spinner as Spinner


type alias Model =
    { loading : Bool
    , commune : Maybe Commune
    , erp : Maybe Erp
    , activiteSlug : Maybe Activite.Slug
    , erpSlug : Maybe Erp.Slug
    , infiniteScroll : InfiniteScroll.Model Msg
    }


type Msg
    = ActivitesReceived (Result Http.Error (List Activite))
    | Back
    | ErpDetailReceived (Result Http.Error Erp)
    | ErpListReceived (WebData (Pager Erp))
    | InfiniteScrollMsg InfiniteScroll.Msg
    | LocateOnMap Erp
    | NextErpListPage ()
    | NextErpListReceived (WebData (Pager Erp))
    | NoOp


init : Session -> Route -> ( Model, Session, Cmd Msg )
init session route =
    let
        defaultInfiniteScroll =
            InfiniteScroll.init (\_ -> Task.perform NextErpListPage (Task.succeed ()))
                |> InfiniteScroll.offset 100

        base =
            { loading = True
            , commune = Nothing
            , erp = Nothing
            , activiteSlug = Nothing
            , erpSlug = Nothing
            , infiniteScroll = defaultInfiniteScroll
            }

        model =
            case route of
                Route.Home ->
                    base

                Route.CommuneHome commune ->
                    { base | commune = Just commune }

                Route.Activite activiteSlug ->
                    { base | activiteSlug = Just activiteSlug }

                Route.Erp erpSlug ->
                    { base | erpSlug = Just erpSlug }

                Route.CommuneActivite commune activiteSlug ->
                    { base
                        | commune = Just commune
                        , activiteSlug = Just activiteSlug
                    }

                Route.CommuneActiviteErp commune activiteSlug erpSlug ->
                    { base
                        | commune = Just commune
                        , activiteSlug = Just activiteSlug
                        , erpSlug = Just erpSlug
                    }

                Route.CommuneErp commune erpSlug ->
                    { base
                        | commune = Just commune
                        , erpSlug = Just erpSlug
                    }
    in
    ( model
    , { session
        | commune = model.commune
        , activiteSlug = model.activiteSlug
        , erpSlug = model.erpSlug
      }
    , Cmd.batch
        [ case model.commune of
            Just commune ->
                Ports.communeMap (Commune.encode commune)

            Nothing ->
                Ports.franceMap ()
        , if session.activites == [] || session.commune /= model.commune then
            Request.Activite.list session model.commune ActivitesReceived

          else
            Cmd.none
        , Request.Erp.list session model.commune model.activiteSlug Nothing ErpListReceived
        , case model.erpSlug of
            Just erpSlug ->
                Request.Erp.get session erpSlug ErpDetailReceived

            Nothing ->
                Cmd.none
        ]
    )


scrollTop : String -> Task Dom.Error ()
scrollTop id =
    Dom.setViewportOf id 0 0


addMapMarkers : List Erp -> Cmd Msg
addMapMarkers =
    Erp.toJsonList (Route.forErp >> Route.toString)
        >> Ports.addMapMarkers


update : Session -> Msg -> Model -> ( Model, Session, Cmd Msg )
update session msg model =
    case msg of
        ActivitesReceived (Ok activites) ->
            ( model
            , { session | activites = activites }
            , scrollTop "a4a-activite-list" |> Task.attempt (always NoOp)
            )

        ActivitesReceived (Err error) ->
            ( model, session |> Session.notifyHttpError error, Cmd.none )

        Back ->
            ( { model | erp = Nothing }, session, Cmd.none )

        ErpDetailReceived (Ok erp) ->
            ( { model | erp = Just erp }
            , session
            , Cmd.batch
                [ addMapMarkers [ erp ]
                , Ports.openMapErpMarker (Route.toString (Route.forErp erp))
                ]
            )

        ErpDetailReceived (Err error) ->
            ( model, session |> Session.notifyHttpError error, Cmd.none )

        ErpListReceived (RemoteData.Success erps) ->
            ( { model
                | infiniteScroll = InfiniteScroll.stopLoading model.infiniteScroll
                , loading = False
              }
            , { session | erps = RemoteData.Success erps }
            , Cmd.batch
                [ scrollTop "a4a-erp-list" |> Task.attempt (always NoOp)

                -- only add erp list markers to map when an erp is not opened
                , if model.erp == Nothing then
                    addMapMarkers erps.results

                  else
                    Cmd.none
                ]
            )

        ErpListReceived (RemoteData.Failure error) ->
            ( { model
                | infiniteScroll = InfiniteScroll.stopLoading model.infiniteScroll
                , loading = False
              }
            , session |> Session.notifyHttpError error
            , Cmd.none
            )

        ErpListReceived RemoteData.NotAsked ->
            ( model, session, Cmd.none )

        ErpListReceived RemoteData.Loading ->
            ( model, session, Cmd.none )

        LocateOnMap erp ->
            ( model
            , session
            , Ports.openMapErpMarker (Route.toString (Route.forErp erp))
            )

        InfiniteScrollMsg msg_ ->
            let
                ( infiniteScroll, cmd ) =
                    InfiniteScroll.update InfiniteScrollMsg msg_ model.infiniteScroll
            in
            ( { model | infiniteScroll = infiniteScroll }
            , session
            , cmd
            )

        NextErpListPage () ->
            ( model
            , session
            , Request.Erp.listNext session NextErpListReceived
            )

        NextErpListReceived (RemoteData.Success nextErps) ->
            ( { model | infiniteScroll = InfiniteScroll.stopLoading model.infiniteScroll }
            , { session | erps = RemoteData.Success nextErps }
            , Cmd.none
            )

        NextErpListReceived (RemoteData.Failure error) ->
            ( model, session |> Session.notifyHttpError error, Cmd.none )

        NextErpListReceived RemoteData.Loading ->
            ( model, session, Cmd.none )

        NextErpListReceived RemoteData.NotAsked ->
            ( model, session, Cmd.none )

        NoOp ->
            ( model, session, Cmd.none )


activitesListView : Session -> Model -> Html Msg
activitesListView session model =
    session.activites
        |> List.map
            (\activite ->
                a
                    [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                    , classList
                        [ ( "active"
                          , model.activiteSlug
                                == Just activite.slug
                                || (model.erp
                                        |> Maybe.andThen .activite
                                        |> Maybe.map (.slug >> (==) activite.slug)
                                        |> Maybe.withDefault False
                                   )
                          )
                        ]
                    , case model.commune of
                        Just commune ->
                            Route.href (Route.CommuneActivite commune activite.slug)

                        Nothing ->
                            Route.href (Route.Activite activite.slug)
                    ]
                    [ text activite.nom
                    , case activite.count of
                        Just count ->
                            span [ class "badge badge-primary badge-pill" ] [ text (String.fromInt count) ]

                        Nothing ->
                            text ""
                    ]
            )
        |> div [ class "list-group list-group-flush border-right" ]


headerView : Session -> Model -> Html Msg
headerView session model =
    header [ class "a4a-app-title row p-0 m-0" ]
        [ div [ class "col pt-2 pb-1" ]
            [ h2 [ class "display-4", id "content", attribute "style" "font-size:32px" ]
                [ case model.commune of
                    Just commune ->
                        span []
                            [ text "Commune de "
                            , a [ Route.href (Route.CommuneHome commune) ] [ text commune.nom ]
                            ]

                    Nothing ->
                        text "Toutes les communes"
                , case model.activiteSlug of
                    Just activiteSlug ->
                        small [ class "text-muted" ]
                            [ text " » "
                            , session.activites
                                |> Activite.findBySlug activiteSlug
                                |> Maybe.map .nom
                                |> Maybe.withDefault ""
                                |> text
                            ]

                    Nothing ->
                        text ""
                ]
            ]
        ]


pageTitle : Session -> Model -> String
pageTitle session model =
    [ model.activiteSlug
        |> Maybe.andThen (\slug -> Activite.findBySlug slug session.activites)
        |> Maybe.map .nom
    , model.commune |> Maybe.map .nom |> Maybe.withDefault "Accueil" |> Just
    ]
        |> List.filterMap identity
        |> String.join " · "


accessibiliteView : Html Msg
accessibiliteView =
    div [ class "mb-2" ]
        [ ul
            [ attribute "aria-label" "Sections"
            , class "nav nav-pills nav-fill mb-2"
            , attribute "role" "tablist"
            ]
            [ li [ class "nav-item" ]
                [ a
                    [ attribute "aria-controls" "entree"
                    , attribute "aria-selected" "true"
                    , class "nav-link px-2 py-1 active"
                    , attribute "data-toggle" "tab"
                    , href "#entree"
                    , id "entree-tab"
                    , attribute "role" "tab"
                    ]
                    [ i [ class "icon icon-entrance mr-2" ]
                        []
                    , text "Entrée        "
                    ]
                ]
            , li [ class "nav-item" ]
                [ a
                    [ attribute "aria-controls" "stationnement"
                    , attribute "aria-selected" "false"
                    , class "nav-link px-2 py-1"
                    , attribute "data-toggle" "tab"
                    , href "#stationnement"
                    , id "stationnement-tab"
                    , attribute "role" "tab"
                    ]
                    [ i [ class "icon icon-car mr-2" ]
                        []
                    , text "Stationnement        "
                    ]
                ]
            , li [ class "nav-item" ]
                [ a
                    [ attribute "aria-controls" "accueil"
                    , attribute "aria-selected" "false"
                    , class "nav-link px-2 py-1"
                    , attribute "data-toggle" "tab"
                    , href "#accueil"
                    , id "accueil-tab"
                    , attribute "role" "tab"
                    ]
                    [ i [ class "icon icon-users mr-2" ]
                        []
                    , text "Accueil        "
                    ]
                ]
            , li [ class "nav-item" ]
                [ a
                    [ attribute "aria-controls" "sanitaires"
                    , attribute "aria-selected" "false"
                    , class "nav-link px-2 py-1"
                    , attribute "data-toggle" "tab"
                    , href "#sanitaires"
                    , id "sanitaires-tab"
                    , attribute "role" "tab"
                    ]
                    [ i [ class "icon icon-male-female mr-2" ]
                        []
                    , text "Sanitaires        "
                    ]
                ]
            ]
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
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ]
                                    []
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
                                [ i [ class "icon icon-times-circle text-danger", attribute "style" "font-size:1.2rem" ]
                                    []
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
                                [ i [ class "icon icon-check-circle text-success", attribute "style" "font-size:1.2rem" ]
                                    []
                                , span [ class "sr-only" ]
                                    [ text "Oui" ]
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
                            , small [ class "text-muted" ]
                                []
                            ]
                        , span []
                            []
                        ]
                    ]
                ]
            , div [ attribute "aria-labelledby" "sanitaires-tab", class "tab-pane", id "sanitaires", attribute "role" "tabpanel" ]
                [ ul [ class "list-group list-group-flush" ]
                    []
                ]
            ]
        ]


erpDetailsView : Session -> Erp -> Html Msg
erpDetailsView session erp =
    div [ class "px-3" ]
        [ p [ class "pt-2" ]
            [ a
                [ Route.href
                    (case ( session.commune, erp.activite ) of
                        ( Just commune, Just activite ) ->
                            Route.CommuneActivite commune activite.slug

                        ( Just commune, Nothing ) ->
                            Route.CommuneHome commune

                        ( Nothing, Just activite ) ->
                            Route.Activite activite.slug

                        _ ->
                            Route.Home
                    )
                ]
                [ text "« Retour" ]
            ]
        , div [ class "a4a-erp-details" ]
            [ h3 []
                [ text erp.nom
                , case erp.activite of
                    Just activite ->
                        small [ class "text-muted" ] [ text (" " ++ activite.nom) ]

                    Nothing ->
                        text ""
                ]
            , address [] [ em [] [ text erp.adresse ] ]

            -- TODO: add accessibiliteView
            ]
        ]


erpListEntryView : Erp -> Html Msg
erpListEntryView erp =
    Html.a
        [ class "list-group-item list-group-item-action d-flex justify-content-between align-items-center a4a-erp-list-item"
        , case Commune.findByNom erp.commune of
            Just commune ->
                Route.href (Route.CommuneErp commune erp.slug)

            Nothing ->
                Route.href (Route.Erp erp.slug)
        ]
        [ span [ class "flex-fill pr-2" ]
            [ text erp.nom
            , br [] []
            , small [ class "text-muted" ]
                [ case erp.activite of
                    Just activite ->
                        span [] [ strong [] [ text activite.nom ], text " » " ]

                    Nothing ->
                        text ""
                , text erp.adresse
                ]
            ]
        , if erp.hasAccessibilite then
            button
                [ class "btn btn-sm btn-outline-success mr-2 a4a-icon-btn"
                , title "Les informations d'accessibilité sont disponibles"
                ]
                [ i [ class "icon icon-checklist" ] []
                , span [ class "sr-only" ]
                    [ text "Les informations d'accessibilités sont disponibles" ]
                ]

          else
            text ""
        , button
            [ type_ "button"
            , class "btn btn-sm btn-outline-primary d-none d-sm-none d-md-block a4a-icon-btn a4a-geo-link"
            , attribute "data-erp-id" "11571"
            , title "Localiser sur la carte"
            , attribute "aria-label" "Localiser sur la carte"
            , custom "click"
                (Decode.succeed
                    { message = LocateOnMap erp
                    , stopPropagation = True
                    , preventDefault = True
                    }
                )
            ]
            [ i [ class "icon icon-target" ] []
            ]
        ]


erpListView : Session -> Model -> Html Msg
erpListView session model =
    case session.erps of
        RemoteData.Success erps ->
            erps.results
                |> List.map (\erp -> erpListEntryView erp)
                |> div
                    [ class "list-group list-group-flush a4a-erp-list-inner"
                    , classList [ ( "loading", model.loading ) ]
                    ]

        _ ->
            div [ class "p-5 text-center" ] [ Spinner.view ]


view : Session -> Model -> ( String, List (Html Msg) )
view session model =
    ( pageTitle session model
    , [ div [ class "container-fluid p-0 m-0 a4a-app-content" ]
            [ headerView session model
            , div [ class "row p-0 m-0" ]
                [ nav
                    [ class "a4a-app-nav col-lg-2 col-md-3 col-sm-4 d-none d-sm-block bg-light activites-list p-0 m-0 border-top overflow-auto"
                    , id "a4a-activite-list"
                    , attribute "role" "navigation"
                    ]
                    [ h3 [ class "sr-only" ] [ text "Liste des domaines d'activité" ]
                    , activitesListView session model
                    ]
                , main_
                    [ class "a4a-app-main col-lg-5 col-md-5 col-sm-8 erp-list p-0 m-0 border-top overflow-auto"
                    , id "a4a-erp-list"
                    , InfiniteScroll.infiniteScroll InfiniteScrollMsg
                    ]
                    [ case model.erp of
                        Just erp ->
                            erpDetailsView session erp

                        Nothing ->
                            erpListView session model
                    ]
                , div [ class "a4a-app-map col-lg-5 col-md-4 d-none d-md-block map-area p-0 m-0" ]
                    [ div [ class "a4a-map", id "map" ] []
                    ]
                ]
            ]
      ]
    )
