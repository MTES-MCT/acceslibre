from django.db.models import Avg
from django_registration.backends.activation.views import RegistrationView
from rest_framework import serializers
from reversion.models import Revision

from compte.models import UserStats


class UserStatsSerializer(serializers.ModelSerializer):
    date_joined = serializers.SerializerMethodField()
    date_last_login = serializers.SerializerMethodField()
    date_last_contrib = serializers.SerializerMethodField()
    activation_key = serializers.SerializerMethodField()
    newsletter_opt_in = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source="user.is_active")
    nb_erps = serializers.IntegerField(source="nb_erp_created")
    nb_erps_administrator = serializers.IntegerField(source="nb_erp_administrator")
    average_completion_rate = serializers.SerializerMethodField()
    nom = serializers.CharField(source="user.last_name")
    prenom = serializers.CharField(source="user.first_name")

    class Meta:
        model = UserStats
        fields = (
            "nb_erps",
            "nb_erps_administrator",
            "average_completion_rate",
            "date_joined",
            "date_last_login",
            "date_last_contrib",
            "is_active",
            "activation_key",
            "newsletter_opt_in",
            "nom",
            "prenom",
        )

    def get_date_last_login(self, instance):
        return instance.user.last_login.strftime("%Y-%m-%d") if instance.user.last_login else ""

    def get_date_last_contrib(self, instance):
        last = Revision.objects.filter(user_id=instance.user_id).order_by("date_created").last()
        return last.date_created.strftime("%Y-%m-%d") if last else ""

    def get_average_completion_rate(self, instance):
        from erp.models import Accessibilite  # noqa

        avg = Accessibilite.objects.filter(erp__user=instance.user).aggregate(avg=Avg("completion_rate"))["avg"]
        return float(f"{avg:.2f}") if avg else 0

    def get_date_joined(self, instance):
        return instance.user.last_login.strftime("%Y-%m-%d")

    def get_activation_key(self, instance):
        return RegistrationView().get_activation_key(instance.user) if not instance.user.is_active else ""

    def get_newsletter_opt_in(self, instance):
        return instance.user.preferences.get().newsletter_opt_in

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {k.upper(): v for k, v in representation.items()}
