module Route exposing (Route(..), fromUrl, href, pushUrl)

import Browser.Navigation as Nav
import Data.Activite as Activite exposing (Activite)
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Html exposing (Attribute)
import Html.Attributes as Attr
import Url exposing (Url)
import Url.Parser as Parser exposing ((</>), (<?>), Parser, s)


type Route
    = Home
    | CommuneHome Commune
    | Activite Activite.Slug
    | Erp Erp.Slug
    | CommuneActivite Commune String
    | CommuneActiviteErp Commune String String
    | CommuneErp Commune String


parser : Parser (Route -> a) a
parser =
    Parser.oneOf
        [ Parser.map Home Parser.top
        , Parser.map CommuneHome Commune.slugParser
        , Parser.map Activite (s "a" </> Activite.slugParser)
        , Parser.map Erp (s "erp" </> Erp.slugParser)
        , Parser.map CommuneActivite (Commune.slugParser </> s "a" </> Parser.string)
        , Parser.map CommuneActiviteErp (Commune.slugParser </> s "a" </> Parser.string </> s "erp" </> Parser.string)
        , Parser.map CommuneErp (Commune.slugParser </> s "a" </> Parser.string)
        ]


{-| Note: as elm-kitchen relies on URL fragment based routing, the source URL is
updated so that the `fragment` part becomes the `path` one.
-}
fromUrl : Url -> Maybe Route
fromUrl url =
    let
        protocol =
            if url.protocol == Url.Https then
                "https"

            else
                "http"

        port_ =
            case url.port_ of
                Just p ->
                    ":" ++ String.fromInt p

                Nothing ->
                    ""

        path =
            Maybe.withDefault "/" url.fragment
    in
    Url.fromString (protocol ++ "://" ++ url.host ++ port_ ++ path)
        |> Maybe.withDefault url
        |> Parser.parse parser


href : Route -> Attribute msg
href route =
    Attr.href (toString route)


pushUrl : Nav.Key -> Route -> Cmd msg
pushUrl key route =
    Nav.pushUrl key (toString route)


toString : Route -> String
toString route =
    let
        pieces =
            case route of
                Home ->
                    []

                CommuneHome commune ->
                    [ Commune.slugToString commune.slug ]

                Activite slug ->
                    [ "a", Activite.slugToString slug ]

                Erp slug ->
                    [ "erp", Erp.slugToString slug ]

                CommuneActivite commune activite ->
                    [ Commune.slugToString commune.slug, "a", activite ]

                CommuneActiviteErp commune activite erp ->
                    [ Commune.slugToString commune.slug, "a", activite, "erp", erp ]

                CommuneErp commune erp ->
                    [ Commune.slugToString commune.slug, "erp", erp ]
    in
    "#/" ++ String.join "/" pieces
