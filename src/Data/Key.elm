module Data.Key exposing (Control(..), Key(..), decode)

import Json.Decode as Decode


type Key
    = CharKey Char
    | ControlKey Control
    | None


type Control
    = Ctrl
    | End
    | Esc
    | Enter
    | LeftArrow
    | Home
    | Other
    | RightArrow
    | Shift
    | Space
    | UpArrow
    | DownArrow


decode : Decode.Decoder Key
decode =
    Decode.map toKey (Decode.field "key" Decode.string)


toKey : String -> Key
toKey string =
    -- See https://github.com/elm/browser/blob/1.0.0/notes/keyboard.md#decoding-for-user-input
    case String.uncons string of
        Nothing ->
            None

        Just ( ' ', "" ) ->
            ControlKey Space

        Just ( char, "" ) ->
            CharKey char

        Just _ ->
            case string of
                "Control" ->
                    ControlKey Ctrl

                "Shift" ->
                    ControlKey Shift

                " " ->
                    ControlKey Space

                "Home" ->
                    ControlKey Home

                "End" ->
                    ControlKey End

                "Enter" ->
                    ControlKey Enter

                "Escape" ->
                    ControlKey Esc

                "ArrowLeft" ->
                    ControlKey LeftArrow

                "ArrowUp" ->
                    ControlKey UpArrow

                "ArrowRight" ->
                    ControlKey RightArrow

                "ArrowDown" ->
                    ControlKey DownArrow

                _ ->
                    ControlKey Other
