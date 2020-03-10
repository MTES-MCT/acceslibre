module Data.Erp exposing
    ( Erp
    , Slug
    , decode
    , slugFromString
    , slugParser
    , slugToString
    )

import Data.Activite as Activite exposing (Activite)
import Data.Point as Point exposing (Point)
import Json.Decode as Decode exposing (Decoder)
import Json.Decode.Pipeline as Pipe
import Url.Parser as Parser exposing (Parser)


type Slug
    = Slug String


type alias Erp =
    { url : String
    , nom : String
    , slug : Slug
    , published : Bool
    , activite : Maybe Activite
    , geom : Maybe Point
    , siret : Maybe String
    , telephone : Maybe String
    , siteInternet : Maybe String
    , numero : Maybe String
    , voie : Maybe String
    , codePostal : String
    , commune : String
    , codeInsee : Maybe String
    }


decode : Decoder Erp
decode =
    Decode.succeed Erp
        |> Pipe.required "url" Decode.string
        |> Pipe.required "nom" Decode.string
        |> Pipe.required "slug" (Decode.map Slug Decode.string)
        |> Pipe.required "published" Decode.bool
        |> Pipe.required "activite" (Decode.nullable Activite.decode)
        |> Pipe.required "geom" (Decode.nullable Point.decode)
        |> Pipe.required "siret" (Decode.nullable Decode.string)
        |> Pipe.required "telephone" (Decode.nullable Decode.string)
        |> Pipe.required "site_internet" (Decode.nullable Decode.string)
        |> Pipe.required "numero" (Decode.nullable Decode.string)
        |> Pipe.required "voie" (Decode.nullable Decode.string)
        |> Pipe.required "code_postal" Decode.string
        |> Pipe.required "commune" Decode.string
        |> Pipe.required "code_insee" (Decode.nullable Decode.string)


slugToString : Slug -> String
slugToString (Slug slug) =
    slug


slugFromString : String -> Slug
slugFromString string =
    Slug string


slugParser : Parser (Slug -> a) a
slugParser =
    Parser.custom "ErpFromSlug" (Just << Slug)
