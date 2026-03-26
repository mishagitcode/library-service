from django.urls import path

from payments.views import (
    PaymentCancelView,
    PaymentDetailView,
    PaymentListView,
    PaymentSuccessView,
)

app_name = "payments"

urlpatterns = [
    path("", PaymentListView.as_view(), name="list"),
    path("<int:pk>/", PaymentDetailView.as_view(), name="detail"),
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
]
