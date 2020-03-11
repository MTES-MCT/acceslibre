port module Ports exposing
    ( addMapMarker
    , clearMapMarkers
    , communeMap
    , franceMap
    , saveStore
    , storeChanged
    )

import Json.Encode as Encode


port addMapMarker : Encode.Value -> Cmd msg


port clearMapMarkers : () -> Cmd msg


port franceMap : () -> Cmd msg


port communeMap : Encode.Value -> Cmd msg


port saveStore : String -> Cmd msg


port storeChanged : (String -> msg) -> Sub msg
