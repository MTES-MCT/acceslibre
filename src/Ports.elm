port module Ports exposing (initMap, saveStore, storeChanged)


port initMap : { x : Int } -> Cmd msg


port saveStore : String -> Cmd msg


port storeChanged : (String -> msg) -> Sub msg
