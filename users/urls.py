from django.urls import path

from users.views import CreateTokenView, CreateUserView, ManageUserView, RefreshTokenView

app_name = "users"

urlpatterns = [
    path("", CreateUserView.as_view(), name="create"),
    path("token/", CreateTokenView.as_view(), name="token"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("me/", ManageUserView.as_view(), name="me"),
]
