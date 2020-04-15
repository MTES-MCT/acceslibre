import random
import string
import unicodedata

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError


def strip_accents(nom):
    return "".join(
        char
        for char in unicodedata.normalize("NFD", nom)
        if unicodedata.category(char) != "Mn"
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", help="Adresse email de la personne")
        pass

    def generate_username(self, email):
        a, *_ = email.split("@")
        return a

    def random_password(self, length=15):
        return "".join(random.choice(string.ascii_letters) for i in range(length))

    def handle(self, *args, **options):
        group = Group.objects.get(name="territoire")
        password = self.random_password()
        email = strip_accents(options["email"]).lower()
        username = self.generate_username(email)
        user = User.objects.create_user(
            username=username, password=password, email=email, is_staff=True,
        )
        user.groups.add(group)
        print(f"Compte créé pour {email}: username={username}, password={password}")
