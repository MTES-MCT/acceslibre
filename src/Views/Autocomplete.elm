module Views.Autocomplete exposing (Config, panel)

import Data.Autocomplete as Autocomplete
import Data.Commune as Commune exposing (Commune)
import Data.Point exposing (Point)
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Route


type alias Config msg =
    { locateMap : Point -> msg
    }


panel : Session -> Config msg -> Html msg
panel { autocomplete, commune } { locateMap } =
    let
        { bans, erps } =
            autocomplete
    in
    if List.length bans > 0 || List.length erps > 0 then
        div [ class "row a4a-autocomplete-items" ]
            [ erps
                |> List.map
                    (\erp ->
                        a
                            [ class "list-group-item list-group-item-action"
                            , Route.href (Route.forAutocompleteEntry erp)
                            ]
                            [ i [ class "icon icon-commercial" ] [], text " ", text erp.value ]
                    )
                |> div [ class "col-6 list-group list-group-flush" ]
            , bans
                |> List.filter
                    (\ban ->
                        case commune of
                            Just commune_ ->
                                String.toLower commune_.nom == String.toLower ban.commune

                            Nothing ->
                                True
                    )
                |> List.map
                    (\ban ->
                        -- FIXME: we want a route here
                        button
                            [ type_ "button"
                            , class "list-group-item list-group-item-action"
                            , onClick (locateMap ban.point)
                            ]
                            [ i [ class "icon icon-road" ] [], text " ", text ban.label ]
                    )
                |> div [ class "col-6 list-group list-group-flush" ]
            ]

    else
        text ""
