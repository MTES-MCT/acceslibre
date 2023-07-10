import factory
from faker import Factory as FakerFactory

faker = FakerFactory.create()


class ErpFactory(factory.django.DjangoModelFactory):
    nom = factory.LazyAttribute(lambda x: faker.name())
    numero = factory.LazyAttribute(lambda x: faker.building_number())
    voie = factory.LazyAttribute(lambda x: faker.street_name())
    code_postal = factory.LazyAttribute(lambda x: faker.postcode())
    commune = factory.LazyAttribute(lambda x: faker.city())
    user_id = None

    class Meta:
        model = "erp.Erp"
        django_get_or_create = ("nom",)


class AccessibiliteFactory(factory.django.DjangoModelFactory):
    erp = factory.SubFactory(ErpFactory)

    class Meta:
        model = "erp.Accessibilite"
