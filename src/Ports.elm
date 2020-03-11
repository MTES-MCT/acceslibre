port module Ports exposing (communeMap, franceMap, saveStore, storeChanged)

import Json.Encode as Encode


port franceMap : () -> Cmd msg


port communeMap : Encode.Value -> Cmd msg


port saveStore : String -> Cmd msg


port storeChanged : (String -> msg) -> Sub msg
