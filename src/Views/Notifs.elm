module Views.Notifs exposing (Config, view)

import Data.Session as Session exposing (Session)
import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)


type alias Config msg =
    { clearNotif : Session.Notif -> msg
    }


viewNotif : Config msg -> Session.Notif -> Html msg
viewNotif { clearNotif } notif =
    case notif of
        Session.ErrorNotif message ->
            div
                [ class "alert alert-danger a4a-notif"
                , attribute "role" "alert"
                ]
                [ button
                    [ type_ "button"
                    , class "close"
                    , attribute "data-dismiss" "alert"
                    , attribute "aria-label" "Close"
                    , onClick (clearNotif notif)
                    ]
                    [ span [ attribute "aria-hidden" "true" ] [ text "×" ] ]
                , text message
                ]


view : Session -> Config msg -> Html msg
view session config =
    session.notifs
        |> List.map (viewNotif config)
        |> div [ class "a4a-notifs" ]
