from django.contrib import admin

from .models import (
    Area,
    Cargo,
    CentroCosto,
    Empresa,
    Ubicacion,
    TipoActivo,
    EstadoActivo,
    TipoEventoActivo,
)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "empresa",
        "padre",
        "tipo",
        "responsable",
        "acepta_asignaciones",
        "activo",
        "fecha_inicio",
        "fecha_fin",
    )
    search_fields = (
        "codigo",
        "nombre",
        "empresa__nombre",
        "padre__codigo",
        "padre__nombre",
    )
    list_filter = (
        "activo",
        "acepta_asignaciones",
        "tipo",
        "empresa",
    )
    list_select_related = ("empresa", "padre", "responsable")
    autocomplete_fields = ("empresa", "padre", "responsable")
    readonly_fields = ("created_at", "updated_at", "mostrar_ruta_jerarquia")
    fieldsets = (
        (
            "Datos maestros",
            {
                "fields": (
                    "codigo",
                    "nombre",
                    "empresa",
                    "tipo",
                    "padre",
                    "mostrar_ruta_jerarquia",
                    "responsable",
                )
            },
        ),
        (
            "Control operativo",
            {
                "fields": (
                    "activo",
                    "acepta_asignaciones",
                    "fecha_inicio",
                    "fecha_fin",
                    "descripcion",
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

    @admin.display(description="Ruta jerarquica")
    def mostrar_ruta_jerarquia(self, obj):
        return obj.ruta_jerarquia if obj.pk else "-"


@admin.register(TipoActivo)
class TipoActivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(EstadoActivo)
class EstadoActivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "permite_asignacion", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("permite_asignacion", "activo")


@admin.register(TipoEventoActivo)
class TipoEventoActivoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)
