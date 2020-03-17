module Request.Pager exposing (Pager, decode, update)

import Http
import Json.Decode as Decode exposing (Decoder)


type alias Pager a =
    { count : Int
    , next : Maybe String
    , previous : Maybe String
    , results : List a
    }


decode : Decoder a -> Decoder (Pager a)
decode decodeItem =
    Decode.map4 Pager
        (Decode.field "count" Decode.int)
        (Decode.field "next" (Decode.nullable Decode.string))
        (Decode.field "previous" (Decode.nullable Decode.string))
        (Decode.field "results" (Decode.list decodeItem))


update : Pager a -> Pager a -> Pager a
update previous new =
    { new | results = previous.results ++ new.results }
