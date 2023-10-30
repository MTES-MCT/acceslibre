import random

import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from factory.fuzzy import BaseFuzzyAttribute
from faker import Factory as FakerFactory

faker = FakerFactory.create()


User = get_user_model()


class FuzzyPoint(BaseFuzzyAttribute):
    def fuzz(self):
        return Point(random.uniform(-180.0, 180.0), random.uniform(-90.0, 90.0))


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("email")
    email = username
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class ActiviteFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    mots_cles = factory.List([])

    class Meta:
        model = "erp.Activite"


class ErpFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    numero = factory.LazyAttribute(lambda x: faker.building_number())
    voie = factory.LazyAttribute(lambda x: faker.street_name())
    code_postal = factory.LazyAttribute(lambda x: faker.postcode())
    commune = factory.LazyAttribute(lambda x: faker.city())
    user = factory.SubFactory(UserFactory)
    activite = factory.SubFactory(ActiviteFactory)
    geom = FuzzyPoint()

    class Meta:
        model = "erp.Erp"
        django_get_or_create = ("nom",)


class AccessibiliteFactory(factory.django.DjangoModelFactory):
    erp = factory.SubFactory(ErpFactory)

    class Meta:
        model = "erp.Accessibilite"


class CommuneFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.city())
    departement = factory.LazyAttribute(lambda x: faker.postcode()[:2])
    geom = FuzzyPoint()

    class Meta:
        model = "erp.Commune"
