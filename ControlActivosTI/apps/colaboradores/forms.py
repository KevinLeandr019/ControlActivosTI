from django import forms

from apps.catalogos.models import Area, Cargo, CentroCosto, Empresa, Ubicacion

from .models import Colaborador


BASE_CLASS = (
    "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
    "shadow-sm outline-none transition duration-200 "
    "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
)
TEXTAREA_CLASS = (
    "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
    "shadow-sm outline-none transition duration-200 resize-none "
    "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
)


class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = [
            "nombres",
            "apellidos",
            "cedula",
            "correo_corporativo",
            "empresa",
            "cargo",
            "area",
            "ubicacion",
            "centro_costo",
            "estado",
            "fecha_ingreso",
            "observaciones",
        ]
        widgets = {
            "fecha_ingreso": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empresa"].queryset = Empresa.objects.filter(activo=True).order_by("nombre")
        self.fields["cargo"].queryset = Cargo.objects.filter(activo=True).order_by("nombre")
        self.fields["area"].queryset = Area.objects.filter(activo=True).order_by("nombre")
        self.fields["ubicacion"].queryset = Ubicacion.objects.filter(activo=True).order_by("nombre")
        self.fields["centro_costo"].queryset = (
            CentroCosto.objects.filter(activo=True).order_by("codigo")
        )
        self.fields["estado"].initial = Colaborador.EstadoColaborador.ACTIVO

        etiquetas = {
            "nombres": "Nombres",
            "apellidos": "Apellidos",
            "cedula": "Cédula",
            "correo_corporativo": "Correo corporativo",
            "empresa": "Empresa",
            "cargo": "Cargo",
            "area": "Área",
            "ubicacion": "Ubicación",
            "centro_costo": "Centro de costo",
            "estado": "Estado",
            "fecha_ingreso": "Fecha de ingreso",
            "observaciones": "Observaciones",
        }

        for nombre_campo, etiqueta in etiquetas.items():
            if nombre_campo in self.fields:
                self.fields[nombre_campo].label = etiqueta

        for nombre_campo, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = TEXTAREA_CLASS
            else:
                field.widget.attrs["class"] = BASE_CLASS

