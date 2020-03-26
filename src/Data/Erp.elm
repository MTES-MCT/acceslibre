module Data.Erp exposing
    ( Erp
    , Slug
    , decode
    , formatDistance
    , slugFromString
    , slugParser
    , slugToString
    , toJson
    , toJsonList
    )

import Data.Activite as Activite exposing (Activite)
import Data.Commune as Commune
import Data.Point as Point exposing (Point)
import Json.Decode as Decode exposing (Decoder)
import Json.Decode.Pipeline as Pipe
import Json.Encode as Encode
import Url.Parser as Parser exposing (Parser)


type Slug
    = Slug String


type alias Erp =
    { nom : String
    , slug : Slug
    , activite : Maybe Activite
    , adresse : String
    , geom : Maybe Point
    , siret : Maybe String
    , telephone : Maybe String
    , siteInternet : Maybe String
    , commune : String
    , codeInsee : Maybe String
    , accessibiliteApiUrl : Maybe String
    , user : Maybe String
    , distance : Maybe Float
    }


decode : Decoder Erp
decode =
    Decode.succeed Erp
        |> Pipe.required "nom" Decode.string
        |> Pipe.required "slug" (Decode.map Slug Decode.string)
        |> Pipe.required "activite" (Decode.nullable Activite.decode)
        |> Pipe.required "adresse" Decode.string
        |> Pipe.required "geom" (Decode.nullable Point.decode)
        |> Pipe.required "siret" (Decode.nullable Decode.string)
        |> Pipe.required "telephone" (Decode.nullable Decode.string)
        |> Pipe.required "site_internet" (Decode.nullable Decode.string)
        |> Pipe.required "commune" Decode.string
        |> Pipe.required "code_insee" (Decode.nullable Decode.string)
        |> Pipe.required "accessibilite" (Decode.nullable Decode.string)
        |> Pipe.required "user" (Decode.nullable Decode.string)
        |> Pipe.required "distance" (Decode.nullable Decode.float)


formatDistance : Float -> String
formatDistance distance =
    let
        meters =
            round distance
    in
    if meters < 1000 then
        String.fromInt meters ++ "m"

    else
        String.fromInt (meters // 1000) ++ "km"


toJson : (Erp -> String) -> Erp -> Encode.Value
toJson toUrl erp =
    Encode.object
        [ ( "nom", Encode.string erp.nom )
        , ( "url", Encode.string (toUrl erp) )
        , ( "slug", Encode.string (slugToString erp.slug) )
        , ( "activite", erp.activite |> Maybe.map (.nom >> Encode.string) |> Maybe.withDefault Encode.null )
        , ( "adresse", Encode.string erp.adresse )
        , ( "geom", erp.geom |> Maybe.map Point.encode |> Maybe.withDefault Encode.null )
        , ( "siret", erp.siret |> Maybe.map Encode.string |> Maybe.withDefault Encode.null )
        , ( "telephone", erp.telephone |> Maybe.map Encode.string |> Maybe.withDefault Encode.null )
        , ( "siteInternet", erp.siteInternet |> Maybe.map Encode.string |> Maybe.withDefault Encode.null )
        , ( "commune", Encode.string erp.commune )
        , ( "codeInsee", erp.codeInsee |> Maybe.map Encode.string |> Maybe.withDefault Encode.null )
        , ( "hasAccessibilite", Encode.bool (erp.accessibiliteApiUrl /= Nothing) )
        ]


toJsonList : (Erp -> String) -> List Erp -> Encode.Value
toJsonList toUrl =
    Encode.list (toJson toUrl)


slugToString : Slug -> String
slugToString (Slug slug) =
    slug


slugFromString : String -> Slug
slugFromString string =
    Slug string


slugParser : Parser (Slug -> a) a
slugParser =
    Parser.custom "ErpFromSlug" (Just << Slug)
