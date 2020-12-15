from django.urls import path

from subscription import views

urlpatterns = [
    path(
        "subscribe/erp/<str:erp_slug>/",
        views.subscribe_erp,
        name="subscribe_erp",
    ),
    path(
        "unsubscribe/erp/<str:erp_slug>/",
        views.unsubscribe_erp,
        name="unsubscribe_erp",
    ),
]
