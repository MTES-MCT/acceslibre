import random
from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from factory.fuzzy import BaseFuzzyAttribute
from faker import Factory as FakerFactory

faker = FakerFactory.create()


User = get_user_model()


class FuzzyPoint(BaseFuzzyAttribute):
    def fuzz(self):
        return Point(random.uniform(-180.0, 180.0), random.uniform(-90.0, 90.0))


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker("email")
    email = username
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    class Meta:
        model = User


class ActiviteFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    mots_cles = factory.List([])

    class Meta:
        model = "erp.Activite"
        django_get_or_create = ("nom",)


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

    def __init__(self, *args, **kwargs):
        self.with_accessibilite = kwargs.pop("with_accessibilite", False)
        super().__init__(*args, **kwargs)

    @classmethod
    def create(cls, **kwargs):
        with_accessibilite = kwargs.pop("with_accessibilite", False)
        erp = super().create(**kwargs)
        if with_accessibilite:
            AccessibiliteFactory(erp=erp)
        return erp


class ErpWithAccessibiliteFactory(ErpFactory):
    with_accessibilite = True


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


class ChallengeFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    created_by = factory.SubFactory(UserFactory)
    start_date = factory.LazyAttribute(lambda x: timezone.now() - timedelta(days=1))
    end_date = factory.LazyAttribute(lambda x: timezone.now() + timedelta(days=1))

    class Meta:
        model = "stats.Challenge"

    @factory.post_generation
    def players(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        for player in extracted:
            self.players.add(player)


class ChallengeTeamFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda x: faker.name())

    class Meta:
        model = "stats.ChallengeTeam"
