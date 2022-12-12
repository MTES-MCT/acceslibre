import re

from erp.imports.mapper.base import BaseMapper


class TypeFormMairie(BaseMapper):
    def csv_to_erp(self, record):
        try:
            dest_fields = {k: self.format_data(v) for k, v in record.items() if k in self.erp_fields}
            dest_fields["nom"] = "Mairie"
            dest_fields["activite"] = "Mairie"
            dest_fields["source"] = "typeform"
            dest_fields["code_postal"] = BaseMapper.handle_5digits_code(record.get("cp"))
            dest_fields["commune"] = record["nom"]
            dest_fields["import_email"] = record["email"]
            dest_fields["latitude"], dest_fields["longitude"] = (
                (float(x) for x in record["geo"].split(",")) if record["geo"] else (0.0, 0.0)
            )

            try:
                dest_fields["numero"], dest_fields["voie"] = re.match("([0-9]*) ?(.*)", record["adresse"]).groups()
            except Exception:
                pass
            dest_fields["accessibilite"] = {}

            field_label = (
                "Votre mairie : {{hidden:nom}}  Y a-t-il une marche (ou plus) pour y rentrer ? (même toute petite) "
            )
            if record[field_label] == "Non, c'est de plain-pied":
                dest_fields["accessibilite"]["entree_plain_pied"] = True
            elif record[field_label] == "Oui, au moins une marche":
                dest_fields["accessibilite"]["entree_plain_pied"] = False

            field_label = "Combien de marches y a-t-il pour entrer dans votre mairie ?"
            try:
                nb_marches = int(record[field_label])
            except ValueError:
                nb_marches = None
            dest_fields["accessibilite"]["entree_marches"] = nb_marches

            field_label = "Est-ce qu'il faut, pour entrer dans la mairie, monter les marches ou les descendre ?"
            if record[field_label] == "Je dois monter le(s) marche(s)":
                dest_fields["accessibilite"]["entree_marches_sens"] = "montant"
            elif record[field_label] == "je dois descendre le(s) marche(s)":
                dest_fields["accessibilite"]["entree_marches_sens"] = "descendant"

            field_label = "Avez-vous une rampe d'accès pour entrer dans votre mairie ?"
            if record[field_label] == "Oui, j'ai une rampe fixe":
                dest_fields["accessibilite"]["entree_marches_rampe"] = "fixe"
            elif record[field_label] == "Oui, j'ai une rampe amovible":
                dest_fields["accessibilite"]["entree_marches_rampe"] = "amovible"
            elif record[field_label] == "Non, pas de rampe":
                dest_fields["accessibilite"]["entree_marches_rampe"] = "aucune"

            field_label = "Vous avez une rampe amovible : avez-vous aussi une sonnette pour appeler à l'intérieur ?"
            if record[field_label] == "True":
                dest_fields["accessibilite"]["entree_dispositif_appel"] = True
            elif record[field_label] == "False":
                dest_fields["accessibilite"]["entree_dispositif_appel"] = False

            field_label = "Est-ce qu’il y a des toilettes adaptées dans votre mairie ?"
            if record[field_label] == "Oui, j'ai des toilettes adaptées":
                dest_fields["accessibilite"]["sanitaires_presence"] = True
                dest_fields["accessibilite"]["sanitaires_adaptes"] = True
            elif record[field_label] == "Non, ce sont des toilettes classiques":
                dest_fields["accessibilite"]["sanitaires_presence"] = True
                dest_fields["accessibilite"]["sanitaires_adaptes"] = False
            elif record[field_label] == "Je n'ai pas de toilettes":
                dest_fields["accessibilite"]["sanitaires_presence"] = False

            field_label = "Avez-vous un parking réservé à vos administrés? "
            if record[field_label] == "Oui, nous avons un parking reservé":
                dest_fields["accessibilite"]["stationnement_presence"] = True
            elif record[field_label] == "Non, nous n'avons pas de parking reservé":
                dest_fields["accessibilite"]["stationnement_presence"] = False

            field_label = "Est-ce qu’il y au moins une place handicapé dans votre parking ?"
            if record[field_label] == "Oui c'est praticable":
                dest_fields["accessibilite"]["cheminement_ext_presence"] = True
                dest_fields["accessibilite"]["cheminement_ext_terrain_stable"] = True
                dest_fields["accessibilite"]["cheminement_ext_plain_pied"] = True
                dest_fields["accessibilite"]["cheminement_ext_retrecissement"] = False
            elif record[field_label] == "Non, ce n'est pas praticable":
                dest_fields["accessibilite"]["cheminement_ext_presence"] = True

            field_label = "Ce chemin n'est pas praticable car : "
            if record[field_label] == "problème de pente":
                dest_fields["accessibilite"]["cheminement_ext_pente_presence"] = True
                dest_fields["accessibilite"]["cheminement_ext_pente_degre_difficulte"] = "importante"
                dest_fields["accessibilite"]["cheminement_ext_pente_longueur"] = "longue"
            elif record[field_label] == "problème de marche":
                dest_fields["accessibilite"]["cheminement_ext_plain_pied"] = False
                dest_fields["accessibilite"]["cheminement_ext_ascenseur"] = False
                dest_fields["accessibilite"]["cheminement_ext_rampe"] = "aucune"

            field_label = "Est-ce qu’il y au moins une place handicapé dans les environs ?"
            if record[field_label] == "Oui, il y a une place  de parking handicapé pas loin":
                dest_fields["accessibilite"]["stationnement_ext_presence"] = True
                dest_fields["accessibilite"]["stationnement_ext_pmr"] = True
            elif record[field_label] == "Non, pas de place handicapé pas loin":
                dest_fields["accessibilite"]["stationnement_ext_presence"] = True
                dest_fields["accessibilite"]["stationnement_ext_pmr"] = False

            return dest_fields
        except KeyError as key:
            raise RuntimeError(f"Impossible d'extraire des données: champ {key} manquant")
