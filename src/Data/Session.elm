module Data.Session exposing
    ( Notif(..)
    , Session
    , Store
    , clearNotif
    , deserializeStore
    , notifyError
    , notifyHttpError
    , resetAutocomplete
    , serializeStore
    )

import Browser.Navigation as Nav
import Data.Activite as Activite exposing (Activite)
import Data.Autocomplete as Autocomplete
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Http
import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode
import Request.Error


type Notif
    = ErrorNotif String


type alias Session =
    { navKey : Nav.Key
    , clientUrl : String
    , store : Store
    , notifs : List Notif
    , commune : Maybe Commune
    , activites : List Activite
    , erps : List Erp
    , activiteSlug : Maybe Activite.Slug
    , erpSlug : Maybe Erp.Slug
    , autocomplete :
        { search : String
        , results : List Autocomplete.Entry
        }
    }


{-| A serializable data structure holding session information you want to share
across browser restarts, typically in localStorage.
-}
type alias Store =
    { counter : Int }


clearNotif : Notif -> Session -> Session
clearNotif notif session =
    { session | notifs = session.notifs |> List.filter ((/=) notif) }


defaultStore : Store
defaultStore =
    { counter = 0 }


decodeStore : Decoder Store
decodeStore =
    Decode.map Store
        (Decode.field "counter" Decode.int)


encodeStore : Store -> Encode.Value
encodeStore v =
    Encode.object
        [ ( "counter", Encode.int v.counter )
        ]


deserializeStore : String -> Store
deserializeStore =
    Decode.decodeString decodeStore >> Result.withDefault defaultStore


notifyError : String -> Session -> Session
notifyError message session =
    { session | notifs = ErrorNotif message :: session.notifs }


notifyHttpError : Http.Error -> Session -> Session
notifyHttpError error session =
    session |> notifyError (Request.Error.toString error)


resetAutocomplete : Session -> Session
resetAutocomplete session =
    { session | autocomplete = { search = "", results = [] } }


serializeStore : Store -> String
serializeStore =
    encodeStore >> Encode.encode 0
