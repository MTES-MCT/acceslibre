module Request.Error exposing (toString)

import Http


toString : Http.Error -> String
toString error =
    case error of
        Http.BadUrl url ->
            "URL malformée: " ++ url

        Http.Timeout ->
            "Délai de traitement de la rquête expiré."

        Http.NetworkError ->
            "Erreur réseau : êtes-vous connecté ?"

        Http.BadStatus status_code ->
            "Erreur HTTP " ++ String.fromInt status_code

        Http.BadBody body ->
            "Impossible de décoder le corps de la réponse HTTP : " ++ body
