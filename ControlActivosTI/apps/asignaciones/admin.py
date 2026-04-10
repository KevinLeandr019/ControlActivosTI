from django.contrib import admin

from .models import Asignacion, AsignacionDetalle


class AsignacionDetalleInline(admin.TabularInline):
    model = AsignacionDetalle
    extra = 0
    fields = (
        "activo",
        "orden",
        "activa",
        "estado_activo_devolucion",
        "observaciones_linea",
        "observaciones_devolucion",
    )
    raw_id_fields = ("activo", "estado_activo_devolucion")


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_asignacion",
        "colaborador",
        "estado_asignacion",
        "fecha_asignacion",
        "mostrar_total_activos",
        "mostrar_activos",
        "usuario_responsable",
        "fecha_devolucion",
    )
    list_filter = (
        "estado_asignacion",
        "fecha_asignacion",
        "fecha_devolucion",
    )
    search_fields = (
        "codigo_asignacion",
        "colaborador__nombres",
        "colaborador__apellidos",
        "colaborador__cedula",
        "detalles__activo__codigo",
        "detalles__activo__serie",
    )
    readonly_fields = (
        "codigo_asignacion",
        "created_at",
        "updated_at",
    )
    inlines = [AsignacionDetalleInline]

    @admin.display(description="Total activos")
    def mostrar_total_activos(self, obj):
        return obj.total_activos

    @admin.display(description="Activos")
    def mostrar_activos(self, obj):
        return obj.resumen_activos or "-"


@admin.register(AsignacionDetalle)
class AsignacionDetalleAdmin(admin.ModelAdmin):
    list_display = (
        "asignacion",
        "activo",
        "orden",
        "activa",
        "estado_activo_devolucion",
        "updated_at",
    )
    list_filter = (
        "activa",
        "estado_activo_devolucion",
    )
    search_fields = (
        "asignacion__codigo_asignacion",
        "activo__codigo",
        "activo__serie",
        "activo__modelo",
    )
    raw_id_fields = (
        "asignacion",
        "activo",
        "estado_activo_devolucion",
    )