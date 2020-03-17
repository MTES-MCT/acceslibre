module Data.Autocomplete exposing
    ( BanEntry
    , Entry(..)
    , ErpEntry
    , addBanEntries
    , addErpEntries
    , decodeBanEntry
    , decodeErpEntry
    , sortScore
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
    Decode.map3 BanEntry
        (Decode.at [ "properties", "label" ] Decode.string)
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


addBanEntries : List BanEntry -> List Entry -> List Entry
addBanEntries bans entries =
    clearBanEntries entries
        ++ List.map Ban bans
        |> sortScore


addErpEntries : List ErpEntry -> List Entry -> List Entry
addErpEntries erps entries =
    clearErpEntries entries
        ++ List.map Erp erps
        |> sortScore


clearBanEntries : List Entry -> List Entry
clearBanEntries =
    List.filter
        (\entry ->
            case entry of
                Ban _ ->
                    False

                Erp _ ->
                    True
        )


clearErpEntries : List Entry -> List Entry
clearErpEntries =
    List.filter
        (\entry ->
            case entry of
                Ban _ ->
                    True

                Erp _ ->
                    False
        )


sortScore : List Entry -> List Entry
sortScore =
    List.map
        (\entry ->
            case entry of
                Ban ban ->
                    ( ban.score, Ban ban )

                Erp erp ->
                    ( erp.score, Erp erp )
        )
        >> List.sortBy Tuple.first
        >> List.map Tuple.second
        >> List.reverse
