from dataclasses import dataclass


@dataclass
class Municipality:
    type_of: str
    name: str
    insee_code: str
    departement: str
    postal_codes: list
    population: int
    parent_municipality: str

    @classmethod
    def from_json(cls, json):
        return cls(
            type_of=json["type"],
            name=json["nom"],
            insee_code=json["code"],
            departement=json["departement"],
            postal_codes=json.get("codesPostaux"),
            population=json.get("population"),
            parent_municipality=json.get("chefLieu"),
        )
