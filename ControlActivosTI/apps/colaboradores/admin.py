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
        "estado",
        "fecha_ingreso",
    )
    search_fields = (
        "nombres",
        "apellidos",
        "cedula",
        "correo_corporativo",
    )
    list_filter = ("estado", "empresa", "area", "cargo", "ubicacion")
    list_select_related = ("empresa", "area", "cargo", "ubicacion")