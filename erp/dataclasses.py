from dataclasses import dataclass


@dataclass
class Municipality:
    nom: str
    code_insee: str
    departement: str
    code_postaux: list
    population: int
    contour: str
    center_lat: float
    center_lon: float

    @classmethod
    def from_api(cls, json):
        return cls(
            nom=json["nom"],
            code_insee=json["code"],
            departement=json["codeDepartement"],
            code_postaux=json["codesPostaux"],
            population=json["population"],
            contour=json["contour"],
            center_lat=json["centre"]["coordinates"][1],
            center_lon=json["centre"]["coordinates"][0],
        )
