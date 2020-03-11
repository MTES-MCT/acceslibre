port module Ports exposing
    ( addMapMarkers
    , communeMap
    , franceMap
    , openMapErpMarker
    , saveStore
    , storeChanged
    )

import Json.Encode as Encode


port addMapMarkers : Encode.Value -> Cmd msg


port communeMap : Encode.Value -> Cmd msg


port franceMap : () -> Cmd msg


port openMapErpMarker : String -> Cmd msg


port saveStore : String -> Cmd msg


port storeChanged : (String -> msg) -> Sub msg
