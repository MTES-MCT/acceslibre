module Request.Accessibilite.Help exposing (get)

import Data.Accessibilite.Help as Help exposing (Help)
import Data.Session as Session exposing (Session)
import Http
import RemoteData exposing (WebData)
import Url.Builder as UrlBuilder


get : Session -> (WebData Help -> msg) -> Cmd msg
get session msg =
    Http.get
        { url = UrlBuilder.crossOrigin session.serverUrl [ "api", "accessibilite", "help" ] []
        , expect = Http.expectJson (RemoteData.fromResult >> msg) Help.decode
        }
