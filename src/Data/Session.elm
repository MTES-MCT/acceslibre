module Data.Session exposing
    ( Notif(..)
    , Session
    , Store
    , addBanEntries
    , addErpEntries
    , clearNotif
    , default
    , deserializeStore
    , initStore
    , notifyError
    , notifyHttpError
    , purgeAutocomplete
    , resetAutocomplete
    , serializeStore
    , setSearch
    )

import Browser.Navigation as Nav
import Data.Activite as Activite exposing (Activite)
import Data.Autocomplete as Autocomplete exposing (Autocomplete)
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Http
import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode
import RemoteData exposing (WebData)
import Request.Error
import Request.Pager as Pager exposing (Pager)


type Notif
    = ErrorNotif String


type alias Session =
    { navKey : Nav.Key
    , clientUrl : String
    , serverUrl : String
    , store : Store
    , notifs : List Notif
    , commune : Maybe Commune
    , activites : List Activite
    , erps : WebData (Pager Erp)
    , activiteSlug : Maybe Activite.Slug
    , erpSlug : Maybe Erp.Slug
    , autocomplete : Autocomplete
    }


type alias Store =
    {}


addBanEntries : List Autocomplete.BanEntry -> Session -> Session
addBanEntries bans ({ autocomplete } as session) =
    { session | autocomplete = { autocomplete | bans = bans } }


addErpEntries : List Autocomplete.ErpEntry -> Session -> Session
addErpEntries erps ({ autocomplete } as session) =
    { session | autocomplete = { autocomplete | erps = erps } }


clearNotif : Notif -> Session -> Session
clearNotif notif session =
    { session | notifs = session.notifs |> List.filter ((/=) notif) }


default : Nav.Key -> String -> String -> Session
default navKey clientUrl serverUrl =
    { navKey = navKey
    , clientUrl = clientUrl
    , serverUrl = serverUrl
    , store = defaultStore
    , notifs = []
    , commune = Nothing
    , activites = []
    , erps = RemoteData.NotAsked
    , activiteSlug = Nothing
    , erpSlug = Nothing
    , autocomplete = Autocomplete.default
    }


defaultStore : Store
defaultStore =
    {}


decodeStore : Decoder Store
decodeStore =
    Decode.succeed {}


encodeStore : Store -> Encode.Value
encodeStore _ =
    Encode.object []


deserializeStore : String -> Store
deserializeStore =
    Decode.decodeString decodeStore >> Result.withDefault defaultStore


initStore : String -> Session -> Session
initStore string session =
    { session | store = deserializeStore string }


notifyError : String -> Session -> Session
notifyError message session =
    { session | notifs = ErrorNotif message :: session.notifs }


notifyHttpError : Http.Error -> Session -> Session
notifyHttpError error session =
    session |> notifyError (Request.Error.toString error)


purgeAutocomplete : Session -> Session
purgeAutocomplete ({ autocomplete } as session) =
    { session | autocomplete = { autocomplete | bans = [], erps = [] } }


setSearch : String -> Session -> Session
setSearch search ({ autocomplete } as session) =
    { session | autocomplete = { autocomplete | search = search } }


resetAutocomplete : Session -> Session
resetAutocomplete session =
    { session | autocomplete = Autocomplete.default }


serializeStore : Store -> String
serializeStore =
    encodeStore >> Encode.encode 0
