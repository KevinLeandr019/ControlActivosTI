from django import forms
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone

from apps.activos.models import Activo
from apps.catalogos.models import EstadoActivo
from apps.colaboradores.models import Colaborador

from .models import Asignacion, AsignacionDetalle


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


class AsignacionCreateForm(forms.ModelForm):
    activos = forms.ModelMultipleChoiceField(
        queryset=Activo.objects.none(),
        widget=forms.SelectMultiple(attrs={"size": 10}),
        label="Activos",
    )

    class Meta:
        model = Asignacion
        fields = [
            "colaborador",
            "fecha_asignacion",
            "observaciones_entrega",
            "activos",
        ]
        widgets = {
            "fecha_asignacion": forms.DateInput(attrs={"type": "date"}),
            "observaciones_entrega": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["colaborador"].queryset = (
            Colaborador.objects.select_related("area", "cargo")
            .filter(estado=Colaborador.EstadoColaborador.ACTIVO)
            .order_by("apellidos", "nombres")
        )
        self.fields["activos"].queryset = (
            Activo.objects.select_related("tipo_activo", "estado_activo")
            .filter(estado_activo__permite_asignacion=True)
            .order_by("codigo")
        )
        self.fields["fecha_asignacion"].initial = timezone.localdate()

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = TEXTAREA_CLASS
            else:
                field.widget.attrs["class"] = BASE_CLASS
            if name == "activos":
                field.help_text = "Mantén presionada Ctrl para seleccionar varios activos."

    def clean_activos(self):
        activos = self.cleaned_data.get("activos")
        if not activos:
            raise forms.ValidationError("Debes seleccionar al menos un activo.")
        return activos

    def save(self, commit=True):
        if not commit:
            raise ValueError("AsignacionCreateForm requiere commit=True.")

        activos = list(self.cleaned_data.pop("activos"))

        with transaction.atomic():
            asignacion = super().save(commit=True)
            for orden, activo in enumerate(activos, start=1):
                AsignacionDetalle.objects.create(
                    asignacion=asignacion,
                    activo=activo,
                    orden=orden,
                )
        return asignacion


class AsignacionDevolucionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = [
            "fecha_devolucion",
            "observaciones_devolucion",
        ]
        widgets = {
            "fecha_devolucion": forms.DateInput(attrs={"type": "date"}),
            "observaciones_devolucion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_devolucion"].initial = timezone.localdate()
        self.fields["fecha_devolucion"].widget.attrs["class"] = BASE_CLASS
        self.fields["observaciones_devolucion"].widget.attrs["class"] = TEXTAREA_CLASS

    def clean_fecha_devolucion(self):
        fecha_devolucion = self.cleaned_data["fecha_devolucion"]
        if self.instance.fecha_asignacion and fecha_devolucion < self.instance.fecha_asignacion:
            raise forms.ValidationError(
                "La fecha de devolución no puede ser anterior a la fecha de asignación."
            )
        return fecha_devolucion


class AsignacionDetalleDevolucionForm(forms.ModelForm):
    class Meta:
        model = AsignacionDetalle
        fields = ["estado_activo_devolucion", "observaciones_devolucion"]
        widgets = {
            "observaciones_devolucion": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estado_activo_devolucion"].queryset = (
            EstadoActivo.objects.filter(activo=True)
            .exclude(nombre__iexact="Asignado")
            .order_by("nombre")
        )
        self.fields["estado_activo_devolucion"].widget.attrs["class"] = BASE_CLASS
        self.fields["observaciones_devolucion"].widget.attrs["class"] = TEXTAREA_CLASS


AsignacionDetalleDevolucionFormSet = inlineformset_factory(
    Asignacion,
    AsignacionDetalle,
    form=AsignacionDetalleDevolucionForm,
    extra=0,
    can_delete=False,
)
