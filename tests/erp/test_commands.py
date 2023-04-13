import pytest

from erp.management.commands.convert_tally_to_schema import Command


class TestConvertTallyToSchema:
    @pytest.mark.parametrize(
        "line, expected_line",
        (
            pytest.param(
                {
                    "Est-ce qu’il y au moins une place handicapé dans votre parking ?": "Oui, nous avons une place handicapé",
                    "cp": "4100",
                    "adresse": "7 grande rue, Saint Martin en Haut",
                    "Combien de marches y a-t-il pour entrer dans votre établissement ?": "124",
                    "email": "contrib@beta.gouv.fr",
                },
                {
                    "stationnement_ext_presence": True,
                    "stationnement_ext_pmr": True,
                    "code_postal": "04100",
                    "code_insee": "04100",
                    "lieu_dit": None,
                    "numero": "7",
                    "voie": "Grande rue",
                    "commune": "Saint Martin en Haut",
                    "entree_marches": 124,
                    "import_email": "contrib@beta.gouv.fr",
                },
                id="nominal_case",
            ),
        ),
    )
    def test_process_line(self, line, expected_line):
        assert Command()._process_line(line) == expected_line
