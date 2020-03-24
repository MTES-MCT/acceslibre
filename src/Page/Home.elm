module Page.Home exposing (Model, Msg(..), init, update, view)

import Browser.Dom as Dom
import Data.Accessibilite as Accessibilite exposing (Accessibilite)
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
import Request.Accessibilite
import Request.Activite
import Request.Erp
import Request.Pager as Pager exposing (Pager)
import Route exposing (Route)
import Task exposing (Task)
import Views.Accessibilite as AccessibiliteView
import Views.Spinner as SpinnerView


type alias Model =
    { loading : Bool
    , commune : Maybe Commune
    , erp : Maybe Erp
    , accessibilite : Maybe Accessibilite
    , accessibiliteTab : Maybe AccessibiliteView.Tab
    , activiteSlug : Maybe Activite.Slug
    , erpSlug : Maybe Erp.Slug
    , infiniteScroll : InfiniteScroll.Model Msg
    , search : Maybe String
    }


type Msg
    = AccessibiliteReceived (Result Http.Error Accessibilite)
    | ActivitesReceived (Result Http.Error (List Activite))
    | Back
    | ErpDetailReceived (Result Http.Error Erp)
    | ErpListReceived (WebData (Pager Erp))
    | InfiniteScrollMsg InfiniteScroll.Msg
    | LocateOnMap Erp
    | NextErpListPage ()
    | NextErpListReceived (WebData (Pager Erp))
    | NoOp
    | Search
    | SwitchAccessibiliteTab AccessibiliteView.Tab


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
            , accessibilite = Nothing
            , accessibiliteTab = Nothing
            , activiteSlug = Nothing
            , erpSlug = Nothing
            , infiniteScroll = defaultInfiniteScroll
            , search = Nothing
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

                Route.CommuneSearch commune search ->
                    { base
                        | commune = Just commune
                        , search = Just search
                    }

                Route.Search search ->
                    { base | search = Just search }
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
        , case model.erpSlug of
            Just erpSlug ->
                Request.Erp.get session erpSlug ErpDetailReceived

            Nothing ->
                Request.Erp.list session model.commune model.activiteSlug model.search ErpListReceived
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
        AccessibiliteReceived (Ok accessibilite) ->
            ( { model | accessibilite = Just accessibilite }
            , session
            , Cmd.none
            )

        AccessibiliteReceived (Err error) ->
            ( model, session |> Session.notifyHttpError error, Cmd.none )

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
                , case erp.accessibiliteApiUrl of
                    Just accessibiliteApiUrl ->
                        Request.Accessibilite.get accessibiliteApiUrl AccessibiliteReceived

                    Nothing ->
                        Cmd.none
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
                |> Session.purgeAutocomplete
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
            , session
                |> Session.purgeAutocomplete
                |> Session.notifyHttpError error
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
            , addMapMarkers nextErps.results
            )

        NextErpListReceived (RemoteData.Failure error) ->
            ( model, session |> Session.notifyHttpError error, Cmd.none )

        NextErpListReceived RemoteData.Loading ->
            ( model, session, Cmd.none )

        NextErpListReceived RemoteData.NotAsked ->
            ( model, session, Cmd.none )

        NoOp ->
            ( model, session, Cmd.none )

        Search ->
            ( { model | search = Just session.autocomplete.search }
            , session
            , Cmd.none
            )

        SwitchAccessibiliteTab tab ->
            ( { model | accessibiliteTab = Just tab }, session, Cmd.none )


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
    [ model.erp
        |> Maybe.map .nom
    , model.activiteSlug
        |> Maybe.andThen (\slug -> Activite.findBySlug slug session.activites)
        |> Maybe.map .nom
    , model.commune |> Maybe.map .nom |> Maybe.withDefault "Accueil" |> Just
    ]
        |> List.filterMap identity
        |> String.join " · "


erpDetailsView : Session -> Model -> Erp -> Html Msg
erpDetailsView session model erp =
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
            , case model.accessibilite of
                Just accessibilite ->
                    AccessibiliteView.view
                        { accessibilite = accessibilite
                        , activeTab = model.accessibiliteTab |> Maybe.withDefault (AccessibiliteView.EntreeTab accessibilite.entree)
                        , noOp = NoOp
                        , session = session
                        , switchTab = SwitchAccessibiliteTab
                        }

                Nothing ->
                    div [ class "alert alert-info" ]
                        [ text "Les données d'accessibilité ne sont pas encore disponibles pour cet établissement."
                        ]
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
        , if erp.accessibiliteApiUrl /= Nothing then
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
            div [ class "p-5 text-center" ] [ SpinnerView.view ]


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
                            erpDetailsView session model erp

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
