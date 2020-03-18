module Views.Autocomplete exposing (Config, panel)

import Data.Autocomplete as Autocomplete
import Data.Commune exposing (Commune)
import Data.Point exposing (Point)
import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import RemoteData
import Route


type alias Config msg =
    { locateMap : Point -> msg
    }


erpListView : List Autocomplete.ErpEntry -> Html msg
erpListView =
    List.map
        (\erp ->
            a
                [ class "list-group-item list-group-item-action"
                , Route.href (Route.forAutocompleteEntry erp)
                ]
                [ i [ class "icon icon-commercial" ] [], text " ", text erp.value ]
        )
        >> div [ class "col-6 list-group list-group-flush" ]


banListView : Maybe Commune -> (Point -> msg) -> List Autocomplete.BanEntry -> Html msg
banListView maybeCommune locateMap =
    List.filter
        (\ban ->
            case maybeCommune of
                Just commune ->
                    String.toLower commune.nom == String.toLower ban.commune

                Nothing ->
                    True
        )
        >> List.map
            (\ban ->
                -- FIXME: we want a route here
                button
                    [ type_ "button"
                    , class "list-group-item list-group-item-action"
                    , onClick (locateMap ban.point)
                    ]
                    [ i [ class "icon icon-road" ] [], text " ", text ban.label ]
            )
        >> div [ class "col-6 list-group list-group-flush" ]


panel : Session -> Config msg -> Html msg
panel { autocomplete, commune, erps } { locateMap } =
    if List.length autocomplete.bans > 0 || List.length autocomplete.erps > 0 && erps /= RemoteData.Loading then
        div [ class "row a4a-autocomplete-items" ]
            [ erpListView autocomplete.erps
            , banListView commune locateMap autocomplete.bans
            ]

    else
        text ""
