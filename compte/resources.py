from django.contrib.auth.models import User
from import_export import resources
from import_export.fields import Field


class UserAdminResource(resources.ModelResource):
    erp_count_published = Field()
    erp_count_total = Field()
    vote_count = Field()

    class Meta:
        model = User
        skip_unchanged = True
        fields = [
            "username",
            "email",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
        ]
        export_order = fields + ["erp_count_published", "erp_count_total", "vote_count"]

    def dehydrate_erp_count_published(self, user):
        return user.erp_count_published

    def dehydrate_count_total(self, user):
        return user.erp_count_total

    def dehydrate_vote_count(self, user):
        return user.vote_count
