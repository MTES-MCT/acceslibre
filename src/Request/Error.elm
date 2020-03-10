module Request.Error exposing (toString)

import Http


toString : Http.Error -> Error
toString error =
    case error of
        Http.BadUrl url ->
            "Bad url: " ++ url

        Http.Timeout ->
            "Request timed out."

        Http.NetworkError ->
            "Network error. Are you online?"

        Http.BadStatus status_code ->
            "HTTP error " ++ String.fromInt status_code

        Http.BadBody body ->
            "Unable to parse response body: " ++ body
