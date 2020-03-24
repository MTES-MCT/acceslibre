module Main exposing (main)

import Browser exposing (Document)
import Browser.Events as BE
import Browser.Navigation as Nav
import Data.Accessibilite.Help as Help exposing (Help)
import Data.Autocomplete as Autocomplete
import Data.Point as Point exposing (Point)
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Http
import Json.Decode as Decode
import Page.Home as Home
import Ports
import RemoteData exposing (WebData)
import Request.Accessibilite.Help
import Request.Autocomplete
import Route exposing (Route)
import Url exposing (Url)
import Views.Page as Page


type alias Flags =
    { clientUrl : String
    , rawStore : String
    }


type Page
    = Blank
    | HomePage Home.Model
    | NotFound


type alias Model =
    { page : Page
    , session : Session
    }


type Msg
    = Autocomplete String
    | AutocompleteBanReceived (Result Http.Error (List Autocomplete.BanEntry))
    | AutocompleteErpReceived (Result Http.Error (List Autocomplete.ErpEntry))
    | AutocompleteClose
    | ClearNotif Session.Notif
    | HelpReceived (WebData Help)
    | HomeMsg Home.Msg
    | LocateMap Point
    | Search
    | StoreChanged String
    | UrlChanged Url
    | UrlRequested Browser.UrlRequest


setRoute : Maybe Route -> Model -> ( Model, Cmd Msg )
setRoute maybeRoute model =
    let
        toPage page subInit subMsg =
            let
                ( subModel, newSession, subCmds ) =
                    subInit

                storeCmd =
                    if model.session.store /= newSession.store then
                        newSession.store |> Session.serializeStore |> Ports.saveStore

                    else
                        Cmd.none
            in
            ( { model | session = newSession, page = page subModel }
            , Cmd.batch [ Cmd.map subMsg subCmds, storeCmd ]
            )
    in
    case maybeRoute of
        Nothing ->
            ( { model | page = NotFound }
            , Cmd.none
            )

        Just route ->
            case route of
                Route.Home ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.CommuneHome _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.Activite _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.Erp _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.CommuneActivite _ _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.CommuneActiviteErp _ _ _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.CommuneErp _ _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.CommuneSearch _ _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg

                Route.Search _ ->
                    toPage HomePage (Home.init model.session route) HomeMsg


init : Flags -> Url -> Nav.Key -> ( Model, Cmd Msg )
init flags url navKey =
    let
        serverUrl =
            if flags.clientUrl == "http://localhost:3000/" then
                "http://localhost:8000"

            else
                "https://access4all.beta.gouv.fr"

        session =
            Session.default navKey flags.clientUrl serverUrl
                |> Session.initStore flags.rawStore
    in
    setRoute (Route.fromUrl url)
        { page = Blank
        , session = session
        }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg ({ page, session } as model) =
    let
        toPage toModel toMsg subUpdate subMsg subModel =
            let
                ( newModel, newSession, newCmd ) =
                    subUpdate session subMsg subModel

                storeCmd =
                    if session.store /= newSession.store then
                        newSession.store |> Session.serializeStore |> Ports.saveStore

                    else
                        Cmd.none
            in
            ( { model | session = newSession, page = toModel newModel }
            , Cmd.map toMsg (Cmd.batch [ newCmd, storeCmd ])
            )
    in
    case ( msg, page ) of
        ( Autocomplete search, _ ) ->
            let
                newSession =
                    session
                        |> Session.purgeAutocomplete
                        |> Session.setSearch search
            in
            ( { model | session = newSession }
            , if String.length search > 2 then
                Cmd.batch
                    [ Request.Autocomplete.ban newSession AutocompleteBanReceived
                    , Request.Autocomplete.erp newSession AutocompleteErpReceived
                    ]

              else
                Cmd.none
            )

        ( AutocompleteBanReceived (Ok results), _ ) ->
            ( { model | session = session |> Session.addBanEntries results }, Cmd.none )

        ( AutocompleteBanReceived (Err error), _ ) ->
            ( { model | session = session |> Session.notifyHttpError error }, Cmd.none )

        ( AutocompleteErpReceived (Ok results), _ ) ->
            ( { model | session = session |> Session.addErpEntries results }, Cmd.none )

        ( AutocompleteErpReceived (Err error), _ ) ->
            ( { model | session = session |> Session.notifyHttpError error }, Cmd.none )

        ( AutocompleteClose, _ ) ->
            ( { model | session = session |> Session.resetAutocomplete }, Cmd.none )

        ( ClearNotif notif, _ ) ->
            ( { model | session = session |> Session.clearNotif notif }, Cmd.none )

        ( LocateMap point, _ ) ->
            ( { model | session = session |> Session.resetAutocomplete }
            , Ports.locateMap (Point.encode point)
            )

        ( HelpReceived remoteData, _ ) ->
            ( { model | session = { session | help = remoteData } }, Cmd.none )

        ( HomeMsg homeMsg, HomePage homeModel ) ->
            toPage HomePage HomeMsg Home.update homeMsg homeModel

        ( Search, HomePage homeModel ) ->
            if String.length session.autocomplete.search > 2 then
                let
                    newSession =
                        Session.purgeAutocomplete session

                    searchRoute =
                        case session.commune of
                            Just commune ->
                                Route.CommuneSearch commune newSession.autocomplete.search

                            Nothing ->
                                Route.Search newSession.autocomplete.search
                in
                ( model
                , Nav.pushUrl newSession.navKey (Route.toString searchRoute)
                )

            else
                ( model, Cmd.none )

        ( StoreChanged json, _ ) ->
            ( { model | session = { session | store = Session.deserializeStore json } }
            , Cmd.none
            )

        ( UrlRequested urlRequest, _ ) ->
            case urlRequest of
                Browser.Internal url ->
                    ( model, Nav.pushUrl session.navKey (Url.toString url) )

                Browser.External href ->
                    ( model, Nav.load href )

        ( UrlChanged url, _ ) ->
            { model | session = Session.resetAutocomplete session }
                |> setRoute (Route.fromUrl url)

        ( _, NotFound ) ->
            ( { model | page = NotFound }, Cmd.none )

        ( _, _ ) ->
            ( model, Cmd.none )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Ports.storeChanged StoreChanged

        -- autocomplete panel close
        , BE.onMouseUp (Decode.succeed AutocompleteClose)
        , case model.page of
            HomePage _ ->
                Sub.none

            NotFound ->
                Sub.none

            Blank ->
                Sub.none
        ]


view : Model -> Document Msg
view { page, session } =
    let
        pageConfig =
            Page.Config session Autocomplete ClearNotif LocateMap Search

        mapMsg msg ( title, content ) =
            ( title, content |> List.map (Html.map msg) )
    in
    case page of
        HomePage homeModel ->
            Home.view session homeModel
                |> mapMsg HomeMsg
                |> Page.frame (pageConfig (Page.Home homeModel.commune))

        NotFound ->
            ( "Page non trouvée", [ Html.text "Page non trouvée" ] )
                |> Page.frame (pageConfig Page.Other)

        Blank ->
            ( "", [] )
                |> Page.frame (pageConfig Page.Other)


main : Program Flags Model Msg
main =
    Browser.application
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        , onUrlChange = UrlChanged
        , onUrlRequest = UrlRequested
        }
