module Data.Activite exposing
    ( Activite
    , Slug
    , decode
    , slugFromString
    , slugParser
    , slugToString
    )

import Json.Decode as Decode exposing (Decoder)
import Json.Decode.Pipeline as Pipe
import Url.Parser as Parser exposing (Parser)


type Slug
    = Slug String


type alias Activite =
    { url : String
    , nom : String
    , slug : Slug
    , count : Maybe Int
    }


decode : Decoder Activite
decode =
    Decode.succeed Activite
        |> Pipe.required "url" Decode.string
        |> Pipe.required "nom" Decode.string
        |> Pipe.required "slug" (Decode.map Slug Decode.string)
        |> Pipe.optional "count" (Decode.maybe Decode.int) Nothing


slugToString : Slug -> String
slugToString (Slug slug) =
    slug


slugFromString : String -> Slug
slugFromString string =
    Slug string


slugParser : Parser (Slug -> a) a
slugParser =
    Parser.custom "ActiviteFromSlug" (Just << Slug)
