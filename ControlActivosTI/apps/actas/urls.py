from django.urls import path

from .views import DescargarActaPorAsignacionView

app_name = "actas"

urlpatterns = [
    path(
        "asignacion/<int:asignacion_id>/<str:tipo>/descargar/",
        DescargarActaPorAsignacionView.as_view(),
        name="descargar_por_asignacion",
    ),
]
