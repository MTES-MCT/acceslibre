module Data.Autocomplete exposing
    ( BanEntry
    , Entry(..)
    , ErpEntry
    , decodeBanEntry
    , decodeErpEntry
    )

import Data.Activite as Activite
import Data.Commune as Commune
import Data.Erp as Erp
import Data.Point as Point exposing (Point)
import Json.Decode as Decode exposing (Decoder)


type Entry
    = Ban BanEntry
    | Erp ErpEntry


type alias BanEntry =
    { label : String
    , commune : String
    , point : Point
    , score : Float
    }


type alias ErpEntry =
    { value : String
    , communeSlug : Commune.Slug
    , erpSlug : Erp.Slug
    , activiteSlug : Maybe Activite.Slug
    , score : Float
    , url : String
    }


decodeBanEntry : Decoder BanEntry
decodeBanEntry =
    Decode.map4 BanEntry
        (Decode.at [ "properties", "label" ] Decode.string)
        (Decode.at [ "properties", "city" ] Decode.string)
        (Decode.at [ "geometry" ] Point.decode)
        (Decode.at [ "properties", "score" ] Decode.float)


decodeErpEntry : Decoder ErpEntry
decodeErpEntry =
    Decode.map6 ErpEntry
        (Decode.field "value" Decode.string)
        (Decode.at [ "data", "commune" ] (Decode.map Commune.slugFromString Decode.string))
        (Decode.at [ "data", "slug" ] (Decode.map Erp.slugFromString Decode.string))
        (Decode.at [ "data", "activite" ] (Decode.nullable (Decode.map Activite.slugFromString Decode.string)))
        (Decode.at [ "data", "score" ] Decode.float)
        (Decode.at [ "data", "url" ] Decode.string)
