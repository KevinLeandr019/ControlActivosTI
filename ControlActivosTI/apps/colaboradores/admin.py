from django.contrib import admin

from .models import Colaborador


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = (
        "apellidos",
        "nombres",
        "cedula",
        "correo_corporativo",
        "empresa",
        "area",
        "cargo",
        "ubicacion",
        "centro_costo",
        "estado",
        "fecha_ingreso",
    )
    search_fields = (
        "nombres",
        "apellidos",
        "cedula",
        "correo_corporativo",
        "centro_costo__codigo",
        "centro_costo__nombre",
    )
    list_filter = ("estado", "empresa", "area", "cargo", "ubicacion", "centro_costo")
    list_select_related = ("empresa", "area", "cargo", "ubicacion", "centro_costo")
    autocomplete_fields = ("empresa", "area", "cargo", "ubicacion", "centro_costo")
