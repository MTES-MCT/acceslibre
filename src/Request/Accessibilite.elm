module Request.Accessibilite exposing (get)

import Data.Accessibilite as Accessibilite exposing (Accessibilite)
import Data.Session as Session exposing (Session)
import Http


get : String -> (Result Http.Error Accessibilite -> msg) -> Cmd msg
get url msg =
    Http.get
        { url = url
        , expect = Http.expectJson msg Accessibilite.decode
        }
