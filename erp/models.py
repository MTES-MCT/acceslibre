import json
import requests

from django.db import models
from django.core.exceptions import ValidationError


class Activite(models.Model):
    nom = models.CharField(max_length=255, unique=True, help_text="Nom de l'activité")
    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


class Erp(models.Model):
    nom = models.CharField(max_length=255, help_text="Nom de l’établissement ou de l’enseigne")
    activite = models.ForeignKey(Activite, null=True, blank=True, on_delete=models.SET_NULL)
    lat = models.FloatField(null=True, blank=True, help_text="Latitude")
    lon = models.FloatField(null=True, blank=True, help_text="Longitude")
    siret = models.CharField(max_length=255, null=True, blank=True, help_text="Numéro SIRET")
    # adresse
    adresse = models.CharField(max_length=255, null=True, blank=True, help_text="Adresse complète")
    numero = models.CharField(max_length=12, null=True, blank=True, help_text="Numéro dans la voie")
    complement = models.CharField(max_length=255, null=True, blank=True, help_text="Complément de numéro (ex. BIS, TER)")
    voie = models.CharField(max_length=255, help_text="Voie")
    lieu_dit = models.CharField(max_length=255, null=True, blank=True, help_text="Lieu dit")
    code_postal = models.CharField(max_length=10, help_text="Code postal")
    commune = models.CharField(max_length=255, help_text="Nom de la commune")
    code_insee = models.CharField(max_length=10, null=True, blank=True, help_text="Code INSEE")
    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ERP #{self.id} ({self.nom})"

    @property
    def adresse(self):
        pieces = filter(lambda x: x is not None, [self.num, self.cplt, self.voie, self.lieu_dit, self.cpost, self.commune])
        return " ".join(pieces).strip()
