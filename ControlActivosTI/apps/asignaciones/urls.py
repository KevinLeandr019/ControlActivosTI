from django.urls import path

from .views import (
    AsignacionCreateView,
    AsignacionDevolucionView,
    AsignacionDetailView,
    AsignacionListView,
)

app_name = "asignaciones"

urlpatterns = [
    path("", AsignacionListView.as_view(), name="lista"),
    path("<int:pk>/", AsignacionDetailView.as_view(), name="detalle"),
    path("devolver/<int:pk>/", AsignacionDevolucionView.as_view(), name="devolver"),
    path("nueva/", AsignacionCreateView.as_view(), name="nueva"),
]
