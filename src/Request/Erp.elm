module Request.Erp exposing (list)

import Data.Activite as Activite exposing (Activite)
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Data.Session as Session exposing (Session)
import Http
import Json.Decode as Decode
import Url.Builder as UrlBuilder


list : Session -> Maybe Commune -> Maybe Activite -> Maybe String -> (Result Http.Error (List Erp) -> msg) -> Cmd msg
list session maybeCommune maybeActivite maybeSearch msg =
    Http.get
        { url =
            UrlBuilder.crossOrigin "http://localhost:8000"
                [ "api", "erps" ]
                (List.concat
                    [ case maybeCommune of
                        Just commune ->
                            [ UrlBuilder.string "commune" commune.nom ]

                        Nothing ->
                            []
                    , case maybeActivite of
                        Just activite ->
                            [ UrlBuilder.string "activite" (Activite.slugToString activite.slug) ]

                        Nothing ->
                            []
                    , case maybeSearch of
                        Just search ->
                            [ UrlBuilder.string "q" search ]

                        Nothing ->
                            []
                    ]
                )
        , expect = Http.expectJson msg (Decode.at [ "results" ] (Decode.list Erp.decode))
        }
