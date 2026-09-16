from django.utils.translation import gettext as translate
from rest_framework import permissions

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class CanModifyErp(permissions.BasePermission):
    message = translate("Cet établissement est labellisé RPA et ne peut être modifié que par son gestionnaire.")

    def has_permission(self, request, view):
        # Write is allowed for all by design, only blocked for RPA ERPs, see has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.can_be_modified_by(request.user)
