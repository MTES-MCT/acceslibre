module Request.Accessibilite exposing (get)

import Data.Accessibilite as Accessibilite exposing (Accessibilite)
import Http
import RemoteData exposing (WebData)


get : String -> (WebData Accessibilite -> msg) -> Cmd msg
get url msg =
    Http.get
        { url = url
        , expect = Http.expectJson (RemoteData.fromResult >> msg) Accessibilite.decode
        }
