from django.contrib import admin
from django.utils.html import format_html

from .models import Activo, FotoActivo, EventoActivo


class FotoActivoInline(admin.TabularInline):
    model = FotoActivo
    extra = 1
    max_num = 5
    fields = ("imagen", "vista_previa", "descripcion", "orden")
    readonly_fields = ("vista_previa",)

    def vista_previa(self, obj):
        if obj.pk and obj.imagen:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 120px; border-radius: 6px;" />',
                obj.imagen.url
            )
        return "Sin imagen"

    vista_previa.short_description = "Vista previa"


@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "tipo_activo",
        "marca",
        "modelo",
        "serie",
        "fecha_compra",
        "valor",
        "estado_activo",
        "sistema_operativo",
        "cantidad_fotos",
        "miniatura_principal",
    )
    search_fields = (
        "codigo",
        "marca",
        "modelo",
        "serie",
        "cpu",
        "ram",
        "disco",
    )
    list_filter = (
        "tipo_activo",
        "estado_activo",
        "marca",
        "sistema_operativo",
        "fecha_compra",
    )
    list_select_related = ("tipo_activo", "estado_activo")
    inlines = [FotoActivoInline]

    def miniatura_principal(self, obj):
        primera_foto = obj.fotos.order_by("orden", "id").first()
        if primera_foto and primera_foto.imagen:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; border-radius: 4px;" />',
                primera_foto.imagen.url
            )
        return "Sin imagen"

    miniatura_principal.short_description = "Imagen"

    def cantidad_fotos(self, obj):
        return obj.fotos.count()

    cantidad_fotos.short_description = "Fotos"


@admin.register(EventoActivo)
class EventoActivoAdmin(admin.ModelAdmin):
    list_display = (
        "activo",
        "tipo_evento",
        "fecha_evento",
        "usuario_responsable",
    )
    search_fields = (
        "activo__codigo",
        "activo__serie",
        "tipo_evento__nombre",
        "detalle",
    )
    list_filter = ("tipo_evento", "fecha_evento")
    list_select_related = ("activo", "tipo_evento", "usuario_responsable")