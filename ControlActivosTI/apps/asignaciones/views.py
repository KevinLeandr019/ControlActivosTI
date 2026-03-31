from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import AsignacionCreateForm, AsignacionDevolucionForm
from .models import Asignacion


class AsignacionListView(LoginRequiredMixin, ListView):
    model = Asignacion
    template_name = "asignaciones/lista.html"
    context_object_name = "asignaciones"
    paginate_by = 10

    def get_queryset(self):
        return (
            Asignacion.objects.select_related(
                "activo",
                "activo__tipo_activo",
                "activo__estado_activo",
                "colaborador",
                "colaborador__cargo",
                "usuario_responsable",
                "usuario_recepcion",
                "estado_activo_devolucion",
            )
            .order_by("-fecha_asignacion", "-id")
        )


class AsignacionCreateView(LoginRequiredMixin, CreateView):
    model = Asignacion
    form_class = AsignacionCreateForm
    template_name = "asignaciones/formulario.html"
    success_url = reverse_lazy("asignaciones:lista")

    def form_valid(self, form):
        form.instance.usuario_responsable = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"La asignación {self.object.codigo_asignacion} fue creada correctamente.",
        )
        return response


class AsignacionDevolucionView(LoginRequiredMixin, UpdateView):
    model = Asignacion
    form_class = AsignacionDevolucionForm
    template_name = "asignaciones/devolucion.html"
    success_url = reverse_lazy("asignaciones:lista")

    def get_queryset(self):
        return Asignacion.objects.select_related(
            "activo",
            "colaborador",
            "usuario_responsable",
        ).filter(
            estado_asignacion=Asignacion.EstadoAsignacion.ACTIVA
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            f"La devolución de {self.object.codigo_asignacion} fue registrada correctamente.",
        )
        return HttpResponseRedirect(self.get_success_url())