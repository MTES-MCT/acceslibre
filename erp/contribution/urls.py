from django.urls import path

from .views import ContributionStepView, contribution_base_success_view

urlpatterns = [
    path(
        "step/<str:erp_slug>/<int:step_number>",
        ContributionStepView.as_view(),
        name="contribution-step",
    ),
    path("<str:erp_slug>/base/success", contribution_base_success_view, name="contribution-base-success"),
]
