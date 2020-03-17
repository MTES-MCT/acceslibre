module Data.Autocomplete exposing (Entry, decode)

import Data.Activite as Activite
import Data.Commune as Commune
import Data.Erp as Erp
import Json.Decode as Decode exposing (Decoder)


type alias Entry =
    { value : String
    , communeSlug : Commune.Slug
    , erpSlug : Erp.Slug
    , activiteSlug : Maybe Activite.Slug
    , score : Float
    , url : String
    }


decode : Decoder Entry
decode =
    Decode.map6 Entry
        (Decode.field "value" Decode.string)
        (Decode.at [ "data", "commune" ] (Decode.map Commune.slugFromString Decode.string))
        (Decode.at [ "data", "slug" ] (Decode.map Erp.slugFromString Decode.string))
        (Decode.at [ "data", "activite" ] (Decode.nullable (Decode.map Activite.slugFromString Decode.string)))
        (Decode.at [ "data", "score" ] Decode.float)
        (Decode.at [ "data", "url" ] Decode.string)
