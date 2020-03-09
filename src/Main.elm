module Main exposing (main)

import Browser exposing (Document)
import Browser.Navigation as Nav
import Data.Autocomplete as Autocomplete
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Http
import Page.Home as Home
import Ports
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
    | AutocompleteReceived (Result Http.Error (List Autocomplete.Entry))
    | HomeMsg Home.Msg
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
                    toPage HomePage (Home.init model.session Nothing) HomeMsg

                Route.CommuneHome commune ->
                    toPage HomePage (Home.init model.session (Just commune)) HomeMsg

                Route.CommuneActivite commune activite ->
                    toPage HomePage (Home.init model.session (Just commune)) HomeMsg

                Route.CommuneActiviteErp commune activite erp ->
                    toPage HomePage (Home.init model.session (Just commune)) HomeMsg

                Route.CommuneErp commune erp ->
                    toPage HomePage (Home.init model.session (Just commune)) HomeMsg


init : Flags -> Url -> Nav.Key -> ( Model, Cmd Msg )
init flags url navKey =
    let
        session =
            { clientUrl = flags.clientUrl
            , navKey = navKey
            , store = Session.deserializeStore flags.rawStore
            , commune = Nothing
            , autocomplete = { search = "", results = [] }
            }
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
                autocomplete =
                    session.autocomplete

                newSession =
                    { session | autocomplete = { autocomplete | search = search, results = [] } }
            in
            ( { model | session = newSession }
            , Request.Autocomplete.run newSession AutocompleteReceived
            )

        ( AutocompleteReceived (Ok results), _ ) ->
            let
                autocomplete =
                    session.autocomplete

                newAutocomplete =
                    { autocomplete | results = results }
            in
            ( { model | session = { session | autocomplete = newAutocomplete } }, Cmd.none )

        ( AutocompleteReceived (Err error), _ ) ->
            let
                _ =
                    Debug.log "error de coding autocomplete results" error
            in
            ( model, Cmd.none )

        ( HomeMsg homeMsg, HomePage homeModel ) ->
            toPage HomePage HomeMsg Home.update homeMsg homeModel

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
            Page.Config session Autocomplete

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
