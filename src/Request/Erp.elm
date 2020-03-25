module Request.Erp exposing (get, list, listNext)

import Data.Activite as Activite
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Data.Session as Session exposing (Session)
import Http
import Json.Decode as Decode
import RemoteData exposing (WebData)
import Request.Pager as Pager exposing (Pager)
import Url.Builder as UrlBuilder


get : Session -> Erp.Slug -> (WebData Erp -> msg) -> Cmd msg
get session slug msg =
    Http.get
        { url =
            UrlBuilder.crossOrigin session.serverUrl
                [ "api", "erps", Erp.slugToString slug ]
                []
        , expect = Http.expectJson (RemoteData.fromResult >> msg) Erp.decode
        }


list : Session -> Maybe Commune -> Maybe Activite.Slug -> Maybe String -> (WebData (Pager Erp) -> msg) -> Cmd msg
list session maybeCommune maybeActiviteSlug maybeSearch msg =
    Http.get
        { url =
            UrlBuilder.crossOrigin session.serverUrl
                [ "api", "erps" ]
                (List.concat
                    [ case maybeCommune of
                        Just commune ->
                            [ UrlBuilder.string "commune" commune.nom ]

                        Nothing ->
                            []
                    , case maybeActiviteSlug of
                        Just activiteSlug ->
                            [ UrlBuilder.string "activite" (Activite.slugToString activiteSlug) ]

                        Nothing ->
                            []
                    , case maybeSearch of
                        Just search ->
                            [ UrlBuilder.string "q" search ]

                        Nothing ->
                            []
                    ]
                )
        , expect = Http.expectJson (RemoteData.fromResult >> msg) (Pager.decode Erp.decode)
        }


listNext : Session -> (WebData (Pager Erp) -> msg) -> Cmd msg
listNext session msg =
    case session.erps of
        RemoteData.Success pager ->
            case pager.next of
                Just next ->
                    Http.get
                        { url = next
                        , expect =
                            Http.expectJson (Result.map (Pager.update pager) >> RemoteData.fromResult >> msg)
                                (Pager.decode Erp.decode)
                        }

                Nothing ->
                    Cmd.none

        _ ->
            Cmd.none
