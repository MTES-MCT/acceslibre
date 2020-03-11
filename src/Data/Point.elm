module Data.Point exposing (Point, decode, encode)

import Json.Decode as Decode exposing (Decoder)
import Json.Encode as Encode


type alias Point =
    { lat : Float
    , lon : Float
    }


decode : Decoder Point
decode =
    Decode.at [ "coordinates" ] (Decode.list Decode.float)
        |> Decode.andThen
            (\arr ->
                case arr of
                    [ lon, lat ] ->
                        Decode.succeed { lat = lat, lon = lon }

                    _ ->
                        Decode.fail "Unable to decode Point"
            )


encode : Point -> Encode.Value
encode v =
    Encode.list Encode.float [ v.lat, v.lon ]
