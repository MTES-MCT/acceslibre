module Data.Autocomplete exposing (Entry, decode)

import Json.Decode as Decode exposing (Decoder)


type alias Entry =
    { value : String
    , score : Float
    , url : String
    }


decode : Decoder Entry
decode =
    Decode.map3 Entry
        (Decode.field "value" Decode.string)
        (Decode.at [ "data", "score" ] Decode.float)
        (Decode.at [ "data", "url" ] Decode.string)
