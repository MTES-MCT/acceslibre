import re

from erp.imports.mapper.base import BaseMapper


class TypeFormBase(BaseMapper):
    def set_erp_fields(self, record, activite, *args, **kwargs):
        dest_fields = {
            k: self.format_data(v) for k, v in record.items() if k in self.erp_fields
        }
        if activite:
            dest_fields["activite"] = activite
        dest_fields["source"] = "typeform"
        dest_fields["code_postal"] = BaseMapper.handle_5digits_code(record.get("cp"))
        dest_fields["commune"] = record["Ville"]
        dest_fields["import_email"] = record["email"]
        if record["geo"]:
            dest_fields["latitude"], dest_fields["longitude"] = (
                float(x) for x in record["geo"].split(",")
            )

        try:
            dest_fields["numero"], dest_fields["voie"] = re.match(
                "([0-9]*) ?(.*)", record["adresse"]
            ).groups()
        except Exception:
            pass

        return dest_fields

    def set_a11y_fields(self, record):
        a11y_data = {}

        field_label = "Votre mairie : {{hidden:nom}}  Y a-t-il une marche (ou plus) pour y rentrer ? (même toute petite) "
        if record[field_label] == "Non, c'est de plain-pied":
            a11y_data["entree_plain_pied"] = True
        elif record[field_label] == "Oui, au moins une marche":
            a11y_data["entree_plain_pied"] = False

        field_label = "Combien de marches y a-t-il pour entrer dans votre mairie ?"
        try:
            nb_marches = int(record[field_label])
        except (ValueError, TypeError):
            nb_marches = None
        a11y_data["entree_marches"] = nb_marches

        field_label = "Est-ce qu'il faut, pour entrer dans la mairie, monter les marches ou les descendre ?"
        if record[field_label] == "Je dois monter le(s) marche(s)":
            a11y_data["entree_marches_sens"] = "montant"
        elif record[field_label] == "je dois descendre le(s) marche(s)":
            a11y_data["entree_marches_sens"] = "descendant"

        field_label = "Avez-vous une rampe d'accès pour entrer dans votre mairie ?"
        if record[field_label] == "Oui, j'ai une rampe fixe":
            a11y_data["entree_marches_rampe"] = "fixe"
        elif record[field_label] == "Oui, j'ai une rampe amovible":
            a11y_data["entree_marches_rampe"] = "amovible"
        elif record[field_label] == "Non, pas de rampe":
            a11y_data["entree_marches_rampe"] = "aucune"

        field_label = "Vous avez une rampe amovible : avez-vous aussi une sonnette pour appeler à l'intérieur ?"
        if record[field_label] == "True":
            a11y_data["entree_dispositif_appel"] = True
        elif record[field_label] == "False":
            a11y_data["entree_dispositif_appel"] = False

        field_label = "Est-ce qu’il y a des toilettes adaptées dans votre mairie ?"
        if record[field_label] == "Oui, j'ai des toilettes adaptées":
            a11y_data["sanitaires_presence"] = True
            a11y_data["sanitaires_adaptes"] = True
        elif record[field_label] == "Non, ce sont des toilettes classiques":
            a11y_data["sanitaires_presence"] = True
            a11y_data["sanitaires_adaptes"] = False
        elif record[field_label] == "Je n'ai pas de toilettes":
            a11y_data["sanitaires_presence"] = False

        field_label = "Avez-vous un parking réservé à vos administrés? "
        if record[field_label] == "Oui, nous avons un parking reservé":
            a11y_data["stationnement_presence"] = True
        elif record[field_label] == "Non, nous n'avons pas de parking reservé":
            a11y_data["stationnement_presence"] = False

        field_label = "Est-ce qu’il y au moins une place handicapé dans votre parking ?"
        if record[field_label] == "Oui c'est praticable":
            a11y_data["cheminement_ext_presence"] = True
            a11y_data["cheminement_ext_terrain_stable"] = True
            a11y_data["cheminement_ext_plain_pied"] = True
            a11y_data["cheminement_ext_retrecissement"] = False
        elif record[field_label] == "Non, ce n'est pas praticable":
            a11y_data["cheminement_ext_presence"] = True

        field_label = "Ce chemin n'est pas praticable car : "
        if record[field_label] == "problème de pente":
            a11y_data["cheminement_ext_pente_presence"] = True
            a11y_data["cheminement_ext_pente_degre_difficulte"] = "importante"
            a11y_data["cheminement_ext_pente_longueur"] = "longue"
        elif record[field_label] == "problème de marche":
            a11y_data["cheminement_ext_plain_pied"] = False
            a11y_data["cheminement_ext_ascenseur"] = False
            a11y_data["cheminement_ext_rampe"] = "aucune"

        field_label = "Est-ce qu’il y au moins une place handicapé dans les environs ?"
        if (
            record[field_label]
            == "Oui, il y a une place  de parking handicapé pas loin"
        ):
            a11y_data["stationnement_ext_presence"] = True
            a11y_data["stationnement_ext_pmr"] = True
        elif record[field_label] == "Non, pas de place handicapé pas loin":
            a11y_data["stationnement_ext_presence"] = True
            a11y_data["stationnement_ext_pmr"] = False

        return a11y_data


class TypeFormMairie(BaseMapper):
    def set_erp_fields(self, record, *args, **kwargs):
        dest_fields = {
            k: self.format_data(v) for k, v in record.items() if k in self.erp_fields
        }
        dest_fields["nom"] = "Mairie"
        dest_fields["activite"] = "Mairie"
        dest_fields["source"] = "typeform"
        dest_fields["code_postal"] = BaseMapper.handle_5digits_code(record.get("cp"))
        dest_fields["commune"] = record["nom"]
        dest_fields["import_email"] = record["email"]
        dest_fields["latitude"], dest_fields["longitude"] = (
            (float(x) for x in record["geo"].split(","))
            if record["geo"]
            else (0.0, 0.0)
        )

        try:
            dest_fields["numero"], dest_fields["voie"] = re.match(
                "([0-9]*) ?(.*)", record["adresse"]
            ).groups()
        except Exception:
            pass

        return dest_fields
