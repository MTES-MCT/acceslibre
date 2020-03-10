module Data.Point exposing (Point, decode)

import Json.Decode as Decode exposing (Decoder)


type alias Point =
    { lon : Float
    , lat : Float
    }


decode : Decoder Point
decode =
    Decode.at [ "coordinates" ] (Decode.list Decode.float)
        |> Decode.andThen
            (\arr ->
                case arr of
                    [ lon, lat ] ->
                        Decode.succeed { lon = lon, lat = lat }

                    _ ->
                        Decode.fail "Unable to decode Point"
            )
