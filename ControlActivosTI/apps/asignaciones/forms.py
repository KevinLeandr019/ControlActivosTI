from django import forms
from django.utils import timezone

from apps.catalogos.models import EstadoActivo
from apps.colaboradores.models import Colaborador
from .models import Asignacion


class AsignacionCreateForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = [
            "colaborador",
            "activo",
            "fecha_asignacion",
            "observaciones_entrega",
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

        self.fields["activo"].queryset = (
            self._meta.model._meta.get_field("activo")
            .related_model.objects.select_related("tipo_activo", "estado_activo")
            .filter(estado_activo__permite_asignacion=True)
            .order_by("codigo")
        )

        self.fields["fecha_asignacion"].initial = timezone.localdate()

        base_class = (
            "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
            "shadow-sm outline-none transition duration-200 "
            "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
        )
        textarea_class = (
            "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
            "shadow-sm outline-none transition duration-200 resize-none "
            "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
        )

        for _, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = textarea_class
            else:
                field.widget.attrs["class"] = base_class


class AsignacionDevolucionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = [
            "fecha_devolucion",
            "estado_activo_devolucion",
            "observaciones_devolucion",
        ]
        widgets = {
            "fecha_devolucion": forms.DateInput(attrs={"type": "date"}),
            "observaciones_devolucion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["fecha_devolucion"].initial = timezone.localdate()
        self.fields["estado_activo_devolucion"].queryset = (
            EstadoActivo.objects.filter(activo=True)
            .exclude(nombre__iexact="Asignado")
            .order_by("nombre")
        )

        base_class = (
            "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
            "shadow-sm outline-none transition duration-200 "
            "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
        )
        textarea_class = (
            "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 "
            "shadow-sm outline-none transition duration-200 resize-none "
            "focus:border-cyan-500 focus:ring-4 focus:ring-cyan-100"
        )

        self.fields["fecha_devolucion"].widget.attrs["class"] = base_class
        self.fields["estado_activo_devolucion"].widget.attrs["class"] = base_class
        self.fields["observaciones_devolucion"].widget.attrs["class"] = textarea_class

        # Importante: esta pantalla ya representa el cierre de la asignación
        self.instance.estado_asignacion = Asignacion.EstadoAsignacion.CERRADA

        if self.user and self.user.is_authenticated:
            self.instance.usuario_recepcion = self.user

    def clean_fecha_devolucion(self):
        fecha_devolucion = self.cleaned_data["fecha_devolucion"]

        if self.instance.fecha_asignacion and fecha_devolucion < self.instance.fecha_asignacion:
            raise forms.ValidationError(
                "La fecha de devolución no puede ser anterior a la fecha de asignación."
            )

        return fecha_devolucion

    def save(self, commit=True):
        asignacion = super().save(commit=False)
        asignacion.estado_asignacion = Asignacion.EstadoAsignacion.CERRADA

        if self.user and self.user.is_authenticated:
            asignacion.usuario_recepcion = self.user

        if commit:
            asignacion.save()

        return asignacion