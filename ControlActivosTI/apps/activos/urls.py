from django.urls import path

from .views import ActivoListView, ActivoDetailView

app_name = "activos"

urlpatterns = [
    path("", ActivoListView.as_view(), name="lista"),
    path("<int:pk>/", ActivoDetailView.as_view(), name="detalle"),
]