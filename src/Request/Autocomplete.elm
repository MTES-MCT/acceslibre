module Request.Autocomplete exposing (errorToString, run)

import Data.Autocomplete as Autocomplete
import Data.Commune as Commune
import Data.Session exposing (Session)
import Http exposing (Error(..))
import Json.Decode as Decode exposing (Decoder)
import Url.Builder as UrlBuilder


errorToString : Http.Error -> String
errorToString error =
    case error of
        BadUrl url ->
            "Bad url: " ++ url

        Timeout ->
            "Request timed out."

        NetworkError ->
            "Network error. Are you online?"

        BadStatus status_code ->
            "HTTP error " ++ String.fromInt status_code

        BadBody body ->
            "Unable to parse response body: " ++ body


run : Session -> (Result Error (List Autocomplete.Entry) -> msg) -> Cmd msg
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
