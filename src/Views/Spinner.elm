module Views.Spinner exposing (view)

import Html exposing (..)
import Html.Attributes exposing (..)


view : Html msg
view =
    div [ class "lds-ring" ]
        [ div [] []
        , div [] []
        , div [] []
        , div [] []
        ]
