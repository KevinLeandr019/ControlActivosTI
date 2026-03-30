from django.urls import path

from .views import ColaboradorDetailView, ColaboradorListView

app_name = "colaboradores"

urlpatterns = [
    path("", ColaboradorListView.as_view(), name="lista"),
    path("<int:pk>/", ColaboradorDetailView.as_view(), name="detalle"),
]