from django.urls import path

from .views import (
    AsignacionCreateView,
    AsignacionDevolucionView,
    AsignacionListView,
)

app_name = "asignaciones"

urlpatterns = [
    path("", AsignacionListView.as_view(), name="lista"),
    path("nueva/", AsignacionCreateView.as_view(), name="nueva"),
    path("<int:pk>/devolver/", AsignacionDevolucionView.as_view(), name="devolver"),
]
