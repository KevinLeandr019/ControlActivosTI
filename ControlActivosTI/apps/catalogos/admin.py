from django import forms
from django.contrib import admin

from .models import (
    Area,
    Cargo,
    CentroCosto,
    DepartamentoEmpresa,
    Empresa,
    Ubicacion,
    TipoActivo,
    EstadoActivo,
    TipoEventoActivo,
)


class CentroCostoAdminForm(forms.ModelForm):
    class Meta:
        model = CentroCosto
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "departamentos" in self.fields:
            departamentos = DepartamentoEmpresa.objects.select_related("empresa").filter(activo=True)
            empresa_id = self.data.get("empresa") if self.is_bound else None

            if empresa_id:
                departamentos = departamentos.filter(empresa_id=empresa_id)
            elif self.instance and self.instance.pk and self.instance.empresa_id:
                departamentos = departamentos.filter(empresa_id=self.instance.empresa_id)

            self.fields["departamentos"].queryset = departamentos.order_by("empresa__nombre", "nombre")

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get("empresa")
        departamentos = cleaned_data.get("departamentos")

        if departamentos and not empresa:
            self.add_error("empresa", "Debes seleccionar una empresa antes de asignar departamentos.")
            return cleaned_data

        if empresa and departamentos:
            departamentos_invalidos = [
                departamento.nombre
                for departamento in departamentos
                if departamento.empresa_id != empresa.id
            ]
            if departamentos_invalidos:
                nombres = ", ".join(departamentos_invalidos)
                self.add_error(
                    "departamentos",
                    (
                        "Todos los departamentos deben pertenecer a la misma empresa del CECO. "
                        f"No corresponden a {empresa.nombre}: {nombres}."
                    ),
                )

        return cleaned_data


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


@admin.register(DepartamentoEmpresa)
class DepartamentoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "activo", "created_at")
    search_fields = ("nombre", "empresa__nombre")
    list_filter = ("empresa", "activo")
    list_select_related = ("empresa",)
    autocomplete_fields = ("empresa",)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "created_at")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    form = CentroCostoAdminForm
    list_display = (
        "codigo",
        "nombre",
        "empresa",
        "mostrar_departamentos",
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
        "departamentos__nombre",
        "padre__codigo",
        "padre__nombre",
    )
    list_filter = (
        "activo",
        "acepta_asignaciones",
        "tipo",
        "empresa",
        "departamentos",
    )
    list_select_related = ("empresa", "padre", "responsable")
    autocomplete_fields = ("empresa", "padre", "responsable", "departamentos")
    readonly_fields = ("created_at", "updated_at", "mostrar_ruta_jerarquia", "mostrar_departamentos")
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
                    "departamentos",
                    "mostrar_departamentos",
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

    @admin.display(description="Departamentos incluidos")
    def mostrar_departamentos(self, obj):
        return obj.departamentos_resumen if obj.pk else "-"


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
