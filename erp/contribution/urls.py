from django.urls import path

from .views import ContributionStepView
urlpatterns = [
    path(
        "step/<str:erp_slug>/<int:step_number>",
        ContributionStepView.as_view(),
        name="contribution-step",
    ),
    ]
