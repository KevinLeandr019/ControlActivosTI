from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import Activo, EventoActivo, FotoActivo, TIPOS_ACTIVO_CON_ESPECIFICACIONES


class ActivoAdminForm(forms.ModelForm):
    campos_tecnicos = ("cpu", "ram", "disco", "sistema_operativo")

    class Meta:
        model = Activo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre_campo in self.campos_tecnicos:
            self.fields[nombre_campo].required = False

        self.fields["cpu"].help_text = "Solo aplica para laptops, PC o equipos de escritorio."
        self.fields["ram"].help_text = "Solo aplica para laptops, PC o equipos de escritorio."
        self.fields["disco"].help_text = "Solo aplica para laptops, PC o equipos de escritorio."
        self.fields["sistema_operativo"].help_text = "Solo aplica para laptops, PC o equipos de escritorio."

    def clean(self):
        cleaned_data = super().clean()
        tipo_activo = cleaned_data.get("tipo_activo")
        nombre_tipo = (tipo_activo.nombre if tipo_activo else "").strip().lower()
        requiere_especificaciones = any(
            clave in nombre_tipo
            for clave in TIPOS_ACTIVO_CON_ESPECIFICACIONES
        )

        if not requiere_especificaciones:
            for nombre_campo in self.campos_tecnicos:
                cleaned_data[nombre_campo] = ""

        return cleaned_data


class FotoActivoInlineForm(forms.ModelForm):
    class Meta:
        model = FotoActivo
        fields = "__all__"

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if self.instance.pk and not imagen:
            return self.instance.imagen
        return imagen


class FotoActivoInline(admin.TabularInline):
    model = FotoActivo
    form = FotoActivoInlineForm
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
    form = ActivoAdminForm
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

    class Media:
        js = ("admin/activos/activo_admin.js",)

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
