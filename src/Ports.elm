port module Ports exposing
    ( addMapMarkers
    , communeMap
    , franceMap
    , getCurrentPosition
    , locateMap
    , openMapErpMarker
    , positionError
    , positionReceived
    , saveStore
    ,  storeChanged
       -- , watchPosition

    )

import Data.Point exposing (Point)
import Json.Encode as Encode



-- Commands


port addMapMarkers : Encode.Value -> Cmd msg


port communeMap : Encode.Value -> Cmd msg


port franceMap : () -> Cmd msg


port getCurrentPosition : () -> Cmd msg


port locateMap : Encode.Value -> Cmd msg


port openMapErpMarker : String -> Cmd msg


port saveStore : String -> Cmd msg



-- TODO: port stopWatchingPosition : () -> Cmd msg
-- port watchPosition : () -> Cmd msg
-- Subscriptions


port positionError : (String -> msg) -> Sub msg


port positionReceived : (Point -> msg) -> Sub msg


port storeChanged : (String -> msg) -> Sub msg
