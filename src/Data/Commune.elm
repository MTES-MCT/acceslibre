module Data.Commune exposing
    ( Commune
    , Slug
    , communes
    , slugFromString
    , slugParser
    , slugToString
    )

import Dict exposing (Dict)
import Url.Parser as Parser exposing (Parser)


type Slug
    = Slug String


type alias Commune =
    { nom : String
    , slug : Slug
    , center : ( Float, Float )
    , zoom : Int
    }


slugToString : Slug -> String
slugToString (Slug slug) =
    slug


slugFromString : String -> Slug
slugFromString string =
    Slug string


slugParser : Parser (Commune -> a) a
slugParser =
    Parser.custom "CommuneFromSlug" (\x -> Dict.get x communes)


communes : Dict String Commune
communes =
    Dict.fromList
        [ ( "92-clichy"
          , { nom = "Clichy"
            , slug = Slug "92-clichy"
            , center = ( 48.9041, 2.2952 )
            , zoom = 15
            }
          )
        , ( "92-courbevoie"
          , { nom = "Courbevoie"
            , slug = Slug "92-courbevoie"
            , center = ( 48.8976, 2.2574 )
            , zoom = 15
            }
          )
        , ( "56-lorient"
          , { nom = "Lorient"
            , slug = Slug "56-lorient"
            , center = ( 47.7494, -3.3792 )
            , zoom = 14
            }
          )
        , ( "69-lyon"
          , { nom = "Lyon"
            , slug = Slug "69-lyon"
            , center = ( 45.7578, 4.8351 )
            , zoom = 13
            }
          )
        , ( "92-rueil-malmaison"
          , { nom = "Rueil-Malmaison"
            , slug = Slug "92-rueil-malmaison"
            , center = ( 48.8718, 2.1806 )
            , zoom = 14
            }
          )
        , ( "69-villeurbanne"
          , { nom = "Villeurbanne"
            , slug = Slug "69-villeurbanne"
            , center = ( 45.772, 4.8898 )
            , zoom = 14
            }
          )
        ]
