module Request.Autocomplete exposing (run)

import Data.Autocomplete as Autocomplete
import Data.Commune as Commune
import Data.Session exposing (Session)
import Http
import Json.Decode as Decode exposing (Decoder)
import Url.Builder as UrlBuilder


run : Session -> (Result Http.Error (List Autocomplete.Entry) -> msg) -> Cmd msg
run session msg =
    case session.commune of
        Just commune ->
            Http.get
                { url =
                    UrlBuilder.crossOrigin "http://localhost:8000"
                        [ "app", Commune.slugToString commune.slug, "autocomplete" ]
                        [ UrlBuilder.string "q" session.autocomplete.search
                        ]
                , expect =
                    Http.expectJson msg
                        (Decode.at [ "suggestions" ]
                            (Decode.list Autocomplete.decode)
                        )
                }

        Nothing ->
            Cmd.none
