module Request.Activite exposing (list)

import Data.Activite as Activite exposing (Activite)
import Data.Commune as Commune exposing (Commune)
import Data.Session as Session exposing (Session)
import Http
import Json.Decode as Decode
import Url.Builder as UrlBuilder


list : Session -> Maybe Commune -> (Result Http.Error (List Activite) -> msg) -> Cmd msg
list session maybeCommune msg =
    Http.get
        { url =
            UrlBuilder.crossOrigin "http://localhost:8000"
                [ "api", "activites" ]
                (case maybeCommune of
                    Just commune ->
                        [ UrlBuilder.string "commune" commune.nom ]

                    Nothing ->
                        []
                )
        , expect =
            Http.expectJson msg
                (Decode.at [ "results" ]
                    (Decode.list Activite.decode)
                )
        }
