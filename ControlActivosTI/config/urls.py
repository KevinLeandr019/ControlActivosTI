from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import InicioView

admin.site.site_header = "ControlActivosTI"
admin.site.site_title = "ControlActivosTI Admin"
admin.site.index_title = "Administración interna"

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", InicioView.as_view(), name="inicio-raiz"),
    path("dashboard/", InicioView.as_view(), name="dashboard-inicio"),

    path("cuentas/", include("apps.accounts.urls")),
    path("activos/", include("apps.activos.urls")),
    path("colaboradores/", include("apps.colaboradores.urls")),
    path("asignaciones/", include("apps.asignaciones.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)