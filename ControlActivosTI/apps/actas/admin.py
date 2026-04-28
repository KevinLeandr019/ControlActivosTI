from django.contrib import admin

from .models import ActaEntrega


@admin.register(ActaEntrega)
class ActaEntregaAdmin(admin.ModelAdmin):
    list_display = (
        "asignacion",
        "devolucion",
        "tipo",
        "nombre_archivo",
        "version_plantilla",
        "usuario_generador",
        "fecha_generacion",
    )
    search_fields = (
        "asignacion__codigo_asignacion",
        "asignacion__detalles__activo__codigo",
        "asignacion__detalles__activo__serie",
        "asignacion__colaborador__nombres",
        "asignacion__colaborador__apellidos",
        "nombre_archivo",
    )
    list_filter = ("tipo", "version_plantilla", "fecha_generacion")
    list_select_related = ("asignacion", "devolucion", "usuario_generador")
