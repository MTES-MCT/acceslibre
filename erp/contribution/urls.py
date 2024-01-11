from django.urls import path

from .views import (
    AdditionalContributionStepView,
    ContributionStepView,
    contribution_additional_success_view,
    contribution_base_success_view,
)

urlpatterns = [
    path(
        "step/<str:erp_slug>/<int:step_number>",
        ContributionStepView.as_view(),
        name="contribution-step",
    ),
    path(
        "step/additional/<str:erp_slug>/<int:step_number>",
        AdditionalContributionStepView.as_view(),
        name="contribution-additional-step",
    ),
    path("<str:erp_slug>/base/success", contribution_base_success_view, name="contribution-base-success"),
    path(
        "<str:erp_slug>/additional/success",
        contribution_additional_success_view,
        name="contribution-additional-success",
    ),
]
