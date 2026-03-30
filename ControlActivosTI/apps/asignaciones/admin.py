from django.contrib import admin

from .models import Asignacion


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = (
        "activo",
        "colaborador",
        "fecha_asignacion",
        "estado_asignacion",
        "usuario_responsable",
        "fecha_devolucion",
    )
    search_fields = (
        "activo__codigo",
        "activo__serie",
        "colaborador__nombres",
        "colaborador__apellidos",
        "colaborador__cedula",
        "colaborador__correo_corporativo",
    )
    list_filter = (
        "estado_asignacion",
        "fecha_asignacion",
        "fecha_devolucion",
        "colaborador__area",
    )
    list_select_related = (
        "activo",
        "colaborador",
        "usuario_responsable",
        "usuario_recepcion",
        "estado_activo_devolucion",
    )