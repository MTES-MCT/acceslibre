import factory
from django.contrib.auth import get_user_model
from faker import Factory as FakerFactory

faker = FakerFactory.create()


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("email")
    email = username
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class ErpFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    numero = factory.LazyAttribute(lambda x: faker.building_number())
    voie = factory.LazyAttribute(lambda x: faker.street_name())
    code_postal = factory.LazyAttribute(lambda x: faker.postcode())
    commune = factory.LazyAttribute(lambda x: faker.city())
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = "erp.Erp"
        django_get_or_create = ("nom",)


class AccessibiliteFactory(factory.django.DjangoModelFactory):
    erp = factory.SubFactory(ErpFactory)

    class Meta:
        model = "erp.Accessibilite"
