module Route exposing
    ( Route(..)
    , forAutocompleteEntry
    , forErp
    , fromUrl
    , href
    , pushUrl
    , toString
    )

import Browser.Navigation as Nav
import Data.Activite as Activite exposing (Activite)
import Data.Autocomplete as Autocomplete
import Data.Commune as Commune exposing (Commune)
import Data.Erp as Erp exposing (Erp)
import Html exposing (Attribute)
import Html.Attributes as Attr
import Url exposing (Url)
import Url.Parser as Parser exposing ((</>), Parser, s)


type Route
    = Home
    | Around
    | AroundActivite Activite.Slug
    | AroundActiviteErp Activite.Slug Erp.Slug
    | CommuneHome Commune
    | Activite Activite.Slug
    | Erp Erp.Slug
    | CommuneActivite Commune Activite.Slug
    | CommuneActiviteErp Commune Activite.Slug Erp.Slug
    | CommuneErp Commune Erp.Slug
    | CommuneSearch Commune String
    | Search String


parser : Parser (Route -> a) a
parser =
    Parser.oneOf
        [ Parser.map Home Parser.top
        , Parser.map Around (s "around")
        , Parser.map AroundActivite (s "around" </> Activite.slugParser)
        , Parser.map AroundActiviteErp (s "around" </> Activite.slugParser </> s "erp" </> Erp.slugParser)
        , Parser.map CommuneHome Commune.slugParser
        , Parser.map Activite (s "a" </> Activite.slugParser)
        , Parser.map Erp (s "erp" </> Erp.slugParser)
        , Parser.map CommuneActivite (Commune.slugParser </> s "a" </> Activite.slugParser)
        , Parser.map CommuneActiviteErp (Commune.slugParser </> s "a" </> Activite.slugParser </> s "erp" </> Erp.slugParser)
        , Parser.map CommuneErp (Commune.slugParser </> s "erp" </> Erp.slugParser)
        , Parser.map CommuneSearch (Commune.slugParser </> s "search" </> Parser.string) -- FIXME: could contain slash
        , Parser.map Search (s "search" </> Parser.string) -- FIXME: could contain slash
        ]


forAutocompleteEntry : Autocomplete.ErpEntry -> Route
forAutocompleteEntry entry =
    case ( entry.activiteSlug, Commune.findBySlug entry.communeSlug ) of
        ( Just activiteSlug, Just commune ) ->
            CommuneActiviteErp commune activiteSlug entry.erpSlug

        ( Nothing, Just commune ) ->
            CommuneErp commune entry.erpSlug

        _ ->
            Erp entry.erpSlug


forErp : Erp -> Route
forErp erp =
    case ( erp.activite, Commune.findByNom erp.commune ) of
        ( Just activite, Just commune ) ->
            CommuneActiviteErp commune activite.slug erp.slug

        ( Nothing, Just commune ) ->
            CommuneErp commune erp.slug

        _ ->
            Erp erp.slug


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

                Around ->
                    [ "around" ]

                AroundActivite activiteSlug ->
                    [ "around", Activite.slugToString activiteSlug ]

                AroundActiviteErp activiteSlug erpSlug ->
                    [ "around", Activite.slugToString activiteSlug, "erp", Erp.slugToString erpSlug ]

                CommuneHome commune ->
                    [ Commune.slugToString commune.slug ]

                Activite slug ->
                    [ "a", Activite.slugToString slug ]

                Erp slug ->
                    [ "erp", Erp.slugToString slug ]

                CommuneActivite commune slug ->
                    [ Commune.slugToString commune.slug, "a", Activite.slugToString slug ]

                CommuneActiviteErp commune activiteSlug erpSlug ->
                    [ Commune.slugToString commune.slug, "a", Activite.slugToString activiteSlug, "erp", Erp.slugToString erpSlug ]

                CommuneErp commune erpSlug ->
                    [ Commune.slugToString commune.slug, "erp", Erp.slugToString erpSlug ]

                CommuneSearch commune search ->
                    [ Commune.slugToString commune.slug, "search", search ]

                Search search ->
                    [ "search", search ]
    in
    "#/" ++ String.join "/" pieces
