from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.services import mark_payment_as_paid


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "borrowing",
            "borrowing__book",
            "borrowing__user",
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(borrowing__user=self.request.user)


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Payment.objects.select_related(
            "borrowing",
            "borrowing__book",
            "borrowing__user",
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(borrowing__user=self.request.user)


class PaymentSuccessView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "session_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.filter(session_id=session_id).first()
        if payment is None:
            return Response(
                {"detail": "Payment session was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment = mark_payment_as_paid(payment)
        if payment.status != Payment.StatusChoices.PAID:
            return Response(
                {
                    "message": "Payment session exists but Stripe has not marked it as paid yet.",
                    "payment_id": payment.id,
                    "status": payment.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Payment was processed successfully.",
                "payment_id": payment.id,
                "status": payment.status,
            }
        )


class PaymentCancelView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "message": (
                    "Payment was canceled or paused. "
                    "You can use the stored session URL to complete it later."
                )
            }
        )
