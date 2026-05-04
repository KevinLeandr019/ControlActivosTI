from django.urls import path

from .views import ColaboradorCreateView, ColaboradorDetailView, ColaboradorListView

app_name = "colaboradores"

urlpatterns = [
    path("", ColaboradorListView.as_view(), name="lista"),
    path("nuevo/", ColaboradorCreateView.as_view(), name="nuevo"),
    path("<int:pk>/", ColaboradorDetailView.as_view(), name="detalle"),
]
