import random
from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from factory.fuzzy import BaseFuzzyAttribute
from faker import Factory as FakerFactory

from erp.models import ExternalSource

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
        django_get_or_create = ("username",)


class ActiviteFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    mots_cles = factory.List([])

    class Meta:
        model = "erp.Activite"
        django_get_or_create = ("nom",)


class ActivitiesGroupFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda x: faker.name())

    @factory.post_generation
    def activities(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        for activity in extracted:
            self.activities.add(activity)

    class Meta:
        model = "erp.ActivitiesGroup"


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

    @classmethod
    def create(cls, **kwargs):
        accessibilite_kwargs = {}
        erp_kwargs = {}

        with_accessibility = kwargs.pop("with_accessibility", False)

        for key, value in kwargs.items():
            if key.startswith("accessibilite__"):
                accessibilite_kwargs[key.replace("accessibilite__", "")] = value
            else:
                erp_kwargs[key] = value

        with_accessibility = accessibilite_kwargs or with_accessibility
        erp = super().create(**erp_kwargs)

        if with_accessibility:
            AccessibiliteFactory(erp=erp, **accessibilite_kwargs)

        return erp


class ExternalSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "erp.ExternalSource"

    erp = factory.SubFactory(ErpFactory)
    source = factory.LazyAttribute(lambda _: random.choice([choice[0] for choice in ExternalSource.SOURCE_CHOICES]))
    source_id = factory.Faker("uuid4")


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
