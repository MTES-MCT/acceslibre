from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from core.lib import text


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email", help="Adresse email de la personne")
        pass

    def generate_username(self, email):
        a, *_ = email.split("@")
        return a

    def handle(self, *args, **options):
        group = Group.objects.get(name="territoire")
        password = text.random_string(15)
        email = text.remove_accents(options["email"]).lower()
        username = self.generate_username(email)
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_staff=True,
        )
        user.groups.add(group)
        print(f"Compte créé pour {email}: username={username}, password={password}")
