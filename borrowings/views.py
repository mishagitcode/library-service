from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingCreateSerializer, BorrowingSerializer
from borrowings.services import process_borrowing_return


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = (
        Borrowing.objects.select_related("book", "user")
        .prefetch_related("payments")
        .all()
    )
    permission_classes = (IsAuthenticated,)
    http_method_names = ["get", "post"]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if not user.is_staff:
            queryset = queryset.filter(user=user)
        elif user_id:
            queryset = queryset.filter(user_id=user_id)

        if is_active is not None:
            normalized_value = is_active.strip().lower()
            queryset = queryset.filter(
                actual_return_date__isnull=normalized_value in {"1", "true", "yes"}
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        borrowing = serializer.save()
        output_serializer = BorrowingSerializer(borrowing, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        borrowing = process_borrowing_return(borrowing)
        serializer = BorrowingSerializer(borrowing, context={"request": request})
        return Response(serializer.data)
