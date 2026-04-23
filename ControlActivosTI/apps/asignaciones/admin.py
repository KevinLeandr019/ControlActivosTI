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
        "mostrar_ceco",
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
        "centro_costo",
    )
    search_fields = (
        "codigo_asignacion",
        "colaborador__nombres",
        "colaborador__apellidos",
        "colaborador__cedula",
        "centro_costo_codigo",
        "centro_costo_nombre",
        "detalles__activo__codigo",
        "detalles__activo__serie",
    )
    readonly_fields = (
        "codigo_asignacion",
        "centro_costo",
        "centro_costo_codigo",
        "centro_costo_nombre",
        "centro_costo_empresa",
        "mostrar_ceco",
        "created_at",
        "updated_at",
    )
    list_select_related = ("colaborador", "centro_costo", "usuario_responsable", "usuario_recepcion")
    inlines = [AsignacionDetalleInline]

    fieldsets = (
        (
            "Asignacion",
            {
                "fields": (
                    "codigo_asignacion",
                    "colaborador",
                    "fecha_asignacion",
                    "usuario_responsable",
                    "estado_asignacion",
                    "observaciones_entrega",
                )
            },
        ),
        (
            "CECO historico",
            {
                "fields": (
                    "mostrar_ceco",
                    "centro_costo",
                    "centro_costo_codigo",
                    "centro_costo_nombre",
                    "centro_costo_empresa",
                )
            },
        ),
        (
            "Devolucion",
            {
                "fields": (
                    "fecha_devolucion",
                    "usuario_recepcion",
                    "observaciones_devolucion",
                )
            },
        ),
        (
            "Auditoria",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Total activos")
    def mostrar_total_activos(self, obj):
        return obj.total_activos

    @admin.display(description="Activos")
    def mostrar_activos(self, obj):
        return obj.resumen_activos or "-"

    @admin.display(description="CECO")
    def mostrar_ceco(self, obj):
        return obj.centro_costo_snapshot


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
