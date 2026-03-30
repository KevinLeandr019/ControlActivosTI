from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import CustomLoginView

app_name = "accounts"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="accounts:login"), name="logout"),
]