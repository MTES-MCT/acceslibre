module Request.Autocomplete exposing (ban, erp)

import Data.Autocomplete as Autocomplete
import Data.Commune as Commune
import Data.Session exposing (Session)
import Http
import Json.Decode as Decode
import Url.Builder as UrlBuilder


ban : Session -> (Result Http.Error (List Autocomplete.BanEntry) -> msg) -> Cmd msg
ban session msg =
    let
        baseTerms =
            [ UrlBuilder.string "type" "street" ]

        qs =
            case session.commune of
                Just commune ->
                    baseTerms
                        ++ [ UrlBuilder.string "q" (session.autocomplete.search ++ ", " ++ commune.nom)
                           , UrlBuilder.string "lat" (String.fromFloat commune.center.lat)
                           , UrlBuilder.string "lon" (String.fromFloat commune.center.lon)
                           ]

                Nothing ->
                    baseTerms
                        ++ [ UrlBuilder.string "q" session.autocomplete.search ]
    in
    Http.get
        { url = UrlBuilder.crossOrigin "https://api-adresse.data.gouv.fr" [ "search" ] qs
        , expect =
            Http.expectJson msg
                (Decode.at [ "features" ]
                    (Decode.list Autocomplete.decodeBanEntry)
                )
        }


erp : Session -> (Result Http.Error (List Autocomplete.ErpEntry) -> msg) -> Cmd msg
erp session msg =
    let
        baseQs =
            [ UrlBuilder.string "q" session.autocomplete.search ]

        qs =
            case session.commune of
                Just commune ->
                    UrlBuilder.string "commune" commune.nom :: baseQs

                Nothing ->
                    baseQs
    in
    Http.get
        { url = UrlBuilder.crossOrigin session.serverUrl [ "app", "autocomplete" ] qs
        , expect =
            Http.expectJson msg
                (Decode.at [ "suggestions" ]
                    (Decode.list Autocomplete.decodeErpEntry)
                )
        }
