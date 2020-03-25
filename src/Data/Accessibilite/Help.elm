module Data.Accessibilite.Help exposing (Entry, Help, decode, get)

import Dict exposing (Dict)
import Json.Decode as Decode exposing (Decoder)


type alias Entry =
    { label : String
    , help : String
    }


type alias Help =
    Dict String Entry


decode : Decoder Help
decode =
    Decode.dict decodeEntry


decodeEntry : Decoder Entry
decodeEntry =
    Decode.map2 Entry
        (Decode.field "label" Decode.string)
        (Decode.field "help" Decode.string)


get : String -> Help -> Entry
get id help =
    Dict.get id help |> Maybe.withDefault { label = id, help = "" }
